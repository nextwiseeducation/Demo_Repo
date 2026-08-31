from rest_framework import serializers

from apps.taxonomy.models import CaseStudy

from .models import (
    AnswerChoice,
    BowTieOption,
    ClozeBlank,
    ClozeOption,
    DragDropCategory,
    DragDropItem,
    HotSpotTarget,
    MatrixColumn,
    MatrixRow,
    Question,
)


class PublicAnswerChoiceSerializer(serializers.ModelSerializer):
    """
    Deliberately omits is_correct and rationale — a question-list response
    must not ship the answer key before the student has actually answered.
    See QuestionSubmitView, which is where that data gets revealed, after
    grading.
    """

    class Meta:
        model = AnswerChoice
        fields = ["id", "choice_text", "display_order"]


# --- NGN public (pre-answer) serializers -----------------------------------
# Same "hide the key" rule as PublicAnswerChoiceSerializer above, applied to
# each NGN stub model: is_correct/rationale are never included here. Each
# type's answer key is instead revealed post-submit by the matching
# build_*_answer_key() in services.py, mirroring how build_answer_key()
# already does this for AnswerChoice.


class PublicMatrixRowSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatrixRow
        fields = ["id", "text", "display_order"]


class PublicMatrixColumnSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatrixColumn
        fields = ["id", "text", "display_order"]


class PublicBowTieOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BowTieOption
        fields = ["id", "section", "option_text", "display_order"]


class PublicClozeOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClozeOption
        fields = ["id", "option_text"]


class PublicClozeBlankSerializer(serializers.ModelSerializer):
    options = PublicClozeOptionSerializer(many=True, read_only=True)

    class Meta:
        model = ClozeBlank
        fields = ["id", "blank_key", "display_order", "options"]


class PublicDragDropCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DragDropCategory
        fields = ["id", "name", "display_order"]


class PublicDragDropItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = DragDropItem
        # Neither correct_category nor correct_order is included — that's
        # the answer key. display_order is the shuffled/starting position
        # the item is presented in, which is fine to reveal upfront.
        fields = ["id", "text", "display_order"]


class PublicHotSpotTargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotSpotTarget
        fields = ["id", "target_text", "display_order"]


class CaseStudySerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseStudy
        fields = ["id", "title", "shared_scenario"]


class QuestionListSerializer(serializers.ModelSerializer):
    # source="<fk>.name" flattens each taxonomy FK down to its display name
    # — the quiz UI filters/labels by name, not by an internal taxonomy row
    # id it has no other use for yet.
    # read_only=True on all three: they are display projections of a
    # ForeignKey, not writable inputs. Without it DRF treats them as
    # writable and would try to assign to a dotted source on save — this
    # serializer is only ever used for output today, so the flag documents
    # and enforces that rather than leaving it to chance.
    nursing_system = serializers.CharField(source="nursing_system.name", read_only=True)
    topic = serializers.CharField(source="topic.name", read_only=True)
    nclex_client_needs_category = serializers.CharField(
        source="nclex_client_needs_category.name", read_only=True
    )
    # Added alongside the id fields below for the quiz-setup facet UI (built
    # against apps.quizzes) — it filters/groups by these taxonomy rows'
    # *ids*, not display names, so the plain name-only fields above aren't
    # enough on their own. domain is nullable (see Question.domain's own
    # comment), hence source="domain.name" with allow_null implied by
    # required=False rather than a plain CharField, which would error on
    # the None case.
    domain = serializers.CharField(source="domain.name", read_only=True, allow_null=True, default=None)
    domain_id = serializers.IntegerField(source="domain.id", read_only=True, allow_null=True, default=None)
    nursing_system_id = serializers.IntegerField(source="nursing_system.id", read_only=True)
    nclex_client_needs_subcategory = serializers.CharField(
        source="nclex_client_needs_subcategory.name", read_only=True
    )
    nclex_client_needs_subcategory_id = serializers.IntegerField(
        source="nclex_client_needs_subcategory.id", read_only=True
    )
    answer_choices = PublicAnswerChoiceSerializer(many=True, read_only=True)

    # --- NGN nested data, added so MATRIX/BOWTIE/CLOZE/DRAG_DROP/HOTSPOT
    # questions carry the fields their renderer actually needs, same as
    # answer_choices does for MCQ/SATA/EMR. Every question serializes all of
    # these regardless of its own question_type — each is simply an empty
    # list/null for a question that isn't that type, which costs nothing
    # (prefetched, not queried per-field) and keeps this serializer from
    # needing a question_type-conditional branch.
    matrix_rows = PublicMatrixRowSerializer(many=True, read_only=True)
    matrix_columns = PublicMatrixColumnSerializer(many=True, read_only=True)
    bowtie_options = PublicBowTieOptionSerializer(many=True, read_only=True)
    cloze_blanks = PublicClozeBlankSerializer(many=True, read_only=True)
    dragdrop_items = PublicDragDropItemSerializer(many=True, read_only=True)
    dragdrop_categories = PublicDragDropCategorySerializer(many=True, read_only=True)
    hotspot_targets = PublicHotSpotTargetSerializer(many=True, read_only=True)
    case_study = CaseStudySerializer(read_only=True)
    image = serializers.FileField(read_only=True, use_url=True, allow_null=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "question_type",
            # Only meaningful when question_type=NGN_CASE — says which real
            # item type (MCQ, MATRIX, BOWTIE, ...) this case-study item
            # should render as. See Question.ngn_type's own docstring.
            "ngn_type",
            "stem",
            "clinical_scenario",
            "image",
            "case_study",
            "case_study_sequence",
            "difficulty",
            "domain",
            "domain_id",
            "nursing_system",
            "nursing_system_id",
            "topic",
            "nclex_client_needs_category",
            "nclex_client_needs_subcategory",
            "nclex_client_needs_subcategory_id",
            "clinical_judgment_skill",
            "answer_choices",
            "matrix_rows",
            "matrix_columns",
            "bowtie_options",
            "cloze_blanks",
            "dragdrop_items",
            "dragdrop_categories",
            "hotspot_targets",
            "key_takeaway",
            "updated_at",
        ]


class QuestionSubmitSerializer(serializers.Serializer):
    """
    Validates the body of POST /api/questions/<id>/submit/.

    This endpoint previously read `request.data.get("selected_choice_ids", [])`
    and iterated it directly, which made it the only view in the project
    with no serializer — and it showed: posting a bare number raised
    `TypeError: 'int' object is not iterable` straight out of the view, so
    a malformed request returned a 500 instead of a 400. A JSON object
    was worse than that, iterating its keys and grading against them
    silently. Declaring the shape here means DRF rejects both with normal
    field errors before any grading code runs.
    """

    # allow_empty=False is a deliberate access-control decision, not just
    # input hygiene. Because grading reveals the full per-choice answer key
    # (is_correct and rationale for every option), accepting an empty
    # submission turned this endpoint into a plain "fetch me the answers"
    # call that a student could make without attempting the question at
    # all. Requiring a real attempt does not stop a determined client from
    # sending an arbitrary guess to see the key — see QuestionSubmitView's
    # docstring on the residual risk — but it does mean skipping a question
    # no longer hands over its answer.
    selected_choice_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
    )
