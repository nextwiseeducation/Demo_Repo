from rest_framework import generics, permissions

from .serializers import QuestionIssueReportSerializer, QuizFeedbackSerializer


class QuizFeedbackCreateView(generics.CreateAPIView):
    """POST-only: submits the end-of-quiz survey. No read endpoints — feedback is reviewed via the admin."""

    serializer_class = QuizFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]


class QuestionIssueReportCreateView(generics.CreateAPIView):
    """POST-only: submits a single 'Report an Issue' click on a question."""

    serializer_class = QuestionIssueReportSerializer
    permission_classes = [permissions.IsAuthenticated]
