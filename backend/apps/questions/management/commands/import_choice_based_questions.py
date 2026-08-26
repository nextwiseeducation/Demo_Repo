import json

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.questions.models import AnswerChoice, Question
from apps.taxonomy.models import ClientNeedsCategory, ClientNeedsSubcategory, ExamType, NursingSystem, Subtopic, Tag, Topic

# Lives at backend/Question JSON/questions.json — the client's first content
# batch, committed to the repo so it ships with a deploy the same way
# ensure_superuser's env vars do, without needing Render shell access (the
# free web-service plan has none — see docs/architecture.md).
QUESTIONS_FILE = settings.BASE_DIR / "Question JSON" / "questions.json"


class Command(BaseCommand):
    """
    Imports questions whose answers are AnswerChoice rows — MCQ, SATA, and
    EMR all share that shape (question_type controls scoring rules, not the
    schema; see AnswerChoice's docstring in models.py). Does NOT handle the
    NGN structural types (Matrix/Grid, Bow-Tie, Drag & Drop, Cloze, Hot
    Spot) — those use entirely different child models, not AnswerChoice,
    and need their own import path when that content arrives.

    Invoked manually/on-demand (`manage.py import_choice_based_questions`),
    not wired into the Render build command — unlike ensure_superuser,
    importing content isn't something every deploy should re-check for.
    It IS idempotent though (safe to re-run; see below), so wiring it in
    later is a one-line change if that ever becomes the preferred workflow.

    Idempotency is by exact `stem` text rather than a dedicated external-id
    field (the schema has none yet) — fine for a one-off batch this size;
    Milestone 2's bulk CSV importer will need a real natural key once
    re-imports/updates to existing questions become a real workflow.

    Rows whose nclex_client_needs_subcategory is the literal string
    "NEEDS_REVIEW" are skipped rather than imported with a placeholder
    value — see CLAUDE.md's "Questions Pending from Content Team" #4: two of
    the four official NCSBN Client Needs categories (Health Promotion and
    Maintenance, Psychosocial Integrity) have no real subcategories, and
    that policy question isn't resolved yet.
    """

    help = "Imports MCQ/SATA/EMR questions (AnswerChoice-based) from Question JSON/questions.json, if it exists."

    def handle(self, *args, **options):
        if not QUESTIONS_FILE.exists():
            self.stdout.write(f"{QUESTIONS_FILE} not found — skipping.")
            return

        with open(QUESTIONS_FILE) as f:
            records = json.load(f)

        created = 0
        skipped_existing = 0
        skipped_needs_review = []

        for record in records:
            meta = record["metadata"]

            if meta.get("nclex_client_needs_subcategory") == "NEEDS_REVIEW":
                skipped_needs_review.append(record["question_id"])
                continue

            if Question.objects.filter(stem=record["stem"]).exists():
                skipped_existing += 1
                continue

            with transaction.atomic():
                nursing_system, _ = NursingSystem.objects.get_or_create(name=meta["nursing_system"])
                topic, _ = Topic.objects.get_or_create(name=meta["topic"], nursing_system=nursing_system)
                subtopic = None
                if meta.get("subtopic"):
                    subtopic, _ = Subtopic.objects.get_or_create(name=meta["subtopic"], topic=topic)
                category, _ = ClientNeedsCategory.objects.get_or_create(
                    name=meta["nclex_client_needs_category"], exam_type=ExamType.RN
                )
                subcategory, _ = ClientNeedsSubcategory.objects.get_or_create(
                    name=meta["nclex_client_needs_subcategory"], category=category
                )

                question = Question.objects.create(
                    question_type=record["question_type"],
                    ngn_type=record.get("ngn_type"),
                    stem=record["stem"],
                    clinical_scenario=record.get("clinical_scenario"),
                    difficulty=meta["difficulty"],
                    nursing_system=nursing_system,
                    topic=topic,
                    subtopic=subtopic,
                    nclex_client_needs_category=category,
                    nclex_client_needs_subcategory=subcategory,
                    clinical_judgment_skill=meta["clinical_judgment_skill"],
                    cognitive_level=meta["cognitive_level"],
                    reference=record.get("reference"),
                )

                for tag_name in meta.get("tags") or []:
                    tag, _ = Tag.objects.get_or_create(name=tag_name)
                    question.tags.add(tag)

                for choice in record["answer_choices"]:
                    AnswerChoice.objects.create(
                        question=question,
                        choice_text=choice["choice_text"],
                        is_correct=choice["is_correct"],
                        display_order=choice["display_order"],
                        rationale=choice.get("rationale", ""),
                    )

            created += 1

        self.stdout.write(self.style.SUCCESS(f"Imported {created} new question(s)."))
        if skipped_existing:
            self.stdout.write(f"Skipped {skipped_existing} already-imported question(s).")
        if skipped_needs_review:
            self.stdout.write(
                self.style.WARNING(
                    f"Skipped {len(skipped_needs_review)} question(s) with an unresolved "
                    f"nclex_client_needs_subcategory (NEEDS_REVIEW): {', '.join(skipped_needs_review)}"
                )
            )
