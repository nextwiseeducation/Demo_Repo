from django.test import TestCase

from .models import BillingInterval, SubscriptionPlan


class SubscriptionPlanTrialFieldsTests(TestCase):
    """
    Confirms the two trial-model fields (added to support the client's
    "time window AND question-count cap" free-trial requirement — see the
    docstring on SubscriptionPlan in models.py) behave correctly on both
    ends: absent by default for a plan with no trial, and settable for one
    that has one.
    """

    def test_trial_fields_are_optional(self):
        # A plan created without mentioning trial_period_days/
        # trial_question_limit at all should leave both as None — proves
        # a "regular" paid plan (no trial) doesn't need to explicitly opt
        # out of anything, and that null=True actually takes effect rather
        # than some other default sneaking in.
        plan = SubscriptionPlan.objects.create(name="Standard", price="19.99", interval=BillingInterval.MONTH)
        self.assertIsNone(plan.trial_period_days)
        self.assertIsNone(plan.trial_question_limit)

    def test_trial_fields_can_be_set(self):
        # A plan explicitly configured with both trial parameters should
        # store and return them exactly as given — the actual enforcement
        # logic (checking these against a student's usage) is Phase 2 work
        # and isn't exercised here; this test only confirms the schema
        # holds the values correctly.
        plan = SubscriptionPlan.objects.create(
            name="Free Trial",
            price="0.00",
            interval=BillingInterval.MONTH,
            trial_period_days=7,
            trial_question_limit=50,
        )
        self.assertEqual(plan.trial_period_days, 7)
        self.assertEqual(plan.trial_question_limit, 50)
