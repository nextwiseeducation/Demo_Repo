from rest_framework import serializers

from apps.questions.models import Question, QuestionType
from apps.questions.serializers import QuestionListSerializer
from apps.questions.services import build_answer_key_for_type, effective_question_type

from .models import Bookmark, QuizSession


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


def _structured_answer_from_payload(q_type: str, payload: dict) -> dict | None:
    """
    Reverses one of the grade_*() functions' `detail` dict (apps.questions.
    services — what actually got stored in StudentResponseLog.selected_payload)
    back into the shape the frontend's StructuredAnswer type expects
    (features/quiz/quizSessionReducer.ts / types/quiz.ts on the frontend).

    The two shapes genuinely differ — e.g. grade_matrix stores
    {"selected_by_row": {row_id: column_id}}, a compact grading-internal
    representation, while the frontend wants
    {"kind": "MATRIX", "selections": [{"row_id": ..., "column_id": ...}]},
    the shape it actually renders and re-submits from — so this is a real
    translation, not just a rename. JSONField round-trips dict keys as
    strings even though grade_matrix/grade_cloze wrote them as ints
    (row_id/blank_id), hence the int(...) conversions below.
    """
    if q_type == QuestionType.MATRIX:
        selections = [
            {"row_id": int(row_id), "column_id": column_id}
            for row_id, column_id in payload.get("selected_by_row", {}).items()
        ]
        return {"kind": "MATRIX", "selections": selections}
    if q_type == QuestionType.BOWTIE:
        return {"kind": "BOWTIE", "selectedOptionIds": payload.get("selected_option_ids", [])}
    if q_type == QuestionType.CLOZE:
        selections = [
            {"blank_id": int(blank_id), "option_id": option_id}
            for blank_id, option_id in payload.get("selected_by_blank", {}).items()
        ]
        return {"kind": "CLOZE", "selections": selections}
    if q_type == QuestionType.DRAG_DROP:
        return {"kind": "DRAG_DROP", "placements": payload.get("placements", [])}
    if q_type == QuestionType.HOTSPOT:
        return {"kind": "HOTSPOT", "selectedTargetIds": payload.get("selected_target_ids", [])}
    return None


class QuizSessionSerializer(serializers.ModelSerializer):
    # SerializerMethodField rather than trusting session.questions.all()'s
    # default ordering to come through the M2M manager transparently — this
    # is explicit and greppable, and it's the one place a silent ordering
    # bug would be easy to introduce (see QuizSessionQuestion's docstring in
    # models.py on why order matters here at all).
    questions = serializers.SerializerMethodField()
    # The three fields below are what let the frontend fully reconstruct
    # in-progress state on load — not just "which question", but which ones
    # are already answered (with their locked-in selection + revealed
    # rationale), which have been seen-but-skipped, and which are flagged —
    # so Previous/Next navigation and the question navigator work correctly
    # immediately after a fresh "Generate Quiz", a resume-from-refresh, or a
    # resume-after-login, with no separate round trip for any of them.
    responses = serializers.SerializerMethodField()
    visited_question_ids = serializers.SerializerMethodField()
    marked_question_ids = serializers.SerializerMethodField()

    class Meta:
        model = QuizSession
        fields = [
            "id",
            "current_question_index",
            "is_complete",
            "started_at",
            "filter_config",
            "questions",
            "responses",
            "visited_question_ids",
            "marked_question_ids",
        ]

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

    def get_responses(self, obj: QuizSession):
        """
        One entry per question this student has already answered in this
        session — most recent attempt wins if a question was ever graded
        more than once, same "latest wins" rule apps.quizzes.services.
        annotate_student_status uses — in the same shape
        QuizAnswerSubmitView returns right after grading it: is_correct,
        what was selected, and the type's revealed answer key. This is what
        lets the frontend restore an answered question's locked-in,
        rationale-revealed state when the student navigates back to it
        (Previous) or resumes the session, instead of re-rendering it as if
        never attempted.
        """
        logs = (
            obj.response_logs.select_related("question")
            .prefetch_related(
                "question__answer_choices",
                "question__bowtie_options",
                "question__cloze_blanks__options",
                "question__dragdrop_items",
                "question__hotspot_targets",
                "selected_choices",
            )
            .order_by("-answered_at")
        )

        seen_question_ids: set = set()
        results = []
        for log in logs:
            if log.question_id in seen_question_ids:
                continue
            seen_question_ids.add(log.question_id)

            q_type = effective_question_type(log.question)
            if q_type in (QuestionType.MCQ, QuestionType.SATA, QuestionType.EMR):
                if log.selected_choice_id:
                    selected_choice_ids = [str(log.selected_choice_id)]
                else:
                    selected_choice_ids = [str(cid) for cid in log.selected_choices.values_list("id", flat=True)]
                structured_answer = None
            else:
                selected_choice_ids = []
                structured_answer = _structured_answer_from_payload(q_type, log.selected_payload)

            results.append(
                {
                    "question_id": str(log.question_id),
                    "is_correct": log.is_correct,
                    "selected_choice_ids": selected_choice_ids,
                    "structured_answer": structured_answer,
                    **build_answer_key_for_type(log.question, q_type),
                }
            )
        return results

    def get_visited_question_ids(self, obj: QuizSession):
        return [
            str(question_id)
            for question_id in obj.session_questions.filter(visited=True).values_list("question_id", flat=True)
        ]

    def get_marked_question_ids(self, obj: QuizSession):
        # Bookmark is cross-session (see its own docstring) — scoped down to
        # just this session's questions here, since that's all the frontend
        # needs to seed the in-quiz "marked for review" state.
        question_ids = obj.session_questions.values_list("question_id", flat=True)
        marked_ids = Bookmark.objects.filter(student=obj.student, question_id__in=question_ids).values_list(
            "question_id", flat=True
        )
        return [str(question_id) for question_id in marked_ids]


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


class QuizSessionPositionSerializer(serializers.Serializer):
    """Validates the body of POST /api/quizzes/sessions/<id>/position/ — which question the student is now viewing."""

    question_id = serializers.UUIDField()


class BookmarkToggleSerializer(serializers.Serializer):
    question_id = serializers.UUIDField()
