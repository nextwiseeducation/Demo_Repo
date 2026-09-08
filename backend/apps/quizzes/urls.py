from django.urls import path

from .views import (
    BookmarkToggleView,
    QuizAnswerSubmitView,
    QuizFacetCountsView,
    QuizSessionAbandonView,
    QuizSessionActiveView,
    QuizSessionCreateView,
    QuizSessionRetrieveView,
)

urlpatterns = [
    path("sessions/", QuizSessionCreateView.as_view(), name="quiz-session-create"),
    path("sessions/active/", QuizSessionActiveView.as_view(), name="quiz-session-active"),
    path("sessions/<uuid:session_id>/", QuizSessionRetrieveView.as_view(), name="quiz-session-retrieve"),
    path("sessions/<uuid:session_id>/answers/", QuizAnswerSubmitView.as_view(), name="quiz-session-answer"),
    path("sessions/<uuid:session_id>/abandon/", QuizSessionAbandonView.as_view(), name="quiz-session-abandon"),
    path("facet-counts/", QuizFacetCountsView.as_view(), name="quiz-facet-counts"),
    path("bookmarks/toggle/", BookmarkToggleView.as_view(), name="quiz-bookmark-toggle"),
]
