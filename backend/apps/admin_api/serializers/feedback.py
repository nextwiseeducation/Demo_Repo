from rest_framework import serializers

from apps.feedback.models import FeedbackStatus, QuestionIssueReport, QuizFeedback, ReportStatus

SURVEY_TEXT_PREVIEW_CHARS = 100


class AdminQuizFeedbackListSerializer(serializers.ModelSerializer):
    """
    The Feedback dashboard's Survey tab row shape. `feedback_text` is
    whichever of improvement_suggestion/liked_most the student actually
    filled in — the dashboard's "feedback text" column has one thing to
    show, but the survey form collects two separate free-text fields, so a
    single row can't just be one model field.
    """

    student_name = serializers.CharField(source="student.full_name", read_only=True)
    student_email = serializers.CharField(source="student.email", read_only=True)
    feedback_text = serializers.SerializerMethodField()

    class Meta:
        model = QuizFeedback
        fields = ["id", "student_name", "student_email", "feedback_text", "status", "created_at"]

    def get_feedback_text(self, obj: QuizFeedback) -> str:
        text = obj.improvement_suggestion or obj.liked_most or ""
        return text[:SURVEY_TEXT_PREVIEW_CHARS]


class AdminQuizFeedbackDetailSerializer(serializers.ModelSerializer):
    """The full survey response, for the detail panel — every rating plus both free-text fields, not just the preview."""

    student_name = serializers.CharField(source="student.full_name", read_only=True)
    student_email = serializers.CharField(source="student.email", read_only=True)

    class Meta:
        model = QuizFeedback
        fields = [
            "id",
            "student_name",
            "student_email",
            "overall_rating",
            "question_quality_rating",
            "difficulty_rating",
            "realism_rating",
            "rationale_helpfulness_rating",
            "had_question_issue",
            "issue_question_number",
            "issue_description",
            "liked_most",
            "improvement_suggestion",
            "recommend_likelihood",
            "status",
            "status_updated_at",
            "created_at",
        ]


class AdminQuizFeedbackStatusUpdateSerializer(serializers.ModelSerializer):
    """PATCH body for the Survey tab — status is the only field an admin may change; every student-submitted field stays read-only."""

    class Meta:
        model = QuizFeedback
        fields = ["status"]

    def validate_status(self, value):
        if value not in FeedbackStatus.values:
            raise serializers.ValidationError(f"Unknown status {value!r}.")
        return value

    def save(self, **kwargs):
        from django.utils import timezone

        return super().save(status_updated_at=timezone.now(), **kwargs)


class AdminQuestionIssueReportListSerializer(serializers.ModelSerializer):
    """The Feedback dashboard's Issue Reports tab row shape."""

    student_name = serializers.CharField(source="student.full_name", read_only=True)
    student_email = serializers.CharField(source="student.email", read_only=True)
    description_preview = serializers.SerializerMethodField()

    class Meta:
        model = QuestionIssueReport
        fields = [
            "id",
            "student_name",
            "student_email",
            "issue_type",
            "description_preview",
            "status",
            "created_at",
        ]

    def get_description_preview(self, obj: QuestionIssueReport) -> str:
        return obj.description[:SURVEY_TEXT_PREVIEW_CHARS]


class AdminQuestionIssueReportDetailSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    student_email = serializers.CharField(source="student.email", read_only=True)

    class Meta:
        model = QuestionIssueReport
        fields = [
            "id",
            "student_name",
            "student_email",
            "question",
            "question_stem_snapshot",
            "question_number_in_quiz",
            "issue_type",
            "description",
            "status",
            "created_at",
        ]


class AdminQuestionIssueReportStatusUpdateSerializer(serializers.ModelSerializer):
    """
    PATCH body for the Issue Reports tab. Uses QuestionIssueReport's own
    existing OPEN/RESOLVED/DISMISSED vocabulary (ReportStatus) rather than
    QuizFeedback's IN_CONSIDERATION/IMPLEMENTED/REJECTED — the two models
    already had independent status fields before this dashboard existed,
    and unifying them into one shared enum would mean either dropping
    ReportStatus.OPEN (there is no survey-feedback equivalent of "not yet
    triaged at all" — every QuizFeedback row starts IN_CONSIDERATION) or
    inventing a meaning for it that doesn't fit issue reports.
    """

    class Meta:
        model = QuestionIssueReport
        fields = ["status"]

    def validate_status(self, value):
        if value not in ReportStatus.values:
            raise serializers.ValidationError(f"Unknown status {value!r}.")
        return value
