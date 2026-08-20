from django.conf import settings
from django.db import models

from apps.core.models import UUIDPKMixin
from apps.questions.models import AnswerChoice, Question


class QuizSession(UUIDPKMixin, models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quiz_sessions")
    questions = models.ManyToManyField(Question, related_name="quiz_sessions")
    current_question_index = models.IntegerField(default=0)
    is_complete = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    # Stores what filters (category, difficulty, question type, topic, ...)
    # the student used to build this session, so it can be reconstructed
    # or reused without a rigid filter schema.
    filter_config = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"QuizSession({self.student}, {self.started_at:%Y-%m-%d})"


class StudentResponseLog(UUIDPKMixin, models.Model):
    """
    Logs which distractor a student picked, not just correct/incorrect —
    required for the Phase 2 "why did I get this wrong" AI feature and
    clinical judgment analysis (see CLAUDE.md).
    """

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="response_logs")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="response_logs")
    # Single-answer question types (MCQ, EMR-as-single) use selected_choice;
    # SATA/EMR-multi use selected_choices. Both stay nullable/optional since
    # which one applies depends on the question's type.
    selected_choice = models.ForeignKey(
        AnswerChoice, on_delete=models.SET_NULL, null=True, blank=True, related_name="single_responses"
    )
    selected_choices = models.ManyToManyField(AnswerChoice, blank=True, related_name="multi_responses")
    is_correct = models.BooleanField()
    time_taken_seconds = models.IntegerField()
    quiz_session = models.ForeignKey(QuizSession, on_delete=models.CASCADE, related_name="response_logs")
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-answered_at"]

    def __str__(self):
        return f"{self.student} -> {self.question_id} ({'correct' if self.is_correct else 'incorrect'})"
