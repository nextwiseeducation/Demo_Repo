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


class QuizAnswerSubmitAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="answer@example.com", password="a-strong-password-123")
        self.other_user = User.objects.create_user(email="other@example.com", password="a-strong-password-123")
        self.client.force_authenticate(self.user)
        self.question = make_question()
        self.correct = AnswerChoice.objects.create(question=self.question, choice_text="Correct", is_correct=True)
        AnswerChoice.objects.create(question=self.question, choice_text="Wrong", is_correct=False)
        self.session = QuizSession.objects.create(student=self.user)
        QuizSessionQuestion.objects.create(quiz_session=self.session, question=self.question, position=0)

    def _url(self, session=None):
        return reverse("quiz-session-answer", args=[(session or self.session).pk])

    def test_grading_persists_a_response_log_and_completes_the_session(self):
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

        self.session.refresh_from_db()
        # This session's only question was just answered — it should now be
        # complete, exercising the current_question_index >= total_questions
        # branch in QuizAnswerSubmitView.
        self.assertEqual(self.session.current_question_index, 1)
        self.assertTrue(self.session.is_complete)
        self.assertIsNotNone(self.session.completed_at)

    def test_cannot_submit_into_another_students_session(self):
        other_session = QuizSession.objects.create(student=self.other_user)
        QuizSessionQuestion.objects.create(quiz_session=other_session, question=self.question, position=0)
        payload = {"question_id": str(self.question.id), "selected_choice_ids": [str(self.correct.id)]}

        response = self.client.post(self._url(other_session), payload, format="json")

        # 404, not 403 — see QuizAnswerSubmitView's own comment on why: one
        # student must not learn another student's session id even exists.
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


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
