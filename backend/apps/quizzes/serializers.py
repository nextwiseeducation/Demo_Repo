from rest_framework import serializers

from apps.questions.models import Question
from apps.questions.serializers import QuestionListSerializer

from .models import QuizSession


class QuizSessionCreateSerializer(serializers.Serializer):
    """Validates the body of POST /api/quizzes/sessions/ — the quiz-setup page's "Generate Quiz"."""

    question_types = serializers.ListField(
        child=serializers.ChoiceField(choices=["TRADITIONAL", "NGN"]), allow_empty=False
    )
    # "STANDARD" (unused-only, no checkboxes shown) vs "CUSTOM" (whatever
    # status_filters carries) — see apps.quizzes.services.resolve_question_queryset.
    question_mode = serializers.ChoiceField(choices=["STANDARD", "CUSTOM"], default="STANDARD")
    status_filters = serializers.ListField(
        child=serializers.ChoiceField(choices=["UNUSED", "INCORRECT", "MARKED", "OMITTED", "CORRECT"]),
        required=False,
        default=list,
    )
    domains = serializers.ListField(child=serializers.IntegerField(), required=False, default=list)
    nursing_systems = serializers.ListField(child=serializers.IntegerField(), required=False, default=list)
    nclex_client_needs_subcategories = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=list
    )
    is_tutor_mode = serializers.BooleanField(default=True)
    is_timed = serializers.BooleanField(default=False)
    time_limit_minutes = serializers.IntegerField(required=False, allow_null=True, min_value=1, default=None)
    question_count = serializers.IntegerField(min_value=1, max_value=500)


class QuizSessionSerializer(serializers.ModelSerializer):
    # SerializerMethodField rather than trusting session.questions.all()'s
    # default ordering to come through the M2M manager transparently — this
    # is explicit and greppable, and it's the one place a silent ordering
    # bug would be easy to introduce (see QuizSessionQuestion's docstring in
    # models.py on why order matters here at all).
    questions = serializers.SerializerMethodField()

    class Meta:
        model = QuizSession
        fields = ["id", "current_question_index", "is_complete", "started_at", "filter_config", "questions"]

    def get_questions(self, obj: QuizSession):
        ordered = (
            Question.objects.filter(session_questions__quiz_session=obj)
            .select_related("domain", "nursing_system", "topic", "nclex_client_needs_category", "nclex_client_needs_subcategory", "case_study")
            .prefetch_related(
                "answer_choices",
                "matrix_rows",
                "matrix_columns",
                "bowtie_options",
                "cloze_blanks__options",
                "dragdrop_items",
                "dragdrop_categories",
                "hotspot_targets",
            )
            .order_by("session_questions__position")
        )
        return QuestionListSerializer(ordered, many=True, context=self.context).data


class QuizAnswerSubmitSerializer(serializers.Serializer):
    """
    Validates the body of POST /api/quizzes/sessions/<id>/answers/.

    Exactly one of the answer fields below must be non-empty, matching
    which family question.question_type (or, for an NGN_CASE item,
    ngn_type) belongs to — see apps.questions.services.effective_question_type
    and QuizAnswerSubmitView, which is what actually dispatches on it.
    selected_choice_ids stays required=False (it used to be allow_empty=False
    and mandatory) because it is now only one of several possible answer
    shapes, not the only one.
    """

    question_id = serializers.UUIDField()
    # MCQ / SATA / EMR — existing shape, unchanged.
    selected_choice_ids = serializers.ListField(child=serializers.UUIDField(), required=False, default=list)
    # MATRIX — one column chosen per row.
    matrix_selections = serializers.ListField(
        child=serializers.DictField(child=serializers.IntegerField()), required=False, default=list
    )
    # BOWTIE — flat list of chosen BowTieOption ids across all three sections.
    bowtie_option_ids = serializers.ListField(child=serializers.IntegerField(), required=False, default=list)
    # CLOZE — one option chosen per dropdown blank.
    cloze_selections = serializers.ListField(
        child=serializers.DictField(child=serializers.IntegerField()), required=False, default=list
    )
    # DRAG_DROP — each item's final category and/or sequence position.
    dragdrop_placements = serializers.ListField(
        child=serializers.DictField(child=serializers.IntegerField(allow_null=True), allow_null=True),
        required=False,
        default=list,
    )
    # HOTSPOT — flat list of selected HotSpotTarget ids.
    hotspot_target_ids = serializers.ListField(child=serializers.IntegerField(), required=False, default=list)
    time_taken_seconds = serializers.IntegerField(required=False, default=0, min_value=0)

    def validate(self, attrs):
        # Same access-control reasoning as QuestionSubmitSerializer's
        # allow_empty=False: an entirely empty submission must not be
        # gradeable, since grading is what reveals the answer key.
        answer_fields = [
            "selected_choice_ids",
            "matrix_selections",
            "bowtie_option_ids",
            "cloze_selections",
            "dragdrop_placements",
            "hotspot_target_ids",
        ]
        if not any(attrs.get(field) for field in answer_fields):
            raise serializers.ValidationError("At least one answer field must be non-empty.")
        return attrs


class BookmarkToggleSerializer(serializers.Serializer):
    question_id = serializers.UUIDField()
