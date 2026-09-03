"""
The per-question-type structural rules, in one place, so the two writers of
question content — the xlsx importer (management/commands/import_ngn_item_bank.py)
and the admin API's writable serializer
(apps.admin_api.serializers.questions.QuestionAdminSerializer) — cannot
drift apart. A rule added here binds both.

Every function here works on NORMALISED structures: plain dicts/lists using
the model field names below, not spreadsheet rows and not raw DRF
validated_data. Callers adapt their own input into this shape first.

STRUCTURE_KEYS below is the single map of "which question type uses which
structure dict keys" — both the importer's dispatch and the serializer's
validate() should read this rather than hardcoding the mapping twice.
"""

import re

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
    QuestionType,
)

# question_type/ngn_type -> the structure dict keys that type reads/writes.
# NGN_CASE itself is never a key here — a case item's EFFECTIVE type is its
# ngn_type (see apps.questions.services.effective_question_type), so callers
# must resolve that before consulting this map.
STRUCTURE_KEYS: dict[str, list[str]] = {
    QuestionType.MCQ: ["answer_choices"],
    QuestionType.SATA: ["answer_choices"],
    QuestionType.EMR: ["answer_choices"],
    QuestionType.MATRIX: ["matrix_columns", "matrix_rows"],
    QuestionType.BOWTIE: ["bowtie_options"],
    QuestionType.CLOZE: ["cloze_blanks"],
    QuestionType.DRAG_DROP: ["dragdrop_categories", "dragdrop_items"],
    QuestionType.HOTSPOT: ["hotspot_targets"],
}

ALL_STRUCTURE_KEYS: set[str] = {key for keys in STRUCTURE_KEYS.values() for key in keys}

CLOZE_TOKEN_PATTERN = re.compile(r"\[([^\[\]]+)\]")


class StructureError(Exception):
    """One structural rule failed. Message is human-readable and safe to surface to an editor."""


def validate_structure(
    *,
    effective_type: str,
    stem: str,
    clinical_scenario: str | None,
    case_scenario: str | None,
    structure: dict,
) -> None:
    """
    Dispatches to the per-type validator for `effective_type` (a plain
    QuestionType value — NGN_CASE must already have been resolved to its
    ngn_type by the caller). `structure` must contain exactly the keys
    STRUCTURE_KEYS[effective_type] names; the caller is responsible for
    rejecting any other keys before calling this.
    """
    if effective_type in (QuestionType.MCQ, QuestionType.SATA, QuestionType.EMR):
        _validate_answer_choices(structure["answer_choices"], effective_type)
    elif effective_type == QuestionType.MATRIX:
        _validate_matrix(structure["matrix_columns"], structure["matrix_rows"])
    elif effective_type == QuestionType.BOWTIE:
        _validate_bowtie(structure["bowtie_options"])
    elif effective_type == QuestionType.CLOZE:
        _validate_cloze(structure["cloze_blanks"], stem)
    elif effective_type == QuestionType.DRAG_DROP:
        _validate_dragdrop(structure["dragdrop_categories"], structure["dragdrop_items"])
    elif effective_type == QuestionType.HOTSPOT:
        _validate_hotspot(structure["hotspot_targets"], stem, clinical_scenario, case_scenario)
    else:
        raise StructureError(f"Unknown effective question type {effective_type!r}")


def write_structure(question, structure: dict) -> None:
    """
    Replaces `question`'s child rows for whichever families are present as
    keys in `structure`. A family whose keys are absent from `structure` is
    left completely untouched — this is what makes a metadata-only edit
    (e.g. flipping is_active) cheap and non-destructive, and it's the
    caller's job to decide which keys belong in `structure` in the first
    place. Caller owns the surrounding transaction.
    """
    if "answer_choices" in structure:
        _write_answer_choices(question, structure["answer_choices"])
    if "matrix_columns" in structure or "matrix_rows" in structure:
        _write_matrix(question, structure.get("matrix_columns", []), structure.get("matrix_rows", []))
    if "bowtie_options" in structure:
        _write_bowtie(question, structure["bowtie_options"])
    if "cloze_blanks" in structure:
        _write_cloze(question, structure["cloze_blanks"])
    if "dragdrop_categories" in structure or "dragdrop_items" in structure:
        _write_dragdrop(
            question, structure.get("dragdrop_categories", []), structure.get("dragdrop_items", [])
        )
    if "hotspot_targets" in structure:
        _write_hotspot(question, structure["hotspot_targets"])


# --- MCQ / SATA / EMR -----------------------------------------------------


def _validate_answer_choices(choices: list[dict], effective_type: str) -> None:
    if not choices:
        raise StructureError("At least one answer choice is required.")

    correct_count = sum(1 for c in choices if c["is_correct"])
    if correct_count == 0:
        raise StructureError("At least one answer choice must be marked correct.")
    if effective_type == QuestionType.MCQ and correct_count != 1:
        raise StructureError(
            f"MCQ questions must have exactly one correct answer choice, found {correct_count}."
        )
    if effective_type in (QuestionType.SATA, QuestionType.EMR) and len(choices) < 2:
        raise StructureError(f"{effective_type} questions require at least 2 answer choices.")

    orders = [c["display_order"] for c in choices]
    if len(set(orders)) != len(orders):
        raise StructureError("Answer choice display_order values must be unique.")


def _write_answer_choices(question, choices: list[dict]) -> None:
    """
    Diff, not replace. AnswerChoice is the one child model with a UUID PK
    that StudentResponseLog references (selected_choice SET_NULL,
    selected_choices M2M) — deleting and recreating every choice on an
    ordinary text/rationale edit would silently null out which distractor
    every past student picked, which is exactly the data StudentResponseLog
    exists to preserve.
    """
    existing = {str(c.id): c for c in question.answer_choices.all()}
    seen_ids = set()
    for item in choices:
        item_id = item.get("id")
        if item_id and item_id in existing:
            choice = existing[item_id]
            choice.choice_text = item["choice_text"]
            choice.is_correct = item["is_correct"]
            choice.display_order = item["display_order"]
            choice.rationale = item.get("rationale", "")
            choice.save(update_fields=["choice_text", "is_correct", "display_order", "rationale"])
            seen_ids.add(item_id)
        else:
            new_choice = AnswerChoice.objects.create(
                question=question,
                choice_text=item["choice_text"],
                is_correct=item["is_correct"],
                display_order=item["display_order"],
                rationale=item.get("rationale", ""),
            )
            # Without this, the cleanup delete() below (anything NOT in
            # seen_ids) would immediately delete every choice just created
            # in this same call, since seen_ids would otherwise only ever
            # contain ids of choices that were UPDATED, not created.
            seen_ids.add(str(new_choice.id))
    question.answer_choices.exclude(id__in=seen_ids).delete()


# --- MATRIX ----------------------------------------------------------------


def _validate_matrix(columns: list[dict], rows: list[dict]) -> None:
    if len(columns) < 2:
        raise StructureError("Matrix/Grid questions require at least 2 columns.")
    if not rows:
        raise StructureError("Matrix/Grid questions require at least 1 row.")

    column_keys = [c["key"] for c in columns]
    if len(set(column_keys)) != len(column_keys):
        raise StructureError("Matrix column keys must be unique.")
    row_keys = [r["key"] for r in rows]
    if len(set(row_keys)) != len(row_keys):
        raise StructureError("Matrix row keys must be unique.")

    column_key_set = set(column_keys)
    for row in rows:
        cell_column_keys = [cell["column_key"] for cell in row["cells"]]
        if len(set(cell_column_keys)) != len(cell_column_keys):
            raise StructureError(f"Row {row['text']!r} references the same column more than once.")
        unresolved = set(cell_column_keys) - column_key_set
        if unresolved:
            raise StructureError(
                f"Row {row['text']!r} references unknown column key(s) {sorted(unresolved)}."
            )
        if set(cell_column_keys) != column_key_set:
            raise StructureError(f"Row {row['text']!r} must supply exactly one cell per column.")

        correct_count = sum(1 for cell in row["cells"] if cell["is_correct"])
        if correct_count != 1:
            raise StructureError(
                f"Row {row['text']!r} must have exactly one correct column, found {correct_count}."
            )


def _write_matrix(question, columns: list[dict], rows: list[dict]) -> None:
    """
    Replace-all: MatrixRow/Column/Cell use plain int PKs and are referenced
    only from StudentResponseLog.selected_payload JSON (already
    best-effort), matching exactly what import_ngn_item_bank._sync_matrix
    does on --update — both writers behave identically.
    """
    question.matrix_rows.all().delete()  # cascades to cells
    question.matrix_columns.all().delete()

    column_objs = {
        col["key"]: MatrixColumn.objects.create(
            question=question, text=col["text"], display_order=col["display_order"]
        )
        for col in columns
    }
    for row in rows:
        row_obj = MatrixRow.objects.create(
            question=question, text=row["text"], display_order=row["display_order"]
        )
        MatrixCell.objects.bulk_create(
            [
                MatrixCell(
                    row=row_obj,
                    column=column_objs[cell["column_key"]],
                    is_correct=cell["is_correct"],
                    rationale=cell.get("rationale", ""),
                )
                for cell in row["cells"]
            ]
        )


# --- BOWTIE ------------------------------------------------------------


def _validate_bowtie(options: list[dict]) -> None:
    by_section: dict[str, list[dict]] = {section: [] for section, _ in BowTieSection.choices}
    for option in options:
        by_section.setdefault(option["section"], []).append(option)

    for section, _ in BowTieSection.choices:
        section_options = by_section.get(section, [])
        if not section_options:
            raise StructureError(f"Bow-Tie questions require at least one {section.title()} option.")
        if not any(o["is_correct"] for o in section_options):
            raise StructureError(f"Bow-Tie {section.title()} section requires at least one correct option.")
        orders = [o["display_order"] for o in section_options]
        if len(set(orders)) != len(orders):
            raise StructureError(f"Bow-Tie {section.title()} display_order values must be unique.")


def _write_bowtie(question, options: list[dict]) -> None:
    question.bowtie_options.all().delete()
    BowTieOption.objects.bulk_create(
        [
            BowTieOption(
                question=question,
                section=o["section"],
                option_text=o["option_text"],
                is_correct=o["is_correct"],
                display_order=o["display_order"],
                rationale=o.get("rationale", ""),
            )
            for o in options
        ]
    )


# --- CLOZE -------------------------------------------------------------


def _normalize_blank_key(key: str) -> str:
    return key.strip().lower()


def _validate_cloze(blanks: list[dict], stem: str) -> None:
    if not blanks:
        raise StructureError("Cloze questions require at least one blank.")

    normalized_keys = [_normalize_blank_key(b["blank_key"]) for b in blanks]
    if len(set(normalized_keys)) != len(normalized_keys):
        raise StructureError("Cloze blank_key values must be unique (case/whitespace-insensitive).")

    stem_tokens = {_normalize_blank_key(t) for t in CLOZE_TOKEN_PATTERN.findall(stem)}
    blank_keys = set(normalized_keys)

    missing_in_stem = blank_keys - stem_tokens
    if missing_in_stem:
        raise StructureError(
            f"Blank key(s) {sorted(missing_in_stem)} have no matching [placeholder] in the stem."
        )
    missing_blank = stem_tokens - blank_keys
    if missing_blank:
        raise StructureError(
            f"The stem has [placeholder] token(s) {sorted(missing_blank)} with no matching blank defined."
        )

    for blank in blanks:
        options = blank["options"]
        if len(options) < 2:
            raise StructureError(f"Blank {blank['blank_key']!r} requires at least 2 options.")
        correct_count = sum(1 for o in options if o["is_correct"])
        if correct_count != 1:
            raise StructureError(
                f"Blank {blank['blank_key']!r} must have exactly one correct option, found {correct_count}."
            )


def _write_cloze(question, blanks: list[dict]) -> None:
    question.cloze_blanks.all().delete()  # cascades to options
    for blank in blanks:
        blank_obj = ClozeBlank.objects.create(
            question=question, blank_key=blank["blank_key"], display_order=blank["display_order"]
        )
        ClozeOption.objects.bulk_create(
            [
                ClozeOption(
                    blank=blank_obj,
                    option_text=o["option_text"],
                    is_correct=o["is_correct"],
                    rationale=o.get("rationale", ""),
                )
                for o in blank["options"]
            ]
        )


# --- DRAG_DROP -----------------------------------------------------------


def _validate_dragdrop(categories: list[dict], items: list[dict]) -> None:
    if not items:
        raise StructureError("Drag and Drop questions require at least one item.")

    category_keys = [c["key"] for c in categories]
    if len(set(category_keys)) != len(category_keys):
        raise StructureError("Drag and Drop category keys must be unique.")

    for item in items:
        has_category = item.get("correct_category_key") is not None
        has_order = item.get("correct_order") is not None
        if has_category and has_order:
            raise StructureError(
                f"Item {item['text']!r} cannot have both a correct_category_key and a correct_order."
            )

    # Variant is DERIVED from whether categories were supplied at all — the
    # exact rule DragDropQuestion.tsx and grade_dragdrop both use — never a
    # separately declared field, which could disagree with the data itself.
    if categories:
        category_key_set = set(category_keys)
        for item in items:
            key = item.get("correct_category_key")
            if key is None:
                raise StructureError(f"Item {item['text']!r} requires a correct_category_key.")
            if key not in category_key_set:
                raise StructureError(f"Item {item['text']!r} references unknown category key {key!r}.")
    else:
        orders = [item.get("correct_order") for item in items]
        if any(o is None for o in orders):
            raise StructureError("Every item requires a correct_order when no categories are defined.")
        if sorted(orders) != list(range(1, len(items) + 1)):
            raise StructureError(
                f"correct_order values must be exactly 1..{len(items)} with no gaps or duplicates, "
                f"got {sorted(orders)}."
            )


def _write_dragdrop(question, categories: list[dict], items: list[dict]) -> None:
    question.dragdrop_items.all().delete()
    question.dragdrop_categories.all().delete()

    category_objs = {
        cat["key"]: DragDropCategory.objects.create(
            question=question, name=cat["name"], display_order=cat["display_order"]
        )
        for cat in categories
    }
    DragDropItem.objects.bulk_create(
        [
            DragDropItem(
                question=question,
                text=item["text"],
                display_order=item["display_order"],
                correct_category=category_objs.get(item["correct_category_key"])
                if item.get("correct_category_key")
                else None,
                correct_order=item.get("correct_order"),
                rationale=item.get("rationale", ""),
            )
            for item in items
        ]
    )


# --- HOTSPOT -------------------------------------------------------------

HOTSPOT_TARGET_TEXT_MAX_LENGTH = 255


def _validate_hotspot(
    targets: list[dict], stem: str, clinical_scenario: str | None, case_scenario: str | None
) -> None:
    if not targets:
        raise StructureError("Hot Spot questions require at least one target.")

    haystack = f"{stem}\n{clinical_scenario or ''}\n{case_scenario or ''}"
    for target in targets:
        text = target["target_text"]
        if len(text) > HOTSPOT_TARGET_TEXT_MAX_LENGTH:
            raise StructureError(
                f"Hot Spot target text is {len(text)} chars, over the {HOTSPOT_TARGET_TEXT_MAX_LENGTH} limit: {text!r}"
            )
        if text not in haystack:
            raise StructureError(
                f"Hot Spot target {text!r} does not appear verbatim in the stem/scenario — the "
                "highlighted phrase and the passage/table text must match exactly, word for word."
            )

    if not any(t["is_correct"] for t in targets):
        raise StructureError("Hot Spot questions require at least one correct target.")


def _write_hotspot(question, targets: list[dict]) -> None:
    question.hotspot_targets.all().delete()
    HotSpotTarget.objects.bulk_create(
        [
            HotSpotTarget(
                question=question,
                target_text=t["target_text"],
                is_correct=t["is_correct"],
                display_order=t["display_order"],
                rationale=t.get("rationale", ""),
            )
            for t in targets
        ]
    )
