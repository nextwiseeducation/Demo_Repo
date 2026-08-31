from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.questions.tests import make_question
from apps.quizzes.models import QuizSession

from .models import QuestionIssueReport, QuizFeedback

User = get_user_model()


def auth_client(client):
    user = User.objects.create_user(
        email="student@example.com", password="a-strong-password-123", is_active=True
    )
    login = client.post(
        reverse("login"), {"email": "student@example.com", "password": "a-strong-password-123"}
    )
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
            self.valid_payload(
                had_question_issue=True,
                issue_question_number=17,
                issue_description="Answer key looked wrong.",
            ),
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


class QuizSessionOwnershipTests(APITestCase):
    """
    A supplied `quiz_session` must belong to the caller.

    Both serializers already refuse to trust a client-supplied `student`
    (they overwrite it with request.user), but `quiz_session` was accepted
    straight from the request body with no ownership check — so an
    authenticated attacker could attach their own feedback or issue report
    to another student's session, corrupting that student's per-session
    data. These tests pin the fix.
    """

    def setUp(self):
        # The victim owns a session; the attacker is a separate, ordinary
        # authenticated account with no relationship to it.
        self.victim = User.objects.create_user(
            email="victim@example.com", password="a-strong-password-123", is_active=True
        )
        self.victim_session = QuizSession.objects.create(student=self.victim)

        self.attacker = User.objects.create_user(
            email="attacker@example.com", password="a-strong-password-123", is_active=True
        )
        login = self.client.post(
            reverse("login"), {"email": "attacker@example.com", "password": "a-strong-password-123"}
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    def feedback_payload(self, **overrides):
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

    def test_feedback_cannot_attach_to_another_students_session(self):
        response = self.client.post(
            reverse("quiz-feedback"),
            self.feedback_payload(quiz_session=str(self.victim_session.pk)),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("quiz_session", response.data)
        # Nothing may be written at all — a rejected request must not leave
        # a row behind with the session merely stripped off.
        self.assertEqual(QuizFeedback.objects.count(), 0)

    def test_issue_report_cannot_attach_to_another_students_session(self):
        response = self.client.post(
            reverse("question-issue-report"),
            {"issue_type": "UNCLEAR", "quiz_session": str(self.victim_session.pk)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("quiz_session", response.data)
        self.assertEqual(QuestionIssueReport.objects.count(), 0)

    def test_feedback_accepts_the_callers_own_session(self):
        # The guard must reject only OTHER people's sessions, not the
        # feature itself.
        own_session = QuizSession.objects.create(student=self.attacker)

        response = self.client.post(
            reverse("quiz-feedback"),
            self.feedback_payload(quiz_session=str(own_session.pk)),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(QuizFeedback.objects.get().quiz_session_id, own_session.pk)

    def test_feedback_still_accepts_an_omitted_session(self):
        # quiz_session is legitimately optional until Milestone 3: the
        # frontend quiz still runs on mock data with fake ids, so there is
        # often no real QuizSession to link to. Omitting it must stay valid.
        response = self.client.post(reverse("quiz-feedback"), self.feedback_payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(QuizFeedback.objects.get().quiz_session_id)

    def test_unknown_session_id_is_indistinguishable_from_someone_elses(self):
        # The rejection message must not reveal whether the id exists,
        # otherwise the endpoint becomes a way to enumerate other students'
        # session ids.
        stranger = self.client.post(
            reverse("quiz-feedback"),
            self.feedback_payload(quiz_session=str(self.victim_session.pk)),
            format="json",
        )
        nonexistent = self.client.post(
            reverse("quiz-feedback"),
            self.feedback_payload(quiz_session="00000000-0000-0000-0000-000000000000"),
            format="json",
        )

        self.assertEqual(stranger.status_code, nonexistent.status_code)
        # Compare the error CODES, not the rendered strings: DRF's message
        # echoes back the pk that was submitted, so the two differ only by
        # the attacker's own input. Matching codes is what proves the server
        # treats "belongs to someone else" and "does not exist" as the same
        # outcome and reveals nothing about which sessions are real.
        self.assertEqual(stranger.data["quiz_session"][0].code, nonexistent.data["quiz_session"][0].code)
        self.assertEqual(stranger.data["quiz_session"][0].code, "does_not_exist")


class FreeTextLengthCapTests(APITestCase):
    """
    The free-text fields are capped at the serializer so an authenticated
    account can't cheaply fill the database with unbounded text. The caps
    are far above genuine student prose, so these tests use deliberately
    absurd input rather than anything a real user would type.
    """

    def setUp(self):
        auth_client(self.client)

    def test_over_length_feedback_text_is_rejected(self):
        response = self.client.post(
            reverse("quiz-feedback"),
            {
                "overall_rating": 4,
                "question_quality_rating": 5,
                "difficulty_rating": "JUST_RIGHT",
                "realism_rating": "VERY_REALISTIC",
                "rationale_helpfulness_rating": 5,
                "had_question_issue": False,
                "recommend_likelihood": "PROBABLY_YES",
                "liked_most": "x" * 5001,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("liked_most", response.data)

    def test_normal_length_prose_is_accepted(self):
        # Guards against a cap set so tight it inconveniences a real user
        # writing a detailed complaint.
        response = self.client.post(
            reverse("quiz-feedback"),
            {
                "overall_rating": 4,
                "question_quality_rating": 5,
                "difficulty_rating": "JUST_RIGHT",
                "realism_rating": "VERY_REALISTIC",
                "rationale_helpfulness_rating": 5,
                "had_question_issue": False,
                "recommend_likelihood": "PROBABLY_YES",
                "improvement_suggestion": "This is a detailed paragraph of feedback. " * 40,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
