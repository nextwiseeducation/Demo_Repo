from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models

from apps.core.models import TimeStampedMixin, UUIDPKMixin
from apps.taxonomy.models import (
    CaseStudy,
    ClientNeedsCategory,
    ClientNeedsSubcategory,
    Domain,
    NursingSystem,
    Subtopic,
    Tag,
    Topic,
)

# Matches DATA_UPLOAD_MAX_MEMORY_SIZE/FILE_UPLOAD_MAX_MEMORY_SIZE in
# config/settings/base.py — those bound what Django will accept for a whole
# request; this bounds the single field, so the limit is the same number
# whichever layer rejects it first and an editor gets a field-level error
# message rather than a generic 400 from the upload machinery.
MAX_QUESTION_IMAGE_BYTES = 5 * 1024 * 1024

# Raster formats only. Deliberately NOT svg: an SVG is an XML document that
# can carry <script>, so the moment question images are served from a real
# host (see MEDIA_ROOT's note in settings — production needs an object store
# in front of this) an uploaded .svg becomes stored XSS running on the
# platform's own origin. Same reasoning excludes .html/.htm and anything
# else the browser will execute rather than decode as pixels.
ALLOWED_QUESTION_IMAGE_EXTENSIONS = ["png", "jpg", "jpeg", "gif", "webp"]


def validate_question_image_size(value) -> None:
    """
    Rejects an oversized Question.image upload with a readable field error.

    Defined at module level, not as a lambda or a nested/bound function,
    because Django serializes every validator on a field into the migration
    that adds it — a callable the migration file can't import by path
    (`apps.questions.models.validate_question_image_size`) can't be written
    into a migration at all.
    """

    if value.size > MAX_QUESTION_IMAGE_BYTES:
        raise ValidationError(
            f"Image must be {MAX_QUESTION_IMAGE_BYTES // (1024 * 1024)} MB or smaller "
            f"(this file is {value.size // 1024} KB)."
        )


class QuestionType(models.TextChoices):
    """
    Every question format the schema is built to support, per CLAUDE.md's
    Milestone 1 brief. Only MCQ/SATA are actually rendered by the (future)
    quiz UI in Phase 1 — the rest (MATRIX through NGN_CASE) have their data
    model in place now ("stubbed") specifically so 4,000+ questions across
    all these types can be imported starting now, without waiting for
    Phase 2's rendering UI and without a schema migration once that UI
    exists.
    """

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
    """
    The six steps of NCSBN's Clinical Judgment Measurement Model (the
    framework the actual NCLEX exam uses to structure Next Generation NCLEX
    items) — tagging each question with which step it exercises is what
    lets Phase 2's "weak area by clinical judgment skill" analytics exist
    without re-tagging the question bank later.
    """

    RECOGNIZE_CUES = "RECOGNIZE_CUES", "Recognize Cues"
    ANALYZE_CUES = "ANALYZE_CUES", "Analyze Cues"
    PRIORITIZE_HYPOTHESES = "PRIORITIZE_HYPOTHESES", "Prioritize Hypotheses"
    GENERATE_SOLUTIONS = "GENERATE_SOLUTIONS", "Generate Solutions"
    TAKE_ACTION = "TAKE_ACTION", "Take Action"
    EVALUATE_OUTCOMES = "EVALUATE_OUTCOMES", "Evaluate Outcomes"


class CognitiveLevel(models.TextChoices):
    """Bloom's Taxonomy levels — how deep the reasoning a question demands is, independent of clinical_judgment_skill (which measures WHERE in the CJ process the question sits, not how hard the thinking is)."""

    REMEMBER = "REMEMBER", "Remember"
    UNDERSTAND = "UNDERSTAND", "Understand"
    APPLY = "APPLY", "Apply"
    ANALYZE = "ANALYZE", "Analyze"
    EVALUATE = "EVALUATE", "Evaluate"
    CREATE = "CREATE", "Create"


class Question(UUIDPKMixin, TimeStampedMixin, models.Model):
    # UUIDPKMixin: id is a UUID, not a sequential int (see apps/core/models.py)
    # — deliberate for a table that will hold 4,000+ rows referenced
    # externally (URLs, StudentResponseLog, quiz session state).
    # TimeStampedMixin: adds created_at/updated_at automatically — useful
    # for content-team auditing (when was this question added/last edited)
    # without any extra fields defined here.

    # The content team's own stable identifier for a question (e.g.
    # "NW-MCQ-001"), carried in the authoring spreadsheet/JSON and preserved
    # here as the natural key an import can match on.
    #
    # Without it, the importer had to decide "have I seen this question
    # before?" by comparing the full `stem` text — an unindexed comparison
    # (a scan per row) that is also wrong in practice: correcting a single
    # typo in a stem makes the question look brand new and silently
    # imports a duplicate.
    #
    # null/blank because it is genuinely optional: questions written by
    # hand in the Django admin have no upstream id, and the rows that
    # existed before this field did have none either. unique=True still
    # applies to the values that ARE set — Postgres treats NULLs as
    # distinct, so any number of admin-authored rows can coexist while
    # imported ones stay unique.
    #
    # Added now, deliberately, while the table holds a handful of rows.
    # Retrofitting a natural key after the 4,000-question batch lands
    # (CLAUDE.md, Milestone 2) would mean backfilling ids onto rows whose
    # only link back to the source file is the very stem text that proved
    # unreliable.
    external_id = models.CharField(max_length=64, unique=True, null=True, blank=True)

    question_type = models.CharField(max_length=20, choices=QuestionType.choices)
    # When question_type=NGN_CASE, ngn_type says which item-type this case
    # question renders as (a case study is a sequence of ordinary items —
    # MCQ, MATRIX, BOWTIE, etc. — sharing one clinical_scenario/case_study).
    # null=True/blank=True: irrelevant (and left empty) for every
    # non-NGN_CASE question, since only a case-study item needs to say
    # "which type am I, within this case".
    ngn_type = models.CharField(max_length=20, choices=QuestionType.choices, null=True, blank=True)

    # The question text itself. TextField (not CharField) — no practical
    # length cap makes sense for exam-style question stems, some of which
    # run several sentences.
    stem = models.TextField()
    # The patient vignette/case context, when a question has one — separate
    # from `stem` because in the UI these are typically displayed as two
    # distinct blocks (a scenario panel, then the actual question below
    # it), and not every question has a scenario (a pure knowledge-recall
    # MCQ might not).
    clinical_scenario = models.TextField(null=True, blank=True)
    # Links a set of questions that all share ONE clinical_scenario (an NGN
    # Case Study is really "6 questions about the same patient") — see
    # apps.taxonomy.CaseStudy.shared_scenario for where that shared text
    # actually lives. null=True since only NGN_CASE questions use this;
    # on_delete=CASCADE means deleting a CaseStudy deletes every Question
    # that belongs to it (a case study with no case makes no sense to keep
    # around).
    case_study = models.ForeignKey(
        CaseStudy, on_delete=models.CASCADE, null=True, blank=True, related_name="questions"
    )
    # Where this question falls within its case study (1st item, 2nd item,
    # ...) — needed because case-study items must be presented in a fixed
    # order, not the arbitrary order they happen to be queried in.
    case_study_sequence = models.IntegerField(null=True, blank=True)
    # Optional accompanying image (lab result table, diagram, EKG strip,
    # etc.). upload_to defines the subdirectory under MEDIA_ROOT files land
    # in; actual serving is handled by Django only when DEBUG=True (see
    # config/urls.py) — production needs a real file host in front of this
    # before question images can go live at scale.
    # validators run on admin/form/serializer saves (they are not a database
    # constraint), which is the path every upload actually takes here.
    # See ALLOWED_QUESTION_IMAGE_EXTENSIONS above for why SVG is excluded.
    image = models.FileField(
        upload_to="question_images/",
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(allowed_extensions=ALLOWED_QUESTION_IMAGE_EXTENSIONS),
            validate_question_image_size,
        ],
    )

    difficulty = models.CharField(max_length=10, choices=Difficulty.choices)

    # --- Taxonomy tagging (apps.taxonomy) ---
    # UWorld's "Subjects" facet (Adult Health, Pharmacology, ...) —
    # orthogonal to nursing_system below (UWorld's "Systems" facet), not a
    # parent/child of it. null=True/blank=True deliberately: this field was
    # added after the first content batch was already imported, and those
    # existing rows have no correct value to guess at (see seed_domains'
    # docstring) — left for the content team/admin to backfill rather than
    # auto-assigned.
    domain = models.ForeignKey(Domain, on_delete=models.PROTECT, null=True, blank=True, related_name="questions")
    # on_delete=PROTECT (not CASCADE, unlike case_study above) is
    # deliberate here: it should be IMPOSSIBLE to delete a NursingSystem/
    # Topic/ClientNeedsCategory/etc. while any Question still references it
    # — doing so would silently delete real exam content as a side effect
    # of an admin cleaning up taxonomy data. PROTECT raises an error and
    # blocks the delete instead, forcing a deliberate reassignment first.
    nursing_system = models.ForeignKey(NursingSystem, on_delete=models.PROTECT, related_name="questions")
    topic = models.ForeignKey(Topic, on_delete=models.PROTECT, related_name="questions")
    # subtopic is optional (null=True) — not every question needs
    # subtopic-level granularity, but topic/nursing_system are required.
    subtopic = models.ForeignKey(
        Subtopic, on_delete=models.PROTECT, null=True, blank=True, related_name="questions"
    )
    # Both Client Needs fields are required (no null=True) — this is the
    # OFFICIAL NCSBN exam blueprint categorization (unlike nursing_system,
    # which is this project's own invented taxonomy), so every question
    # must be classified against it for the content bank to be
    # representative of the real exam's category weighting.
    nclex_client_needs_category = models.ForeignKey(
        ClientNeedsCategory, on_delete=models.PROTECT, related_name="questions"
    )
    nclex_client_needs_subcategory = models.ForeignKey(
        ClientNeedsSubcategory, on_delete=models.PROTECT, related_name="questions"
    )

    clinical_judgment_skill = models.CharField(max_length=25, choices=ClinicalJudgmentSkill.choices)
    # Optional second CJ-process step a question also exercises (e.g. a
    # question primarily tagged Take Action that also draws on Recognize
    # Cues). null/blank because most questions only exercise one step —
    # required content teams don't tag a secondary skill at all, and this
    # must not force one. Added ahead of the content team's NGN batch
    # (which does tag a secondary skill on several items) specifically so
    # that data isn't dropped on import; Phase 2's clinical-judgment
    # analytics (CLAUDE.md) is the eventual consumer.
    clinical_judgment_skill_secondary = models.CharField(
        max_length=25, choices=ClinicalJudgmentSkill.choices, null=True, blank=True
    )
    cognitive_level = models.CharField(max_length=15, choices=CognitiveLevel.choices)
    # ManyToMany (not ForeignKey): a single question can carry several free-
    # form tags at once (e.g. both "pediatric" and "med-math"). blank=True
    # means a question can have zero tags — unlike the required taxonomy
    # fields above, tagging is supplementary, not mandatory classification.
    tags = models.ManyToManyField(Tag, blank=True, related_name="questions")

    # A single, question-level explanation of the correct answer — no
    # longer required (previously was) now that AnswerChoice.rationale
    # gives MCQ/SATA/EMR questions a per-choice explanation instead. Still
    # useful for question types with no per-choice structure to hang a
    # rationale off (Cloze, Hot Spot, etc.), and left populated on older
    # content rather than migrated away.
    rationale_correct = models.TextField(null=True, blank=True)
    # Explanation of why the distractors are wrong, as a single blob rather
    # than split per choice — same transitional/non-choice-based role as
    # rationale_correct above, superseded by AnswerChoice.rationale for
    # MCQ/SATA/EMR.
    rationale_incorrect = models.TextField(null=True, blank=True)
    # Citation (textbook, NCSBN test plan section, etc.) backing the
    # rationale — optional, free text rather than a structured citation
    # model, since Phase 1 has no requirement to parse/validate citations.
    reference = models.TextField(null=True, blank=True)
    # A short, single "big idea" the student should walk away with — shown
    # in the results review beneath the rationale. Optional and not
    # required at question creation: the content team populates this
    # during a later authoring pass, not required for a question to go
    # live.
    key_takeaway = models.TextField(null=True, blank=True)

    # Soft-delete flag: an inactive question is excluded from quizzes
    # without deleting the row (and its historical StudentResponseLog
    # entries, which reference it by ForeignKey) — lets a flawed or
    # retired question be pulled from circulation while preserving the
    # data trail of students who already answered it.
    is_active = models.BooleanField(default=True)

    class Meta:
        # Newest questions first by default — most relevant when browsing
        # the admin's question list (recently added/imported content is
        # what an editor is most likely checking).
        ordering = ["-created_at"]
        indexes = [
            # The quiz-builder query: "active questions, optionally narrowed
            # by type and difficulty, newest first" (CLAUDE.md Milestone 3 —
            # quiz creation with filters). Composite and column order both
            # matter: is_active leads because every such query filters on it
            # and it is the most selective single condition once retired
            # content accumulates; -created_at trails so the index can also
            # satisfy the default ordering without a separate sort step.
            # A prefix of a composite index is usable on its own, so this
            # also serves is_active alone and is_active+question_type.
            models.Index(
                fields=["is_active", "question_type", "difficulty", "-created_at"],
                name="question_active_filter_idx",
            ),
            # Taxonomy-driven filtering ("give me Cardiovascular questions")
            # is the other half of quiz building. The FK columns are already
            # indexed individually by Django, but not as a pair, so a query
            # constraining both still had to intersect two indexes.
            models.Index(fields=["nursing_system", "topic"], name="question_taxonomy_idx"),
            # The quiz-setup facet-counts endpoint (apps.quizzes.services)
            # filters/groups by domain on every filter change — worth its
            # own index alongside is_active the same way question_type does
            # above.
            models.Index(fields=["is_active", "domain"], name="question_domain_idx"),
        ]

    def __str__(self):
        # [MCQ] A client with heart failure reports weight... — truncated
        # to 60 chars so this stays readable in the admin list/dropdowns
        # rather than dumping an entire multi-sentence stem inline.
        return f"[{self.question_type}] {self.stem[:60]}"


class AnswerChoice(UUIDPKMixin, models.Model):
    """Used by MCQ, SATA, and EMR — question_type controls scoring rules, not the schema."""

    # No TimeStampedMixin here (unlike Question) — an individual answer
    # choice's own creation/edit time isn't independently useful once it
    # belongs to a timestamped Question; UUIDPKMixin is still used so each
    # choice has a stable, externally-referenceable id (needed by
    # StudentResponseLog.selected_choice in apps.quizzes, which records
    # exactly which choice a student picked).
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answer_choices")
    choice_text = models.TextField()
    # No constraint enforcing "exactly one is_correct=True for MCQ" or "at
    # least one for SATA" at the database level — that validation is
    # question_type-dependent business logic, left to be enforced by the
    # (future) admin import validation or serializer layer, not the schema
    # itself. This is intentional: the same AnswerChoice model has to
    # support MCQ's exactly-one-correct rule AND SATA's variable-number-
    # correct rule AND EMR's rules, so no single DB constraint could
    # capture all three anyway.
    is_correct = models.BooleanField(default=False)
    # Explicit ordering field rather than relying on insertion/PK order —
    # lets an editor reorder answer choices (e.g. via drag-and-drop in a
    # future admin UI) independent of the order they were created in.
    display_order = models.IntegerField(default=0)
    # Per-choice explanation, shown inline directly under this option once
    # the student submits — this is the primary rationale mechanism for
    # MCQ/SATA/EMR questions (client-requested Aug 2026), not just an
    # explanation for the correct answer with a separate generic blurb
    # about the rest. blank=True since older/imported content may not have
    # this filled in per choice yet; Question.rationale_correct/
    # rationale_incorrect (below) still exist for that transitional case
    # and for non-choice-based NGN types, but are no longer what the
    # MCQ/SATA quiz UI actually renders.
    rationale = models.TextField(blank=True)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return f"{self.choice_text[:40]} ({'correct' if self.is_correct else 'incorrect'})"


# --- NGN stub models: schema only, no rendering logic until Phase 2 ---
# Everything below exists so the content team can start writing NGN content
# now and it lands in a shape the Phase 2 UI can consume directly — none of
# it has a corresponding "take this quiz question" UI yet (that's Phase 2's
# NGN rendering work), only Django admin CRUD via apps/questions/admin.py.


class MatrixRow(models.Model):
    """One row of a Matrix/Grid question (e.g. one assessment finding)."""

    # No UUIDPKMixin/TimeStampedMixin on any of the NGN stub models below —
    # unlike Question/AnswerChoice, these are never referenced by
    # StudentResponseLog or any other cross-app relationship, so a plain
    # auto-increment int PK (Django's default) is sufficient; there's no
    # need for UUID unguessability or independent audit timestamps on a row
    # that only ever exists nested under one Question in the admin.
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="matrix_rows")
    text = models.TextField()
    display_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return self.text[:40]


class MatrixColumn(models.Model):
    """One column of a Matrix/Grid question (e.g. 'Expected' / 'Unexpected')."""

    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="matrix_columns")
    # CharField (not TextField, unlike MatrixRow.text) — column headers are
    # short labels, not full sentences, so a bounded length is appropriate.
    text = models.CharField(max_length=255)
    display_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return self.text[:40]


class MatrixCell(models.Model):
    """The row x column intersection — is this combination correct?"""

    row = models.ForeignKey(MatrixRow, on_delete=models.CASCADE, related_name="cells")
    column = models.ForeignKey(MatrixColumn, on_delete=models.CASCADE, related_name="cells")
    is_correct = models.BooleanField(default=False)
    # Per-cell explanation, same role as AnswerChoice.rationale — why this
    # row/column combination is (or isn't) correct. blank=True since older
    # content may not have this filled in.
    rationale = models.TextField(blank=True)

    class Meta:
        # Guarantees at most one cell per (row, column) pair — a grid can't
        # have two different "is this correct" answers for the same
        # intersection. Expressed as a named UniqueConstraint rather than
        # the older unique_together, which current Django steers away from.
        constraints = [
            models.UniqueConstraint(fields=["row", "column"], name="unique_matrix_cell_per_row_column")
        ]

    def __str__(self):
        return f"{self.row} x {self.column} ({'correct' if self.is_correct else 'incorrect'})"


class BowTieSection(models.TextChoices):
    """The three zones of a Bow-Tie item: a central Condition flanked by contributing Assessment findings and required Actions."""

    ASSESSMENT = "ASSESSMENT", "Assessment"
    CONDITION = "CONDITION", "Condition"
    ACTION = "ACTION", "Action"


class BowTieOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="bowtie_options")
    # Which of the three bow-tie zones this option belongs to — a single
    # flat list of options per question, disambiguated by this field,
    # rather than three separate models (BowTieAssessmentOption,
    # BowTieConditionOption, BowTieActionOption) that would otherwise be
    # near-identical.
    section = models.CharField(max_length=15, choices=BowTieSection.choices)
    option_text = models.TextField()
    is_correct = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)
    rationale = models.TextField(blank=True)

    class Meta:
        # Grouped by section first (all Assessment options together, then
        # Condition, then Action), then by display_order within each
        # section — matches how a bow-tie diagram is actually laid out.
        ordering = ["section", "display_order"]

    def __str__(self):
        return f"[{self.section}] {self.option_text[:40]}"


class ClozeBlank(models.Model):
    """blank_key must match a [dropdown N] placeholder in the parent Question.stem."""

    # This is the mechanism that connects a specific blank to its position
    # within the stem text: the content author writes something like "The
    # nurse should first assess the client's [dropdown 1]." in Question.stem,
    # and blank_key="dropdown 1" here is what a renderer would match against
    # that placeholder to know where to insert a dropdown.
    #
    # Originally documented as a {{blank_1}}-style token — changed to
    # [dropdown N] to match the content team's actual authoring convention
    # (confirmed against their NGN Item Bank spreadsheet) rather than
    # requiring them to write in a syntax nothing has ever actually used.
    # blank_key is free text either way (no format enforced at the field
    # level), so this is a documentation/convention change, not a schema
    # change — no migration needed.
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="cloze_blanks")
    blank_key = models.CharField(max_length=50)
    display_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["display_order"]
        # A given question can't define the same blank_key twice — each
        # placeholder token must uniquely identify one ClozeBlank.
        constraints = [
            models.UniqueConstraint(
                fields=["question", "blank_key"], name="unique_cloze_blank_key_per_question"
            )
        ]

    def __str__(self):
        return self.blank_key


class ClozeOption(models.Model):
    """One dropdown choice for a single ClozeBlank."""

    blank = models.ForeignKey(ClozeBlank, on_delete=models.CASCADE, related_name="options")
    option_text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    rationale = models.TextField(blank=True)

    # No display_order here (unlike most other option/choice models in this
    # file) — dropdown options are typically presented alphabetically or in
    # authoring order without needing manual reordering; can be added later
    # without breaking existing data if that assumption turns out wrong.
    def __str__(self):
        return self.option_text


class DragDropCategory(models.Model):
    """One 'bucket' items can be sorted into (used by the sort-into-categories drag-drop variant)."""

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
    # Used only by the "sort into categories" variant — which
    # DragDropCategory this item is supposed to end up in. null/blank so it
    # can be left empty for the sequencing variant.
    correct_category = models.ForeignKey(
        DragDropCategory, on_delete=models.CASCADE, null=True, blank=True, related_name="items"
    )
    # Used only by the "put these in the correct order" variant — this
    # item's correct position (1st, 2nd, 3rd...). null/blank so it can be
    # left empty for the categorization variant. Deliberately not the same
    # field as display_order above: display_order controls how items are
    # initially presented to the student (e.g. shuffled or fixed starting
    # order), while correct_order is the answer key for where they should
    # end up.
    correct_order = models.IntegerField(null=True, blank=True)
    rationale = models.TextField(blank=True)

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
    # The exact word/phrase (as it appears in stem/clinical_scenario) that
    # is one of the selectable options — a renderer would need to locate
    # this substring within the text to make it clickable, rather than
    # this model storing a position/offset directly.
    target_text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)
    rationale = models.TextField(blank=True)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return self.target_text
