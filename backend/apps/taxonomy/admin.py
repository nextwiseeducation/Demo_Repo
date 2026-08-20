from django.contrib import admin

from .models import (
    CaseStudy,
    ClientNeedsCategory,
    ClientNeedsSubcategory,
    NursingSystem,
    Subtopic,
    Tag,
    Topic,
)


@admin.register(NursingSystem)
class NursingSystemAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("name", "nursing_system")
    list_filter = ("nursing_system",)
    search_fields = ("name",)


@admin.register(Subtopic)
class SubtopicAdmin(admin.ModelAdmin):
    list_display = ("name", "topic")
    list_filter = ("topic__nursing_system", "topic")
    search_fields = ("name",)


@admin.register(ClientNeedsCategory)
class ClientNeedsCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "exam_type")
    list_filter = ("exam_type",)
    search_fields = ("name",)


@admin.register(ClientNeedsSubcategory)
class ClientNeedsSubcategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "category")
    list_filter = ("category",)
    search_fields = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(CaseStudy)
class CaseStudyAdmin(admin.ModelAdmin):
    list_display = ("title",)
    search_fields = ("title",)
