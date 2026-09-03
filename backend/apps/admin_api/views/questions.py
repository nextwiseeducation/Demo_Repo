from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsContentAdminOrAbove
from apps.admin_api.serializers.questions import (
    AdminQuestionDetailSerializer,
    AdminQuestionListSerializer,
    QuestionAdminSerializer,
)
from apps.admin_api.services.question_filters import apply_admin_question_filters
from apps.core.pagination import AdminTablePagination
from apps.questions.models import Question

_DETAIL_SELECT_RELATED = (
    "domain",
    "nursing_system",
    "topic",
    "subtopic",
    "nclex_client_needs_category",
    "nclex_client_needs_subcategory",
    "case_study",
)
_DETAIL_PREFETCH_RELATED = (
    "tags",
    "answer_choices",
    "matrix_rows__cells",
    "matrix_columns",
    "bowtie_options",
    "cloze_blanks__options",
    "dragdrop_categories",
    "dragdrop_items",
    "hotspot_targets",
)


class AdminQuestionListView(generics.ListCreateAPIView):
    """
    GET /api/admin/questions/ — the Content Team question table.

    Unlike apps.questions.views.QuestionListView (the student-facing
    endpoint), this deliberately does NOT filter is_active=True — an editor
    needs to see and manage retired questions too, not just what's live in
    quizzes.

    POST /api/admin/questions/ — create a question of any of the 9 types,
    full NGN structure included. See QuestionAdminSerializer for the
    payload shape and apps.questions.authoring for the per-type validation
    rules it enforces.
    """

    permission_classes = [IsContentAdminOrAbove]
    pagination_class = AdminTablePagination

    def get_serializer_class(self):
        return QuestionAdminSerializer if self.request.method == "POST" else AdminQuestionListSerializer

    def get_queryset(self):
        queryset = Question.objects.select_related("nursing_system").order_by("-created_at")
        return apply_admin_question_filters(queryset, self.request.query_params)

    def create(self, request, *args, **kwargs):
        # NOT calling super().create(): its default implementation builds
        # its response from `serializer.data`, which would run
        # QuestionAdminSerializer's own to_representation() — and that
        # serializer's nested input fields (e.g. AdminMatrixColumnInputSerializer)
        # declare write-only synthetic fields like `key` that don't exist as
        # attributes on the real model instances, so reading it back
        # crashes. Re-serializing the saved question through
        # AdminQuestionDetailSerializer instead avoids ever calling
        # QuestionAdminSerializer.data, and gives a response shaped exactly
        # like a subsequent GET .../:id/ would return.
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = serializer.save()
        question = (
            Question.objects.select_related(*_DETAIL_SELECT_RELATED)
            .prefetch_related(*_DETAIL_PREFETCH_RELATED)
            .get(pk=question.pk)
        )
        return Response(AdminQuestionDetailSerializer(question).data, status=status.HTTP_201_CREATED)


class AdminQuestionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/admin/questions/:id/ — full question detail, answer key
    included, for the edit form.
    PUT /api/admin/questions/:id/ — full update (see QuestionAdminSerializer).
    DELETE /api/admin/questions/:id/ — single-question delete.
    """

    permission_classes = [IsContentAdminOrAbove]
    queryset = Question.objects.select_related(*_DETAIL_SELECT_RELATED).prefetch_related(
        *_DETAIL_PREFETCH_RELATED
    )

    def get_serializer_class(self):
        return AdminQuestionDetailSerializer if self.request.method == "GET" else QuestionAdminSerializer

    def update(self, request, *args, **kwargs):
        # See AdminQuestionListView.create's comment: avoids ever touching
        # QuestionAdminSerializer's own to_representation().
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        question = serializer.save()
        question = (
            Question.objects.select_related(*_DETAIL_SELECT_RELATED)
            .prefetch_related(*_DETAIL_PREFETCH_RELATED)
            .get(pk=question.pk)
        )
        return Response(AdminQuestionDetailSerializer(question).data)


class AdminQuestionBulkDeleteView(APIView):
    """
    POST /api/admin/questions/bulk-delete/ — deletes every Question whose id
    appears in the request body's `ids` list.

    Unknown ids are silently ignored (deleting "everything that exists
    among these ids" is well-defined even if some no longer do — e.g. a
    stale selection from before someone else deleted one of them);
    a malformed body is a 400, not a 500.
    """

    permission_classes = [IsContentAdminOrAbove]

    def post(self, request):
        ids = request.data.get("ids")
        if not isinstance(ids, list) or not all(isinstance(i, str) for i in ids):
            return Response(
                {"ids": ["This field must be a list of question id strings."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # QuerySet.delete()'s first return value is the TOTAL rows deleted
        # across every model touched by CASCADE (answer choices, NGN child
        # rows, response logs, ...) — not just Question rows. The per-model
        # breakdown dict is what actually answers "how many questions were
        # deleted", which is the number the bulk-delete confirmation modal
        # needs to report back accurately.
        _, deleted_by_model = Question.objects.filter(id__in=ids).delete()
        deleted_count = deleted_by_model.get("questions.Question", 0)
        return Response({"deleted": deleted_count})
