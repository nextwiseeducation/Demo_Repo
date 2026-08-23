from django.urls import path

from .views import QuestionIssueReportCreateView, QuizFeedbackCreateView

# Mounted at /api/feedback/ by config/urls.py.
urlpatterns = [
    path("quiz/", QuizFeedbackCreateView.as_view(), name="quiz-feedback"),
    path("question-issue/", QuestionIssueReportCreateView.as_view(), name="question-issue-report"),
]
