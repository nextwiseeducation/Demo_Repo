from rest_framework import serializers

from apps.taxonomy.models import (
    CaseStudy,
    ClientNeedsCategory,
    ClientNeedsSubcategory,
    Domain,
    NursingSystem,
    Subtopic,
    Tag,
    Topic,
)


class SubtopicOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subtopic
        fields = ["id", "name"]


class TopicOptionSerializer(serializers.ModelSerializer):
    """
    Nests subtopics so the admin question form's cascading Topic ->
    Subtopic dropdowns need no further request once the taxonomy tree has
    loaded once (see useTaxonomyOptions, cached with staleTime: Infinity).
    """

    subtopics = SubtopicOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Topic
        fields = ["id", "name", "subtopics"]


class NursingSystemOptionSerializer(serializers.ModelSerializer):
    topics = TopicOptionSerializer(many=True, read_only=True)

    class Meta:
        model = NursingSystem
        fields = ["id", "name", "topics"]


class DomainOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ["id", "name"]


class ClientNeedsSubcategoryOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientNeedsSubcategory
        fields = ["id", "name"]


class ClientNeedsCategoryOptionSerializer(serializers.ModelSerializer):
    subcategories = ClientNeedsSubcategoryOptionSerializer(many=True, read_only=True)

    class Meta:
        model = ClientNeedsCategory
        fields = ["id", "name", "exam_type", "subcategories"]


class TagOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]


class CaseStudyOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseStudy
        fields = ["id", "external_id", "title"]
