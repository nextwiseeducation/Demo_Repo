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

from .models import AnswerChoice, Question


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
