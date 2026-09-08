from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.questions.models import AnswerChoice
from apps.taxonomy.models import Domain

# Reuses the make_question() fixture helper defined in apps.questions.tests
# instead of duplicating that taxonomy + Question setup boilerplate here —
# cross-app test-helper reuse, not a production code dependency.
from apps.questions.tests import make_question

from .models import Bookmark, QuizSession, QuizSessionQuestion, StudentResponseLog
from .services import compute_facet_counts

User = get_user_model()


class StudentResponseLogTests(TestCase):
    """
    Specifically exercises the distinction StudentResponseLog's docstring
    calls out: selected_choice (single-answer types) vs. selected_choices
    (SATA/multi-answer types) are two independent fields on the same model,
    and both need to work correctly since Phase 2's AI features will read
    whichever one applies per question type.
    """

    def setUp(self):
        self.student = User.objects.create_user(email="student@example.com", password="a-strong-password-123")

    def _make_session(self, question):
        # Small local helper (not shared across test files, unlike
        # make_question) since QuizSession creation is specific to this
        # app's tests. Goes through QuizSessionQuestion directly (not
        # session.questions.add()) since the M2M now requires a `position`
        # the plain add() manager can't supply — see QuizSessionQuestion's
        # own docstring in models.py.
        session = QuizSession.objects.create(student=self.student)
        QuizSessionQuestion.objects.create(quiz_session=session, question=question, position=0)
        return session

    def test_single_answer_response_uses_selected_choice(self):
        question = make_question()
        correct = AnswerChoice.objects.create(question=question, choice_text="Correct", is_correct=True)
        session = self._make_session(question)

        response = StudentResponseLog.objects.create(
            student=self.student,
            question=question,
            selected_choice=correct,
            is_correct=True,
            time_taken_seconds=42,
            quiz_session=session,
        )

        self.assertEqual(response.selected_choice, correct)
        # Confirms creating a response via selected_choice doesn't
        # accidentally also populate the (unrelated) selected_choices M2M —
        # the two fields should be independent.
        self.assertEqual(response.selected_choices.count(), 0)

    def test_sata_response_uses_selected_choices(self):
        question = make_question()
        choice_1 = AnswerChoice.objects.create(question=question, choice_text="A", is_correct=True)
        choice_2 = AnswerChoice.objects.create(question=question, choice_text="B", is_correct=True)
        session = self._make_session(question)

        # selected_choice is simply omitted here (stays null, since it's
        # nullable) — a ManyToMany field can't be set directly in .create()
        # the way a ForeignKey can, so it's populated afterward via .set().
        response = StudentResponseLog.objects.create(
            student=self.student,
            question=question,
            is_correct=True,
            time_taken_seconds=30,
            quiz_session=session,
        )
        response.selected_choices.set([choice_1, choice_2])

        self.assertIsNone(response.selected_choice)
        self.assertEqual(response.selected_choices.count(), 2)

    def test_response_log_records_which_distractor_was_chosen(self):
        # The core Phase-2-enabling behavior under test: the log doesn't
        # just record is_correct=False, it records WHICH specific wrong
        # choice was picked — this is what a future "why did I get this
        # wrong" AI feature needs to reference.
        question = make_question()
        wrong_choice = AnswerChoice.objects.create(
            question=question, choice_text="Distractor", is_correct=False
        )
        session = self._make_session(question)

        response = StudentResponseLog.objects.create(
            student=self.student,
            question=question,
            selected_choice=wrong_choice,
            is_correct=False,
            time_taken_seconds=15,
            quiz_session=session,
        )

        self.assertFalse(response.is_correct)
        self.assertEqual(response.selected_choice, wrong_choice)


# A filters dict with every dimension present but empty — apply_taxonomy_filters
# treats "key missing" and "key present but empty" identically (both skip that
# dimension), but tests build this explicitly so a typo'd key name in
# services.py would show up as a KeyError here rather than being silently
# ignored.
EMPTY_FILTERS = {
    "question_types": [],
    "status_filters": [],
    "domains": [],
    "nursing_systems": [],
    "nclex_client_needs_subcategories": [],
}


class FacetCountsTests(TestCase):
    """
    apps.quizzes.services.compute_facet_counts — the query logic behind
    every live count on the quiz-setup page.
    """

    def setUp(self):
        self.student = User.objects.create_user(email="facet@example.com", password="a-strong-password-123")
        self.question = make_question()
        AnswerChoice.objects.create(question=self.question, choice_text="Correct", is_correct=True)
        AnswerChoice.objects.create(question=self.question, choice_text="Wrong", is_correct=False)

    def test_unanswered_question_counts_as_unused(self):
        counts = compute_facet_counts(self.student, EMPTY_FILTERS)
        self.assertEqual(counts["question_mode"]["UNUSED"]["count"], 1)
        self.assertEqual(counts["question_mode"]["CORRECT"]["count"], 0)

    def test_correct_response_moves_the_question_out_of_unused(self):
        session = QuizSession.objects.create(student=self.student)
        QuizSessionQuestion.objects.create(quiz_session=session, question=self.question, position=0)
        correct_choice = self.question.answer_choices.get(is_correct=True)
        StudentResponseLog.objects.create(
            student=self.student,
            question=self.question,
            selected_choice=correct_choice,
            is_correct=True,
            time_taken_seconds=10,
            quiz_session=session,
        )

        counts = compute_facet_counts(self.student, EMPTY_FILTERS)
        self.assertEqual(counts["question_mode"]["UNUSED"]["count"], 0)
        self.assertEqual(counts["question_mode"]["CORRECT"]["count"], 1)

    def test_bookmark_is_an_overlapping_tag_not_a_replacement_status(self):
        Bookmark.objects.create(student=self.student, question=self.question)
        counts = compute_facet_counts(self.student, EMPTY_FILTERS)
        self.assertEqual(counts["question_mode"]["MARKED"]["count"], 1)
        # Marking doesn't answer the question — it's still Unused too.
        self.assertEqual(counts["question_mode"]["UNUSED"]["count"], 1)

    def test_domain_filter_excludes_non_matching_questions(self):
        domain = Domain.objects.create(name="Adult Health")
        self.question.domain = domain
        self.question.save(update_fields=["domain"])

        matching = compute_facet_counts(self.student, dict(EMPTY_FILTERS, domains=[domain.id]))
        self.assertEqual(matching["question_mode"]["UNUSED"]["count"], 1)

        other_domain = Domain.objects.create(name="Pharmacology")
        non_matching = compute_facet_counts(self.student, dict(EMPTY_FILTERS, domains=[other_domain.id]))
        self.assertEqual(non_matching["question_mode"]["UNUSED"]["count"], 0)

    def test_domains_list_includes_every_domain_even_with_zero_matches(self):
        Domain.objects.create(name="Mental Health")
        counts = compute_facet_counts(self.student, EMPTY_FILTERS)
        names = {row["name"]: row["count"] for row in counts["domains"]}
        self.assertIn("Mental Health", names)
        self.assertEqual(names["Mental Health"], 0)


class QuizSessionCreateAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="session@example.com", password="a-strong-password-123")
        self.client.force_authenticate(self.user)
        self.question = make_question()
        AnswerChoice.objects.create(question=self.question, choice_text="Correct", is_correct=True)

    def test_requires_authentication(self):
        self.client.force_authenticate(None)
        response = self.client.post(reverse("quiz-session-create"), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_creates_a_session_with_the_matching_question(self):
        payload = {"question_types": ["TRADITIONAL"], "question_count": 1}
        response = self.client.post(reverse("quiz-session-create"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data["questions"]), 1)
        self.assertEqual(response.data["questions"][0]["id"], str(self.question.id))

        session = QuizSession.objects.get(pk=response.data["id"])
        self.assertEqual(session.student, self.user)
        self.assertEqual(session.session_questions.count(), 1)

    def test_no_matching_questions_returns_400(self):
        # Only a TRADITIONAL-type question exists in this test's data — an
        # NGN-only request has nothing to draw from.
        payload = {"question_types": ["NGN"], "question_count": 5}
        response = self.client.post(reverse("quiz-session-create"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_generating_a_new_quiz_abandons_the_students_other_in_progress_sessions(self):
        # Otherwise an old session the student walked away from mid-quiz
        # (browser closed without finishing) lingers as "in progress"
        # forever and can resurface as a confusing, unrelated "continue
        # your last quiz?" prompt well after this newer quiz is done.
        stale_session = QuizSession.objects.create(student=self.user)
        QuizSessionQuestion.objects.create(quiz_session=stale_session, question=self.question, position=0)
        completed_session = QuizSession.objects.create(student=self.user, is_complete=True)
        other_students_session = QuizSession.objects.create(student=User.objects.create_user(email="bystander@example.com", password="a-strong-password-123"))

        payload = {"question_types": ["TRADITIONAL"], "question_count": 1}
        self.client.post(reverse("quiz-session-create"), payload, format="json")

        stale_session.refresh_from_db()
        completed_session.refresh_from_db()
        other_students_session.refresh_from_db()
        self.assertTrue(stale_session.is_abandoned)
        # A session already complete must not be touched — it was never
        # "in progress" to begin with, and is_abandoned would be misleading
        # (and irrelevant) on a session that finished normally.
        self.assertFalse(completed_session.is_abandoned)
        self.assertFalse(other_students_session.is_abandoned)


class QuizAnswerSubmitAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="answer@example.com", password="a-strong-password-123")
        self.other_user = User.objects.create_user(email="other@example.com", password="a-strong-password-123")
        self.client.force_authenticate(self.user)
        self.question = make_question()
        self.correct = AnswerChoice.objects.create(question=self.question, choice_text="Correct", is_correct=True)
        AnswerChoice.objects.create(question=self.question, choice_text="Wrong", is_correct=False)
        self.session = QuizSession.objects.create(student=self.user, total_questions=1)
        QuizSessionQuestion.objects.create(quiz_session=self.session, question=self.question, position=0)

    def _url(self, session=None):
        return reverse("quiz-session-answer", args=[(session or self.session).pk])

    def test_grading_persists_a_response_log(self):
        payload = {
            "question_id": str(self.question.id),
            "selected_choice_ids": [str(self.correct.id)],
            "time_taken_seconds": 12,
        }
        response = self.client.post(self._url(), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_correct"])
        log = StudentResponseLog.objects.get(student=self.user, question=self.question)
        self.assertEqual(log.selected_choice, self.correct)
        self.assertEqual(log.time_taken_seconds, 12)

    def test_answering_does_not_move_position(self):
        # Position is owned entirely by QuizSessionPositionView (free
        # Previous/Next navigation means answering a question is a separate
        # event from moving past it) — grading must not have that side
        # effect, unlike the old forward-only flow.
        second_question = make_question(stem="A second question, left unanswered.")
        AnswerChoice.objects.create(question=second_question, choice_text="Correct", is_correct=True)
        QuizSessionQuestion.objects.create(quiz_session=self.session, question=second_question, position=1)
        self.session.total_questions = 2
        self.session.save(update_fields=["total_questions"])

        payload = {"question_id": str(self.question.id), "selected_choice_ids": [str(self.correct.id)]}
        self.client.post(self._url(), payload, format="json")

        self.session.refresh_from_db()
        self.assertEqual(self.session.current_question_index, 0)

    def test_answering_the_last_remaining_question_auto_completes_the_session(self):
        # This session has exactly one question — answering it means every
        # question now has a response, so the session should complete on
        # its own without a separate explicit "Finish Quiz" call. Without
        # this, a student who answers everything and just closes the tab
        # (the natural thing to do once every question is graded) would
        # leave the session is_complete=False forever, and
        # QuizSessionActiveView would keep resurfacing "continue your last
        # quiz?" on every future login even though nothing is left to do.
        payload = {"question_id": str(self.question.id), "selected_choice_ids": [str(self.correct.id)]}
        self.client.post(self._url(), payload, format="json")

        self.session.refresh_from_db()
        self.assertTrue(self.session.is_complete)
        self.assertIsNotNone(self.session.completed_at)

    def test_answering_only_some_questions_does_not_complete_the_session(self):
        second_question = make_question(stem="A second question, left unanswered.")
        AnswerChoice.objects.create(question=second_question, choice_text="Correct", is_correct=True)
        QuizSessionQuestion.objects.create(quiz_session=self.session, question=second_question, position=1)
        self.session.total_questions = 2
        self.session.save(update_fields=["total_questions"])

        payload = {"question_id": str(self.question.id), "selected_choice_ids": [str(self.correct.id)]}
        self.client.post(self._url(), payload, format="json")

        self.session.refresh_from_db()
        self.assertFalse(self.session.is_complete)
        self.assertIsNone(self.session.completed_at)

    def test_cannot_submit_into_an_already_complete_session(self):
        self.session.is_complete = True
        self.session.save(update_fields=["is_complete"])
        payload = {"question_id": str(self.question.id), "selected_choice_ids": [str(self.correct.id)]}

        response = self.client.post(self._url(), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertFalse(StudentResponseLog.objects.filter(quiz_session=self.session).exists())

    def test_cannot_submit_into_an_abandoned_session(self):
        self.session.is_abandoned = True
        self.session.save(update_fields=["is_abandoned"])
        payload = {"question_id": str(self.question.id), "selected_choice_ids": [str(self.correct.id)]}

        response = self.client.post(self._url(), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertFalse(StudentResponseLog.objects.filter(quiz_session=self.session).exists())

    def test_cannot_submit_into_another_students_session(self):
        other_session = QuizSession.objects.create(student=self.other_user)
        QuizSessionQuestion.objects.create(quiz_session=other_session, question=self.question, position=0)
        payload = {"question_id": str(self.question.id), "selected_choice_ids": [str(self.correct.id)]}

        response = self.client.post(self._url(other_session), payload, format="json")

        # 404, not 403 — see QuizAnswerSubmitView's own comment on why: one
        # student must not learn another student's session id even exists.
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class QuizSessionRetrieveAPITests(APITestCase):
    """GET /api/quizzes/sessions/<id>/ — the refresh-resume lookup."""

    def setUp(self):
        self.user = User.objects.create_user(email="retrieve@example.com", password="a-strong-password-123")
        self.other_user = User.objects.create_user(email="retrieve-other@example.com", password="a-strong-password-123")
        self.client.force_authenticate(self.user)
        self.question = make_question()
        self.session = QuizSession.objects.create(student=self.user)
        QuizSessionQuestion.objects.create(quiz_session=self.session, question=self.question, position=0)

    def test_returns_the_session_with_its_ordered_questions(self):
        response = self.client.get(reverse("quiz-session-retrieve", args=[self.session.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.session.pk))
        self.assertEqual(len(response.data["questions"]), 1)

    def test_cannot_retrieve_another_students_session(self):
        self.client.force_authenticate(self.other_user)
        response = self.client.get(reverse("quiz-session-retrieve", args=[self.session.pk]))
        # 404, not 403 — same reasoning as QuizAnswerSubmitView.
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class QuizSessionResponseHydrationAPITests(APITestCase):
    """
    The `responses` / `visited_question_ids` / `marked_question_ids` fields
    on QuizSessionSerializer — what lets the frontend restore navigation
    (Previous/Next), already-answered questions, skipped questions, and
    flags after a resume, not just "which question index".
    """

    def setUp(self):
        self.user = User.objects.create_user(email="hydrate@example.com", password="a-strong-password-123")
        self.client.force_authenticate(self.user)
        self.question = make_question()
        self.correct = AnswerChoice.objects.create(question=self.question, choice_text="Correct", is_correct=True)
        AnswerChoice.objects.create(question=self.question, choice_text="Wrong", is_correct=False)
        self.other_question = make_question()
        self.session = QuizSession.objects.create(student=self.user)
        QuizSessionQuestion.objects.create(quiz_session=self.session, question=self.question, position=0)
        QuizSessionQuestion.objects.create(quiz_session=self.session, question=self.other_question, position=1)

    def _get(self):
        return self.client.get(reverse("quiz-session-retrieve", args=[self.session.pk]))

    def test_answered_question_appears_in_responses_with_its_answer_key(self):
        StudentResponseLog.objects.create(
            student=self.user,
            question=self.question,
            quiz_session=self.session,
            selected_choice=self.correct,
            is_correct=True,
            time_taken_seconds=5,
        )

        data = self._get().data

        self.assertEqual(len(data["responses"]), 1)
        entry = data["responses"][0]
        self.assertEqual(entry["question_id"], str(self.question.id))
        self.assertTrue(entry["is_correct"])
        self.assertEqual(entry["selected_choice_ids"], [str(self.correct.id)])
        self.assertIsNone(entry["structured_answer"])
        # The revealed answer key rides along in the same response — no
        # second round trip needed to show rationale on a resumed question.
        self.assertEqual(len(entry["choices"]), 2)

    def test_only_the_latest_response_per_question_is_returned(self):
        StudentResponseLog.objects.create(
            student=self.user, question=self.question, quiz_session=self.session,
            selected_choice=self.correct, is_correct=True, time_taken_seconds=5,
        )
        wrong = self.question.answer_choices.get(is_correct=False)
        StudentResponseLog.objects.create(
            student=self.user, question=self.question, quiz_session=self.session,
            selected_choice=wrong, is_correct=False, time_taken_seconds=3,
        )

        data = self._get().data

        self.assertEqual(len(data["responses"]), 1)
        self.assertFalse(data["responses"][0]["is_correct"])

    def test_visited_question_ids_reflects_the_visited_flag(self):
        QuizSessionQuestion.objects.filter(quiz_session=self.session, question=self.question).update(visited=True)

        data = self._get().data

        self.assertEqual(data["visited_question_ids"], [str(self.question.id)])

    def test_marked_question_ids_reflects_bookmarks_scoped_to_this_session(self):
        Bookmark.objects.create(student=self.user, question=self.question)
        # A bookmark on a question NOT in this session must not leak in.
        Bookmark.objects.create(student=self.user, question=make_question())

        data = self._get().data

        self.assertEqual(data["marked_question_ids"], [str(self.question.id)])


class QuizSessionPositionAPITests(APITestCase):
    """POST /api/quizzes/sessions/<id>/position/ — free Previous/Next/jump navigation."""

    def setUp(self):
        self.user = User.objects.create_user(email="position@example.com", password="a-strong-password-123")
        self.other_user = User.objects.create_user(email="position-other@example.com", password="a-strong-password-123")
        self.client.force_authenticate(self.user)
        self.question_a = make_question()
        self.question_b = make_question()
        self.session = QuizSession.objects.create(student=self.user)
        QuizSessionQuestion.objects.create(quiz_session=self.session, question=self.question_a, position=0)
        QuizSessionQuestion.objects.create(quiz_session=self.session, question=self.question_b, position=1)

    def _url(self):
        return reverse("quiz-session-position", args=[self.session.pk])

    def test_moving_forward_updates_position_and_marks_visited(self):
        response = self.client.post(self._url(), {"question_id": str(self.question_b.id)}, format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.session.refresh_from_db()
        self.assertEqual(self.session.current_question_index, 1)
        session_question = QuizSessionQuestion.objects.get(quiz_session=self.session, question=self.question_b)
        self.assertTrue(session_question.visited)

    def test_moving_backward_is_allowed_unlike_the_old_answer_submit_gate(self):
        self.client.post(self._url(), {"question_id": str(self.question_b.id)}, format="json")
        response = self.client.post(self._url(), {"question_id": str(self.question_a.id)}, format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.session.refresh_from_db()
        self.assertEqual(self.session.current_question_index, 0)

    def test_cannot_set_position_on_another_students_session(self):
        self.client.force_authenticate(self.other_user)
        response = self.client.post(self._url(), {"question_id": str(self.question_a.id)}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class QuizSessionFinishAPITests(APITestCase):
    """POST /api/quizzes/sessions/<id>/finish/ — the explicit "Finish Quiz" action."""

    def setUp(self):
        self.user = User.objects.create_user(email="finish@example.com", password="a-strong-password-123")
        self.other_user = User.objects.create_user(email="finish-other@example.com", password="a-strong-password-123")
        self.client.force_authenticate(self.user)
        self.question = make_question()
        self.session = QuizSession.objects.create(student=self.user)
        QuizSessionQuestion.objects.create(quiz_session=self.session, question=self.question, position=0)

    def _url(self, session=None):
        return reverse("quiz-session-finish", args=[(session or self.session).pk])

    def test_marks_the_session_complete_even_with_unanswered_questions(self):
        # The whole point of an explicit finish action: the student can end
        # the quiz having skipped questions, not just after answering every
        # last one.
        response = self.client.post(self._url())
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.session.refresh_from_db()
        self.assertTrue(self.session.is_complete)
        self.assertIsNotNone(self.session.completed_at)

    def test_no_longer_returned_as_the_active_session_afterward(self):
        self.client.post(self._url())
        response = self.client.get(reverse("quiz-session-active"))
        self.assertIsNone(response.data["session"])

    def test_cannot_finish_another_students_session(self):
        self.client.force_authenticate(self.other_user)
        response = self.client.post(self._url())
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.session.refresh_from_db()
        self.assertFalse(self.session.is_complete)


class QuizSessionActiveAPITests(APITestCase):
    """GET /api/quizzes/sessions/active/ — what powers the post-login resume prompt."""

    def setUp(self):
        self.user = User.objects.create_user(email="active@example.com", password="a-strong-password-123")
        self.client.force_authenticate(self.user)
        self.question = make_question()

    def test_no_sessions_returns_null(self):
        response = self.client.get(reverse("quiz-session-active"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["session"])

    def test_returns_an_in_progress_session(self):
        session = QuizSession.objects.create(student=self.user)
        QuizSessionQuestion.objects.create(quiz_session=session, question=self.question, position=0)

        response = self.client.get(reverse("quiz-session-active"))

        self.assertIsNotNone(response.data["session"])
        self.assertEqual(response.data["session"]["id"], str(session.pk))

    def test_completed_sessions_are_not_returned(self):
        session = QuizSession.objects.create(student=self.user, is_complete=True)
        QuizSessionQuestion.objects.create(quiz_session=session, question=self.question, position=0)

        response = self.client.get(reverse("quiz-session-active"))

        self.assertIsNone(response.data["session"])

    def test_abandoned_sessions_are_not_returned(self):
        session = QuizSession.objects.create(student=self.user, is_abandoned=True)
        QuizSessionQuestion.objects.create(quiz_session=session, question=self.question, position=0)

        response = self.client.get(reverse("quiz-session-active"))

        self.assertIsNone(response.data["session"])


class QuizSessionAbandonAPITests(APITestCase):
    """POST /api/quizzes/sessions/<id>/abandon/ — declining the resume prompt."""

    def setUp(self):
        self.user = User.objects.create_user(email="abandon@example.com", password="a-strong-password-123")
        self.other_user = User.objects.create_user(email="abandon-other@example.com", password="a-strong-password-123")
        self.client.force_authenticate(self.user)
        self.question = make_question()
        self.session = QuizSession.objects.create(student=self.user)
        QuizSessionQuestion.objects.create(quiz_session=self.session, question=self.question, position=0)

    def test_marks_the_session_abandoned_without_marking_it_complete(self):
        response = self.client.post(reverse("quiz-session-abandon", args=[self.session.pk]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.session.refresh_from_db()
        self.assertTrue(self.session.is_abandoned)
        self.assertFalse(self.session.is_complete)

    def test_no_longer_returned_as_the_active_session_afterward(self):
        self.client.post(reverse("quiz-session-abandon", args=[self.session.pk]))
        response = self.client.get(reverse("quiz-session-active"))
        self.assertIsNone(response.data["session"])

    def test_cannot_abandon_another_students_session(self):
        self.client.force_authenticate(self.other_user)
        response = self.client.post(reverse("quiz-session-abandon", args=[self.session.pk]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.session.refresh_from_db()
        self.assertFalse(self.session.is_abandoned)


class BookmarkToggleAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="mark@example.com", password="a-strong-password-123")
        self.client.force_authenticate(self.user)
        self.question = make_question()

    def test_toggling_creates_then_removes_a_bookmark(self):
        url = reverse("quiz-bookmark-toggle")
        payload = {"question_id": str(self.question.id)}

        first = self.client.post(url, payload, format="json")
        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertTrue(first.data["marked"])
        self.assertTrue(Bookmark.objects.filter(student=self.user, question=self.question).exists())

        second = self.client.post(url, payload, format="json")
        self.assertFalse(second.data["marked"])
        self.assertFalse(Bookmark.objects.filter(student=self.user, question=self.question).exists())
