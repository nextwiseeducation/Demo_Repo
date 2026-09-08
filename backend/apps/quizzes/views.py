from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.core.query_params import parse_int_csv
from apps.questions.models import Question, QuestionType
from apps.questions.services import (
    QuestionNotGradeable,
    build_answer_key_for_type,
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
    QuizSessionPositionSerializer,
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

    Also retires (abandons) any other session of this student's that is
    still in progress. The product only ever shows the student one "quiz in
    progress" at a time (QuizSessionActiveView's resume prompt, the nav bar's
    single "Practice" entry point) — without this, starting a fresh quiz
    while an old one was left mid-way (browser closed without finishing)
    would silently orphan that old session, which then resurfaces as a
    confusing, unrelated "continue your last quiz?" prompt on some later
    login, well after the student finished the NEWER quiz and forgot the
    old one ever existed.
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
            QuizSession.objects.filter(student=request.user).in_progress().update(is_abandoned=True)
            session = QuizSession.objects.create(
                student=request.user, filter_config=filters, total_questions=len(pool)
            )
            QuizSessionQuestion.objects.bulk_create(
                [
                    QuizSessionQuestion(quiz_session=session, question=question, position=index)
                    for index, question in enumerate(pool)
                ]
            )

        return Response(QuizSessionSerializer(session).data, status=status.HTTP_201_CREATED)


class QuizSessionRetrieveView(APIView):
    """
    GET /api/quizzes/sessions/<uuid:session_id>/ — re-fetches an existing
    session (id, current_question_index, ordered questions, ...) exactly as
    QuizSessionCreateView's response shapes it.

    Exists for session resume: a full page refresh on the quiz-session page
    loses the React Router location.state QuizSessionPage was originally
    handed, so the frontend falls back to re-requesting the session it
    already knows the id of (kept in sessionStorage) rather than bouncing
    the student back to quiz setup.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        session = get_object_or_404(QuizSession, pk=session_id, student=request.user)
        return Response(QuizSessionSerializer(session).data)


class QuizSessionActiveView(APIView):
    """
    GET /api/quizzes/sessions/active/ — the student's most recent
    in-progress session (not finished, not declined), if any.

    Used right after login (see the frontend's AppShell) to decide whether
    to offer "continue the quiz you left?" — this is deliberately separate
    from the sessionStorage-based silent-resume path a same-tab refresh
    uses (QuizSessionRetrieveView above): sessionStorage does not survive
    the browser actually closing, so this is what recovers an in-progress
    session across a real login rather than just a refresh.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # QuizSession.Meta.ordering is already -started_at, so .first() is
        # the most recently started one.
        session = QuizSession.objects.filter(student=request.user).in_progress().first()
        if session is None:
            return Response({"session": None})
        return Response({"session": QuizSessionSerializer(session).data})


class QuizSessionAbandonView(APIView):
    """
    POST /api/quizzes/sessions/<uuid:session_id>/abandon/ — the student
    declined the "continue your last quiz?" prompt. Marks the session so it
    is never offered again and its remaining questions become OMITTED
    (see annotate_student_status), without touching is_complete (this quiz
    was NOT finished, and must not be counted as if it were — see
    apps.admin_api.services.analytics' use of is_complete).
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, session_id):
        session = get_object_or_404(QuizSession, pk=session_id, student=request.user)
        if not session.is_complete:
            session.is_abandoned = True
            session.save(update_fields=["is_abandoned"])
        return Response(status=status.HTTP_204_NO_CONTENT)


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
        if not session.is_open:
            return Response(
                {"detail": "This quiz session is no longer accepting answers."}, status=status.HTTP_409_CONFLICT
            )
        if session.close_if_time_expired():
            return Response(
                {"detail": "This quiz session's time limit has been reached."}, status=status.HTTP_409_CONFLICT
            )

        serializer = QuizAnswerSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        session_question = get_object_or_404(
            QuizSessionQuestion.objects.select_related("question").prefetch_related(
                "question__answer_choices",
                "question__matrix_rows",
                "question__matrix_columns",
                "question__bowtie_options",
                "question__cloze_blanks__options",
                "question__dragdrop_items",
                "question__dragdrop_categories",
                "question__hotspot_targets",
            ),
            quiz_session=session,
            question_id=data["question_id"],
        )
        question = session_question.question

        # Which family of question this actually is — for an NGN_CASE item
        # that's ngn_type, not question_type itself (see
        # effective_question_type's own docstring).
        q_type = effective_question_type(question)

        try:
            if q_type in (QuestionType.MCQ, QuestionType.SATA, QuestionType.EMR):
                if not data["selected_choice_ids"]:
                    return Response({"detail": "selected_choice_ids is required for this question type."}, status=status.HTTP_400_BAD_REQUEST)
                graded = grade_submission(question, data["selected_choice_ids"])
                if q_type == QuestionType.MCQ and len(graded.selected_ids) > 1:
                    # MCQ has exactly one correct answer by definition — unlike
                    # SATA/EMR, which render as checkboxes on the frontend and
                    # are meant to allow several. Reject rather than silently
                    # picking an arbitrary one of the submitted ids to log.
                    return Response(
                        {"detail": "MCQ accepts only one selected choice."}, status=status.HTTP_400_BAD_REQUEST
                    )
            elif q_type == QuestionType.MATRIX:
                graded = grade_matrix(question, data["matrix_selections"])
            elif q_type == QuestionType.BOWTIE:
                graded = grade_bowtie(question, data["bowtie_option_ids"])
            elif q_type == QuestionType.CLOZE:
                graded = grade_cloze(question, data["cloze_selections"])
            elif q_type == QuestionType.DRAG_DROP:
                graded = grade_dragdrop(question, data["dragdrop_placements"])
            elif q_type == QuestionType.HOTSPOT:
                graded = grade_hotspot(question, data["hotspot_target_ids"])
            else:
                return Response(
                    {"detail": f"Question type {q_type} is not gradeable yet."}, status=status.HTTP_409_CONFLICT
                )
        except QuestionNotGradeable:
            return Response(
                {"detail": "This question is not available for grading."}, status=status.HTTP_409_CONFLICT
            )

        is_correct = graded.is_correct
        response_body = build_answer_key_for_type(question, q_type)

        log = StudentResponseLog.objects.create(
            student=request.user,
            question=question,
            quiz_session=session,
            is_correct=is_correct,
            time_taken_seconds=data["time_taken_seconds"],
        )
        if q_type in (QuestionType.MCQ, QuestionType.SATA, QuestionType.EMR):
            if q_type in (QuestionType.SATA, QuestionType.EMR):
                # Both render as checkboxes on the frontend and allow several
                # selections (EMRChoiceList reuses SATAChoiceList's markup) —
                # only MCQ is constrained to exactly one, enforced above.
                log.selected_choices.set(graded.selected_ids)
            elif graded.selected_ids:
                # MCQ: exactly one id expected (enforced above);
                # grade_submission already discarded anything not a real
                # choice of this question.
                log.selected_choice_id = next(iter(graded.selected_ids))
                log.save(update_fields=["selected_choice"])
            if not graded.selected_ids and data["selected_choice_ids"]:
                # Every submitted id was discarded by grade_submission as not
                # belonging to this question (stale/deleted choice, tampered
                # request) — there is no real AnswerChoice left to point
                # selected_choice(s) at, but CLAUDE.md requires this log to
                # capture what the student actually chose, not just
                # correct/incorrect. Keep the raw submitted ids here rather
                # than dropping them silently.
                log.selected_payload = {
                    "submitted_choice_ids": [str(choice_id) for choice_id in data["selected_choice_ids"]]
                }
                log.save(update_fields=["selected_payload"])
        else:
            log.selected_payload = graded.detail
            log.save(update_fields=["selected_payload"])

        # Deliberately does NOT touch session.current_question_index —
        # position is owned entirely by QuizSessionPositionView (called on
        # every Previous/Next/jump, not just a submission), since free
        # navigation means answering a question is no longer the same event
        # as moving past it.
        #
        # Completion, however, DOES get checked here: if this answer was the
        # last remaining unanswered question, the session auto-completes
        # rather than relying solely on the student explicitly clicking
        # "Finish Quiz" (QuizSessionFinishView). Without this, a student who
        # answers every question and simply closes the tab — the natural
        # thing to do once every question shows "correct"/"incorrect" — would
        # leave the session permanently is_complete=False, so
        # QuizSessionActiveView keeps surfacing it as "continue your last
        # quiz?" on every future login, forever, even though nothing is left
        # to answer. QuizSessionFinishView stays as the explicit action for
        # ending a quiz EARLY (some questions still skipped/unanswered).
        with transaction.atomic():
            # select_for_update: two near-simultaneous submissions for the
            # last two unanswered questions must not both read
            # "not yet complete" and race to write it — the lock serializes
            # them so only the request that actually observes the final
            # count performs the completion write.
            locked_session = QuizSession.objects.select_for_update().get(pk=session.pk)
            answered_questions = locked_session.response_logs.values("question_id").distinct().count()
            if answered_questions >= locked_session.total_questions:
                locked_session.is_complete = True
                locked_session.completed_at = timezone.now()
                locked_session.save(update_fields=["is_complete", "completed_at"])

        return Response({"is_correct": is_correct, **response_body})


class QuizSessionPositionView(APIView):
    """
    POST /api/quizzes/sessions/<uuid:session_id>/position/ — records which
    question the student is currently viewing. Called by the frontend on
    every Previous/Next/jump navigation, not just after a graded submission
    (see QuizAnswerSubmitView above, which no longer touches position at
    all) — that's what makes free backward/forward navigation possible
    while still resuming at the exact right question later.

    Also marks that question's QuizSessionQuestion.visited=True, which is
    what lets the frontend's question navigator distinguish "skipped"
    (visited, still no StudentResponseLog) from "not reached yet".
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, session_id):
        session = get_object_or_404(QuizSession, pk=session_id, student=request.user)
        if not session.is_open:
            return Response(
                {"detail": "This quiz session is no longer accepting position updates."},
                status=status.HTTP_409_CONFLICT,
            )
        if session.close_if_time_expired():
            return Response(
                {"detail": "This quiz session's time limit has been reached."}, status=status.HTTP_409_CONFLICT
            )
        serializer = QuizSessionPositionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session_question = get_object_or_404(
            QuizSessionQuestion, quiz_session=session, question_id=serializer.validated_data["question_id"]
        )

        if session.current_question_index != session_question.position:
            session.current_question_index = session_question.position
            session.save(update_fields=["current_question_index"])

        if not session_question.visited:
            session_question.visited = True
            session_question.save(update_fields=["visited"])

        return Response(status=status.HTTP_204_NO_CONTENT)


class QuizSessionFinishView(APIView):
    """
    POST /api/quizzes/sessions/<uuid:session_id>/finish/ — the student
    explicitly ended the quiz (the "Finish Quiz" action on the last
    question). Completion is a deliberate action rather than an implicit
    side effect of answering: free Previous/Next/jump navigation means
    reaching the last question's index no longer implies every question in
    the session has been seen, let alone answered.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, session_id):
        session = get_object_or_404(QuizSession, pk=session_id, student=request.user)
        if session.is_abandoned:
            # An abandoned session (resume prompt declined) is closed for
            # good — finishing it now would leave is_complete=True and
            # is_abandoned=True both set, a combination none of the
            # "in progress" queries elsewhere (QuizSessionQuerySet.in_progress)
            # expect to see.
            return Response(
                {"detail": "This quiz session was abandoned and can no longer be finished."},
                status=status.HTTP_409_CONFLICT,
            )
        if not session.is_complete:
            session.is_complete = True
            session.completed_at = timezone.now()
            session.save(update_fields=["is_complete", "completed_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)


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
        return parse_int_csv(get_list(name))

    return {
        "question_types": get_list("question_types"),
        "status_filters": get_list("status_filters"),
        "domains": get_int_list("domains"),
        "nursing_systems": get_int_list("nursing_systems"),
        "nclex_client_needs_subcategories": get_int_list("nclex_client_needs_subcategories"),
    }
