"""
All ORM aggregation behind GET /api/admin/analytics/ lives here rather than
in the view, matching this project's existing convention of keeping
business logic in a per-app services.py (see apps.questions.services,
apps.quizzes.services).

Two metrics have no direct field to read and are deliberately DERIVED
rather than invented:

- "Total revenue": apps.payments has no Payment/Invoice model, only
  SubscriptionPlan.price. What's computed here is the combined price of
  every currently ACTIVE/TRIALING subscription (i.e. MRR-shaped), not
  revenue collected to date. Both are $0 today since Stripe isn't active.
  Named `total_revenue` to match the brief; the imprecision is documented
  here rather than silently assumed away.
- "Average quiz score": QuizSession has no `score` field. This computes
  the mean, across all quiz sessions, of that session's own percent-
  correct rate (not a flat correct/total over every StudentResponseLog
  ever created) — so a student who took one 5-question quiz and one
  50-question quiz counts equally, rather than the 50-question quiz
  dominating the average.

Every aggregate is written to survive an empty database: Coalesce for
sums, explicit zero-guards for ratios, and `None` (never a fabricated
number) for a rate that has no meaningful baseline yet.
"""

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import (
    Avg,
    Case,
    Count,
    DecimalField,
    ExpressionWrapper,
    F,
    FloatField,
    Q,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.accounts.models import UserRole
from apps.payments.models import SubscriptionStatus as PaymentsSubscriptionStatus
from apps.payments.models import UserSubscription
from apps.quizzes.models import QuizSession, StudentResponseLog
from apps.taxonomy.models import NursingSystem

# A nursing system needs at least this many attempts before it's eligible
# for the "weakest systems" ranking. Without this floor, a system with a
# single attempt that happened to be wrong scores 0% and would outrank a
# genuinely weak system with hundreds of attempts at, say, 41% correct —
# the floor removes both that statistical noise and the division-by-zero
# case in one filter.
MIN_ATTEMPTS_FOR_WEAK_SYSTEM = 5

WEAKEST_SYSTEMS_LIMIT = 5
TOP_SYSTEMS_LIMIT = 10


def _total_students() -> int:
    return _student_queryset().count()


def _student_queryset():
    return get_user_model().objects.filter(role=UserRole.STUDENT)


def _total_revenue() -> Decimal:
    """
    STRIPE SWAP POINT ------------------------------------------------------
    Sum of SubscriptionPlan.price across every currently ACTIVE/TRIALING
    UserSubscription row. Both tables are empty until Phase 2 activates
    Stripe, so this returns Decimal("0.00") today — Coalesce is what makes
    that true instead of the bare Sum() returning None, which a
    DecimalField serializer would 500 on.

    To make this real once Stripe webhooks populate apps.payments: either
    keep this shape (it already reflects "value of active subscriptions"
    correctly once real rows exist) or, if the client wants true
    revenue-to-date rather than current subscription value, sum actual
    Stripe charge/invoice amounts from a new ledger table instead — nothing
    outside this function needs to change either way.
    -------------------------------------------------------------------------
    """
    result = UserSubscription.objects.filter(
        status__in=(PaymentsSubscriptionStatus.ACTIVE, PaymentsSubscriptionStatus.TRIALING)
    ).aggregate(
        total=Coalesce(
            Sum("plan__price"),
            Value(Decimal("0.00")),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )
    )
    return result["total"]


def _mom_student_growth() -> float | None:
    """
    Month-over-month growth in student registrations. Returns None (not 0,
    not a fabricated 100%) when there is no prior month to compare against
    — any number computed from zero would misrepresent an absence of data
    as a real trend.
    """
    now = timezone.now()
    this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # Subtracting one day from the 1st of this month always lands in the
    # previous month regardless of month length or a year boundary, and
    # .replace(day=1) then snaps it to that month's start — safer than
    # hand-rolling "month - 1" arithmetic, which breaks in January.
    prev_month_start = (this_month_start - timedelta(days=1)).replace(day=1)

    counts = (
        _student_queryset()
        .filter(date_joined__gte=prev_month_start)
        .aggregate(
            this_month=Count("id", filter=Q(date_joined__gte=this_month_start)),
            prev_month=Count(
                "id", filter=Q(date_joined__gte=prev_month_start, date_joined__lt=this_month_start)
            ),
        )
    )
    if counts["prev_month"] == 0:
        return None
    growth = (counts["this_month"] - counts["prev_month"]) / counts["prev_month"] * 100
    return round(growth, 1)


def _total_questions_answered() -> int:
    return StudentResponseLog.objects.count()


def _top_systems_by_attempts() -> list[dict]:
    """
    Real data (no sample badge). One query: NursingSystem -> Question ->
    StudentResponseLog is a single LEFT JOIN pair aggregated with one
    GROUP BY, so a system with zero attempts still appears with attempts=0
    (needed for a "top 10" list to render meaningfully before the platform
    has much usage data). The "name" tiebreaker keeps ordering
    deterministic across page loads when several systems tie at 0.
    """
    return list(
        NursingSystem.objects.annotate(attempts=Count("questions__response_logs"))
        .values("id", "name", "attempts")
        .order_by("-attempts", "name")[:TOP_SYSTEMS_LIMIT]
    )


def _avg_quiz_score() -> float | None:
    """
    Mean of each quiz session's own percent-correct rate — see module
    docstring for why this (rather than a flat correct/total ratio over
    every response ever logged) is the right definition of "average quiz
    score" given QuizSession has no score field of its own.
    """
    # Postgres refuses to CAST a boolean directly to double precision, so
    # is_correct is converted via a CASE expression (1.0/0.0) instead of
    # Cast() — the two are equivalent for Avg's purposes.
    per_session = StudentResponseLog.objects.values("quiz_session").annotate(
        pct=Avg(Case(When(is_correct=True, then=Value(1.0)), default=Value(0.0), output_field=FloatField()))
        * 100
    )
    result = per_session.aggregate(overall=Avg("pct"))
    overall = result["overall"]
    return None if overall is None else round(overall, 1)


def _completion_rate() -> float:
    sessions = QuizSession.objects.aggregate(
        total=Count("id"), complete=Count("id", filter=Q(is_complete=True))
    )
    if sessions["total"] == 0:
        # Unlike avg_quiz_score, 0.0 here is a real and meaningful answer
        # ("no sessions have been completed yet"), not a misleading
        # zero-out-of-nothing — so no None branch is needed.
        return 0.0
    return round(sessions["complete"] / sessions["total"] * 100, 1)


def _weakest_systems() -> list[dict]:
    """
    Both Count()s below traverse the SAME join chain
    (questions__response_logs), so there is no fan-out double-counting and
    distinct=True is unnecessary. That would only be needed if a second,
    INDEPENDENT multi-valued join (e.g. questions__tags) were added to this
    queryset later — don't do that without revisiting this comment.
    """
    return list(
        NursingSystem.objects.annotate(
            attempts=Count("questions__response_logs"),
            correct=Count(
                "questions__response_logs",
                filter=Q(questions__response_logs__is_correct=True),
            ),
        )
        .filter(attempts__gte=MIN_ATTEMPTS_FOR_WEAK_SYSTEM)
        .annotate(
            correct_rate=ExpressionWrapper(F("correct") * 100.0 / F("attempts"), output_field=FloatField())
        )
        .values("id", "name", "attempts", "correct", "correct_rate")
        .order_by("correct_rate", "-attempts", "name")[:WEAKEST_SYSTEMS_LIMIT]
    )


def _sample_revenue_series() -> dict:
    """
    STRIPE SWAP POINT ------------------------------------------------------
    Twelve months of revenue, currently fabricated. Month labels are REAL
    (generated backwards from today) so the chart's x-axis is already
    correct the moment the values become real — only `revenue` is
    invented.

    To make this real: replace the loop body with a query against actual
    Stripe charge/invoice data (or a local ledger table synced from Stripe
    webhooks — apps.payments has neither yet) grouped by month, and drop
    is_sample to False. Nothing outside this function needs to change: the
    amber "Sample data" badge on the frontend is driven by is_sample in
    this response, not a frontend-side constant.
    -------------------------------------------------------------------------
    """
    this_month_start = timezone.now().replace(day=1)
    # Walk backwards one month at a time from the current month's 1st —
    # (day - timedelta(days=1)).replace(day=1) always lands on the
    # previous month's 1st regardless of month length or a year boundary,
    # which hand-rolled "month - 1" arithmetic gets wrong in January.
    months = [this_month_start]
    for _ in range(11):
        months.append((months[-1] - timedelta(days=1)).replace(day=1))
    months.reverse()

    points = [
        # Fabricated but deterministic-looking values, oldest month first —
        # only the number is invented, the month label is real.
        {"month": month.strftime("%b %Y"), "revenue": (index * 137 % 900) + 400}
        for index, month in enumerate(months)
    ]
    return {"points": points, "is_sample": True}


def _sample_subscription_mix() -> dict:
    """STRIPE SWAP POINT — see _sample_revenue_series. Real tiers, fabricated percentages."""
    return {
        "points": [
            {"tier": "Free", "percentage": 60.0},
            {"tier": "Basic", "percentage": 25.0},
            {"tier": "Pro", "percentage": 15.0},
        ],
        "is_sample": True,
    }


def build_admin_analytics() -> dict:
    """
    The single entry point GET /api/admin/analytics/ calls. Returns a plain
    dict shaped to AdminAnalyticsSerializer — kept as one function (rather
    than one query per view method) so every metric here is documented and
    tested in one place.
    """
    return {
        "total_students": _total_students(),
        "total_revenue": _total_revenue(),
        "mom_student_growth": _mom_student_growth(),
        "total_questions_answered": _total_questions_answered(),
        "top_systems_by_attempts": _top_systems_by_attempts(),
        "avg_quiz_score": _avg_quiz_score(),
        "completion_rate": _completion_rate(),
        "weakest_systems": _weakest_systems(),
        "revenue_series": _sample_revenue_series(),
        "subscription_mix": _sample_subscription_mix(),
    }
