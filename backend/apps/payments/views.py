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

    # Deliberately NOT rate-limited, unlike every other unauthenticated
    # endpoint in this project.
    #
    # Throttling a webhook receiver is actively harmful: Stripe delivers
    # events in bursts (a billing run touches many subscriptions at once)
    # and treats any non-2xx as a delivery failure to retry with backoff.
    # A throttle would therefore turn a legitimate burst into rejected
    # events, retry storms, and — once this handler does real work in Phase
    # 2 — subscription states that silently fall out of sync with Stripe.
    #
    # The right control for a webhook is authenticity, not volume: verify
    # the Stripe-Signature header against STRIPE_WEBHOOK_SECRET and reject
    # anything unsigned. That is Phase 2 work, and until it exists this
    # endpoint is safe only because it reads nothing and does nothing.
    throttle_classes = []

    def post(self, request):
        # Always returns 200 immediately with no processing — this is
        # deliberately a no-op. The real handler (Phase 2) will need to:
        # verify the Stripe-Signature header against
        # settings.STRIPE_WEBHOOK_SECRET, parse the event type, and update
        # UserSubscription/User.subscription_status accordingly. Returning
        # 200 unconditionally right now just proves the endpoint exists and
        # is reachable, which is all Milestone 1 requires.
        return Response(status=200)
