from rest_framework import serializers

from apps.quizzes.models import QuizSession

from .models import QuestionIssueReport, QuizFeedback

# Serializer-level caps on the free-text fields below. The models keep
# plain TextFields (no max_length) on purpose: the admin/content team
# occasionally needs to paste long content into these rows, and adding a
# DB-level cap would mean a migration now plus another one every time the
# limit needs tuning. Capping at the serializer instead bounds only the
# untrusted path — what a student can POST — which is the actual abuse
# vector (an authenticated user writing unbounded text rows to fill the
# database; the "feedback" throttle on the views bounds the rate, these
# bound the size).
#
# Both numbers are deliberately far beyond what genuine student prose
# looks like (5,000 characters is roughly two pages of typing), so a real
# user writing a detailed complaint will never hit them.
MAX_FREE_TEXT_LENGTH = 5000
# Larger than the others because this one isn't student prose — it's a
# verbatim copy of the question the student was looking at, and an NGN
# case-study stem plus its clinical scenario is legitimately long.
MAX_STEM_SNAPSHOT_LENGTH = 10000


class OwnedQuizSessionMixin:
    """
    Restricts `quiz_session` to sessions belonging to the requesting user.

    Both serializers here already refuse to trust a client-supplied
    `student` (they overwrite it with request.user in create()), but
    `quiz_session` was previously accepted straight from the request body
    with no ownership check — so an authenticated attacker could POST their
    own feedback/issue report carrying a victim's QuizSession UUID and have
    it persist attached to the victim's session, corrupting that student's
    per-session data.

    The guard works by narrowing the related field's queryset rather than
    by adding a validate_quiz_session() check, and that choice is the whole
    point. A custom validator runs only AFTER DRF's PrimaryKeyRelatedField
    has already resolved the pk, so the two rejections would come back
    differently: a nonexistent id would fail at the field with
    'Invalid pk ... object does not exist', while a real id owned by
    somebody else would fail with the custom message. That difference is a
    session-id enumeration oracle — it tells an attacker exactly which
    UUIDs are real sessions. Narrowing the queryset instead makes another
    student's session literally not exist as far as this request is
    concerned, so both cases produce the identical DRF error.

    Note the deliberate asymmetry with `question` on QuestionIssueReport,
    which needs no equivalent treatment: a Question is global content shared
    by every student, not a per-user row, so pointing a report at any
    question id is exactly what the feature is for. Only user-owned rows
    (today: QuizSession) need scoping here.
    """

    def get_fields(self):
        fields = super().get_fields()
        quiz_session = fields.get("quiz_session")
        if quiz_session is None:
            return fields

        request = self.context.get("request")
        if request is not None and request.user.is_authenticated:
            quiz_session.queryset = QuizSession.objects.filter(student=request.user)
        else:
            # Fails closed. These serializers are only reached through
            # IsAuthenticated create views, so this branch should be
            # unreachable in practice — but if one is ever reused somewhere
            # without a request in context, refusing every session is the
            # safe direction to be wrong in.
            quiz_session.queryset = QuizSession.objects.none()
        return fields


class QuizFeedbackSerializer(OwnedQuizSessionMixin, serializers.ModelSerializer):
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
        # extra_kwargs (rather than redeclaring each field explicitly) keeps
        # every other property ModelSerializer already infers from the model
        # — notably required=False/allow_blank for these blank=True fields —
        # while adding only the length cap. See MAX_FREE_TEXT_LENGTH above
        # for why the cap lives here and not on the model.
        extra_kwargs = {
            "issue_description": {"max_length": MAX_FREE_TEXT_LENGTH},
            "liked_most": {"max_length": MAX_FREE_TEXT_LENGTH},
            "improvement_suggestion": {"max_length": MAX_FREE_TEXT_LENGTH},
        }

    def create(self, validated_data):
        # student is never accepted from the request body — always the
        # authenticated caller, set here rather than trusted as client input.
        # (quiz_session, which IS accepted from the body, is scoped to the
        # caller's own sessions by OwnedQuizSessionMixin above.)
        validated_data["student"] = self.context["request"].user
        return super().create(validated_data)


class QuestionIssueReportSerializer(OwnedQuizSessionMixin, serializers.ModelSerializer):
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
        extra_kwargs = {
            "question_stem_snapshot": {"max_length": MAX_STEM_SNAPSHOT_LENGTH},
            "description": {"max_length": MAX_FREE_TEXT_LENGTH},
        }

    def create(self, validated_data):
        validated_data["student"] = self.context["request"].user
        return super().create(validated_data)
