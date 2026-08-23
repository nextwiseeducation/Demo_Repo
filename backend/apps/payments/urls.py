from django.urls import path

from .views import StripeWebhookView

# Mounted at /api/payments/ by config/urls.py, so this becomes
# POST /api/payments/webhook/ — the single URL Stripe would be configured
# to send webhook events to once Phase 2 activates real payments.
urlpatterns = [
    path("webhook/", StripeWebhookView.as_view(), name="stripe-webhook"),
]
