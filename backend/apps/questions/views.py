from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Question
from .serializers import QuestionListSerializer


class QuestionListView(generics.ListAPIView):
    """
    GET /api/questions/ — every active question, answer key omitted (see
    PublicAnswerChoiceSerializer). No server-side filtering yet: the quiz
    setup UI filters this list client-side, same as it did against the mock
    data it's replacing. Real filter/search query params belong to
    Milestone 2/3, once the question bank is large enough to need them —
    fetching the whole active set is fine at this scale.
    """

    queryset = Question.objects.filter(is_active=True).select_related(
        "nursing_system", "topic", "nclex_client_needs_category"
    ).prefetch_related("answer_choices")
    serializer_class = QuestionListSerializer


class QuestionSubmitView(APIView):
    """
    POST /api/questions/<id>/submit/ — grades a single question and reveals
    the answer key (is_correct + rationale per choice) now that the student
    has actually answered.

    Stateless: nothing is persisted (no StudentResponseLog row). Doing that
    for real needs a QuizSession to attach it to, and QuizSession has no API
    of its own yet (Milestone 3 scope per CLAUDE.md) — the quiz UI already
    tells students results aren't saved in this preview ("it isn't saved to
    your account").

    Grading rule (exact selected-set match) mirrors the frontend's
    isAnswerCorrect, which is itself flagged as "the simplest defensible
    SATA rule, pending Milestone 3's real grading logic" — see
    quizSessionReducer.ts.
    """

    def post(self, request, pk):
        try:
            question = Question.objects.prefetch_related("answer_choices").get(pk=pk, is_active=True)
        except Question.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        choices = list(question.answer_choices.all())
        valid_ids = {str(c.id) for c in choices}
        # Any id in the request that isn't actually one of this question's
        # choices (malformed/tampered request) is silently dropped rather
        # than erroring — grading just treats it as "not selected".
        selected_ids = {str(i) for i in request.data.get("selected_choice_ids", [])} & valid_ids
        correct_ids = {str(c.id) for c in choices if c.is_correct}

        return Response(
            {
                "is_correct": selected_ids == correct_ids,
                "choices": [
                    {"id": str(c.id), "is_correct": c.is_correct, "rationale": c.rationale} for c in choices
                ],
            }
        )
