import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import UserRole
from apps.admin_api.services.analytics import build_admin_analytics
from apps.payments.models import BillingInterval, SubscriptionPlan, UserSubscription
from apps.payments.models import SubscriptionStatus as PaymentsSubscriptionStatus

# Reuses the make_question() fixture helper from apps.questions.tests
# rather than duplicating the taxonomy + Question setup boilerplate here —
# cross-app test-helper reuse, not a production code dependency (same
# pattern apps.quizzes.tests already establishes).
from apps.questions.models import Question, QuestionType
from apps.questions.tests import make_question
from apps.quizzes.models import QuizSession, QuizSessionQuestion, StudentResponseLog
from apps.taxonomy.models import NursingSystem

User = get_user_model()


def _make_session_with_response(student, question, *, is_correct, is_complete=True):
    """
    Local helper mirroring apps.quizzes.tests._make_session — builds one
    QuizSession with exactly one graded response, which is the minimum
    fixture every analytics aggregation test below needs.
    """
    session = QuizSession.objects.create(student=student, is_complete=is_complete)
    QuizSessionQuestion.objects.create(quiz_session=session, question=question, position=0)
    StudentResponseLog.objects.create(
        student=student,
        question=question,
        is_correct=is_correct,
        time_taken_seconds=30,
        quiz_session=session,
    )
    return session


class AnalyticsEmptyDatabaseTests(APITestCase):
    """
    The single most valuable analytics test: every aggregate must survive
    a database with zero users/sessions/logs/subscriptions without a
    ZeroDivisionError, a None reaching a non-nullable serializer field, or
    a fabricated number standing in for "no data yet".
    """

    def setUp(self):
        self.superuser = User.objects.create_user(
            email="root@example.com",
            password="a-strong-password-123",
            is_active=True,
            role=UserRole.SUPERUSER,
        )
        self.client.force_authenticate(self.superuser)

    def test_empty_database_returns_200_with_safe_defaults(self):
        response = self.client.get(reverse("admin-analytics"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_students"], 0)
        self.assertEqual(response.data["total_revenue"], "0.00")
        self.assertIsNone(response.data["mom_student_growth"])
        self.assertEqual(response.data["total_questions_answered"], 0)
        self.assertEqual(response.data["top_systems_by_attempts"], [])
        self.assertIsNone(response.data["avg_quiz_score"])
        self.assertEqual(response.data["completion_rate"], 0.0)
        self.assertEqual(response.data["weakest_systems"], [])
        self.assertTrue(response.data["revenue_series"]["is_sample"])
        self.assertEqual(len(response.data["revenue_series"]["points"]), 12)
        self.assertTrue(response.data["subscription_mix"]["is_sample"])


class AnalyticsAccessControlTests(APITestCase):
    """GET /api/admin/analytics/ is superuser-only — content_admin and student must both be rejected."""

    def setUp(self):
        self.student = User.objects.create_user(
            email="student@example.com", password="a-strong-password-123", is_active=True
        )
        self.content_admin = User.objects.create_user(
            email="content@example.com",
            password="a-strong-password-123",
            is_active=True,
            role=UserRole.CONTENT_ADMIN,
        )
        self.superuser = User.objects.create_user(
            email="root2@example.com",
            password="a-strong-password-123",
            is_active=True,
            role=UserRole.SUPERUSER,
        )

    def test_anonymous_is_unauthorized(self):
        response = self.client.get(reverse("admin-analytics"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student_is_forbidden(self):
        self.client.force_authenticate(self.student)
        response = self.client.get(reverse("admin-analytics"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_content_admin_is_forbidden(self):
        self.client.force_authenticate(self.content_admin)
        response = self.client.get(reverse("admin-analytics"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_superuser_is_allowed(self):
        self.client.force_authenticate(self.superuser)
        response = self.client.get(reverse("admin-analytics"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AnalyticsWithDataTests(TestCase):
    """
    Exercises build_admin_analytics() directly (not through the view) so
    these assertions are about the aggregation logic itself, independent
    of serialization or permissions — both already covered above.
    """

    def setUp(self):
        self.student_a = User.objects.create_user(email="a@example.com", password="a-strong-password-123")
        self.student_b = User.objects.create_user(email="b@example.com", password="a-strong-password-123")

    def test_total_students_excludes_non_student_roles(self):
        User.objects.create_user(
            email="admin@example.com", password="a-strong-password-123", role=UserRole.CONTENT_ADMIN
        )
        data = build_admin_analytics()
        # student_a and student_b default to STUDENT; the content admin
        # above must not be counted.
        self.assertEqual(data["total_students"], 2)

    def test_total_revenue_sums_only_active_and_trialing_subscriptions(self):
        plan = SubscriptionPlan.objects.create(name="Monthly", price="19.99", interval=BillingInterval.MONTH)
        UserSubscription.objects.create(
            user=self.student_a, plan=plan, status=PaymentsSubscriptionStatus.ACTIVE
        )
        UserSubscription.objects.create(
            user=self.student_b, plan=plan, status=PaymentsSubscriptionStatus.CANCELED
        )
        data = build_admin_analytics()
        # Only the ACTIVE subscription counts — CANCELED must not.
        self.assertEqual(str(data["total_revenue"]), "19.99")

    def test_top_systems_by_attempts_orders_by_attempt_count(self):
        busy_system = NursingSystem.objects.create(name="Cardiovascular Test System")
        quiet_system = NursingSystem.objects.create(name="Renal Test System")
        busy_question = make_question(nursing_system=busy_system, external_id="ANALYTICS-BUSY")
        quiet_question = make_question(nursing_system=quiet_system, external_id="ANALYTICS-QUIET")

        _make_session_with_response(self.student_a, busy_question, is_correct=True)
        _make_session_with_response(self.student_b, busy_question, is_correct=False)
        _make_session_with_response(self.student_a, quiet_question, is_correct=True)

        data = build_admin_analytics()
        by_name = {row["name"]: row["attempts"] for row in data["top_systems_by_attempts"]}
        self.assertEqual(by_name["Cardiovascular Test System"], 2)
        self.assertEqual(by_name["Renal Test System"], 1)

    def test_weakest_systems_excludes_systems_below_minimum_attempts(self):
        # One attempt, wrong: would score 0% and dominate "weakest" if the
        # minimum-attempts floor didn't exclude it.
        noisy_system = NursingSystem.objects.create(name="Noisy Test System")
        noisy_question = make_question(nursing_system=noisy_system, external_id="ANALYTICS-NOISY")
        _make_session_with_response(self.student_a, noisy_question, is_correct=False)

        data = build_admin_analytics()
        names = {row["name"] for row in data["weakest_systems"]}
        self.assertNotIn("Noisy Test System", names)

    def test_avg_quiz_score_is_mean_of_per_session_rates(self):
        question = make_question(external_id="ANALYTICS-SCORE")
        # Session 1: 1/1 correct = 100%. Session 2: 0/1 correct = 0%.
        # Mean-of-sessions gives 50%, whereas a flat correct/total ratio
        # over all StudentResponseLog rows would also give 50% here by
        # coincidence — the real distinguishing case is documented in the
        # service module; this test just pins the expected value.
        _make_session_with_response(self.student_a, question, is_correct=True)
        _make_session_with_response(self.student_b, question, is_correct=False)

        data = build_admin_analytics()
        self.assertEqual(data["avg_quiz_score"], 50.0)

    def test_completion_rate_counts_only_complete_sessions(self):
        question = make_question(external_id="ANALYTICS-COMPLETION")
        _make_session_with_response(self.student_a, question, is_correct=True, is_complete=True)
        _make_session_with_response(self.student_b, question, is_correct=True, is_complete=False)

        data = build_admin_analytics()
        self.assertEqual(data["completion_rate"], 50.0)

    def test_mom_growth_is_none_without_a_prior_month_baseline(self):
        # Both students in setUp joined "now" (auto_now_add), so there is
        # no prior-month cohort to compare against.
        data = build_admin_analytics()
        self.assertIsNone(data["mom_student_growth"])


class AdminQuestionListAccessControlTests(APITestCase):
    """GET /api/admin/questions/ is content_admin-or-above — student must be rejected, both admin roles allowed."""

    def setUp(self):
        self.student = User.objects.create_user(
            email="student3@example.com", password="a-strong-password-123", is_active=True
        )
        self.content_admin = User.objects.create_user(
            email="content3@example.com",
            password="a-strong-password-123",
            is_active=True,
            role=UserRole.CONTENT_ADMIN,
        )
        self.superuser = User.objects.create_user(
            email="root3@example.com",
            password="a-strong-password-123",
            is_active=True,
            role=UserRole.SUPERUSER,
        )

    def test_anonymous_is_unauthorized(self):
        response = self.client.get(reverse("admin-question-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student_is_forbidden(self):
        self.client.force_authenticate(self.student)
        response = self.client.get(reverse("admin-question-list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_content_admin_is_allowed(self):
        self.client.force_authenticate(self.content_admin)
        response = self.client.get(reverse("admin-question-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_superuser_is_allowed(self):
        self.client.force_authenticate(self.superuser)
        response = self.client.get(reverse("admin-question-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AdminQuestionListTests(APITestCase):
    def setUp(self):
        self.content_admin = User.objects.create_user(
            email="content4@example.com",
            password="a-strong-password-123",
            is_active=True,
            role=UserRole.CONTENT_ADMIN,
        )
        self.client.force_authenticate(self.content_admin)

    def test_includes_inactive_questions_unlike_the_student_facing_endpoint(self):
        # apps.questions.views.QuestionListView filters is_active=True; this
        # admin endpoint must NOT — an editor needs to see retired content
        # to manage it, not just what's currently live in quizzes.
        make_question(external_id="LIST-ACTIVE", is_active=True)
        make_question(external_id="LIST-INACTIVE", is_active=False)

        response = self.client.get(reverse("admin-question-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_page_size_is_20(self):
        for i in range(25):
            make_question(external_id=f"LIST-PAGE-{i}")
        response = self.client.get(reverse("admin-question-list"))
        self.assertEqual(len(response.data["results"]), 20)
        self.assertEqual(response.data["count"], 25)

    def test_stem_preview_is_truncated_to_80_chars(self):
        long_stem = "A" * 200
        make_question(external_id="LIST-LONGSTEM", stem=long_stem)
        response = self.client.get(reverse("admin-question-list"))
        self.assertEqual(len(response.data["results"][0]["stem_preview"]), 80)

    def test_filter_by_question_type(self):
        make_question(external_id="LIST-MCQ", question_type=QuestionType.MCQ)
        make_question(external_id="LIST-SATA", question_type=QuestionType.SATA)
        response = self.client.get(reverse("admin-question-list"), {"question_type": "SATA"})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["question_type"], "SATA")

    def test_filter_by_is_active(self):
        make_question(external_id="LIST-ACTIVE-2", is_active=True)
        make_question(external_id="LIST-INACTIVE-2", is_active=False)
        response = self.client.get(reverse("admin-question-list"), {"is_active": "false"})
        self.assertEqual(response.data["count"], 1)
        self.assertFalse(response.data["results"][0]["is_active"])

    def test_search_is_case_insensitive_on_stem(self):
        make_question(external_id="LIST-SEARCH", stem="A client with HEART FAILURE reports weight gain")
        response = self.client.get(reverse("admin-question-list"), {"search": "heart failure"})
        self.assertEqual(response.data["count"], 1)

    def test_unknown_query_param_is_ignored_not_an_error(self):
        make_question(external_id="LIST-UNKNOWN-PARAM")
        response = self.client.get(reverse("admin-question-list"), {"not_a_real_filter": "x"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)


class AdminTaxonomyViewTests(APITestCase):
    def setUp(self):
        self.content_admin = User.objects.create_user(
            email="content5@example.com",
            password="a-strong-password-123",
            is_active=True,
            role=UserRole.CONTENT_ADMIN,
        )
        self.student = User.objects.create_user(
            email="student4@example.com", password="a-strong-password-123", is_active=True
        )

    def test_student_is_forbidden(self):
        self.client.force_authenticate(self.student)
        response = self.client.get(reverse("admin-taxonomy"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_nursing_systems_nest_topics_and_subtopics(self):
        make_question(external_id="TAXONOMY-NEST")  # builds Cardiovascular -> Heart Failure via make_question
        self.client.force_authenticate(self.content_admin)
        response = self.client.get(reverse("admin-taxonomy"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        system = next(s for s in response.data["nursing_systems"] if s["name"] == "Cardiovascular")
        self.assertTrue(any(t["name"] == "Heart Failure" for t in system["topics"]))


class AdminQuestionDetailAccessControlTests(APITestCase):
    def setUp(self):
        self.question = make_question(external_id="DETAIL-ACCESS")
        self.student = User.objects.create_user(
            email="student5@example.com", password="a-strong-password-123", is_active=True
        )
        self.content_admin = User.objects.create_user(
            email="content6@example.com",
            password="a-strong-password-123",
            is_active=True,
            role=UserRole.CONTENT_ADMIN,
        )

    def test_anonymous_is_unauthorized(self):
        response = self.client.get(reverse("admin-question-detail", args=[self.question.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student_is_forbidden(self):
        self.client.force_authenticate(self.student)
        response = self.client.get(reverse("admin-question-detail", args=[self.question.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_content_admin_can_retrieve(self):
        self.client.force_authenticate(self.content_admin)
        response = self.client.get(reverse("admin-question-detail", args=[self.question.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AdminQuestionDetailTests(APITestCase):
    def setUp(self):
        self.content_admin = User.objects.create_user(
            email="content7@example.com",
            password="a-strong-password-123",
            is_active=True,
            role=UserRole.CONTENT_ADMIN,
        )
        self.client.force_authenticate(self.content_admin)

    def test_answer_key_is_included_unlike_the_student_facing_endpoint(self):
        # apps.questions.serializers.PublicAnswerChoiceSerializer omits
        # is_correct/rationale entirely — the admin variant must expose
        # both, since managing the answer key is the whole point of this
        # endpoint.
        from apps.questions.models import AnswerChoice

        question = make_question(external_id="DETAIL-ANSWERKEY")
        AnswerChoice.objects.create(
            question=question, choice_text="Correct", is_correct=True, rationale="Because X."
        )

        response = self.client.get(reverse("admin-question-detail", args=[question.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        choice = response.data["answer_choices"][0]
        self.assertTrue(choice["is_correct"])
        self.assertEqual(choice["rationale"], "Because X.")

    def test_delete_removes_question(self):
        question = make_question(external_id="DETAIL-DELETE")
        response = self.client.delete(reverse("admin-question-detail", args=[question.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Question.objects.filter(id=question.id).exists())


class AdminQuestionBulkDeleteTests(APITestCase):
    def setUp(self):
        self.content_admin = User.objects.create_user(
            email="content8@example.com",
            password="a-strong-password-123",
            is_active=True,
            role=UserRole.CONTENT_ADMIN,
        )
        self.client.force_authenticate(self.content_admin)

    def test_deletes_only_given_ids(self):
        keep = make_question(external_id="BULK-KEEP")
        delete_1 = make_question(external_id="BULK-DELETE-1")
        delete_2 = make_question(external_id="BULK-DELETE-2")

        response = self.client.post(
            reverse("admin-question-bulk-delete"),
            {"ids": [str(delete_1.id), str(delete_2.id)]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["deleted"], 2)
        self.assertTrue(Question.objects.filter(id=keep.id).exists())
        self.assertFalse(Question.objects.filter(id__in=[delete_1.id, delete_2.id]).exists())

    def test_unknown_ids_are_ignored_not_an_error(self):
        response = self.client.post(
            reverse("admin-question-bulk-delete"), {"ids": [str(uuid.uuid4())]}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["deleted"], 0)

    def test_non_list_payload_is_400_not_500(self):
        response = self.client.post(
            reverse("admin-question-bulk-delete"), {"ids": "not-a-list"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_student_is_forbidden(self):
        student = User.objects.create_user(
            email="student6@example.com", password="a-strong-password-123", is_active=True
        )
        self.client.force_authenticate(student)
        response = self.client.post(reverse("admin-question-bulk-delete"), {"ids": []}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


def _make_taxonomy_ids():
    """
    make_question()'s get_or_create taxonomy chain, exposed as plain ids so
    a serializer payload can reference it directly. Builds and immediately
    deletes a throwaway Question — cheaper than duplicating make_question's
    taxonomy setup here, and keeps the shared chain identical to what every
    other test in this suite uses.
    """
    throwaway = make_question(external_id=f"TAXHELPER-{uuid.uuid4()}")
    ids = {
        "nursing_system_id": throwaway.nursing_system_id,
        "topic_id": throwaway.topic_id,
        "nclex_client_needs_category_id": throwaway.nclex_client_needs_category_id,
        "nclex_client_needs_subcategory_id": throwaway.nclex_client_needs_subcategory_id,
    }
    throwaway.delete()
    return ids


def _base_admin_payload(question_type, **overrides):
    payload = {
        "question_type": question_type,
        "stem": "Stem text for the admin serializer test suite.",
        "difficulty": "MEDIUM",
        "clinical_judgment_skill": "TAKE_ACTION",
        "cognitive_level": "APPLY",
        **_make_taxonomy_ids(),
    }
    payload.update(overrides)
    return payload


class QuestionAdminSerializerCreateTests(APITestCase):
    """
    One create round trip per question-type family through the real HTTP
    endpoint (not just apps.questions.authoring directly) — proves
    QuestionAdminSerializer's field wiring (PrimaryKeyRelatedFields, nested
    input serializers, effective-type dispatch) actually works end to end,
    which the pure authoring.py unit tests above cannot.
    """

    def setUp(self):
        self.content_admin = User.objects.create_user(
            email="creator@example.com",
            password="a-strong-password-123",
            is_active=True,
            role=UserRole.CONTENT_ADMIN,
        )
        self.client.force_authenticate(self.content_admin)

    def test_create_mcq(self):
        payload = _base_admin_payload(
            "MCQ",
            answer_choices=[
                {"choice_text": "Correct", "is_correct": True, "display_order": 0, "rationale": "Why."},
                {"choice_text": "Wrong", "is_correct": False, "display_order": 1, "rationale": "Why not."},
            ],
        )
        response = self.client.post(reverse("admin-question-list"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(len(response.data["answer_choices"]), 2)

    def test_create_matrix_and_round_trip_via_detail_get(self):
        payload = _base_admin_payload(
            "MATRIX",
            matrix_columns=[
                {"key": "c0", "text": "Expected", "display_order": 0},
                {"key": "c1", "text": "Unexpected", "display_order": 1},
            ],
            matrix_rows=[
                {
                    "key": "r0",
                    "text": "BP 88/54",
                    "display_order": 0,
                    "cells": [
                        {"column_key": "c0", "is_correct": False, "rationale": ""},
                        {"column_key": "c1", "is_correct": True, "rationale": "Hypotension is not expected."},
                    ],
                }
            ],
        )
        create_response = self.client.post(reverse("admin-question-list"), payload, format="json")
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED, create_response.data)
        question_id = create_response.data["id"]

        detail_response = self.client.get(reverse("admin-question-detail", args=[question_id]))
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(detail_response.data["matrix_columns"]), 2)
        row = detail_response.data["matrix_rows"][0]
        self.assertEqual(len(row["cells"]), 2)
        correct_cell = next(c for c in row["cells"] if c["is_correct"])
        correct_column = next(
            c for c in detail_response.data["matrix_columns"] if c["id"] == correct_cell["column_id"]
        )
        self.assertEqual(correct_column["text"], "Unexpected")

    def test_create_bowtie(self):
        payload = _base_admin_payload(
            "BOWTIE",
            bowtie_options=[
                {
                    "section": "ASSESSMENT",
                    "option_text": "Crackles",
                    "is_correct": True,
                    "display_order": 0,
                    "rationale": "",
                },
                {
                    "section": "CONDITION",
                    "option_text": "Fluid overload",
                    "is_correct": True,
                    "display_order": 0,
                    "rationale": "",
                },
                {
                    "section": "ACTION",
                    "option_text": "Give furosemide",
                    "is_correct": True,
                    "display_order": 0,
                    "rationale": "",
                },
            ],
        )
        response = self.client.post(reverse("admin-question-list"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

    def test_create_cloze(self):
        payload = _base_admin_payload(
            "CLOZE",
            stem="The nurse should first assess the client's [dropdown 1].",
            cloze_blanks=[
                {
                    "blank_key": "dropdown 1",
                    "display_order": 0,
                    "options": [
                        {"option_text": "airway", "is_correct": True, "rationale": ""},
                        {"option_text": "temperature", "is_correct": False, "rationale": ""},
                    ],
                }
            ],
        )
        response = self.client.post(reverse("admin-question-list"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

    def test_create_dragdrop_sequencing_variant(self):
        payload = _base_admin_payload(
            "DRAG_DROP",
            dragdrop_categories=[],
            dragdrop_items=[
                {"text": "Don gloves", "display_order": 0, "correct_order": 1, "rationale": ""},
                {"text": "Assess site", "display_order": 1, "correct_order": 2, "rationale": ""},
            ],
        )
        response = self.client.post(reverse("admin-question-list"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

    def test_create_hotspot(self):
        payload = _base_admin_payload(
            "HOTSPOT",
            stem="A client is diaphoretic and pale.",
            hotspot_targets=[
                {"target_text": "diaphoretic", "is_correct": True, "display_order": 0, "rationale": ""}
            ],
        )
        response = self.client.post(reverse("admin-question-list"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

    def test_create_ngn_case_creates_case_study_inline(self):
        payload = _base_admin_payload(
            "NGN_CASE",
            ngn_type="MCQ",
            case_study={
                "external_id": "CASE-ADMIN-1",
                "title": "Post-op hip",
                "shared_scenario": "A 72-year-old...",
            },
            case_study_sequence=1,
            answer_choices=[
                {"choice_text": "Correct", "is_correct": True, "display_order": 0, "rationale": ""},
                {"choice_text": "Wrong", "is_correct": False, "display_order": 1, "rationale": ""},
            ],
        )
        response = self.client.post(reverse("admin-question-list"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data["case_study"]["external_id"], "CASE-ADMIN-1")

    def test_ngn_case_without_ngn_type_is_400(self):
        payload = _base_admin_payload(
            "NGN_CASE",
            case_study={"title": "X", "shared_scenario": "Y"},
            case_study_sequence=1,
        )
        response = self.client.post(reverse("admin-question-list"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_wrong_structure_key_for_type_is_400(self):
        payload = _base_admin_payload(
            "MCQ",
            matrix_columns=[{"key": "c0", "text": "X", "display_order": 0}],
            matrix_rows=[],
        )
        response = self.client.post(reverse("admin-question-list"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mcq_with_two_correct_choices_is_400_not_500(self):
        payload = _base_admin_payload(
            "MCQ",
            answer_choices=[
                {"choice_text": "A", "is_correct": True, "display_order": 0, "rationale": ""},
                {"choice_text": "B", "is_correct": True, "display_order": 1, "rationale": ""},
            ],
        )
        response = self.client.post(reverse("admin-question-list"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_student_cannot_create(self):
        student = User.objects.create_user(
            email="createstudent@example.com", password="a-strong-password-123", is_active=True
        )
        self.client.force_authenticate(student)
        response = self.client.post(reverse("admin-question-list"), _base_admin_payload("MCQ"), format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class QuestionAdminSerializerUpdateTests(APITestCase):
    """
    Update semantics: the "absent key = untouched" rule, and the
    diff-by-id AnswerChoice sync that protects StudentResponseLog history —
    the two riskiest behaviours in the write path, since getting either
    wrong silently corrupts or discards data rather than raising.
    """

    def setUp(self):
        self.content_admin = User.objects.create_user(
            email="updater@example.com",
            password="a-strong-password-123",
            is_active=True,
            role=UserRole.CONTENT_ADMIN,
        )
        self.client.force_authenticate(self.content_admin)

    def test_put_omitting_answer_choices_leaves_them_untouched(self):
        from apps.questions.models import AnswerChoice

        question = make_question(external_id="UPDATE-METADATA-ONLY")
        AnswerChoice.objects.create(
            question=question, choice_text="Correct", is_correct=True, display_order=0
        )
        AnswerChoice.objects.create(question=question, choice_text="Wrong", is_correct=False, display_order=1)

        payload = _base_admin_payload("MCQ", is_active=False)
        # answer_choices deliberately omitted — this is a metadata-only edit.
        payload.pop("answer_choices", None)
        response = self.client.put(
            reverse("admin-question-detail", args=[question.id]), payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(AnswerChoice.objects.filter(question=question).count(), 2)
        question.refresh_from_db()
        self.assertFalse(question.is_active)

    def test_put_updating_existing_choice_by_id_preserves_response_log_link(self):
        from apps.questions.models import AnswerChoice
        from apps.quizzes.models import QuizSession, QuizSessionQuestion, StudentResponseLog

        question = make_question(external_id="UPDATE-PRESERVE-LOG")
        correct = AnswerChoice.objects.create(
            question=question, choice_text="Correct", is_correct=True, display_order=0
        )
        wrong = AnswerChoice.objects.create(
            question=question, choice_text="Wrong", is_correct=False, display_order=1
        )

        student = User.objects.create_user(
            email="historystudent@example.com", password="a-strong-password-123"
        )
        session = QuizSession.objects.create(student=student)
        QuizSessionQuestion.objects.create(quiz_session=session, question=question, position=0)
        log = StudentResponseLog.objects.create(
            student=student,
            question=question,
            selected_choice=wrong,
            is_correct=False,
            time_taken_seconds=10,
            quiz_session=session,
        )

        payload = _base_admin_payload(
            "MCQ",
            answer_choices=[
                {
                    "id": str(correct.id),
                    "choice_text": "Correct (edited)",
                    "is_correct": True,
                    "display_order": 0,
                    "rationale": "",
                },
                {
                    "id": str(wrong.id),
                    "choice_text": "Wrong (edited)",
                    "is_correct": False,
                    "display_order": 1,
                    "rationale": "",
                },
            ],
        )
        response = self.client.put(
            reverse("admin-question-detail", args=[question.id]), payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        log.refresh_from_db()
        wrong.refresh_from_db()
        self.assertEqual(log.selected_choice_id, wrong.id)
        self.assertEqual(wrong.choice_text, "Wrong (edited)")

    def test_put_omitting_a_previously_existing_choice_deletes_it_and_nulls_the_log(self):
        from apps.questions.models import AnswerChoice
        from apps.quizzes.models import QuizSession, QuizSessionQuestion, StudentResponseLog

        question = make_question(external_id="UPDATE-DELETE-CHOICE")
        correct = AnswerChoice.objects.create(
            question=question, choice_text="Correct", is_correct=True, display_order=0
        )
        wrong = AnswerChoice.objects.create(
            question=question, choice_text="Wrong", is_correct=False, display_order=1
        )

        student = User.objects.create_user(
            email="historystudent2@example.com", password="a-strong-password-123"
        )
        session = QuizSession.objects.create(student=student)
        QuizSessionQuestion.objects.create(quiz_session=session, question=question, position=0)
        log = StudentResponseLog.objects.create(
            student=student,
            question=question,
            selected_choice=wrong,
            is_correct=False,
            time_taken_seconds=10,
            quiz_session=session,
        )

        payload = _base_admin_payload(
            "MCQ",
            answer_choices=[
                {
                    "id": str(correct.id),
                    "choice_text": "Correct",
                    "is_correct": True,
                    "display_order": 0,
                    "rationale": "",
                },
            ],
        )
        response = self.client.put(
            reverse("admin-question-detail", args=[question.id]), payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        self.assertFalse(AnswerChoice.objects.filter(id=wrong.id).exists())
        log.refresh_from_db()
        self.assertIsNone(log.selected_choice_id)
        # The log row itself survives — only the FK it pointed at is gone.
        self.assertTrue(StudentResponseLog.objects.filter(id=log.id).exists())

    def test_changing_question_type_on_update_is_400(self):
        question = make_question(external_id="UPDATE-RETYPE", question_type=QuestionType.MCQ)
        payload = _base_admin_payload(
            "SATA",
            answer_choices=[
                {"choice_text": "A", "is_correct": True, "display_order": 0, "rationale": ""},
                {"choice_text": "B", "is_correct": True, "display_order": 1, "rationale": ""},
            ],
        )
        response = self.client.put(
            reverse("admin-question-detail", args=[question.id]), payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


def _workbook_upload(wb, filename="ngn_item_bank.xlsx"):
    """Serializes an in-memory openpyxl workbook into a SimpleUploadedFile, the shape a real multipart upload arrives as."""
    import io

    from django.core.files.uploadedfile import SimpleUploadedFile

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return SimpleUploadedFile(
        filename,
        buffer.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


class QuestionImportViewTests(APITestCase):
    def setUp(self):
        from apps.questions.tests import _build_workbook

        NursingSystem.objects.get_or_create(name="Cardiovascular")
        from apps.taxonomy.models import ClientNeedsCategory, ClientNeedsSubcategory, Domain, Topic

        nursing_system = NursingSystem.objects.get(name="Cardiovascular")
        Topic.objects.get_or_create(nursing_system=nursing_system, name="Heart Failure")
        Domain.objects.get_or_create(name="Adult Health")
        category, _ = ClientNeedsCategory.objects.get_or_create(name="Physiological Integrity")
        ClientNeedsSubcategory.objects.get_or_create(category=category, name="Reduction of Risk Potential")

        self._build_workbook = _build_workbook
        self.content_admin = User.objects.create_user(
            email="importer1@example.com",
            password="a-strong-password-123",
            is_active=True,
            role=UserRole.CONTENT_ADMIN,
        )
        self.client.force_authenticate(self.content_admin)

    def test_happy_path_returns_structured_result_and_writes_import_log(self):
        from apps.questions.models import ImportLog

        upload = _workbook_upload(self._build_workbook())
        response = self.client.post(reverse("admin-import"), {"file": upload}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["created"], 8)
        self.assertEqual(response.data["case_studies_created"], 1)
        self.assertEqual(response.data["rows_failed"], 0)

        log = ImportLog.objects.latest("uploaded_at")
        self.assertEqual(log.uploaded_by, self.content_admin)
        self.assertEqual(log.source_filename, "ngn_item_bank.xlsx")
        self.assertEqual(log.questions_imported, 8)

    def test_one_bad_row_still_returns_200_with_the_rest_imported(self):
        wb = self._build_workbook()
        ws = wb["Answer_Options"]
        ws.append(["EHS-1", "Highlight 2", "this text is not in the stem at all", "TRUE", "Ambiguous."])

        response = self.client.post(
            reverse("admin-import"), {"file": _workbook_upload(wb)}, format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["rows_failed"], 1)
        self.assertGreater(response.data["created"], 0)

    def test_dry_run_does_not_write_import_log(self):
        from apps.questions.models import ImportLog

        upload = _workbook_upload(self._build_workbook())
        response = self.client.post(
            reverse("admin-import"), {"file": upload, "dry_run": "true"}, format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertTrue(response.data["dry_run"])
        self.assertEqual(ImportLog.objects.count(), 0)
        self.assertEqual(Question.objects.count(), 0)

    def test_wrong_extension_is_400(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        upload = SimpleUploadedFile("questions.csv", b"not,a,workbook", content_type="text/csv")
        response = self.client.post(reverse("admin-import"), {"file": upload}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_oversized_file_is_400(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        from apps.questions.importer import MAX_IMPORT_FILE_BYTES

        oversized = SimpleUploadedFile(
            "big.xlsx",
            b"0" * (MAX_IMPORT_FILE_BYTES + 1),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response = self.client.post(reverse("admin-import"), {"file": oversized}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_workbook_missing_a_required_sheet_is_400_not_500(self):
        import openpyxl

        wb = openpyxl.Workbook()
        wb.active.title = "Item_Master"  # only sheet — missing Answer_Options, NGN_Cases, etc.
        response = self.client.post(
            reverse("admin-import"), {"file": _workbook_upload(wb)}, format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_student_is_forbidden(self):
        student = User.objects.create_user(
            email="importstudent@example.com", password="a-strong-password-123", is_active=True
        )
        self.client.force_authenticate(student)
        upload = _workbook_upload(self._build_workbook())
        response = self.client.post(reverse("admin-import"), {"file": upload}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminImportLogListViewTests(APITestCase):
    def setUp(self):
        self.content_admin = User.objects.create_user(
            email="importer2@example.com",
            password="a-strong-password-123",
            is_active=True,
            role=UserRole.CONTENT_ADMIN,
        )
        self.client.force_authenticate(self.content_admin)

    def test_lists_most_recent_first(self):
        from apps.questions.models import ImportLog

        older = ImportLog.objects.create(questions_imported=3, rows_failed=0, source_filename="batch1.xlsx")
        newer = ImportLog.objects.create(questions_imported=5, rows_failed=1, source_filename="batch2.xlsx")

        response = self.client.get(reverse("admin-import-log"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [row["id"] for row in response.data["results"]]
        self.assertEqual(ids, [str(newer.id), str(older.id)])

    def test_null_uploader_serializes_as_none(self):
        from apps.questions.models import ImportLog

        ImportLog.objects.create(questions_imported=1, rows_failed=0, uploaded_by=None)
        response = self.client.get(reverse("admin-import-log"))
        self.assertIsNone(response.data["results"][0]["uploaded_by_email"])

    def test_student_is_forbidden(self):
        student = User.objects.create_user(
            email="importloguser@example.com", password="a-strong-password-123", is_active=True
        )
        self.client.force_authenticate(student)
        response = self.client.get(reverse("admin-import-log"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


def _make_quiz_feedback(student, **overrides):
    from apps.feedback.models import DifficultyRating, QuizFeedback, RealismRating, RecommendLikelihood

    defaults = dict(
        student=student,
        overall_rating=4,
        question_quality_rating=4,
        difficulty_rating=DifficultyRating.JUST_RIGHT,
        realism_rating=RealismRating.MODERATELY_REALISTIC,
        rationale_helpfulness_rating=5,
        liked_most="The rationales were clear.",
        improvement_suggestion="More Matrix/Grid questions please.",
        recommend_likelihood=RecommendLikelihood.PROBABLY_YES,
    )
    defaults.update(overrides)
    return QuizFeedback.objects.create(**defaults)


def _make_issue_report(student, **overrides):
    from apps.feedback.models import QuestionIssueReport, QuestionIssueType

    defaults = dict(
        student=student,
        question_stem_snapshot="A client with heart failure...",
        issue_type=QuestionIssueType.UNCLEAR,
        description="The stem is ambiguous about timing.",
    )
    defaults.update(overrides)
    return QuestionIssueReport.objects.create(**defaults)


class AdminFeedbackListViewTests(APITestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            email="feedbackstudent@example.com", password="a-strong-password-123", is_active=True
        )
        self.content_admin = User.objects.create_user(
            email="feedbackadmin@example.com",
            password="a-strong-password-123",
            is_active=True,
            role=UserRole.CONTENT_ADMIN,
        )
        self.client.force_authenticate(self.content_admin)

    def test_defaults_to_survey_kind(self):
        _make_quiz_feedback(self.student)
        response = self.client.get(reverse("admin-feedback-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertIn("feedback_text", response.data["results"][0])

    def test_issue_kind_returns_question_issue_reports(self):
        _make_quiz_feedback(self.student)
        _make_issue_report(self.student)
        response = self.client.get(reverse("admin-feedback-list"), {"kind": "issue"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertIn("issue_type", response.data["results"][0])

    def test_invalid_kind_is_400(self):
        response = self.client.get(reverse("admin-feedback-list"), {"kind": "nonsense"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_by_status(self):
        from apps.feedback.models import FeedbackStatus

        _make_quiz_feedback(self.student, status=FeedbackStatus.IMPLEMENTED)
        _make_quiz_feedback(self.student, status=FeedbackStatus.IN_CONSIDERATION)
        response = self.client.get(reverse("admin-feedback-list"), {"status": "IMPLEMENTED"})
        self.assertEqual(response.data["count"], 1)

    def test_page_size_is_25(self):
        for _ in range(30):
            _make_quiz_feedback(self.student)
        response = self.client.get(reverse("admin-feedback-list"))
        self.assertEqual(len(response.data["results"]), 25)

    def test_newest_first(self):
        older = _make_quiz_feedback(self.student)
        newer = _make_quiz_feedback(self.student)
        response = self.client.get(reverse("admin-feedback-list"))
        ids = [row["id"] for row in response.data["results"]]
        self.assertEqual(ids, [str(newer.id), str(older.id)])

    def test_student_is_forbidden(self):
        self.client.force_authenticate(self.student)
        response = self.client.get(reverse("admin-feedback-list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminFeedbackDetailViewTests(APITestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            email="feedbackstudent2@example.com", password="a-strong-password-123", is_active=True
        )
        self.content_admin = User.objects.create_user(
            email="feedbackadmin2@example.com",
            password="a-strong-password-123",
            is_active=True,
            role=UserRole.CONTENT_ADMIN,
        )
        self.client.force_authenticate(self.content_admin)

    def test_get_survey_detail(self):
        fb = _make_quiz_feedback(self.student)
        response = self.client.get(reverse("admin-feedback-detail", args=["survey", fb.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["improvement_suggestion"], "More Matrix/Grid questions please.")

    def test_patch_survey_status_to_implemented(self):
        fb = _make_quiz_feedback(self.student)
        response = self.client.patch(
            reverse("admin-feedback-detail", args=["survey", fb.id]), {"status": "IMPLEMENTED"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        fb.refresh_from_db()
        self.assertEqual(fb.status, "IMPLEMENTED")
        self.assertIsNotNone(fb.status_updated_at)

    def test_patch_invalid_status_is_400(self):
        fb = _make_quiz_feedback(self.student)
        response = self.client.patch(
            reverse("admin-feedback-detail", args=["survey", fb.id]),
            {"status": "NOT_A_REAL_STATUS"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_issue_report_uses_its_own_status_vocabulary(self):
        report = _make_issue_report(self.student)
        response = self.client.patch(
            reverse("admin-feedback-detail", args=["issue", report.id]), {"status": "RESOLVED"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        report.refresh_from_db()
        self.assertEqual(report.status, "RESOLVED")

    def test_patch_issue_report_rejects_survey_only_status_value(self):
        report = _make_issue_report(self.student)
        response = self.client.patch(
            reverse("admin-feedback-detail", args=["issue", report.id]),
            {"status": "IMPLEMENTED"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_removes_record(self):
        from apps.feedback.models import QuizFeedback

        fb = _make_quiz_feedback(self.student)
        response = self.client.delete(reverse("admin-feedback-detail", args=["survey", fb.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(QuizFeedback.objects.filter(id=fb.id).exists())

    def test_wrong_kind_for_id_is_404(self):
        fb = _make_quiz_feedback(self.student)
        # fb.id belongs to QuizFeedback, not QuestionIssueReport — asking
        # for it under the wrong kind must 404, not silently succeed.
        response = self.client.get(reverse("admin-feedback-detail", args=["issue", fb.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_student_is_forbidden(self):
        fb = _make_quiz_feedback(self.student)
        self.client.force_authenticate(self.student)
        response = self.client.get(reverse("admin-feedback-detail", args=["survey", fb.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
