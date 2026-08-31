from rest_framework import generics, permissions

# ScopedRateThrottle reads a view's `throttle_scope` attribute and looks up
# the matching rate in REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]
# (settings/base.py) — the same pattern the throttled auth views in
# apps/accounts/views.py use.
from rest_framework.throttling import ScopedRateThrottle

from .serializers import QuestionIssueReportSerializer, QuizFeedbackSerializer


class QuizFeedbackCreateView(generics.CreateAPIView):
    """POST-only: submits the end-of-quiz survey. No read endpoints — feedback is reviewed via the admin."""

    serializer_class = QuizFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    # 20/hour per authenticated user (see settings/base.py). Being logged in
    # is not by itself a reason to allow unlimited writes: these rows carry
    # free text, so without a rate limit one account could cheaply fill the
    # database. A student finishing a quiz submits this once, so 20/hour is
    # far above any legitimate usage. The serializer's max_length caps bound
    # the size of each row; this bounds how many of them arrive.
    throttle_scope = "feedback"


class QuestionIssueReportCreateView(generics.CreateAPIView):
    """POST-only: submits a single 'Report an Issue' click on a question."""

    serializer_class = QuestionIssueReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    # Shares the "feedback" bucket with the survey endpoint above, deliberately:
    # the two endpoints write to the same kind of free-text storage, so one
    # combined budget is what actually bounds the abuse. 20/hour still leaves
    # room for a student who genuinely flags several bad questions in a sitting.
    throttle_scope = "feedback"
