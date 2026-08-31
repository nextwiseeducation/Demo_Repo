from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.taxonomy.models import ClientNeedsCategory, ClientNeedsSubcategory, NursingSystem, Topic

from .models import (
    MAX_QUESTION_IMAGE_BYTES,
    AnswerChoice,
    ClinicalJudgmentSkill,
    CognitiveLevel,
    Difficulty,
    Question,
    QuestionType,
)
from .services import QuestionNotGradeable, grade_submission

User = get_user_model()


def make_question(**overrides):
    """
    Shared test fixture builder: creates a minimal-but-valid taxonomy chain
    (NursingSystem -> Topic, ClientNeedsCategory -> ClientNeedsSubcategory)
    plus a Question referencing them, so individual tests don't each have to
    repeat this required-field boilerplate. **overrides lets a test replace
    any default (e.g. question_type=QuestionType.SATA) without redefining
    every other field.
    """

    # get_or_create, not create: the taxonomy rows are uniquely constrained
    # by name, so a test that builds a SECOND question would otherwise blow
    # up on a duplicate NursingSystem before it got anywhere near what it
    # was actually testing. Reusing the existing chain makes this helper
    # composable — call it as many times as a test needs, and every question
    # simply shares one taxonomy, which is what these tests want anyway.
    nursing_system, _ = NursingSystem.objects.get_or_create(name="Cardiovascular")
    topic, _ = Topic.objects.get_or_create(nursing_system=nursing_system, name="Heart Failure")
    category, _ = ClientNeedsCategory.objects.get_or_create(name="Physiological Adaptation")
    subcategory, _ = ClientNeedsSubcategory.objects.get_or_create(
        category=category, name="Illness Management"
    )

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
        AnswerChoice.objects.create(
            question=question, choice_text="Correct 1", is_correct=True, display_order=1
        )
        AnswerChoice.objects.create(
            question=question, choice_text="Correct 2", is_correct=True, display_order=2
        )
        AnswerChoice.objects.create(question=question, choice_text="Wrong", is_correct=False, display_order=3)

        self.assertEqual(question.answer_choices.filter(is_correct=True).count(), 2)

    def test_rationale_is_optional_but_can_be_set_per_choice(self):
        # Each choice carries its own explanation (shown inline under that
        # option in the quiz UI) rather than relying on a single
        # question-level blob — confirms the field defaults to empty
        # (older/imported content may not have it yet) and holds a real
        # value when a choice does provide one.
        question = make_question()
        without_rationale = AnswerChoice.objects.create(question=question, choice_text="No explanation yet")
        with_rationale = AnswerChoice.objects.create(
            question=question,
            choice_text="Notify the provider",
            is_correct=True,
            rationale="Rapid weight gain indicates fluid retention and should be reported immediately.",
        )

        self.assertEqual(without_rationale.rationale, "")
        self.assertEqual(
            with_rationale.rationale,
            "Rapid weight gain indicates fluid retention and should be reported immediately.",
        )

    def test_question_rationale_correct_accepts_null(self):
        # rationale_correct was previously NOT NULL at the database level —
        # explicitly setting it to None would have raised an IntegrityError.
        # Now that AnswerChoice.rationale is the primary explanation
        # mechanism for MCQ/SATA/EMR questions, this must be genuinely
        # optional, not just "blank at the form layer."
        question = make_question(rationale_correct=None)
        self.assertIsNone(question.rationale_correct)


class GradeSubmissionTests(TestCase):
    """
    Direct tests of the grading rule, with no HTTP involved.

    Grading lives in services.py rather than in the view precisely so it can
    be exercised like this — and because Milestone 3's quiz engine and Phase
    2's analytics will call the same function. These tests are what stop the
    rule drifting when SATA partial credit arrives.
    """

    def setUp(self):
        self.question = make_question()
        self.right = AnswerChoice.objects.create(
            question=self.question, choice_text="Correct", is_correct=True, display_order=1
        )
        self.wrong = AnswerChoice.objects.create(
            question=self.question, choice_text="Wrong", is_correct=False, display_order=2
        )

    def test_selecting_the_correct_choice_is_correct(self):
        result = grade_submission(self.question, [self.right.id])
        self.assertTrue(result.is_correct)
        self.assertEqual(result.selected_ids, frozenset({self.right.id}))
        self.assertEqual(result.correct_ids, frozenset({self.right.id}))

    def test_selecting_a_distractor_is_incorrect(self):
        self.assertFalse(grade_submission(self.question, [self.wrong.id]).is_correct)

    def test_sata_requires_the_exact_set(self):
        question = make_question(
            question_type=QuestionType.SATA,
            stem="Select all that apply.",
            nursing_system=self.question.nursing_system,
            topic=self.question.topic,
            nclex_client_needs_category=self.question.nclex_client_needs_category,
            nclex_client_needs_subcategory=self.question.nclex_client_needs_subcategory,
        )
        a = AnswerChoice.objects.create(question=question, choice_text="A", is_correct=True, display_order=1)
        b = AnswerChoice.objects.create(question=question, choice_text="B", is_correct=True, display_order=2)
        c = AnswerChoice.objects.create(question=question, choice_text="C", is_correct=False, display_order=3)

        self.assertTrue(grade_submission(question, [a.id, b.id]).is_correct)
        # A partial selection is wrong under the current all-or-nothing
        # rule. This assertion is the one that will change when Phase 2
        # introduces partial credit — and it should change HERE, once.
        self.assertFalse(grade_submission(question, [a.id]).is_correct)
        # Superset: everything correct, plus a distractor.
        self.assertFalse(grade_submission(question, [a.id, b.id, c.id]).is_correct)

    def test_ids_from_another_question_are_discarded_not_counted(self):
        other = make_question(
            stem="A different question.",
            nursing_system=self.question.nursing_system,
            topic=self.question.topic,
            nclex_client_needs_category=self.question.nclex_client_needs_category,
            nclex_client_needs_subcategory=self.question.nclex_client_needs_subcategory,
        )
        foreign = AnswerChoice.objects.create(
            question=other, choice_text="Foreign", is_correct=True, display_order=1
        )

        result = grade_submission(self.question, [self.right.id, foreign.id])
        # Still correct: the foreign id is dropped rather than treated as an
        # extra selection that would spoil the exact-set match.
        self.assertTrue(result.is_correct)
        self.assertNotIn(foreign.id, result.selected_ids)

    def test_garbage_values_are_discarded_without_raising(self):
        # Defence in depth: the serializer normally rejects these before
        # grading is reached, but a future non-HTTP caller might not have
        # one, and grading must not explode.
        result = grade_submission(self.question, ["not-a-uuid", None, 42, self.right.id])
        self.assertTrue(result.is_correct)

    def test_question_with_no_correct_choice_raises(self):
        # The bug this guards: with no correct choices the expected set is
        # empty, so a naive set comparison reports an empty submission as
        # CORRECT — telling a student they were right about a question that
        # has no right answer.
        broken = make_question(
            stem="Broken question with no correct answer.",
            nursing_system=self.question.nursing_system,
            topic=self.question.topic,
            nclex_client_needs_category=self.question.nclex_client_needs_category,
            nclex_client_needs_subcategory=self.question.nclex_client_needs_subcategory,
        )
        AnswerChoice.objects.create(question=broken, choice_text="A", is_correct=False, display_order=1)

        with self.assertRaises(QuestionNotGradeable):
            grade_submission(broken, [])


class QuestionListAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="student@example.com", password="a-strong-password-123", is_active=True
        )
        self.question = make_question()
        self.choice = AnswerChoice.objects.create(
            question=self.question,
            choice_text="Notify the provider",
            is_correct=True,
            display_order=1,
            rationale="Rapid weight gain signals fluid retention.",
        )

    def test_requires_authentication(self):
        self.assertEqual(self.client.get(reverse("question-list")).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_response_is_paginated(self):
        # The endpoint used to return a bare list of every active question.
        # At the specced 4,000+ questions that response ran to megabytes, so
        # the paginated envelope is load-bearing, not cosmetic.
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("question-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertIn("count", response.data)

    def test_list_never_exposes_the_answer_key(self):
        # The single most important assertion in this file. If
        # PublicAnswerChoiceSerializer ever starts including is_correct or
        # rationale, every quiz becomes trivially cheatable by reading the
        # question list — and nothing else in the suite would notice.
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("question-list"))

        choice = response.data["results"][0]["answer_choices"][0]
        self.assertNotIn("is_correct", choice)
        self.assertNotIn("rationale", choice)
        self.assertIn("choice_text", choice)

    def test_inactive_questions_are_excluded(self):
        self.question.is_active = False
        self.question.save(update_fields=["is_active"])
        self.client.force_authenticate(self.user)

        self.assertEqual(self.client.get(reverse("question-list")).data["count"], 0)


class QuestionSubmitAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="student@example.com", password="a-strong-password-123", is_active=True
        )
        self.client.force_authenticate(self.user)
        self.question = make_question()
        self.right = AnswerChoice.objects.create(
            question=self.question,
            choice_text="Right",
            is_correct=True,
            display_order=1,
            rationale="Because.",
        )
        self.wrong = AnswerChoice.objects.create(
            question=self.question, choice_text="Wrong", is_correct=False, display_order=2, rationale="Nope."
        )
        self.url = reverse("question-submit", args=[self.question.pk])

    def submit(self, payload):
        return self.client.post(self.url, payload, format="json")

    def test_requires_authentication(self):
        self.client.force_authenticate(None)
        self.assertEqual(
            self.submit({"selected_choice_ids": [str(self.right.id)]}).status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_correct_answer_is_graded_and_reveals_the_key(self):
        response = self.submit({"selected_choice_ids": [str(self.right.id)]})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_correct"])
        # Revealing the key is the intended behaviour AFTER answering — the
        # student needs the rationale to learn from the question.
        keyed = {c["id"]: c for c in response.data["choices"]}
        self.assertTrue(keyed[str(self.right.id)]["is_correct"])
        self.assertEqual(keyed[str(self.right.id)]["rationale"], "Because.")

    def test_wrong_answer_is_graded_as_incorrect(self):
        self.assertFalse(self.submit({"selected_choice_ids": [str(self.wrong.id)]}).data["is_correct"])

    def test_integer_payload_returns_400_not_500(self):
        # The exact crash this endpoint used to have: a bare number hit
        # `for i in request.data.get(...)` and raised TypeError out of the
        # view, producing a 500.
        self.assertEqual(self.submit({"selected_choice_ids": 5}).status_code, status.HTTP_400_BAD_REQUEST)

    def test_object_payload_returns_400_not_silently_graded(self):
        # Worse than the crash: a dict used to iterate its KEYS and grade
        # against them, so a malformed request was silently accepted.
        self.assertEqual(
            self.submit({"selected_choice_ids": {"a": 1}}).status_code, status.HTTP_400_BAD_REQUEST
        )

    def test_string_payload_returns_400(self):
        self.assertEqual(self.submit({"selected_choice_ids": "abc"}).status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_field_returns_400(self):
        self.assertEqual(self.submit({}).status_code, status.HTTP_400_BAD_REQUEST)

    def test_empty_selection_is_rejected_and_reveals_nothing(self):
        # An empty submission used to return 200 with the full answer key,
        # which made this endpoint a plain "give me the answers" call for
        # any question the student chose to skip.
        response = self.submit({"selected_choice_ids": []})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn("choices", response.data)

    def test_non_uuid_id_returns_400(self):
        self.assertEqual(
            self.submit({"selected_choice_ids": ["not-a-uuid"]}).status_code, status.HTTP_400_BAD_REQUEST
        )

    def test_unknown_but_valid_uuid_is_graded_as_a_wrong_answer(self):
        # A well-formed id that isn't one of this question's choices is
        # dropped, leaving an empty selection — which cannot match the
        # answer key, so it grades as incorrect rather than erroring.
        response = self.submit({"selected_choice_ids": ["00000000-0000-0000-0000-000000000000"]})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_correct"])

    def test_inactive_question_returns_404(self):
        self.question.is_active = False
        self.question.save(update_fields=["is_active"])

        self.assertEqual(
            self.submit({"selected_choice_ids": [str(self.right.id)]}).status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_question_with_no_correct_choice_returns_409(self):
        self.right.is_correct = False
        self.right.save(update_fields=["is_correct"])

        response = self.submit({"selected_choice_ids": [str(self.right.id)]})

        # 409, not 200-with-is_correct-false: the question is broken
        # content, and the student must not be told they answered it wrong.
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertNotIn("choices", response.data)


class ExternalIdTests(TestCase):
    """
    external_id is the natural key the importer matches on. Its uniqueness
    is what makes re-importing safe; its nullability is what keeps
    hand-authored admin questions possible.
    """

    def test_external_id_is_unique(self):
        first = make_question(external_id="NW-MCQ-001")
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_question(
                external_id="NW-MCQ-001",
                stem="A different stem entirely.",
                nursing_system=first.nursing_system,
                topic=first.topic,
                nclex_client_needs_category=first.nclex_client_needs_category,
                nclex_client_needs_subcategory=first.nclex_client_needs_subcategory,
            )

    def test_multiple_questions_may_have_no_external_id(self):
        # NULLs are distinct under a unique constraint, so any number of
        # admin-authored questions can coexist without one.
        first = make_question()
        make_question(
            stem="Another hand-written question.",
            nursing_system=first.nursing_system,
            topic=first.topic,
            nclex_client_needs_category=first.nclex_client_needs_category,
            nclex_client_needs_subcategory=first.nclex_client_needs_subcategory,
        )
        self.assertEqual(Question.objects.filter(external_id__isnull=True).count(), 2)


class QuestionImageValidationTests(TestCase):
    """
    Question.image is a FileField with no content-type checking of its own.
    These validators are what stop an executable file being stored as a
    "question image" — which becomes stored XSS on the platform's own origin
    the moment media is served from a real host (see MEDIA_ROOT's note in
    settings; production still needs an object store in front of it).
    """

    def test_svg_upload_is_rejected(self):
        # SVG is the important case: it is an XML document that can carry
        # <script>, so browsers execute it rather than merely decoding it.
        question = make_question()
        question.image = SimpleUploadedFile(
            "payload.svg", b"<svg xmlns='http://www.w3.org/2000/svg'><script>alert(1)</script></svg>"
        )
        with self.assertRaises(ValidationError):
            question.full_clean()

    def test_html_upload_is_rejected(self):
        question = make_question()
        question.image = SimpleUploadedFile("payload.html", b"<script>alert(1)</script>")
        with self.assertRaises(ValidationError):
            question.full_clean()

    def test_oversized_image_is_rejected(self):
        question = make_question()
        question.image = SimpleUploadedFile(
            "huge.png", b"x" * (MAX_QUESTION_IMAGE_BYTES + 1), content_type="image/png"
        )
        with self.assertRaises(ValidationError):
            question.full_clean()

    def test_ordinary_png_is_accepted(self):
        question = make_question()
        question.image = SimpleUploadedFile("diagram.png", b"fake png bytes", content_type="image/png")
        # Must not raise — the validators have to leave legitimate content
        # alone or they simply block the feature.
        question.full_clean()


class PaginationContractTests(APITestCase):
    """
    Pins the exact envelope the frontend's listQuestions() depends on.

    That client pages by explicit ?page=N and stops when `next` is null,
    accumulating `results` into one flat array (see
    frontend/src/lib/api/questions.ts). If any of those three keys were
    renamed or the traversal terminated differently, the quiz setup page
    would silently receive a partial question bank — it builds its filter
    dropdowns and match counts from whatever it gets back, so a truncated
    list looks like working software rather than an error.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="student@example.com", password="a-strong-password-123", is_active=True
        )
        self.client.force_authenticate(self.user)
        # Deliberately more than one page: DefaultPagination.page_size is 50,
        # so 55 questions forces the multi-page path the client relies on.
        # A single-page fixture would pass even if traversal were broken.
        for index in range(55):
            make_question(stem=f"Question number {index}.", external_id=f"NW-PAGE-{index:03d}")

    def test_envelope_exposes_the_keys_the_client_reads(self):
        data = self.client.get(reverse("question-list")).data
        for key in ("count", "next", "previous", "results"):
            self.assertIn(key, data)

    def test_paging_by_explicit_page_number_returns_every_question(self):
        # Mirrors the client loop exactly, including its termination
        # condition, rather than asserting on page contents directly.
        collected = []
        page = 1
        while page <= 200:
            data = self.client.get(reverse("question-list"), {"page": page}).data
            collected.extend(data["results"])
            if not data["next"]:
                break
            page += 1

        self.assertEqual(len(collected), 55)
        self.assertEqual(data["count"], 55)
        # No duplicates across pages — an off-by-one in either the client's
        # or the server's paging would show up here.
        self.assertEqual(len({q["id"] for q in collected}), 55)

    def test_last_page_reports_next_as_null(self):
        # The client's only stop signal. If this were ever an empty string
        # or an absent key, the loop would run to its MAX_PAGES ceiling on
        # every single page load.
        data = self.client.get(reverse("question-list"), {"page": 2}).data
        self.assertIsNone(data["next"])
