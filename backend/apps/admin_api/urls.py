from django.urls import path

from apps.admin_api.views.analytics import AdminAnalyticsView
from apps.admin_api.views.feedback import AdminFeedbackDetailView, AdminFeedbackListView
from apps.admin_api.views.imports import AdminImportLogListView, QuestionImportView
from apps.admin_api.views.questions import (
    AdminQuestionBulkDeleteView,
    AdminQuestionDetailView,
    AdminQuestionListView,
)
from apps.admin_api.views.taxonomy import AdminTaxonomyView

# Mounted at /api/admin/ by config/urls.py. Filled in phase by phase as
# each admin_api view lands — see the implementation plan.
urlpatterns = [
    path("analytics/", AdminAnalyticsView.as_view(), name="admin-analytics"),
    path("taxonomy/", AdminTaxonomyView.as_view(), name="admin-taxonomy"),
    path("questions/", AdminQuestionListView.as_view(), name="admin-question-list"),
    path("questions/bulk-delete/", AdminQuestionBulkDeleteView.as_view(), name="admin-question-bulk-delete"),
    path("questions/<uuid:pk>/", AdminQuestionDetailView.as_view(), name="admin-question-detail"),
    path("import/", QuestionImportView.as_view(), name="admin-import"),
    path("import-log/", AdminImportLogListView.as_view(), name="admin-import-log"),
    path("feedback/", AdminFeedbackListView.as_view(), name="admin-feedback-list"),
    # `kind` (survey|issue) disambiguates QuizFeedback from
    # QuestionIssueReport — see AdminFeedbackDetailView's own docstring.
    path("feedback/<str:kind>/<uuid:pk>/", AdminFeedbackDetailView.as_view(), name="admin-feedback-detail"),
]
