from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class StripeWebhookView(APIView):
    """
    Stubbed per CLAUDE.md: endpoint exists and accepts requests now so
    Phase 2 Stripe activation is a config change, not a migration. No
    signature verification or event processing yet — STRIPE_WEBHOOK_SECRET
    is a placeholder env var until that logic is built.
    """

    # Must be reachable without authentication — Stripe's own servers call
    # this endpoint directly (not a logged-in user's browser), so there's
    # no JWT to check. Real signature verification (using
    # STRIPE_WEBHOOK_SECRET, settings/base.py) is what will actually secure
    # this endpoint once built in Phase 2 — AllowAny is safe for now only
    # because the handler below does nothing with the request body yet.
    permission_classes = [AllowAny]

    def post(self, request):
        # Always returns 200 immediately with no processing — this is
        # deliberately a no-op. The real handler (Phase 2) will need to:
        # verify the Stripe-Signature header against
        # settings.STRIPE_WEBHOOK_SECRET, parse the event type, and update
        # UserSubscription/User.subscription_status accordingly. Returning
        # 200 unconditionally right now just proves the endpoint exists and
        # is reachable, which is all Milestone 1 requires.
        return Response(status=200)
