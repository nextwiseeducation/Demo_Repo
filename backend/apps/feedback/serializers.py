from rest_framework import serializers

from .models import QuestionIssueReport, QuizFeedback


class QuizFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizFeedback
        fields = [
            "id",
            "quiz_session",
            "overall_rating",
            "question_quality_rating",
            "difficulty_rating",
            "realism_rating",
            "rationale_helpfulness_rating",
            "had_question_issue",
            "issue_question_number",
            "issue_description",
            "liked_most",
            "improvement_suggestion",
            "recommend_likelihood",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        # student is never accepted from the request body — always the
        # authenticated caller, set here rather than trusted as client input.
        validated_data["student"] = self.context["request"].user
        return super().create(validated_data)


class QuestionIssueReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionIssueReport
        fields = [
            "id",
            "question",
            "question_stem_snapshot",
            "quiz_session",
            "question_number_in_quiz",
            "issue_type",
            "description",
            "status",
            "created_at",
        ]
        # status is read-only from the student's side — every report starts
        # OPEN (the model default) and can only move to RESOLVED/DISMISSED
        # via the admin, not by whatever a student's POST body happens to say.
        read_only_fields = ["id", "status", "created_at"]

    def create(self, validated_data):
        validated_data["student"] = self.context["request"].user
        return super().create(validated_data)
