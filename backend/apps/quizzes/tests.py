from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.questions.models import AnswerChoice
from apps.questions.tests import make_question

from .models import QuizSession, StudentResponseLog

User = get_user_model()


class StudentResponseLogTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(email="student@example.com", password="a-strong-password-123")

    def _make_session(self, question):
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
        self.assertEqual(response.selected_choices.count(), 0)

    def test_sata_response_uses_selected_choices(self):
        question = make_question()
        choice_1 = AnswerChoice.objects.create(question=question, choice_text="A", is_correct=True)
        choice_2 = AnswerChoice.objects.create(question=question, choice_text="B", is_correct=True)
        session = self._make_session(question)

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
        question = make_question()
        wrong_choice = AnswerChoice.objects.create(question=question, choice_text="Distractor", is_correct=False)
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
