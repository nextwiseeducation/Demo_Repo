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

# Every taxonomy model gets its own plain ModelAdmin — CLAUDE.md's Milestone
# 1 scope is just "categorisation management" existing via the default
# admin; custom bulk-import/CRUD tooling for these is Milestone 2 work.
# The pattern repeated below (list_display for the columns shown in the
# list view, search_fields for the admin's search box, list_filter for the
# sidebar filters) is standard Django admin configuration, not custom logic.


@admin.register(NursingSystem)
class NursingSystemAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("name", "nursing_system")
    # Lets an admin narrow the Topic list down to one system at a time —
    # useful once there are many systems each with many topics.
    list_filter = ("nursing_system",)
    search_fields = ("name",)


@admin.register(Subtopic)
class SubtopicAdmin(admin.ModelAdmin):
    list_display = ("name", "topic")
    # Two-level filter: narrow by system first, then by the topics within
    # it — mirrors the actual nursing_system -> topic -> subtopic hierarchy.
    list_filter = ("topic__nursing_system", "topic")
    search_fields = ("name",)


@admin.register(ClientNeedsCategory)
class ClientNeedsCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "exam_type")
    # Lets an admin view just the RN categories or just the PN ones, which
    # matters once both are populated (only RN is seeded in Phase 1).
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
    # shared_scenario (the long clinical vignette text) is intentionally
    # left out of list_display — showing a full TextField in a list-view
    # column would make the list unreadable; the admin's detail/edit page is
    # still where the full text is viewed/edited.
    list_display = ("title",)
    search_fields = ("title",)
