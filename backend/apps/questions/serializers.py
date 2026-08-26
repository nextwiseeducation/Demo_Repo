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
    nursing_system = serializers.CharField(source="nursing_system.name")
    topic = serializers.CharField(source="topic.name")
    nclex_client_needs_category = serializers.CharField(source="nclex_client_needs_category.name")
    answer_choices = PublicAnswerChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "question_type",
            "stem",
            "clinical_scenario",
            "difficulty",
            "nursing_system",
            "topic",
            "nclex_client_needs_category",
            "clinical_judgment_skill",
            "answer_choices",
        ]
