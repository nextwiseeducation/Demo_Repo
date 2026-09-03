from django.contrib import admin

from .models import (
    AnswerChoice,
    BowTieOption,
    ClozeBlank,
    ClozeOption,
    DragDropCategory,
    DragDropItem,
    HotSpotTarget,
    MatrixCell,
    MatrixColumn,
    MatrixRow,
    Question,
)


class AnswerChoiceInline(admin.TabularInline):
    # TabularInline renders AnswerChoice rows directly inside the Question
    # edit page (as an editable table) instead of requiring a separate trip
    # to the AnswerChoice admin — this is what lets an editor create an MCQ
    # and its choices in one screen. extra=0 means no blank extra rows are
    # pre-rendered by default (an editor adds rows explicitly via "Add
    # another"), rather than cluttering the form with empty placeholders.
    model = AnswerChoice
    extra = 0


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    # "__str__" as a list_display column reuses Question.__str__ (the
    # "[TYPE] truncated stem" format) as the row label, instead of showing
    # the raw UUID pk.
    list_display = (
        "__str__",
        "question_type",
        "difficulty",
        "domain",
        "nursing_system",
        "topic",
        "is_active",
    )
    list_filter = ("question_type", "difficulty", "domain", "nursing_system", "is_active")
    # Lets an editor free-text search question stems from the admin's
    # search box — the only field indexed for search here, since stem is
    # the field most likely to be searched by content ("find the question
    # about heart failure").
    search_fields = ("stem",)
    # Embeds the AnswerChoiceInline defined above directly on this page —
    # only meaningful for MCQ/SATA/EMR questions (the types that actually
    # use AnswerChoice); for other question types the inline just shows
    # empty and unused, which is acceptable for Milestone 1's plain-admin
    # scope (custom per-type admin forms are Milestone 2 work).
    inlines = [AnswerChoiceInline]


@admin.register(AnswerChoice)
class AnswerChoiceAdmin(admin.ModelAdmin):
    # A standalone admin page for AnswerChoice also exists (separate from
    # the inline above) so choices can be browsed/searched/filtered across
    # ALL questions at once — e.g. to audit every choice marked correct.
    list_display = ("__str__", "question", "is_correct", "display_order")
    list_filter = ("is_correct",)
    search_fields = ("choice_text", "rationale")


@admin.register(MatrixRow)
class MatrixRowAdmin(admin.ModelAdmin):
    list_display = ("__str__", "question", "display_order")


@admin.register(MatrixColumn)
class MatrixColumnAdmin(admin.ModelAdmin):
    list_display = ("__str__", "question", "display_order")


@admin.register(MatrixCell)
class MatrixCellAdmin(admin.ModelAdmin):
    list_display = ("row", "column", "is_correct")


@admin.register(BowTieOption)
class BowTieOptionAdmin(admin.ModelAdmin):
    list_display = ("__str__", "question", "section", "is_correct")
    # Lets an editor isolate e.g. just the Condition options across every
    # bow-tie question, or just the options currently marked correct.
    list_filter = ("section", "is_correct")


@admin.register(ClozeBlank)
class ClozeBlankAdmin(admin.ModelAdmin):
    list_display = ("blank_key", "question", "display_order")


@admin.register(ClozeOption)
class ClozeOptionAdmin(admin.ModelAdmin):
    list_display = ("__str__", "blank", "is_correct")


@admin.register(DragDropCategory)
class DragDropCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "question", "display_order")


@admin.register(DragDropItem)
class DragDropItemAdmin(admin.ModelAdmin):
    # Shows both correct_category and correct_order columns regardless of
    # which drag-drop variant a given item uses — whichever one wasn't set
    # for that item just displays as empty/None, which is an acceptable
    # simple default for this plain admin (see DragDropItem's docstring in
    # models.py for why only one of the two is ever populated per row).
    list_display = ("__str__", "question", "correct_category", "correct_order")


@admin.register(HotSpotTarget)
class HotSpotTargetAdmin(admin.ModelAdmin):
    list_display = ("target_text", "question", "is_correct")
    list_filter = ("is_correct",)
