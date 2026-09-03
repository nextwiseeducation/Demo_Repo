from rest_framework import serializers


class SystemAttemptRowSerializer(serializers.Serializer):
    """One row of the real-data top-10-nursing-systems-by-attempts bar chart."""

    id = serializers.IntegerField()
    name = serializers.CharField()
    attempts = serializers.IntegerField()


class WeakSystemRowSerializer(serializers.Serializer):
    """One row of the real-data weakest-5-nursing-systems table."""

    id = serializers.IntegerField()
    name = serializers.CharField()
    attempts = serializers.IntegerField()
    correct = serializers.IntegerField()
    correct_rate = serializers.FloatField()


class RevenuePointSerializer(serializers.Serializer):
    month = serializers.CharField()
    revenue = serializers.IntegerField()


class RevenueSeriesSerializer(serializers.Serializer):
    points = RevenuePointSerializer(many=True)
    is_sample = serializers.BooleanField()


class SubscriptionMixPointSerializer(serializers.Serializer):
    tier = serializers.CharField()
    percentage = serializers.FloatField()


class SubscriptionMixSerializer(serializers.Serializer):
    points = SubscriptionMixPointSerializer(many=True)
    is_sample = serializers.BooleanField()


class AdminAnalyticsSerializer(serializers.Serializer):
    """
    Serializes the plain dict returned by
    apps.admin_api.services.analytics.build_admin_analytics().

    total_revenue is a DecimalField so it round-trips through JSON as a
    fixed-precision string (e.g. "0.00") rather than a float that could
    misrepresent cents. mom_student_growth and avg_quiz_score are
    allow_null=True because both are legitimately undefined on a database
    with no prior-month baseline / no completed quiz sessions yet — see
    services/analytics.py for why a fabricated number would be worse than
    null here.
    """

    total_students = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    mom_student_growth = serializers.FloatField(allow_null=True)
    total_questions_answered = serializers.IntegerField()
    top_systems_by_attempts = SystemAttemptRowSerializer(many=True)
    avg_quiz_score = serializers.FloatField(allow_null=True)
    completion_rate = serializers.FloatField()
    weakest_systems = WeakSystemRowSerializer(many=True)
    revenue_series = RevenueSeriesSerializer()
    subscription_mix = SubscriptionMixSerializer()
