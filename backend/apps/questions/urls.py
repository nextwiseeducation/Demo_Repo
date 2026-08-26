from django.urls import path

from .views import QuestionListView, QuestionSubmitView

urlpatterns = [
    path("", QuestionListView.as_view(), name="question-list"),
    path("<uuid:pk>/submit/", QuestionSubmitView.as_view(), name="question-submit"),
]
