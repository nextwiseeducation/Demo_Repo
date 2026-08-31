from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.questions.models import Question, QuestionType
from apps.questions.services import (
    QuestionNotGradeable,
    build_answer_key,
    build_bowtie_answer_key,
    build_cloze_answer_key,
    build_dragdrop_answer_key,
    build_hotspot_answer_key,
    build_matrix_answer_key,
    effective_question_type,
    grade_bowtie,
    grade_cloze,
    grade_dragdrop,
    grade_hotspot,
    grade_matrix,
    grade_submission,
)

from .models import Bookmark, QuizSession, QuizSessionQuestion, StudentResponseLog
from .serializers import (
    BookmarkToggleSerializer,
    QuizAnswerSubmitSerializer,
    QuizSessionCreateSerializer,
    QuizSessionSerializer,
)
from .services import compute_facet_counts, resolve_question_queryset


class QuizSessionCreateView(APIView):
    """
    POST /api/quizzes/sessions/ — the quiz-setup page's "Generate Quiz".

    Resolves the student's current filter selection to an actual pool of
    questions via apps.quizzes.services.resolve_question_queryset — the
    same function QuizFacetCountsView uses to compute the counts the
    student saw just before clicking this button, so what gets drawn can
    never silently disagree with what was promised — then randomly samples
    question_count of them and persists the QuizSession plus its ordered
    QuizSessionQuestion rows in one transaction.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = QuizSessionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        filters = serializer.validated_data

        # order_by("?") is plain RANDOM() — simplest correct option at the
        # question bank's expected size (~4,000 rows). Known caveat: a
        # full-table random sort gets slow in the tens-of-thousands+ range;
        # not worth a more complex sampling scheme at current scale.
        pool = list(resolve_question_queryset(request.user, filters).order_by("?")[: filters["question_count"]])
        if not pool:
            return Response(
                {"detail": "No questions match the selected filters."}, status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            session = QuizSession.objects.create(student=request.user, filter_config=filters)
            QuizSessionQuestion.objects.bulk_create(
                [
                    QuizSessionQuestion(quiz_session=session, question=question, position=index)
                    for index, question in enumerate(pool)
                ]
            )

        return Response(QuizSessionSerializer(session).data, status=status.HTTP_201_CREATED)


class QuizAnswerSubmitView(APIView):
    """
    POST /api/quizzes/sessions/<uuid:session_id>/answers/ — grades one
    answer AND persists it (a real StudentResponseLog row), unlike
    apps.questions.QuestionSubmitView's stateless preview.

    Lives here rather than in apps.questions deliberately: apps.quizzes
    already imports from apps.questions (Question, grade_submission), so
    the reverse import would be circular.
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "question_submit"

    def post(self, request, session_id):
        # student=request.user in the lookup itself (not a separate check
        # after fetching) — one student cannot even discover whether
        # another student's session id exists via a 403-vs-404 distinction.
        session = get_object_or_404(QuizSession, pk=session_id, student=request.user)

        serializer = QuizAnswerSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        session_question = get_object_or_404(
            QuizSessionQuestion, quiz_session=session, question_id=data["question_id"]
        )
        question = (
            Question.objects.prefetch_related(
                "answer_choices",
                "matrix_rows",
                "matrix_columns",
                "bowtie_options",
                "cloze_blanks__options",
                "dragdrop_items",
                "dragdrop_categories",
                "hotspot_targets",
            )
            .get(pk=data["question_id"])
        )

        # Which family of question this actually is — for an NGN_CASE item
        # that's ngn_type, not question_type itself (see
        # effective_question_type's own docstring).
        q_type = effective_question_type(question)

        try:
            if q_type in (QuestionType.MCQ, QuestionType.SATA, QuestionType.EMR):
                if not data["selected_choice_ids"]:
                    return Response({"detail": "selected_choice_ids is required for this question type."}, status=status.HTTP_400_BAD_REQUEST)
                graded = grade_submission(question, data["selected_choice_ids"])
                is_correct, response_body = graded.is_correct, {"choices": build_answer_key(question)}
            elif q_type == QuestionType.MATRIX:
                graded = grade_matrix(question, data["matrix_selections"])
                is_correct, response_body = graded.is_correct, {"matrix_cells": build_matrix_answer_key(question)}
            elif q_type == QuestionType.BOWTIE:
                graded = grade_bowtie(question, data["bowtie_option_ids"])
                is_correct, response_body = graded.is_correct, {"bowtie_options": build_bowtie_answer_key(question)}
            elif q_type == QuestionType.CLOZE:
                graded = grade_cloze(question, data["cloze_selections"])
                is_correct, response_body = graded.is_correct, {"cloze_blanks": build_cloze_answer_key(question)}
            elif q_type == QuestionType.DRAG_DROP:
                graded = grade_dragdrop(question, data["dragdrop_placements"])
                is_correct, response_body = graded.is_correct, {"dragdrop_items": build_dragdrop_answer_key(question)}
            elif q_type == QuestionType.HOTSPOT:
                graded = grade_hotspot(question, data["hotspot_target_ids"])
                is_correct, response_body = graded.is_correct, {"hotspot_targets": build_hotspot_answer_key(question)}
            else:
                return Response(
                    {"detail": f"Question type {q_type} is not gradeable yet."}, status=status.HTTP_409_CONFLICT
                )
        except QuestionNotGradeable:
            return Response(
                {"detail": "This question is not available for grading."}, status=status.HTTP_409_CONFLICT
            )

        log = StudentResponseLog.objects.create(
            student=request.user,
            question=question,
            quiz_session=session,
            is_correct=is_correct,
            time_taken_seconds=data["time_taken_seconds"],
        )
        if q_type in (QuestionType.MCQ, QuestionType.SATA, QuestionType.EMR):
            if q_type == QuestionType.SATA:
                log.selected_choices.set(graded.selected_ids)
            elif graded.selected_ids:
                # MCQ/EMR-as-single: exactly one id expected; grade_submission
                # already discarded anything not a real choice of this question.
                log.selected_choice_id = next(iter(graded.selected_ids))
                log.save(update_fields=["selected_choice"])
        else:
            log.selected_payload = graded.detail
            log.save(update_fields=["selected_payload"])

        # max(), not a flat overwrite: re-answering an earlier question
        # (student navigates back) must not move progress backwards.
        session.current_question_index = max(session.current_question_index, session_question.position + 1)
        total_questions = session.session_questions.count()
        if session.current_question_index >= total_questions:
            session.is_complete = True
            session.completed_at = timezone.now()
        session.save(update_fields=["current_question_index", "is_complete", "completed_at"])

        return Response({"is_correct": is_correct, **response_body})


class QuizFacetCountsView(APIView):
    """
    GET /api/quizzes/facet-counts/ — every live count the quiz-setup page's
    5 cards need, scoped to the requesting student and whatever filters are
    currently selected on the other cards. See apps.quizzes.services for
    the actual query logic.
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "quiz_facet_counts"

    def get(self, request):
        filters = _parse_facet_query_params(request.query_params)
        return Response(compute_facet_counts(request.user, filters))


class BookmarkToggleView(APIView):
    """POST /api/quizzes/bookmarks/toggle/ — UWorld's "Marked" flag, independent of any specific session."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BookmarkToggleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = get_object_or_404(Question, pk=serializer.validated_data["question_id"], is_active=True)

        bookmark = Bookmark.objects.filter(student=request.user, question=question).first()
        if bookmark is not None:
            bookmark.delete()
            return Response({"marked": False})

        Bookmark.objects.create(student=request.user, question=question)
        return Response({"marked": True})


def _parse_facet_query_params(params) -> dict:
    """
    GET query params are accepted either repeated (domains=1&domains=2,
    axios' default array serialization) or comma-joined (domains=1,2) — both
    forms, so the frontend's exact serialization choice isn't locked in
    ahead of time.
    """

    def get_list(name: str) -> list[str]:
        values = params.getlist(name)
        if len(values) == 1 and "," in values[0]:
            return [v for v in values[0].split(",") if v]
        return [v for v in values if v]

    def get_int_list(name: str) -> list[int]:
        return [int(v) for v in get_list(name) if v.lstrip("-").isdigit()]

    return {
        "question_types": get_list("question_types"),
        "status_filters": get_list("status_filters"),
        "domains": get_int_list("domains"),
        "nursing_systems": get_int_list("nursing_systems"),
        "nclex_client_needs_subcategories": get_int_list("nclex_client_needs_subcategories"),
    }
