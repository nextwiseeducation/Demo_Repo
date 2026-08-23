from django.contrib import admin

from .models import QuizSession, StudentResponseLog


@admin.register(QuizSession)
class QuizSessionAdmin(admin.ModelAdmin):
    # "id" (the raw UUID) is shown directly here rather than relying on
    # __str__, since QuizSession.__str__ isn't especially more informative
    # for admin browsing than the id + the other listed columns already are.
    list_display = ("id", "student", "is_complete", "started_at", "completed_at")
    list_filter = ("is_complete",)
    # __ (double underscore) traverses the ForeignKey to student's email
    # field — lets an admin search sessions by the student's email without
    # a dedicated search field on QuizSession itself.
    search_fields = ("student__email",)


@admin.register(StudentResponseLog)
class StudentResponseLogAdmin(admin.ModelAdmin):
    list_display = ("student", "question", "is_correct", "time_taken_seconds", "answered_at")
    list_filter = ("is_correct",)
    search_fields = ("student__email",)
