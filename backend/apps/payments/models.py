from django.conf import settings
from django.db import models


class BillingInterval(models.TextChoices):
    MONTH = "MONTH", "Monthly"
    YEAR = "YEAR", "Yearly"


class SubscriptionPlan(models.Model):
    """
    Empty/unused in Phase 1 — table exists now so Phase 2 Stripe activation is config, not migration.

    trial_period_days / trial_question_limit are data, not code, for the
    client's requested trial model (a time window AND a distinct-question
    cap, whichever is hit first) — so the exact numbers can be tuned later
    without a deploy. Enforcement itself (checking these against
    UserSubscription.current_period_end and a distinct-question count from
    StudentResponseLog/QuizSession) is Phase 2 permission-check logic, not
    a schema concern — nothing reads these fields yet.
    """

    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    interval = models.CharField(max_length=10, choices=BillingInterval.choices)
    stripe_price_id = models.CharField(max_length=255, blank=True)
    trial_period_days = models.PositiveIntegerField(null=True, blank=True)
    trial_question_limit = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} (${self.price}/{self.interval.lower()})"


class SubscriptionStatus(models.TextChoices):
    """Mirrors Stripe's own subscription.status values — see apps.accounts.models.User.subscription_status."""

    TRIALING = "TRIALING", "Trialing"
    ACTIVE = "ACTIVE", "Active"
    PAST_DUE = "PAST_DUE", "Past due"
    CANCELED = "CANCELED", "Canceled"
    UNPAID = "UNPAID", "Unpaid"
    INCOMPLETE = "INCOMPLETE", "Incomplete"


class UserSubscription(models.Model):
    """Empty/unused in Phase 1 — synced from Stripe webhooks in Phase 2."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name="subscriptions")
    status = models.CharField(max_length=15, choices=SubscriptionStatus.choices)
    stripe_subscription_id = models.CharField(max_length=255, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.plan} ({self.status})"
