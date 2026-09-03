from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.accounts.permissions import IsContentAdminOrAbove
from apps.admin_api.serializers.imports import (
    ImportLogSerializer,
    ImportResultSerializer,
    QuestionImportUploadSerializer,
)
from apps.core.pagination import AdminTablePagination
from apps.questions.importer import InvalidWorkbookError, NgnItemBankImporter, write_import_log
from apps.questions.models import ImportLog


class QuestionImportView(APIView):
    """
    POST /api/admin/import/ — uploads an NGN Item Bank workbook and imports
    it synchronously, returning per-row results.

    Synchronous by decision: this project has no task queue (no Celery, no
    Redis — config/settings/base.py's CACHES uses DatabaseCache precisely
    because Render's free tier has no Redis broker), so a 202-plus-polling
    design would need new infrastructure. The cost is that a large workbook
    holds a gunicorn worker for the run's duration — MAX_IMPORT_FILE_BYTES
    (apps.questions.importer) and the "admin_import" throttle scope
    (config/settings/base.py) bound that together with a raised gunicorn
    worker timeout (render.yaml).

    Partial success is the contract, matching the management command's
    per-row isolation: a workbook with 3 bad rows out of 200 returns 200
    with 197 imported and 3 entries in `errors`, not a 400.
    """

    permission_classes = [IsContentAdminOrAbove]
    parser_classes = [MultiPartParser]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "admin_import"

    def post(self, request):
        serializer = QuestionImportUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        upload = serializer.validated_data["file"]

        importer = NgnItemBankImporter(
            allow_update=serializer.validated_data["update"],
            dry_run=serializer.validated_data["dry_run"],
        )
        try:
            result = importer.run(upload)
        except InvalidWorkbookError as exc:
            # A wrong-format upload or one missing a required sheet raises
            # deep inside openpyxl/read_sheets — caught here so it's a 400,
            # not a 500.
            return Response({"file": [str(exc)]}, status=status.HTTP_400_BAD_REQUEST)

        write_import_log(result, uploaded_by=request.user, source_filename=upload.name)
        return Response(ImportResultSerializer(result).data)


class AdminImportLogListView(generics.ListAPIView):
    """GET /api/admin/import-log/ — paginated history of past bulk imports, most recent first."""

    serializer_class = ImportLogSerializer
    permission_classes = [IsContentAdminOrAbove]
    pagination_class = AdminTablePagination
    queryset = ImportLog.objects.select_related("uploaded_by")
