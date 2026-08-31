from rest_framework import serializers

from .models import AnswerChoice, Question


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

    class Meta:
        model = Question
        fields = [
            "id",
            "question_type",
            "stem",
            "clinical_scenario",
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
