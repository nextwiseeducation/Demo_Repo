from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .models import Question
from .serializers import QuestionListSerializer, QuestionSubmitSerializer
from .services import QuestionNotGradeable, build_answer_key, grade_submission


class QuestionListView(generics.ListAPIView):
    """
    GET /api/questions/ — active questions, answer key omitted (see
    PublicAnswerChoiceSerializer).

    No server-side filtering yet: the quiz setup UI filters this list
    client-side, same as it did against the mock data it replaced. Real
    filter/search query params belong to Milestone 2/3.

    Paginated via the project-wide DEFAULT_PAGINATION_CLASS
    (apps/core/pagination.py), NOT because this view opts in. That is worth
    knowing before adding filtering here: this endpoint used to return every
    active question in one unpaginated response, which was survivable only
    while the bank held a dozen rows. At the specced 4,000+ questions
    (CLAUDE.md), each serializing its stem, clinical scenario and every
    answer choice, that response ran to megabytes on Render's free tier.
    Clients must page through; they cannot assume one request sees
    everything.
    """

    queryset = (
        Question.objects.filter(is_active=True)
        .select_related(
            "domain", "nursing_system", "topic", "nclex_client_needs_category", "nclex_client_needs_subcategory", "case_study"
        )
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
    )
    serializer_class = QuestionListSerializer


class QuestionSubmitView(APIView):
    """
    POST /api/questions/<id>/submit/ — grades one question and reveals the
    answer key (is_correct + rationale per choice) now that the student has
    actually answered.

    Stateless: nothing is persisted (no StudentResponseLog row). The real,
    session-aware graded/persisted path now lives in
    apps.quizzes.views.QuizAnswerSubmitView (POST
    /api/quizzes/sessions/<id>/answers/), which every real quiz-taking flow
    uses instead of this one. This endpoint is kept deliberately as a
    stateless preview path (e.g. future content-team preview tooling that
    wants to test a question without it counting as an attempt) — not dead
    code, just not what a student's real quiz hits anymore.

    KNOWN RESIDUAL RISK — read before extending this endpoint.
    Grading is the moment the answer key becomes visible, and because
    nothing is recorded, there is no cost to asking. Any authenticated
    account can therefore walk the question bank and harvest the key by
    submitting an arbitrary guess per question; the id of every active
    question is available from the list endpoint above. Two things bound
    that today: a submission must contain at least one real selection (so
    merely skipping a question no longer returns its answers), and the
    "question_submit" throttle caps the rate at 300/hour — far above a real
    quiz-taker, far below a practical scrape of thousands of questions.
    Neither is a fix by itself — that risk is specific to THIS stateless
    endpoint. QuizAnswerSubmitView (see above) is the actual fix: it grades
    only within a real QuizSession and writes a StudentResponseLog row each
    time, so answers are revealed once per question per attempt and any
    harvesting shows up as data rather than passing unseen. This endpoint
    stays as-is, residual risk and all, for its narrower preview use case.

    Grading itself lives in services.py, not here — Milestone 3's quiz
    engine and Phase 2's analytics need the identical rule, and SATA
    partial credit will change it.
    """

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "question_submit"

    def post(self, request, pk):
        # Validated before the question is even fetched: a malformed body is
        # a client error regardless of whether the id exists, and checking
        # first keeps a bad payload from reaching the grading code.
        serializer = QuestionSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            question = Question.objects.prefetch_related("answer_choices").get(pk=pk, is_active=True)
        except Question.DoesNotExist:
            # is_active=True is part of the lookup, so a retired question is
            # reported as missing rather than being gradeable — a question
            # pulled from circulation should not still be answerable.
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            graded = grade_submission(question, serializer.validated_data["selected_choice_ids"])
        except QuestionNotGradeable:
            # The question has no correct answer recorded — a content bug,
            # not something the student did wrong, so it must not be
            # reported as a wrong answer. 409 Conflict says the request was
            # fine but the resource is in a state that can't satisfy it.
            # Deliberately vague to the client (the detailed reason is in
            # the exception, for logs) while still being actionable enough
            # for the UI to say "skip this one".
            return Response(
                {"detail": "This question is not available for grading."},
                status=status.HTTP_409_CONFLICT,
            )

        return Response({"is_correct": graded.is_correct, "choices": build_answer_key(question)})
