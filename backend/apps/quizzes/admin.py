from django.contrib import admin

from .models import QuizSession, StudentResponseLog


@admin.register(QuizSession)
class QuizSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "is_complete", "started_at", "completed_at")
    list_filter = ("is_complete",)
    search_fields = ("student__email",)


@admin.register(StudentResponseLog)
class StudentResponseLogAdmin(admin.ModelAdmin):
    list_display = ("student", "question", "is_correct", "time_taken_seconds", "answered_at")
    list_filter = ("is_correct",)
    search_fields = ("student__email",)
