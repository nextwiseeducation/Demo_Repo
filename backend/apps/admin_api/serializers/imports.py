from django.core.validators import FileExtensionValidator
from rest_framework import serializers

from apps.questions.importer import MAX_IMPORT_FILE_BYTES
from apps.questions.models import ImportLog


def validate_import_file_size(value) -> None:
    if value.size > MAX_IMPORT_FILE_BYTES:
        raise serializers.ValidationError(
            f"Import file must be {MAX_IMPORT_FILE_BYTES // (1024 * 1024)} MB or smaller "
            f"(this file is {value.size // 1024} KB)."
        )


class QuestionImportUploadSerializer(serializers.Serializer):
    """
    xlsx/xlsm only — the item bank format is inherently a 6-sheet workbook
    (Item_Master, Answer_Options, NGN_Cases, NGN_Components, References,
    Valid_Values); a plain .csv cannot express that, so it is rejected
    here with a clear reason rather than accepted and failing obscurely
    deeper in openpyxl.
    """

    file = serializers.FileField(
        validators=[FileExtensionValidator(["xlsx", "xlsm"]), validate_import_file_size]
    )
    update = serializers.BooleanField(default=False)
    dry_run = serializers.BooleanField(default=False)


class ImportRowErrorSerializer(serializers.Serializer):
    label = serializers.CharField()
    message = serializers.CharField()


class ImportResultSerializer(serializers.Serializer):
    """Serializes the apps.questions.importer.ImportResult dataclass returned by one import run."""

    created = serializers.IntegerField()
    updated = serializers.IntegerField()
    skipped_existing = serializers.IntegerField()
    case_studies_created = serializers.IntegerField()
    case_studies_updated = serializers.IntegerField()
    questions_imported = serializers.IntegerField()
    rows_failed = serializers.IntegerField()
    created_taxonomy = serializers.SerializerMethodField()
    errors = ImportRowErrorSerializer(many=True)
    dry_run = serializers.BooleanField()

    def get_created_taxonomy(self, result) -> list[str]:
        return result.distinct_taxonomy


class ImportLogSerializer(serializers.ModelSerializer):
    uploaded_by_email = serializers.CharField(source="uploaded_by.email", read_only=True, default=None)

    class Meta:
        model = ImportLog
        fields = [
            "id",
            "uploaded_at",
            "uploaded_by_email",
            "source_filename",
            "questions_imported",
            "rows_failed",
            "errors",
        ]
