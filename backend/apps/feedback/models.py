from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import UUIDPKMixin
from apps.questions.models import Question
from apps.quizzes.models import QuizSession

# Shared by every 1-5 star rating field below, so the choice list (and its
# intent) isn't repeated three separate times.
STAR_RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]


class DifficultyRating(models.TextChoices):
    MUCH_TOO_EASY = "MUCH_TOO_EASY", "Much too easy"
    SOMEWHAT_EASY = "SOMEWHAT_EASY", "Somewhat easy"
    JUST_RIGHT = "JUST_RIGHT", "Just right"
    SOMEWHAT_DIFFICULT = "SOMEWHAT_DIFFICULT", "Somewhat difficult"
    MUCH_TOO_DIFFICULT = "MUCH_TOO_DIFFICULT", "Much too difficult"


class RealismRating(models.TextChoices):
    NOT_REALISTIC = "NOT_REALISTIC", "Not realistic"
    SLIGHTLY_REALISTIC = "SLIGHTLY_REALISTIC", "Slightly realistic"
    MODERATELY_REALISTIC = "MODERATELY_REALISTIC", "Moderately realistic"
    VERY_REALISTIC = "VERY_REALISTIC", "Very realistic"
    EXTREMELY_REALISTIC = "EXTREMELY_REALISTIC", "Extremely realistic"


class RecommendLikelihood(models.TextChoices):
    DEFINITELY_NOT = "DEFINITELY_NOT", "Definitely not"
    PROBABLY_NOT = "PROBABLY_NOT", "Probably not"
    MAYBE = "MAYBE", "Maybe"
    PROBABLY_YES = "PROBABLY_YES", "Probably yes"
    DEFINITELY_YES = "DEFINITELY_YES", "Definitely yes"


class QuizFeedback(UUIDPKMixin, models.Model):
    """One student's end-of-quiz survey response."""

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quiz_feedback"
    )
    # Nullable: the quiz-taking flow is still mock-only on the frontend
    # (no QuizSession row exists yet for a mock session), so this stays
    # empty until Milestone 3's real quiz engine creates real sessions to
    # link back to. SET_NULL (not CASCADE) so deleting a session doesn't
    # destroy the feedback submitted about it.
    quiz_session = models.ForeignKey(
        QuizSession, on_delete=models.SET_NULL, null=True, blank=True, related_name="feedback"
    )

    overall_rating = models.PositiveSmallIntegerField(
        choices=STAR_RATING_CHOICES, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    question_quality_rating = models.PositiveSmallIntegerField(
        choices=STAR_RATING_CHOICES, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    difficulty_rating = models.CharField(max_length=20, choices=DifficultyRating.choices)
    realism_rating = models.CharField(max_length=25, choices=RealismRating.choices)
    rationale_helpfulness_rating = models.PositiveSmallIntegerField(
        choices=STAR_RATING_CHOICES, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    # "Did you encounter any question that was unclear/incorrect/etc?" — a
    # quick free-text flag distinct from the structured per-question
    # QuestionIssueReport below: the student types a number they remember
    # rather than the frontend supplying an exact question reference.
    had_question_issue = models.BooleanField(default=False)
    issue_question_number = models.PositiveIntegerField(null=True, blank=True)
    issue_description = models.TextField(blank=True)

    liked_most = models.TextField(blank=True)
    improvement_suggestion = models.TextField(blank=True)
    recommend_likelihood = models.CharField(max_length=20, choices=RecommendLikelihood.choices)

    # Write-once: a feedback submission is never edited afterward, so only
    # created_at is needed (no updated_at/TimeStampedMixin).
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Quiz feedback"

    def __str__(self):
        return f"QuizFeedback({self.student}, {self.overall_rating}★, {self.created_at:%Y-%m-%d})"


class QuestionIssueType(models.TextChoices):
    ANSWER_INCORRECT = "ANSWER_INCORRECT", "Answer may be incorrect"
    UNCLEAR = "UNCLEAR", "Question is unclear"
    RATIONALE_NEEDS_IMPROVEMENT = "RATIONALE_NEEDS_IMPROVEMENT", "Rationale needs improvement"
    CLINICAL_INFO_INCORRECT = "CLINICAL_INFO_INCORRECT", "Clinical information seems incorrect"
    TYPO_GRAMMAR = "TYPO_GRAMMAR", "Typo/grammar"
    REFERENCE_ISSUE = "REFERENCE_ISSUE", "Reference issue"
    OTHER = "OTHER", "Other"


class ReportStatus(models.TextChoices):
    """Lets the content team triage reports from the admin without a separate workflow tool."""

    OPEN = "OPEN", "Open"
    RESOLVED = "RESOLVED", "Resolved"
    DISMISSED = "DISMISSED", "Dismissed"


class QuestionIssueReport(UUIDPKMixin, models.Model):
    """
    A single 'Report an Issue' click on a specific question — lets a
    student flag a problem in the moment instead of having to remember it
    for the end-of-quiz survey.
    """

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="question_issue_reports"
    )
    # Nullable for the same reason as QuizFeedback.quiz_session: today's
    # frontend quiz runs entirely on mock data with fake string ids (e.g.
    # "q1"), not real Question rows, so there is often nothing valid to
    # link to yet. question_stem_snapshot below is what keeps a report
    # meaningful even when this is null — once Milestone 3 serves real
    # questions, the frontend should start sending a real id here.
    question = models.ForeignKey(
        Question, on_delete=models.SET_NULL, null=True, blank=True, related_name="issue_reports"
    )
    # Captured at report time regardless of whether `question` is set —
    # protects against both the mock-data case above AND a real Question's
    # stem being edited/removed later, so the report always shows what the
    # student actually saw.
    question_stem_snapshot = models.TextField(blank=True)
    quiz_session = models.ForeignKey(
        QuizSession, on_delete=models.SET_NULL, null=True, blank=True, related_name="issue_reports"
    )
    # Position within the quiz as the student experienced it (e.g. "Q17") —
    # useful for admin triage even once `question` is reliably populated.
    question_number_in_quiz = models.PositiveIntegerField(null=True, blank=True)

    issue_type = models.CharField(max_length=30, choices=QuestionIssueType.choices)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=ReportStatus.choices, default=ReportStatus.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.issue_type}] {self.question_stem_snapshot[:40] or self.question_id} ({self.status})"
