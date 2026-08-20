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

    permission_classes = [AllowAny]

    def post(self, request):
        return Response(status=200)
