from django.test import TestCase

from .models import BillingInterval, SubscriptionPlan


class SubscriptionPlanTrialFieldsTests(TestCase):
    def test_trial_fields_are_optional(self):
        plan = SubscriptionPlan.objects.create(name="Standard", price="19.99", interval=BillingInterval.MONTH)
        self.assertIsNone(plan.trial_period_days)
        self.assertIsNone(plan.trial_question_limit)

    def test_trial_fields_can_be_set(self):
        plan = SubscriptionPlan.objects.create(
            name="Free Trial",
            price="0.00",
            interval=BillingInterval.MONTH,
            trial_period_days=7,
            trial_question_limit=50,
        )
        self.assertEqual(plan.trial_period_days, 7)
        self.assertEqual(plan.trial_question_limit, 50)
