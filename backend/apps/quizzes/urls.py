from django.urls import path

from .views import (
    BookmarkToggleView,
    QuizAnswerSubmitView,
    QuizFacetCountsView,
    QuizSessionCreateView,
)

urlpatterns = [
    path("sessions/", QuizSessionCreateView.as_view(), name="quiz-session-create"),
    path("sessions/<uuid:session_id>/answers/", QuizAnswerSubmitView.as_view(), name="quiz-session-answer"),
    path("facet-counts/", QuizFacetCountsView.as_view(), name="quiz-facet-counts"),
    path("bookmarks/toggle/", BookmarkToggleView.as_view(), name="quiz-bookmark-toggle"),
]
