from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsSuperuser
from apps.admin_api.serializers.analytics import AdminAnalyticsSerializer
from apps.admin_api.services.analytics import build_admin_analytics


class AdminAnalyticsView(APIView):
    """
    GET /api/admin/analytics/ — platform-wide business metrics for the
    Business Analytics dashboard. Superuser only: this is the one admin
    section that exposes revenue figures, which content admins have no
    business need to see.
    """

    permission_classes = [IsSuperuser]

    def get(self, request):
        data = build_admin_analytics()
        return Response(AdminAnalyticsSerializer(data).data)
