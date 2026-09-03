from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsContentAdminOrAbove
from apps.admin_api.serializers.feedback import (
    AdminQuestionIssueReportDetailSerializer,
    AdminQuestionIssueReportListSerializer,
    AdminQuestionIssueReportStatusUpdateSerializer,
    AdminQuizFeedbackDetailSerializer,
    AdminQuizFeedbackListSerializer,
    AdminQuizFeedbackStatusUpdateSerializer,
)
from apps.core.pagination import AdminFeedbackPagination
from apps.feedback.models import QuestionIssueReport, QuizFeedback

SURVEY_KIND = "survey"
ISSUE_KIND = "issue"
VALID_KINDS = (SURVEY_KIND, ISSUE_KIND)

_MODEL_BY_KIND = {SURVEY_KIND: QuizFeedback, ISSUE_KIND: QuestionIssueReport}
_LIST_SERIALIZER_BY_KIND = {
    SURVEY_KIND: AdminQuizFeedbackListSerializer,
    ISSUE_KIND: AdminQuestionIssueReportListSerializer,
}
_DETAIL_SERIALIZER_BY_KIND = {
    SURVEY_KIND: AdminQuizFeedbackDetailSerializer,
    ISSUE_KIND: AdminQuestionIssueReportDetailSerializer,
}
_STATUS_SERIALIZER_BY_KIND = {
    SURVEY_KIND: AdminQuizFeedbackStatusUpdateSerializer,
    ISSUE_KIND: AdminQuestionIssueReportStatusUpdateSerializer,
}


def _require_valid_kind(kind: str) -> None:
    if kind not in VALID_KINDS:
        raise ValidationError({"kind": [f"Must be one of {VALID_KINDS}."]})


class AdminFeedbackListView(generics.ListAPIView):
    """
    GET /api/admin/feedback/?kind=survey|issue&status=... — the Feedback
    dashboard's two tabs (end-of-quiz survey responses, and per-question
    issue reports) share one list endpoint, disambiguated by `kind`, since
    they're the same screen's two tabs and a single query-string switch is
    simpler than two near-identical endpoints.
    """

    permission_classes = [IsContentAdminOrAbove]
    pagination_class = AdminFeedbackPagination

    def get_serializer_class(self):
        kind = self.request.query_params.get("kind", SURVEY_KIND)
        _require_valid_kind(kind)
        return _LIST_SERIALIZER_BY_KIND[kind]

    def get_queryset(self):
        kind = self.request.query_params.get("kind", SURVEY_KIND)
        _require_valid_kind(kind)
        queryset = _MODEL_BY_KIND[kind].objects.select_related("student")
        if status_filter := self.request.query_params.get("status"):
            queryset = queryset.filter(status=status_filter)
        return queryset


class AdminFeedbackDetailView(APIView):
    """
    GET /api/admin/feedback/<kind>/<id>/ — full detail for the side panel.
    PATCH /api/admin/feedback/<kind>/<id>/ — status update only.
    DELETE /api/admin/feedback/<kind>/<id>/ — remove the record.

    `kind` in the URL (rather than inferring it from the id) disambiguates
    which of the two independent models — QuizFeedback or
    QuestionIssueReport — this id belongs to; both use UUID primary keys
    from unrelated sequences, so there's no way to tell them apart from the
    id alone.
    """

    permission_classes = [IsContentAdminOrAbove]

    def _get_object(self, kind: str, pk: str):
        _require_valid_kind(kind)
        model = _MODEL_BY_KIND[kind]
        # Malformed UUIDs never reach here: the <uuid:pk> URL converter
        # (see admin_api/urls.py) only matches well-formed UUID strings.
        return get_object_or_404(model.objects.select_related("student"), pk=pk)

    def get(self, request, kind: str, pk: str):
        obj = self._get_object(kind, pk)
        serializer = _DETAIL_SERIALIZER_BY_KIND[kind](obj)
        return Response(serializer.data)

    def patch(self, request, kind: str, pk: str):
        obj = self._get_object(kind, pk)
        serializer = _STATUS_SERIALIZER_BY_KIND[kind](obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(_DETAIL_SERIALIZER_BY_KIND[kind](obj).data)

    def delete(self, request, kind: str, pk: str):
        obj = self._get_object(kind, pk)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
