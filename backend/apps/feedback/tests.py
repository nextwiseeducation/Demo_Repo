from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.questions.tests import make_question

from .models import QuestionIssueReport, QuizFeedback

User = get_user_model()


def auth_client(client):
    user = User.objects.create_user(email="student@example.com", password="a-strong-password-123", is_active=True)
    login = client.post(reverse("login"), {"email": "student@example.com", "password": "a-strong-password-123"})
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
    return user


class QuizFeedbackTests(APITestCase):
    def valid_payload(self, **overrides):
        payload = dict(
            overall_rating=4,
            question_quality_rating=5,
            difficulty_rating="JUST_RIGHT",
            realism_rating="VERY_REALISTIC",
            rationale_helpfulness_rating=5,
            had_question_issue=False,
            recommend_likelihood="PROBABLY_YES",
        )
        payload.update(overrides)
        return payload

    def test_submit_feedback_assigns_authenticated_student(self):
        user = auth_client(self.client)

        response = self.client.post(reverse("quiz-feedback"), self.valid_payload())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        feedback = QuizFeedback.objects.get()
        self.assertEqual(feedback.student, user)
        self.assertEqual(feedback.overall_rating, 4)

    def test_submit_feedback_requires_authentication(self):
        response = self.client.post(reverse("quiz-feedback"), self.valid_payload())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_rating_out_of_range_rejected(self):
        auth_client(self.client)
        response = self.client.post(reverse("quiz-feedback"), self.valid_payload(overall_rating=6))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_question_issue_details_are_optional(self):
        # had_question_issue=False and no quiz_session (mock quiz flow has
        # no real session to link to yet) — should still succeed, since
        # quiz_session/issue_question_number/issue_description are all
        # optional on the model.
        auth_client(self.client)
        response = self.client.post(reverse("quiz-feedback"), self.valid_payload())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_reported_issue_captures_question_number_and_description(self):
        auth_client(self.client)
        response = self.client.post(
            reverse("quiz-feedback"),
            self.valid_payload(had_question_issue=True, issue_question_number=17, issue_description="Answer key looked wrong."),
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        feedback = QuizFeedback.objects.get()
        self.assertTrue(feedback.had_question_issue)
        self.assertEqual(feedback.issue_question_number, 17)


class QuestionIssueReportTests(APITestCase):
    def test_report_without_a_real_question_still_succeeds(self):
        # Mirrors today's mock quiz flow: no real Question row exists for
        # the question being reported, so the frontend sends only a text
        # snapshot, no `question` id.
        auth_client(self.client)
        response = self.client.post(
            reverse("question-issue-report"),
            {
                "question_stem_snapshot": "A client with heart failure reports weight gain...",
                "question_number_in_quiz": 3,
                "issue_type": "UNCLEAR",
                "description": "Not sure what 'priority' means here.",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        report = QuestionIssueReport.objects.get()
        self.assertIsNone(report.question)
        self.assertEqual(report.status, "OPEN")

    def test_report_can_link_a_real_question(self):
        auth_client(self.client)
        question = make_question()

        response = self.client.post(
            reverse("question-issue-report"),
            {"question": str(question.pk), "issue_type": "ANSWER_INCORRECT"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        report = QuestionIssueReport.objects.get()
        self.assertEqual(report.question, question)

    def test_status_cannot_be_set_by_the_client(self):
        # status is read_only on the serializer — even if a client tries to
        # submit a report that's already "RESOLVED", it should be ignored
        # and the model default (OPEN) should win.
        auth_client(self.client)
        response = self.client.post(
            reverse("question-issue-report"),
            {"issue_type": "TYPO_GRAMMAR", "status": "RESOLVED"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "OPEN")

    def test_report_requires_authentication(self):
        response = self.client.post(reverse("question-issue-report"), {"issue_type": "OTHER"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
