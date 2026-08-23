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

    # No UUIDPKMixin/TimeStampedMixin here — unlike Question/User/etc,
    # SubscriptionPlan rows are a handful of admin-defined pricing tiers
    # (e.g. "Monthly", "Annual"), not per-user or externally-referenced
    # entities, so Django's default auto-increment int PK is sufficient.
    name = models.CharField(max_length=100)
    # DecimalField (not FloatField) is required for money — floats can't
    # represent values like 19.99 exactly in binary, which would cause
    # subtle rounding errors in prices; max_digits=8/decimal_places=2
    # supports up to 999999.99.
    price = models.DecimalField(max_digits=8, decimal_places=2)
    interval = models.CharField(max_length=10, choices=BillingInterval.choices)
    # blank=True (no null=True — CharField stores "none" as ""): empty
    # until a real Stripe Price object exists for this plan, which won't
    # happen until Phase 2 activation.
    stripe_price_id = models.CharField(max_length=255, blank=True)
    # How many days the trial lasts, if this plan offers one. null=True
    # (not just blank=True, unlike stripe_price_id above) because this is
    # an IntegerField — there's no equivalent "empty string" for numbers,
    # so "this plan has no trial" must be represented as NULL rather than 0
    # (0 would ambiguously mean "a trial that ends immediately").
    trial_period_days = models.PositiveIntegerField(null=True, blank=True)
    # How many distinct questions a trialing student may answer before
    # being paywalled, if this plan caps that. Also null=True for the same
    # reason as trial_period_days — "no cap" must be distinguishable from
    # "a cap of zero questions".
    trial_question_limit = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        # e.g. "Monthly ($19.99/month)" — interval.lower() turns "MONTH"
        # into "month" for a more natural-reading label than the raw
        # TextChoices value.
        return f"{self.name} (${self.price}/{self.interval.lower()})"


class SubscriptionStatus(models.TextChoices):
    """Mirrors Stripe's own subscription.status values — see apps.accounts.models.User.subscription_status."""

    # Deliberately more granular than apps.accounts.models.SubscriptionStatus
    # (which only has FREE/ACTIVE/PAST_DUE/CANCELED): this is the actual
    # system-of-record status synced from Stripe webhooks in Phase 2, so it
    # needs to represent every state Stripe itself can report, including
    # transitional ones Stripe uses (TRIALING, UNPAID, INCOMPLETE) that the
    # simpler denormalized cache on User doesn't need to distinguish.
    TRIALING = "TRIALING", "Trialing"
    ACTIVE = "ACTIVE", "Active"
    PAST_DUE = "PAST_DUE", "Past due"
    CANCELED = "CANCELED", "Canceled"
    UNPAID = "UNPAID", "Unpaid"
    INCOMPLETE = "INCOMPLETE", "Incomplete"


class UserSubscription(models.Model):
    """Empty/unused in Phase 1 — synced from Stripe webhooks in Phase 2."""

    # No UUIDPKMixin/TimeStampedMixin here either — same reasoning as
    # SubscriptionPlan; this table has zero rows in Phase 1, and when
    # Phase 2 populates it, Stripe's own subscription id
    # (stripe_subscription_id below) is the meaningful external identifier,
    # not this row's own PK.
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscriptions")
    # on_delete=PROTECT (not CASCADE): a SubscriptionPlan shouldn't be
    # deletable while any user still has a subscription referencing it —
    # mirrors the same protective pattern used for taxonomy FKs on Question
    # (apps/questions/models.py), preventing an admin from accidentally
    # orphaning real subscription data by deleting a pricing plan.
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name="subscriptions")
    status = models.CharField(max_length=15, choices=SubscriptionStatus.choices)
    # The Stripe subscription object's own id (e.g. "sub_...") — what
    # actually ties this row back to Stripe's system of record; blank until
    # Phase 2 creates real Stripe subscriptions.
    stripe_subscription_id = models.CharField(max_length=255, blank=True)
    # When the current billing period (or trial, per
    # SubscriptionPlan.trial_period_days) ends — this is the field the
    # trial/paywall enforcement logic (Phase 2) checks against "now" to
    # decide if access should still be granted; mirrors how Stripe itself
    # models a subscription's current_period_end.
    current_period_end = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.plan} ({self.status})"
