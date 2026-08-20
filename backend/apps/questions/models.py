from django.db import models

from apps.core.models import TimeStampedMixin, UUIDPKMixin
from apps.taxonomy.models import CaseStudy, ClientNeedsCategory, ClientNeedsSubcategory, NursingSystem, Subtopic, Tag, Topic


class QuestionType(models.TextChoices):
    MCQ = "MCQ", "Multiple Choice (single answer)"
    SATA = "SATA", "Select All That Apply"
    MATRIX = "MATRIX", "Matrix/Grid"
    BOWTIE = "BOWTIE", "Bow-Tie"
    EMR = "EMR", "Extended Multiple Response"
    DRAG_DROP = "DRAG_DROP", "Drag and Drop"
    CLOZE = "CLOZE", "Drop-down Cloze"
    HOTSPOT = "HOTSPOT", "Enhanced Hot Spot"
    NGN_CASE = "NGN_CASE", "NGN Case Study"


class Difficulty(models.TextChoices):
    EASY = "EASY", "Easy"
    MEDIUM = "MEDIUM", "Medium"
    HARD = "HARD", "Hard"


class ClinicalJudgmentSkill(models.TextChoices):
    RECOGNIZE_CUES = "RECOGNIZE_CUES", "Recognize Cues"
    ANALYZE_CUES = "ANALYZE_CUES", "Analyze Cues"
    PRIORITIZE_HYPOTHESES = "PRIORITIZE_HYPOTHESES", "Prioritize Hypotheses"
    GENERATE_SOLUTIONS = "GENERATE_SOLUTIONS", "Generate Solutions"
    TAKE_ACTION = "TAKE_ACTION", "Take Action"
    EVALUATE_OUTCOMES = "EVALUATE_OUTCOMES", "Evaluate Outcomes"


class CognitiveLevel(models.TextChoices):
    REMEMBER = "REMEMBER", "Remember"
    UNDERSTAND = "UNDERSTAND", "Understand"
    APPLY = "APPLY", "Apply"
    ANALYZE = "ANALYZE", "Analyze"
    EVALUATE = "EVALUATE", "Evaluate"
    CREATE = "CREATE", "Create"


class Question(UUIDPKMixin, TimeStampedMixin, models.Model):
    question_type = models.CharField(max_length=20, choices=QuestionType.choices)
    # When question_type=NGN_CASE, ngn_type says which item-type this case
    # question renders as (a case study is a sequence of ordinary items —
    # MCQ, MATRIX, BOWTIE, etc. — sharing one clinical_scenario/case_study).
    ngn_type = models.CharField(max_length=20, choices=QuestionType.choices, null=True, blank=True)

    stem = models.TextField()
    clinical_scenario = models.TextField(null=True, blank=True)
    case_study = models.ForeignKey(
        CaseStudy, on_delete=models.CASCADE, null=True, blank=True, related_name="questions"
    )
    case_study_sequence = models.IntegerField(null=True, blank=True)
    image = models.FileField(upload_to="question_images/", null=True, blank=True)

    difficulty = models.CharField(max_length=10, choices=Difficulty.choices)

    nursing_system = models.ForeignKey(NursingSystem, on_delete=models.PROTECT, related_name="questions")
    topic = models.ForeignKey(Topic, on_delete=models.PROTECT, related_name="questions")
    subtopic = models.ForeignKey(
        Subtopic, on_delete=models.PROTECT, null=True, blank=True, related_name="questions"
    )
    nclex_client_needs_category = models.ForeignKey(
        ClientNeedsCategory, on_delete=models.PROTECT, related_name="questions"
    )
    nclex_client_needs_subcategory = models.ForeignKey(
        ClientNeedsSubcategory, on_delete=models.PROTECT, related_name="questions"
    )

    clinical_judgment_skill = models.CharField(max_length=25, choices=ClinicalJudgmentSkill.choices)
    cognitive_level = models.CharField(max_length=15, choices=CognitiveLevel.choices)
    tags = models.ManyToManyField(Tag, blank=True, related_name="questions")

    rationale_correct = models.TextField()
    rationale_incorrect = models.TextField(null=True, blank=True)
    reference = models.TextField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.question_type}] {self.stem[:60]}"


class AnswerChoice(UUIDPKMixin, models.Model):
    """Used by MCQ, SATA, and EMR — question_type controls scoring rules, not the schema."""

    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answer_choices")
    choice_text = models.TextField()
    is_correct = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return f"{self.choice_text[:40]} ({'correct' if self.is_correct else 'incorrect'})"


# --- NGN stub models: schema only, no rendering logic until Phase 2 ---


class MatrixRow(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="matrix_rows")
    text = models.TextField()
    display_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return self.text[:40]


class MatrixColumn(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="matrix_columns")
    text = models.CharField(max_length=255)
    display_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return self.text[:40]


class MatrixCell(models.Model):
    row = models.ForeignKey(MatrixRow, on_delete=models.CASCADE, related_name="cells")
    column = models.ForeignKey(MatrixColumn, on_delete=models.CASCADE, related_name="cells")
    is_correct = models.BooleanField(default=False)

    class Meta:
        unique_together = ("row", "column")

    def __str__(self):
        return f"{self.row} x {self.column} ({'correct' if self.is_correct else 'incorrect'})"


class BowTieSection(models.TextChoices):
    ASSESSMENT = "ASSESSMENT", "Assessment"
    CONDITION = "CONDITION", "Condition"
    ACTION = "ACTION", "Action"


class BowTieOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="bowtie_options")
    section = models.CharField(max_length=15, choices=BowTieSection.choices)
    option_text = models.TextField()
    is_correct = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["section", "display_order"]

    def __str__(self):
        return f"[{self.section}] {self.option_text[:40]}"


class ClozeBlank(models.Model):
    """blank_key must match a {{token}} placeholder in the parent Question.stem."""

    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="cloze_blanks")
    blank_key = models.CharField(max_length=50)
    display_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["display_order"]
        unique_together = ("question", "blank_key")

    def __str__(self):
        return self.blank_key


class ClozeOption(models.Model):
    blank = models.ForeignKey(ClozeBlank, on_delete=models.CASCADE, related_name="options")
    option_text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.option_text


class DragDropCategory(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="dragdrop_categories")
    name = models.CharField(max_length=150)
    display_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return self.name


class DragDropItem(models.Model):
    """
    Covers both drag-drop variants without a third model: sort-into-buckets
    sets correct_category and leaves correct_order null; sequence/prioritize
    sets correct_order and leaves correct_category null.
    """

    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="dragdrop_items")
    text = models.TextField()
    display_order = models.IntegerField(default=0)
    correct_category = models.ForeignKey(
        DragDropCategory, on_delete=models.CASCADE, null=True, blank=True, related_name="items"
    )
    correct_order = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return self.text[:40]


class HotSpotTarget(models.Model):
    """
    Text-based Enhanced Hot Spot: the student selects the correct word/phrase
    within the question's stem or clinical_scenario. Question.image remains
    available separately for accompanying lab tables/diagrams — this model
    assumes text spans, not image click-coordinates. Confirm with the content
    team before writing HOTSPOT content if image-region hotspots are wanted
    instead; that needs coordinate fields and would be a schema change.
    """

    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="hotspot_targets")
    target_text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return self.target_text
