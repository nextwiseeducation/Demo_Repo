from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsContentAdminOrAbove
from apps.admin_api.serializers.taxonomy import (
    CaseStudyOptionSerializer,
    ClientNeedsCategoryOptionSerializer,
    DomainOptionSerializer,
    NursingSystemOptionSerializer,
    TagOptionSerializer,
)
from apps.taxonomy.models import CaseStudy, ClientNeedsCategory, Domain, NursingSystem, Tag


class AdminTaxonomyView(APIView):
    """
    GET /api/admin/taxonomy/ — every taxonomy value the Content Team form
    needs, nested (NursingSystem -> Topic -> Subtopic, ClientNeedsCategory
    -> ClientNeedsSubcategory) so the cascading dropdowns need no further
    request.

    Not in the original endpoint list: /api/quizzes/facet-counts/ already
    exposes systems/domains/client-needs-subcategories but not topics, and
    the admin question form needs topics for its Nursing System -> Topic
    cascade. Read-only, content-admin-or-above (same audience as the
    question form itself).
    """

    permission_classes = [IsContentAdminOrAbove]

    def get(self, request):
        return Response(
            {
                "nursing_systems": NursingSystemOptionSerializer(
                    NursingSystem.objects.prefetch_related("topics__subtopics"), many=True
                ).data,
                "domains": DomainOptionSerializer(Domain.objects.all(), many=True).data,
                "client_needs_categories": ClientNeedsCategoryOptionSerializer(
                    ClientNeedsCategory.objects.prefetch_related("subcategories"), many=True
                ).data,
                "tags": TagOptionSerializer(Tag.objects.all(), many=True).data,
                "case_studies": CaseStudyOptionSerializer(CaseStudy.objects.all(), many=True).data,
            }
        )
