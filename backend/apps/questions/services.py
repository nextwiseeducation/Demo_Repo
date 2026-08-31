"""
Grading rules for choice-based questions.

Extracted out of QuestionSubmitView deliberately. Grading is about to have
three separate callers, and they must not each carry their own copy of the
rule:

  - the stateless preview endpoint (QuestionSubmitView, today);
  - Milestone 3's quiz engine, which grades an answer AND writes a
    StudentResponseLog row against a QuizSession;
  - Phase 2's analytics, which re-derives correctness when it evaluates
    clinical-judgment performance.

It also has to change: SATA is currently all-or-nothing, and the real NCLEX
awards partial credit. When that lands it must land in exactly one place.

Kept as module-level functions rather than methods on Question because
grading takes a submission as well as a question — a Question.grade() would
read as if correctness were a property of the question alone, and this way
the rules can be unit-tested against plain data with no ORM instance at all.
"""

from dataclasses import dataclass
from uuid import UUID

from .models import AnswerChoice, MatrixCell, Question, QuestionType


class QuestionNotGradeable(Exception):
    """
    Raised when a question cannot be graded because its own content is
    broken — specifically, when no answer choice is marked correct.

    This is a content-authoring bug, not a client mistake, so it is
    surfaced as an exception for the caller to translate rather than being
    silently absorbed. It matters because the obvious set-comparison
    implementation gets this case actively wrong: with no correct choices
    the expected set is empty, so an empty submission compares EQUAL to it
    and the student is told they were right about a question that has no
    right answer.
    """


@dataclass(frozen=True)
class GradedAnswer:
    """
    The outcome of grading one submission.

    frozen=True because a grading result is a fact about an submission that
    already happened — nothing downstream should be able to edit a score
    after the fact.
    """

    is_correct: bool
    # The ids the student actually selected, after invalid ones were
    # discarded. Returned rather than recomputed by the caller so that
    # Milestone 3 can persist exactly what was graded.
    selected_ids: frozenset[UUID]
    correct_ids: frozenset[UUID]


def grade_submission(question: Question, selected_choice_ids) -> GradedAnswer:
    """
    Grades `selected_choice_ids` against `question`'s answer key.

    The current rule is exact set match: the selection is correct only if it
    is precisely the set of choices marked is_correct. That covers MCQ
    (where the set happens to have one member) and SATA (where it may have
    several) with one rule, which is why AnswerChoice can back both types
    without the schema knowing which is which.

    Ids that are not choices of this question are discarded rather than
    rejected. They can only come from a malformed or tampered-with request,
    and treating them as "not selected" grades the submission on its
    meaningful content instead of failing the whole request. The serializer
    layer is what rejects genuinely malformed input shapes.
    """
    choices = list(question.answer_choices.all())
    valid_ids = {choice.id for choice in choices}
    correct_ids = frozenset(choice.id for choice in choices if choice.is_correct)

    if not correct_ids:
        raise QuestionNotGradeable(
            f"Question {question.pk} has no answer choice marked correct and cannot be graded."
        )

    # Intersecting with valid_ids is what performs the "discard unknown ids"
    # rule described above.
    selected_ids = frozenset(_coerce_uuids(selected_choice_ids) & valid_ids)

    return GradedAnswer(
        is_correct=selected_ids == correct_ids,
        selected_ids=selected_ids,
        correct_ids=correct_ids,
    )


def _coerce_uuids(values) -> set[UUID]:
    """
    Normalises an iterable of ids to a set of UUIDs, dropping anything that
    isn't one.

    Callers reach this function through a serializer that has already
    validated the payload shape, so this is a second line of defence rather
    than the primary one — it exists so that a future caller (a management
    command, a Phase 2 batch job) that skips the serializer still cannot
    make grading raise on unexpected input.
    """
    coerced: set[UUID] = set()
    for value in values:
        if isinstance(value, UUID):
            coerced.add(value)
            continue
        try:
            coerced.add(UUID(str(value)))
        except (AttributeError, TypeError, ValueError):
            # Not an id at all — same treatment as an id belonging to some
            # other question: it simply doesn't count as a selection.
            continue
    return coerced


def build_answer_key(question: Question) -> list[dict]:
    """
    The per-choice answer key revealed to a student after they submit.

    Separate from grade_submission because these are two different
    decisions — "was this answer right" and "what may this student now be
    shown" — and the second one is the sensitive half. Keeping it its own
    named function makes the disclosure point greppable, so it stays
    obvious where the answer key leaves the server.
    """
    return [
        {"id": str(choice.id), "is_correct": choice.is_correct, "rationale": choice.rationale}
        for choice in question.answer_choices.all()
    ]


def choices_for(question: Question) -> list[AnswerChoice]:
    """Convenience accessor kept next to the rules that consume it."""
    return list(question.answer_choices.all())


def effective_question_type(question: Question) -> str:
    """
    The type that decides how a question is rendered and graded.

    For every question except NGN_CASE this is just question_type. An
    NGN_CASE item's own question_type is the wrapper flag "this is a case
    study item"; ngn_type says which real type (MCQ, MATRIX, BOWTIE, ...) it
    actually is, per Question.ngn_type's docstring. Falls back to
    question_type itself if ngn_type was left blank on a NGN_CASE row (a
    content bug, not something grading should crash on).
    """
    if question.question_type == QuestionType.NGN_CASE and question.ngn_type:
        return question.ngn_type
    return question.question_type


@dataclass(frozen=True)
class GradedResult:
    """
    Generic grading outcome for the NGN types below — unlike GradedAnswer
    (AnswerChoice-specific: a set of UUIDs), each of these submissions has
    its own shape, so `detail` carries whatever that type needs persisted
    (StudentResponseLog.selected_payload) rather than forcing every type
    into the same fields.
    """

    is_correct: bool
    detail: dict


def _coerce_ints(values) -> set[int]:
    """Same defensive role as _coerce_uuids, for the NGN stub models below, which use plain integer PKs (see MatrixRow/BowTieOption/etc.'s own 'no UUIDPKMixin' comments)."""
    coerced: set[int] = set()
    for value in values:
        try:
            coerced.add(int(value))
        except (TypeError, ValueError):
            continue
    return coerced


def grade_matrix(question: Question, matrix_selections) -> GradedResult:
    """
    matrix_selections: [{"row_id": int, "column_id": int}, ...] — the
    column the student picked for each row (single-select per row, the
    standard NGN Matrix/Grid format).

    Correct only if every row that has a designated correct column was
    answered with one of its correct columns. A row with no correct cell at
    all raises QuestionNotGradeable, same reasoning as grade_submission: an
    unanswerable row must never silently compare as satisfied.
    """
    rows = list(question.matrix_rows.all())
    if not rows:
        raise QuestionNotGradeable(f"Question {question.pk} has no matrix rows and cannot be graded.")

    correct_by_row: dict[int, set[int]] = {}
    for cell in MatrixCell.objects.filter(row__question=question, is_correct=True).values_list(
        "row_id", "column_id"
    ):
        correct_by_row.setdefault(cell[0], set()).add(cell[1])

    if any(row.id not in correct_by_row for row in rows):
        raise QuestionNotGradeable(f"Question {question.pk} has a matrix row with no correct column and cannot be graded.")

    selected_by_row: dict[int, int] = {}
    for selection in matrix_selections:
        row_id = _coerce_ints([selection.get("row_id")])
        column_id = _coerce_ints([selection.get("column_id")])
        if row_id and column_id:
            selected_by_row[next(iter(row_id))] = next(iter(column_id))

    is_correct = all(selected_by_row.get(row.id) in correct_by_row[row.id] for row in rows)
    return GradedResult(is_correct=is_correct, detail={"selected_by_row": selected_by_row})


def grade_bowtie(question: Question, bowtie_option_ids) -> GradedResult:
    """
    bowtie_option_ids: flat list of BowTieOption ids selected across all
    three sections (Assessment/Condition/Action) — each option already
    knows its own section, so grading is exact-set-match against every
    option flagged is_correct, the same rule grade_submission uses for
    AnswerChoice, just generalised to this model.
    """
    options = list(question.bowtie_options.all())
    valid_ids = {option.id for option in options}
    correct_ids = {option.id for option in options if option.is_correct}
    if not correct_ids:
        raise QuestionNotGradeable(f"Question {question.pk} has no correct bow-tie option and cannot be graded.")

    selected_ids = _coerce_ints(bowtie_option_ids) & valid_ids
    return GradedResult(is_correct=selected_ids == correct_ids, detail={"selected_option_ids": sorted(selected_ids)})


def grade_cloze(question: Question, cloze_selections) -> GradedResult:
    """cloze_selections: [{"blank_id": int, "option_id": int}, ...] — one chosen option per dropdown blank."""
    blanks = list(question.cloze_blanks.prefetch_related("options").all())
    if not blanks:
        raise QuestionNotGradeable(f"Question {question.pk} has no cloze blanks and cannot be graded.")

    correct_by_blank: dict[int, int] = {}
    for blank in blanks:
        correct_option = next((o for o in blank.options.all() if o.is_correct), None)
        if correct_option is None:
            raise QuestionNotGradeable(f"Cloze blank {blank.pk} has no correct option and cannot be graded.")
        correct_by_blank[blank.id] = correct_option.id

    selected_by_blank: dict[int, int] = {}
    for selection in cloze_selections:
        blank_id = _coerce_ints([selection.get("blank_id")])
        option_id = _coerce_ints([selection.get("option_id")])
        if blank_id and option_id:
            selected_by_blank[next(iter(blank_id))] = next(iter(option_id))

    is_correct = all(selected_by_blank.get(blank_id) == correct for blank_id, correct in correct_by_blank.items())
    return GradedResult(is_correct=is_correct, detail={"selected_by_blank": selected_by_blank})


def grade_dragdrop(question: Question, dragdrop_placements) -> GradedResult:
    """
    dragdrop_placements: [{"item_id": int, "category_id": int|None, "order": int|None}, ...].

    Covers both DragDropItem variants (see its own docstring): a question
    is graded as "sort into categories" if its items carry correct_category,
    or as "sequence" if they carry correct_order — whichever the content
    was actually authored as.
    """
    items = list(question.dragdrop_items.all())
    if not items:
        raise QuestionNotGradeable(f"Question {question.pk} has no drag-drop items and cannot be graded.")

    is_category_variant = any(item.correct_category_id is not None for item in items)
    is_order_variant = any(item.correct_order is not None for item in items)
    if not is_category_variant and not is_order_variant:
        raise QuestionNotGradeable(f"Question {question.pk} has no drag-drop answer key and cannot be graded.")

    placement_by_item: dict[int, dict] = {}
    for placement in dragdrop_placements:
        item_id = _coerce_ints([placement.get("item_id")])
        if not item_id:
            continue
        placement_by_item[next(iter(item_id))] = placement

    if is_category_variant:
        is_correct = all(
            _coerce_ints([placement_by_item.get(item.id, {}).get("category_id")]) == _coerce_ints([item.correct_category_id])
            for item in items
        )
    else:
        is_correct = all(
            placement_by_item.get(item.id, {}).get("order") == item.correct_order for item in items
        )

    return GradedResult(is_correct=is_correct, detail={"placements": list(dragdrop_placements)})


def grade_hotspot(question: Question, hotspot_target_ids) -> GradedResult:
    """hotspot_target_ids: flat list of selected HotSpotTarget ids — exact-set-match against every target flagged is_correct."""
    targets = list(question.hotspot_targets.all())
    valid_ids = {target.id for target in targets}
    correct_ids = {target.id for target in targets if target.is_correct}
    if not correct_ids:
        raise QuestionNotGradeable(f"Question {question.pk} has no correct hot spot target and cannot be graded.")

    selected_ids = _coerce_ints(hotspot_target_ids) & valid_ids
    return GradedResult(is_correct=selected_ids == correct_ids, detail={"selected_target_ids": sorted(selected_ids)})


def build_matrix_answer_key(question: Question) -> list[dict]:
    return [
        {"row_id": cell.row_id, "column_id": cell.column_id, "is_correct": cell.is_correct, "rationale": cell.rationale}
        for cell in MatrixCell.objects.filter(row__question=question).select_related("row", "column")
    ]


def build_bowtie_answer_key(question: Question) -> list[dict]:
    return [
        {"id": option.id, "is_correct": option.is_correct, "rationale": option.rationale}
        for option in question.bowtie_options.all()
    ]


def build_cloze_answer_key(question: Question) -> list[dict]:
    return [
        {
            "blank_id": blank.id,
            "options": [
                {"id": option.id, "is_correct": option.is_correct, "rationale": option.rationale}
                for option in blank.options.all()
            ],
        }
        for blank in question.cloze_blanks.prefetch_related("options").all()
    ]


def build_dragdrop_answer_key(question: Question) -> list[dict]:
    return [
        {
            "id": item.id,
            "correct_category_id": item.correct_category_id,
            "correct_order": item.correct_order,
            "rationale": item.rationale,
        }
        for item in question.dragdrop_items.all()
    ]


def build_hotspot_answer_key(question: Question) -> list[dict]:
    return [
        {"id": target.id, "is_correct": target.is_correct, "rationale": target.rationale}
        for target in question.hotspot_targets.all()
    ]
