from django.conf import settings
from django.db import models

from apps.core.models import UUIDPKMixin
from apps.questions.models import AnswerChoice, Question


class QuizSession(UUIDPKMixin, models.Model):
    """
    One student's attempt at a set of questions — created when a student
    starts a quiz (filters -> question set), and updated as they progress
    through it. No TimeStampedMixin here since started_at/completed_at
    below already cover the timestamps this model actually needs (a
    generic updated_at wouldn't add anything meaningful).
    """

    # settings.AUTH_USER_MODEL (not importing User directly from
    # apps.accounts.models) is the Django-recommended way to reference the
    # user model in a ForeignKey — avoids a hard cross-app import and
    # respects whatever AUTH_USER_MODEL is configured to, even though in
    # practice it always resolves to apps.accounts.User here.
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quiz_sessions"
    )
    # The actual set of questions in this quiz — a ManyToMany rather than a
    # fixed-size set of ForeignKeys, since a quiz can contain any number of
    # questions decided at creation time by the student's filter choices.
    questions = models.ManyToManyField(Question, related_name="quiz_sessions")
    # Tracks progress through `questions` (e.g. index 3 = currently on the
    # 4th question) — what makes "resume mid-quiz" possible (CLAUDE.md
    # Milestone 3 requirement) without recomputing progress from
    # StudentResponseLog each time.
    current_question_index = models.IntegerField(default=0)
    is_complete = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    # Only set once the session is actually finished — stays null for the
    # entire duration the student is still taking the quiz.
    completed_at = models.DateTimeField(null=True, blank=True)
    # Stores what filters (category, difficulty, question type, topic, ...)
    # the student used to build this session, so it can be reconstructed
    # or reused without a rigid filter schema.
    # JSONField chosen deliberately over a fixed set of FK/choice columns:
    # the exact filter shape (which categories, difficulty range, question
    # types, etc.) is still evolving as quiz-building UI gets built in
    # Milestone 3, so this avoids a migration every time a new filter type
    # is added — at the cost of not being queryable/indexable the way a
    # normal column would be.
    filter_config = models.JSONField(default=dict, blank=True)

    class Meta:
        # Most recently started sessions first — matches how a "resume your
        # last quiz" or history view would want to list them.
        ordering = ["-started_at"]

    def __str__(self):
        return f"QuizSession({self.student}, {self.started_at:%Y-%m-%d})"


class StudentResponseLog(UUIDPKMixin, models.Model):
    """
    Logs which distractor a student picked, not just correct/incorrect —
    required for the Phase 2 "why did I get this wrong" AI feature and
    clinical judgment analysis (see CLAUDE.md).
    """

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="response_logs"
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="response_logs")
    # Single-answer question types (MCQ, EMR-as-single) use selected_choice;
    # SATA/EMR-multi use selected_choices. Both stay nullable/optional since
    # which one applies depends on the question's type.
    # on_delete=SET_NULL (not CASCADE): if the referenced AnswerChoice is
    # ever deleted (e.g. a content edit removes a distractor), this
    # historical response log entry should NOT be deleted along with it —
    # it stays as a record that "the student answered this question and got
    # it right/wrong", just losing the specific-choice detail. Requires
    # null=True, which is already set for this field.
    selected_choice = models.ForeignKey(
        AnswerChoice, on_delete=models.SET_NULL, null=True, blank=True, related_name="single_responses"
    )
    # For SATA (and any other multi-correct-answer type): every choice the
    # student selected, not just one. blank=True since a ManyToMany field
    # is optional by nature at the database level regardless (there's no
    # NOT NULL equivalent for M2M — an empty set is always valid), stated
    # here for form/admin validation purposes.
    selected_choices = models.ManyToManyField(AnswerChoice, blank=True, related_name="multi_responses")
    # No default — every response log entry must explicitly state whether
    # it was correct at creation time (this is computed by the scoring
    # logic that creates the row, not inferred later from selected_choice).
    is_correct = models.BooleanField()
    # How long the student spent on this question — feeds future analytics
    # (e.g. "students spend unusually long on this question" as a signal
    # the question might be ambiguous or genuinely hard).
    time_taken_seconds = models.IntegerField()
    # Which QuizSession this individual answer belongs to — lets all
    # answers for one quiz attempt be retrieved together (session.response_logs.all())
    # separately from a student's full answer history across all sessions
    # (student.response_logs.all()).
    quiz_session = models.ForeignKey(QuizSession, on_delete=models.CASCADE, related_name="response_logs")
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-answered_at"]

    def __str__(self):
        # question_id (not question, i.e. the raw FK id rather than
        # triggering a full Question fetch via __str__) — keeps this cheap
        # to render in bulk admin list views, where fetching+truncating
        # every related Question's stem for every row would be wasteful.
        return f"{self.student} -> {self.question_id} ({'correct' if self.is_correct else 'incorrect'})"
