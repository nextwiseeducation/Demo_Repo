from django.db import transaction
from rest_framework import serializers

from apps.questions.authoring import (
    ALL_STRUCTURE_KEYS,
    STRUCTURE_KEYS,
    StructureError,
    validate_structure,
    write_structure,
)
from apps.questions.models import (
    AnswerChoice,
    BowTieOption,
    BowTieSection,
    ClozeBlank,
    ClozeOption,
    DragDropCategory,
    DragDropItem,
    HotSpotTarget,
    MatrixCell,
    MatrixColumn,
    MatrixRow,
    Question,
    QuestionType,
)
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

STEM_PREVIEW_CHARS = 80


class AdminQuestionListSerializer(serializers.ModelSerializer):
    """
    The Content Team question table's row shape — deliberately thin (no
    answer choices, no NGN child rows) since a 20-row page of full question
    structures would be needlessly heavy for a list view whose only job is
    browse/filter/select. The full structure is what
    AdminQuestionDetailSerializer (GET .../:id/) returns for one question
    at a time, when a row is actually opened for editing.
    """

    nursing_system = serializers.CharField(source="nursing_system.name", read_only=True)
    stem_preview = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            "id",
            "stem_preview",
            "question_type",
            "nursing_system",
            "difficulty",
            "is_active",
            "created_at",
        ]

    def get_stem_preview(self, obj: Question) -> str:
        return obj.stem[:STEM_PREVIEW_CHARS]


# --- Admin detail serializers -------------------------------------------
#
# These mirror the shape of the Public* serializers in
# apps.questions.serializers used by QuestionListSerializer, but — unlike
# those — DO expose is_correct/rationale on every child model. The Public*
# ones deliberately strip the answer key before a student has submitted;
# an editor managing the question bank needs to see and change the answer
# key itself, so a separate admin-only set of read serializers is
# necessary rather than reusing the public ones.
#
# Field/key naming here intentionally matches what
# apps.questions.management.commands.import_ngn_item_bank and the future
# writable QuestionAdminSerializer (Phase 5 of the implementation plan)
# will accept, so GET -> edit -> PUT round-trips through (almost) the same
# shape once the write path lands.


class AdminAnswerChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerChoice
        fields = ["id", "choice_text", "is_correct", "display_order", "rationale"]


class AdminMatrixCellSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatrixCell
        # column_id is MatrixCell's own FK attribute name (Django appends
        # _id to any ForeignKey automatically) — no explicit field
        # declaration needed for ModelSerializer to pick it up.
        fields = ["column_id", "is_correct", "rationale"]


class AdminMatrixColumnSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatrixColumn
        fields = ["id", "text", "display_order"]


class AdminMatrixRowSerializer(serializers.ModelSerializer):
    cells = AdminMatrixCellSerializer(many=True, read_only=True)

    class Meta:
        model = MatrixRow
        fields = ["id", "text", "display_order", "cells"]


class AdminBowTieOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BowTieOption
        fields = ["id", "section", "option_text", "is_correct", "display_order", "rationale"]


class AdminClozeOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClozeOption
        fields = ["id", "option_text", "is_correct", "rationale"]


class AdminClozeBlankSerializer(serializers.ModelSerializer):
    options = AdminClozeOptionSerializer(many=True, read_only=True)

    class Meta:
        model = ClozeBlank
        fields = ["id", "blank_key", "display_order", "options"]


class AdminDragDropCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DragDropCategory
        fields = ["id", "name", "display_order"]


class AdminDragDropItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = DragDropItem
        fields = ["id", "text", "display_order", "correct_category", "correct_order", "rationale"]


class AdminHotSpotTargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotSpotTarget
        fields = ["id", "target_text", "is_correct", "display_order", "rationale"]


class AdminCaseStudySerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseStudy
        fields = ["id", "external_id", "title", "shared_scenario"]


class AdminQuestionDetailSerializer(serializers.ModelSerializer):
    """
    GET /api/admin/questions/:id/ — the full question, answer key included,
    every NGN child collection the question's type could use (empty for
    the families that don't apply, same "serialize all of them, most are
    empty" approach QuestionListSerializer already takes).

    Read-only for now (Phase 4 of the implementation plan: delete/bulk-
    delete). Phase 5 turns this into a writable ModelSerializer backing
    POST/PUT — see apps.questions.authoring for where the per-type
    structural validation will live once that lands.
    """

    nursing_system_id = serializers.IntegerField(source="nursing_system.id", read_only=True)
    nursing_system = serializers.CharField(source="nursing_system.name", read_only=True)
    topic_id = serializers.IntegerField(source="topic.id", read_only=True)
    topic = serializers.CharField(source="topic.name", read_only=True)
    subtopic_id = serializers.IntegerField(
        source="subtopic.id", read_only=True, allow_null=True, default=None
    )
    domain_id = serializers.IntegerField(source="domain.id", read_only=True, allow_null=True, default=None)
    domain = serializers.CharField(source="domain.name", read_only=True, allow_null=True, default=None)
    nclex_client_needs_category_id = serializers.IntegerField(
        source="nclex_client_needs_category.id", read_only=True
    )
    nclex_client_needs_subcategory_id = serializers.IntegerField(
        source="nclex_client_needs_subcategory.id", read_only=True
    )
    tag_ids = serializers.PrimaryKeyRelatedField(source="tags", many=True, read_only=True)

    answer_choices = AdminAnswerChoiceSerializer(many=True, read_only=True)
    matrix_columns = AdminMatrixColumnSerializer(many=True, read_only=True)
    matrix_rows = AdminMatrixRowSerializer(many=True, read_only=True)
    bowtie_options = AdminBowTieOptionSerializer(many=True, read_only=True)
    cloze_blanks = AdminClozeBlankSerializer(many=True, read_only=True)
    dragdrop_categories = AdminDragDropCategorySerializer(many=True, read_only=True)
    dragdrop_items = AdminDragDropItemSerializer(many=True, read_only=True)
    hotspot_targets = AdminHotSpotTargetSerializer(many=True, read_only=True)
    case_study = AdminCaseStudySerializer(read_only=True)
    image = serializers.FileField(read_only=True, use_url=True, allow_null=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "external_id",
            "question_type",
            "ngn_type",
            "stem",
            "clinical_scenario",
            "image",
            "case_study",
            "case_study_sequence",
            "difficulty",
            "domain",
            "domain_id",
            "nursing_system",
            "nursing_system_id",
            "topic",
            "topic_id",
            "subtopic_id",
            "nclex_client_needs_category_id",
            "nclex_client_needs_subcategory_id",
            "clinical_judgment_skill",
            "clinical_judgment_skill_secondary",
            "cognitive_level",
            "tag_ids",
            "rationale_correct",
            "rationale_incorrect",
            "reference",
            "key_takeaway",
            "is_active",
            "created_at",
            "updated_at",
            "answer_choices",
            "matrix_columns",
            "matrix_rows",
            "bowtie_options",
            "cloze_blanks",
            "dragdrop_categories",
            "dragdrop_items",
            "hotspot_targets",
        ]


# --- Writable admin serializer (Phase 5) ---------------------------------
#
# Input shapes for the 8 structure-family collections. Plain
# serializers.Serializer (not ModelSerializer): every write here goes
# through apps.questions.authoring.write_structure, which does its own
# manual create/update/delete, so there is no benefit to DRF's
# ModelSerializer nested-writable machinery — these classes exist purely to
# validate field TYPES and SHAPES before authoring.py's structural rules
# (uniqueness, cross-references, counts) run in QuestionAdminSerializer.validate().
#
# `key` fields (matrix columns/rows, dragdrop categories) are a
# request-scoped, client-supplied identifier used only to let a new
# row (no `id` yet) be referenced by another new row in the SAME request —
# e.g. a new MatrixCell pointing at a new MatrixColumn. They are never
# persisted.


class AdminAnswerChoiceInputSerializer(serializers.Serializer):
    id = serializers.CharField(required=False, allow_null=True)
    choice_text = serializers.CharField()
    is_correct = serializers.BooleanField()
    display_order = serializers.IntegerField()
    rationale = serializers.CharField(required=False, allow_blank=True, default="")


class AdminMatrixColumnInputSerializer(serializers.Serializer):
    key = serializers.CharField()
    text = serializers.CharField(max_length=255)
    display_order = serializers.IntegerField()


class AdminMatrixCellInputSerializer(serializers.Serializer):
    column_key = serializers.CharField()
    is_correct = serializers.BooleanField()
    rationale = serializers.CharField(required=False, allow_blank=True, default="")


class AdminMatrixRowInputSerializer(serializers.Serializer):
    key = serializers.CharField()
    text = serializers.CharField()
    display_order = serializers.IntegerField()
    cells = AdminMatrixCellInputSerializer(many=True)


class AdminBowTieOptionInputSerializer(serializers.Serializer):
    section = serializers.ChoiceField(choices=BowTieSection.choices)
    option_text = serializers.CharField()
    is_correct = serializers.BooleanField()
    display_order = serializers.IntegerField()
    rationale = serializers.CharField(required=False, allow_blank=True, default="")


class AdminClozeOptionInputSerializer(serializers.Serializer):
    option_text = serializers.CharField(max_length=255)
    is_correct = serializers.BooleanField()
    rationale = serializers.CharField(required=False, allow_blank=True, default="")


class AdminClozeBlankInputSerializer(serializers.Serializer):
    blank_key = serializers.CharField(max_length=50)
    display_order = serializers.IntegerField()
    options = AdminClozeOptionInputSerializer(many=True)


class AdminDragDropCategoryInputSerializer(serializers.Serializer):
    key = serializers.CharField()
    name = serializers.CharField(max_length=150)
    display_order = serializers.IntegerField()


class AdminDragDropItemInputSerializer(serializers.Serializer):
    text = serializers.CharField()
    display_order = serializers.IntegerField()
    correct_category_key = serializers.CharField(required=False, allow_null=True, default=None)
    correct_order = serializers.IntegerField(required=False, allow_null=True, default=None)
    rationale = serializers.CharField(required=False, allow_blank=True, default="")


class AdminHotSpotTargetInputSerializer(serializers.Serializer):
    target_text = serializers.CharField(max_length=255)
    is_correct = serializers.BooleanField()
    display_order = serializers.IntegerField()
    rationale = serializers.CharField(required=False, allow_blank=True, default="")


class AdminCaseStudyInputSerializer(serializers.Serializer):
    """
    Nested writable "attach or create a case study" input. `id` present
    means attach to (and optionally update) an existing CaseStudy;
    otherwise get_or_create on external_id, or a bare create if
    external_id is also absent.
    """

    id = serializers.IntegerField(required=False, allow_null=True)
    external_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    title = serializers.CharField(required=False, allow_blank=True, default="")
    shared_scenario = serializers.CharField(required=False, allow_blank=True, default="")


class QuestionAdminSerializer(serializers.ModelSerializer):
    """
    The single writable representation of a Question and every child-row
    family the 9 question types use — backs POST/PUT
    /api/admin/questions/[:id/].

    Key names deliberately mirror AdminQuestionDetailSerializer's output
    (which in turn mirrors apps.questions.serializers.QuestionListSerializer)
    so the admin edit form's GET -> mutate -> PUT round-trip is a near-
    identity mapping. Only the child collections belonging to the
    question's EFFECTIVE type (question_type, or ngn_type when
    question_type is NGN_CASE — see apps.questions.services.
    effective_question_type) may be present; validate() rejects the rest.

    On update, a structure-family key that is ABSENT from the request body
    is left completely untouched — so a metadata-only edit (flipping
    is_active, fixing a typo) never rebuilds child rows and never orphans
    the row ids historical StudentResponseLog.selected_payload entries
    point at. Supplying ANY key for a family requires supplying ALL of that
    family's keys (e.g. matrix_columns and matrix_rows always travel
    together) — a partial family is rejected rather than silently
    completed with an empty list, since "no columns" is indistinguishable
    from "columns not provided" once both are absent.

    All structural rules (uniqueness, cross-references, per-type counts)
    live in apps.questions.authoring, not here, because the xlsx importer
    applies the identical rules and the two must not drift.
    """

    domain_id = serializers.PrimaryKeyRelatedField(
        source="domain", queryset=Domain.objects.all(), required=False, allow_null=True
    )
    nursing_system_id = serializers.PrimaryKeyRelatedField(
        source="nursing_system", queryset=NursingSystem.objects.all()
    )
    topic_id = serializers.PrimaryKeyRelatedField(source="topic", queryset=Topic.objects.all())
    subtopic_id = serializers.PrimaryKeyRelatedField(
        source="subtopic", queryset=Subtopic.objects.all(), required=False, allow_null=True
    )
    nclex_client_needs_category_id = serializers.PrimaryKeyRelatedField(
        source="nclex_client_needs_category", queryset=ClientNeedsCategory.objects.all()
    )
    nclex_client_needs_subcategory_id = serializers.PrimaryKeyRelatedField(
        source="nclex_client_needs_subcategory", queryset=ClientNeedsSubcategory.objects.all()
    )
    tag_ids = serializers.PrimaryKeyRelatedField(
        source="tags", queryset=Tag.objects.all(), many=True, required=False
    )
    case_study = AdminCaseStudyInputSerializer(required=False, allow_null=True)
    image = serializers.FileField(read_only=True, use_url=True, allow_null=True)

    answer_choices = AdminAnswerChoiceInputSerializer(many=True, required=False)
    matrix_columns = AdminMatrixColumnInputSerializer(many=True, required=False)
    matrix_rows = AdminMatrixRowInputSerializer(many=True, required=False)
    bowtie_options = AdminBowTieOptionInputSerializer(many=True, required=False)
    cloze_blanks = AdminClozeBlankInputSerializer(many=True, required=False)
    dragdrop_categories = AdminDragDropCategoryInputSerializer(many=True, required=False)
    dragdrop_items = AdminDragDropItemInputSerializer(many=True, required=False)
    hotspot_targets = AdminHotSpotTargetInputSerializer(many=True, required=False)

    class Meta:
        model = Question
        fields = [
            "id",
            "external_id",
            "question_type",
            "ngn_type",
            "stem",
            "clinical_scenario",
            "image",
            "case_study",
            "case_study_sequence",
            "difficulty",
            "domain_id",
            "nursing_system_id",
            "topic_id",
            "subtopic_id",
            "nclex_client_needs_category_id",
            "nclex_client_needs_subcategory_id",
            "clinical_judgment_skill",
            "clinical_judgment_skill_secondary",
            "cognitive_level",
            "tag_ids",
            "rationale_correct",
            "rationale_incorrect",
            "reference",
            "key_takeaway",
            "is_active",
            "created_at",
            "updated_at",
            "answer_choices",
            "matrix_columns",
            "matrix_rows",
            "bowtie_options",
            "cloze_blanks",
            "dragdrop_categories",
            "dragdrop_items",
            "hotspot_targets",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        instance = self.instance

        if (
            instance is not None
            and "question_type" in attrs
            and attrs["question_type"] != instance.question_type
        ):
            # Retyping a question with existing StudentResponseLog rows
            # would strand every one of them against a structure that no
            # longer exists — retype is delete + recreate, deliberately.
            raise serializers.ValidationError(
                {
                    "question_type": "Cannot change the type of an existing question. Delete and recreate it instead."
                }
            )

        question_type = attrs.get("question_type", getattr(instance, "question_type", None))
        if question_type is None:
            raise serializers.ValidationError({"question_type": "This field is required."})

        ngn_type = attrs.get("ngn_type", getattr(instance, "ngn_type", None))
        if question_type == QuestionType.NGN_CASE:
            if not ngn_type:
                raise serializers.ValidationError({"ngn_type": "Required when question_type is NGN_CASE."})
            if ngn_type == QuestionType.NGN_CASE:
                raise serializers.ValidationError({"ngn_type": "ngn_type cannot itself be NGN_CASE."})
            has_existing_case_study = instance is not None and instance.case_study_id is not None
            if "case_study" not in attrs and not has_existing_case_study:
                raise serializers.ValidationError({"case_study": "Required when question_type is NGN_CASE."})
            case_study_sequence = attrs.get(
                "case_study_sequence", getattr(instance, "case_study_sequence", None)
            )
            if case_study_sequence is None:
                raise serializers.ValidationError(
                    {"case_study_sequence": "Required when question_type is NGN_CASE."}
                )
            effective_type = ngn_type
        else:
            effective_type = question_type

        allowed_keys = set(STRUCTURE_KEYS.get(effective_type, []))
        present_keys = {key for key in ALL_STRUCTURE_KEYS if key in attrs}
        disallowed = present_keys - allowed_keys
        if disallowed:
            raise serializers.ValidationError(
                {key: f"Not a valid field for a {effective_type} question." for key in sorted(disallowed)}
            )

        present_for_family = present_keys & allowed_keys
        if instance is None:
            missing = allowed_keys - present_for_family
            if missing:
                raise serializers.ValidationError({key: "This field is required." for key in sorted(missing)})
        elif present_for_family and present_for_family != allowed_keys:
            missing = allowed_keys - present_for_family
            raise serializers.ValidationError(
                {
                    key: f"Must be supplied together with {sorted(present_for_family)}."
                    for key in sorted(missing)
                }
            )

        structure = {key: attrs[key] for key in allowed_keys if key in attrs}
        if structure:
            stem = attrs.get("stem", getattr(instance, "stem", ""))
            clinical_scenario = attrs.get("clinical_scenario", getattr(instance, "clinical_scenario", None))
            case_scenario = self._resolve_case_scenario(attrs, instance)
            try:
                validate_structure(
                    effective_type=effective_type,
                    stem=stem,
                    clinical_scenario=clinical_scenario,
                    case_scenario=case_scenario,
                    structure=structure,
                )
            except StructureError as exc:
                raise serializers.ValidationError({"non_field_errors": [str(exc)]}) from exc

        return attrs

    def _resolve_case_scenario(self, attrs, instance) -> str:
        case_study_data = attrs.get("case_study")
        if case_study_data:
            if case_study_data.get("id"):
                try:
                    return CaseStudy.objects.get(pk=case_study_data["id"]).shared_scenario
                except CaseStudy.DoesNotExist:
                    return ""
            return case_study_data.get("shared_scenario", "")
        if instance is not None and instance.case_study_id:
            return instance.case_study.shared_scenario
        return ""

    def _resolve_case_study(self, data: dict) -> CaseStudy:
        if data.get("id"):
            case_study = CaseStudy.objects.get(pk=data["id"])
            if data.get("title"):
                case_study.title = data["title"]
            if data.get("shared_scenario"):
                case_study.shared_scenario = data["shared_scenario"]
            case_study.save()
            return case_study
        external_id = data.get("external_id") or None
        if external_id:
            case_study, _ = CaseStudy.objects.get_or_create(
                external_id=external_id,
                defaults={"title": data.get("title", ""), "shared_scenario": data.get("shared_scenario", "")},
            )
            return case_study
        return CaseStudy.objects.create(
            title=data.get("title", ""), shared_scenario=data.get("shared_scenario", "")
        )

    @staticmethod
    def _pop_structure(validated_data: dict) -> dict:
        return {key: validated_data.pop(key) for key in list(validated_data) if key in ALL_STRUCTURE_KEYS}

    @transaction.atomic
    def create(self, validated_data):
        structure = self._pop_structure(validated_data)
        case_study_data = validated_data.pop("case_study", None)
        tags = validated_data.pop("tags", None)
        if case_study_data is not None:
            validated_data["case_study"] = self._resolve_case_study(case_study_data)
        question = Question.objects.create(**validated_data)
        if tags is not None:
            question.tags.set(tags)
        write_structure(question, structure)
        return question

    @transaction.atomic
    def update(self, instance, validated_data):
        structure = self._pop_structure(validated_data)
        case_study_data = validated_data.pop("case_study", None)
        tags = validated_data.pop("tags", None)
        if case_study_data is not None:
            validated_data["case_study"] = self._resolve_case_study(case_study_data)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tags is not None:
            instance.tags.set(tags)
        write_structure(instance, structure)
        return instance
