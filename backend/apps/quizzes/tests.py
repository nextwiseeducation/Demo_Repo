from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.questions.models import AnswerChoice

# Reuses the make_question() fixture helper defined in apps.questions.tests
# instead of duplicating that taxonomy + Question setup boilerplate here —
# cross-app test-helper reuse, not a production code dependency.
from apps.questions.tests import make_question

from .models import QuizSession, StudentResponseLog

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
        # app's tests.
        session = QuizSession.objects.create(student=self.student)
        session.questions.add(question)
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
