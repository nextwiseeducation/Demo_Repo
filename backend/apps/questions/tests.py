from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.taxonomy.models import ClientNeedsCategory, ClientNeedsSubcategory, NursingSystem, Topic

from .models import AnswerChoice, ClinicalJudgmentSkill, CognitiveLevel, Difficulty, Question, QuestionType


def make_question(**overrides):
    """
    Shared test fixture builder: creates a minimal-but-valid taxonomy chain
    (NursingSystem -> Topic, ClientNeedsCategory -> ClientNeedsSubcategory)
    plus a Question referencing them, so individual tests don't each have to
    repeat this required-field boilerplate. **overrides lets a test replace
    any default (e.g. question_type=QuestionType.SATA) without redefining
    every other field.
    """

    nursing_system = NursingSystem.objects.create(name="Cardiovascular")
    topic = Topic.objects.create(nursing_system=nursing_system, name="Heart Failure")
    category = ClientNeedsCategory.objects.create(name="Physiological Adaptation")
    subcategory = ClientNeedsSubcategory.objects.create(category=category, name="Illness Management")

    # Only the fields Question actually requires (no null=True/blank=True in
    # models.py) are set here — subtopic, tags, rationale_incorrect,
    # reference, image, etc. are all optional and left unset, since a
    # minimal valid Question is exactly what most tests need.
    defaults = dict(
        question_type=QuestionType.MCQ,
        stem="A client with heart failure reports weight gain of 3 lbs in 2 days. What is the priority action?",
        difficulty=Difficulty.MEDIUM,
        nursing_system=nursing_system,
        topic=topic,
        nclex_client_needs_category=category,
        nclex_client_needs_subcategory=subcategory,
        clinical_judgment_skill=ClinicalJudgmentSkill.TAKE_ACTION,
        cognitive_level=CognitiveLevel.APPLY,
        rationale_correct="Rapid weight gain indicates fluid retention and should be reported immediately.",
    )
    defaults.update(overrides)
    return Question.objects.create(**defaults)


class QuestionTests(TestCase):
    def test_str_includes_type_and_stem(self):
        question = make_question()
        self.assertIn("MCQ", str(question))

    def test_missing_required_fk_raises(self):
        # nursing_system/topic/nclex_client_needs_category/
        # nclex_client_needs_subcategory are all required ForeignKeys (no
        # null=True in models.py) — omitting them entirely should fail at
        # the database level (NOT NULL constraint), confirming the schema
        # actually enforces "every question must be fully taxonomy-tagged"
        # rather than that constraint only existing in application code
        # that could be bypassed.
        with self.assertRaises(IntegrityError), transaction.atomic():
            Question.objects.create(
                question_type=QuestionType.MCQ,
                stem="Incomplete question",
                difficulty=Difficulty.EASY,
                clinical_judgment_skill=ClinicalJudgmentSkill.RECOGNIZE_CUES,
                cognitive_level=CognitiveLevel.REMEMBER,
                rationale_correct="n/a",
            )


class AnswerChoiceTests(TestCase):
    def test_ordered_by_display_order(self):
        # Deliberately creates "Second" (display_order=2) before "First"
        # (display_order=1) — if AnswerChoice.Meta.ordering weren't applied,
        # this query would return them in creation order ("Second" first)
        # instead of by display_order, so this test would only pass by
        # accident if the ordering weren't actually working.
        question = make_question(question_type=QuestionType.SATA)
        AnswerChoice.objects.create(question=question, choice_text="Second", display_order=2)
        AnswerChoice.objects.create(question=question, choice_text="First", display_order=1)

        # question.answer_choices is the related_name from
        # AnswerChoice.question — accessing it as a reverse relation
        # confirms both the ForeignKey wiring and the Meta ordering work
        # together correctly.
        ordered_texts = list(question.answer_choices.values_list("choice_text", flat=True))
        self.assertEqual(ordered_texts, ["First", "Second"])

    def test_sata_supports_multiple_correct_choices(self):
        # Confirms the schema has no constraint limiting is_correct=True to
        # a single row per question — essential for SATA (Select All That
        # Apply), which can have any number of correct choices, unlike MCQ.
        # See AnswerChoice's docstring in models.py: this rule isn't
        # enforced by the database at all, it's just that nothing here
        # prevents it.
        question = make_question(question_type=QuestionType.SATA)
        AnswerChoice.objects.create(question=question, choice_text="Correct 1", is_correct=True, display_order=1)
        AnswerChoice.objects.create(question=question, choice_text="Correct 2", is_correct=True, display_order=2)
        AnswerChoice.objects.create(question=question, choice_text="Wrong", is_correct=False, display_order=3)

        self.assertEqual(question.answer_choices.filter(is_correct=True).count(), 2)
