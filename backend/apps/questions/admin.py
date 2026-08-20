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
    model = AnswerChoice
    extra = 0


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("__str__", "question_type", "difficulty", "nursing_system", "topic", "is_active")
    list_filter = ("question_type", "difficulty", "nursing_system", "is_active")
    search_fields = ("stem",)
    inlines = [AnswerChoiceInline]


@admin.register(AnswerChoice)
class AnswerChoiceAdmin(admin.ModelAdmin):
    list_display = ("__str__", "question", "is_correct", "display_order")
    list_filter = ("is_correct",)


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
    list_display = ("__str__", "question", "correct_category", "correct_order")


@admin.register(HotSpotTarget)
class HotSpotTargetAdmin(admin.ModelAdmin):
    list_display = ("target_text", "question", "is_correct")
    list_filter = ("is_correct",)
