from django.contrib import admin

from .models import QuestionIssueReport, QuizFeedback


@admin.register(QuizFeedback)
class QuizFeedbackAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "overall_rating",
        "question_quality_rating",
        "difficulty_rating",
        "recommend_likelihood",
        "had_question_issue",
        "created_at",
    )
    list_filter = ("difficulty_rating", "realism_rating", "recommend_likelihood", "had_question_issue")
    search_fields = ("student__email", "liked_most", "improvement_suggestion", "issue_description")
    readonly_fields = ("created_at",)


@admin.register(QuestionIssueReport)
class QuestionIssueReportAdmin(admin.ModelAdmin):
    list_display = ("__str__", "student", "issue_type", "status", "created_at")
    list_filter = ("issue_type", "status")
    search_fields = ("student__email", "question_stem_snapshot", "description")
    # Lets the content team change status directly from the list view
    # (Open -> Resolved/Dismissed) without opening each report individually.
    list_editable = ("status",)
    readonly_fields = ("created_at",)
