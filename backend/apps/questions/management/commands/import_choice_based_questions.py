import json

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.questions.models import AnswerChoice, Question
from apps.taxonomy.models import (
    ClientNeedsCategory,
    ClientNeedsSubcategory,
    ExamType,
    NursingSystem,
    Subtopic,
    Tag,
    Topic,
)

# Lives at backend/Question JSON/questions.json — the client's first content
# batch, committed to the repo so it ships with a deploy the same way
# ensure_superuser's env vars do, without needing Render shell access (the
# free web-service plan has none — see docs/architecture.md).
QUESTIONS_FILE = settings.BASE_DIR / "Question JSON" / "questions.json"

# A row whose nclex_client_needs_subcategory is this literal string is
# skipped rather than imported with a placeholder. Originally this covered
# an unresolved policy question (CLAUDE.md's "Questions Pending from
# Content Team" #4: two of the four official NCSBN Client Needs categories,
# Health Promotion and Maintenance and Psychosocial Integrity, have no real
# subcategories) — that's now resolved (see seed_client_needs.py: each of
# those two categories is seeded with itself as its own subcategory,
# confirmed against both UWorld's live product and the client's own Excel
# batch). The sentinel/skip mechanism itself stays, since a row can still
# legitimately arrive with a subcategory nobody has assigned yet.
NEEDS_REVIEW_SENTINEL = "NEEDS_REVIEW"


class RowError(Exception):
    """
    One row failed validation. Carries a human-readable reason.

    Rows are validated and reported individually rather than letting the
    first bad record abort the run with a traceback: a content editor needs
    to see everything wrong with their file in one pass, not fix one typo,
    re-run, and discover the next. CLAUDE.md's Milestone 2 requires exactly
    this ("bulk CSV/Excel import with row-level validation and
    human-readable errors") for the spreadsheet importer — the shape is
    established here so that importer can reuse it.
    """


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

    Idempotency is by `external_id` (the content team's own "NW-MCQ-001"
    style identifier, carried in the source file). It previously matched on
    exact `stem` text, which meant an unindexed scan per row and, worse,
    silently imported a duplicate whenever anyone fixed a typo in a stem.
    Rows already present are left untouched by default; pass --update to
    refresh their editable content from the file instead.

    Validation is strict about the things that are expensive to discover
    late. Django's `choices=` is NOT a database constraint and
    `objects.create()` skips `full_clean()`, so before this command
    validated, a misspelled difficulty or cognitive_level was written
    happily and only surfaced much later as a filter that mysteriously
    returned nothing.
    """

    help = (
        "Imports MCQ/SATA/EMR questions (AnswerChoice-based) from Question JSON/questions.json, if it exists."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate and report without writing anything. Use this to check a new content batch.",
        )
        parser.add_argument(
            "--update",
            action="store_true",
            help="Refresh questions that already exist (matched on external_id) instead of skipping them.",
        )
        parser.add_argument(
            "--file",
            default=None,
            help=f"Path to the JSON file to import. Defaults to {QUESTIONS_FILE}.",
        )

    def handle(self, *args, **options):
        path = options["file"] or QUESTIONS_FILE
        dry_run = options["dry_run"]

        if not QUESTIONS_FILE.exists() and options["file"] is None:
            self.stdout.write(f"{QUESTIONS_FILE} not found — skipping.")
            return

        with open(path) as f:
            records = json.load(f)

        created = 0
        updated = 0
        skipped_existing = 0
        skipped_needs_review: list[str] = []
        errors: list[str] = []
        # Taxonomy rows this run brought into existence. Reported at the end
        # because auto-creation is how a typo becomes a permanent second
        # "Cardiovacular" system — surfacing them makes that visible
        # immediately instead of leaving it to be noticed months later.
        created_taxonomy: list[str] = []

        for index, record in enumerate(records, start=1):
            label = record.get("question_id") or f"row {index}"
            try:
                # Each row is its own transaction, so one bad record can
                # neither abort the run nor leave a half-written question
                # (a Question with no AnswerChoices) behind.
                with transaction.atomic():
                    outcome = self._import_record(record, options["update"], created_taxonomy)

                    if dry_run:
                        # Roll the row back: --dry-run must validate exactly
                        # the same code path a real run takes, including
                        # taxonomy creation and full_clean, while leaving
                        # the database untouched.
                        transaction.set_rollback(True)

                if outcome == "created":
                    created += 1
                elif outcome == "updated":
                    updated += 1
                elif outcome == "needs_review":
                    skipped_needs_review.append(label)
                else:
                    skipped_existing += 1
            except RowError as exc:
                errors.append(f"  {label}: {exc}")

        if dry_run:
            # created_taxonomy is reported anyway: knowing a dry run WOULD
            # have invented a new nursing system is exactly the signal that
            # catches a typo before it is written.
            self.stdout.write(self.style.WARNING("DRY RUN — nothing was written."))

        self._report(created, updated, skipped_existing, skipped_needs_review, created_taxonomy, errors)

    def _import_record(self, record, allow_update, created_taxonomy) -> str:
        """Imports one record. Returns what happened, or raises RowError."""
        try:
            meta = record["metadata"]
        except KeyError as exc:
            raise RowError("missing required 'metadata' object") from exc

        if meta.get("nclex_client_needs_subcategory") == NEEDS_REVIEW_SENTINEL:
            return "needs_review"

        external_id = record.get("question_id")
        if not external_id:
            raise RowError("missing 'question_id' — it is the key imports match on, so it is required")

        existing = Question.objects.filter(external_id=external_id).first()
        if existing is not None and not allow_update:
            return "skipped"

        nursing_system, topic, subtopic = self._resolve_own_taxonomy(meta, created_taxonomy)
        category, subcategory = self._resolve_client_needs(meta)

        fields = {
            "external_id": external_id,
            "question_type": record.get("question_type"),
            "ngn_type": record.get("ngn_type"),
            "stem": record.get("stem") or "",
            "clinical_scenario": record.get("clinical_scenario"),
            "difficulty": meta.get("difficulty"),
            "nursing_system": nursing_system,
            "topic": topic,
            "subtopic": subtopic,
            "nclex_client_needs_category": category,
            "nclex_client_needs_subcategory": subcategory,
            "clinical_judgment_skill": meta.get("clinical_judgment_skill"),
            "cognitive_level": meta.get("cognitive_level"),
            "reference": record.get("reference"),
            # Previously dropped on the floor along with the two fields
            # below, even though the model has carried them for some time.
            "key_takeaway": record.get("key_takeaway"),
            "rationale_correct": record.get("rationale_correct"),
            "rationale_incorrect": record.get("rationale_incorrect"),
        }

        question = existing or Question()
        for name, value in fields.items():
            setattr(question, name, value)

        # `image` is a FileField, so a value here would have to be a file
        # this command can resolve and store, not just a string. Every
        # record in the current batch has image: null, so rather than guess
        # at a half-built pipeline, non-null values are rejected loudly — an
        # editor gets told the importer can't handle images yet instead of
        # silently losing one. Wiring this up means deciding where the
        # source files live relative to the JSON and copying them into
        # MEDIA_ROOT (or object storage) on import.
        if record.get("image"):
            raise RowError(
                "'image' is set, but importing image files is not supported yet — "
                "add the image via the Django admin after import"
            )

        # full_clean() is the whole point of this block: it runs the field
        # validators AND the choices= checks that the database does not
        # enforce, so a misspelled enum is caught here rather than becoming
        # a silently-unfilterable row. exclude the M2M/relations Django
        # can't validate on an unsaved instance.
        try:
            question.full_clean(exclude=["id"])
        except ValidationError as exc:
            raise RowError(self._format_validation_error(exc)) from exc

        question.save()

        self._sync_tags(question, meta.get("tags") or [], created_taxonomy)
        self._sync_choices(question, record.get("answer_choices") or [])

        return "updated" if existing else "created"

    def _resolve_own_taxonomy(self, meta, created_taxonomy):
        """
        NursingSystem/Topic/Subtopic are this project's own invented
        taxonomy (not NCSBN's), and the content team is still finalising the
        list — so these are created on demand rather than required to exist
        up front. Every creation is recorded so the run reports it: silent
        auto-creation is how "Cardiovascular" and "Cardiovascualr" end up
        coexisting forever.
        """
        system_name = (meta.get("nursing_system") or "").strip()
        if not system_name:
            raise RowError("missing 'nursing_system'")
        nursing_system, made = NursingSystem.objects.get_or_create(name=system_name)
        if made:
            created_taxonomy.append(f"NursingSystem: {system_name}")

        topic_name = (meta.get("topic") or "").strip()
        if not topic_name:
            raise RowError("missing 'topic'")
        topic, made = Topic.objects.get_or_create(name=topic_name, nursing_system=nursing_system)
        if made:
            created_taxonomy.append(f"Topic: {system_name} / {topic_name}")

        subtopic = None
        subtopic_name = (meta.get("subtopic") or "").strip()
        if subtopic_name:
            subtopic, made = Subtopic.objects.get_or_create(name=subtopic_name, topic=topic)
            if made:
                created_taxonomy.append(f"Subtopic: {system_name} / {topic_name} / {subtopic_name}")

        return nursing_system, topic, subtopic

    @staticmethod
    def _resolve_client_needs(meta):
        """
        Client Needs categories are looked up STRICTLY — never created.

        Unlike the taxonomy above, these are the official NCSBN exam
        blueprint categories. Auto-creating one on a typo doesn't just add a
        stray row: it silently changes what the question bank claims about
        its own coverage of the real exam's category weighting, which is the
        thing the categorisation exists to guarantee. Failing the row is the
        correct outcome — the fix is to correct the spelling or to add the
        category deliberately via the admin.
        """
        category_name = (meta.get("nclex_client_needs_category") or "").strip()
        if not category_name:
            raise RowError("missing 'nclex_client_needs_category'")
        category = ClientNeedsCategory.objects.filter(
            name__iexact=category_name, exam_type=ExamType.RN
        ).first()
        if category is None:
            raise RowError(
                f"unknown Client Needs category {category_name!r} — official NCSBN categories are not "
                "created automatically; add it in the admin if it is genuinely new"
            )

        subcategory_name = (meta.get("nclex_client_needs_subcategory") or "").strip()
        if not subcategory_name:
            raise RowError("missing 'nclex_client_needs_subcategory'")
        subcategory = ClientNeedsSubcategory.objects.filter(
            name__iexact=subcategory_name, category=category
        ).first()
        if subcategory is None:
            raise RowError(f"unknown Client Needs subcategory {subcategory_name!r} under {category_name!r}")

        return category, subcategory

    @staticmethod
    def _sync_tags(question, tag_names, created_taxonomy):
        tags = []
        for name in tag_names:
            name = (name or "").strip()
            if not name:
                continue
            tag, made = Tag.objects.get_or_create(name=name)
            if made:
                created_taxonomy.append(f"Tag: {name}")
            tags.append(tag)
        # set() rather than add(): on --update this must also REMOVE tags
        # that were taken off the question in the source file, which add()
        # alone would silently keep.
        question.tags.set(tags)

    @staticmethod
    def _sync_choices(question, choices):
        if not choices:
            raise RowError("no 'answer_choices' — a choice-based question needs at least one")

        correct_count = sum(1 for choice in choices if choice.get("is_correct"))
        if correct_count == 0:
            # Grading treats a question with no correct answer as
            # ungradeable (see services.QuestionNotGradeable), so importing
            # one just plants a question that breaks when a student reaches
            # it. Catch it at the door instead.
            raise RowError("no answer choice is marked is_correct")
        if question.question_type == "MCQ" and correct_count > 1:
            raise RowError(f"question_type is MCQ but {correct_count} choices are marked correct")

        # Replace wholesale rather than diffing: choices have no stable
        # identifier of their own in the source file (choice_id is "A"/"B",
        # positional within the row), so matching them up across an update
        # would be guesswork. Safe because AnswerChoice rows are only
        # referenced by StudentResponseLog, which uses on_delete=SET_NULL
        # precisely so historical responses survive content edits.
        question.answer_choices.all().delete()
        for choice in choices:
            AnswerChoice.objects.create(
                question=question,
                choice_text=choice.get("choice_text") or "",
                is_correct=bool(choice.get("is_correct")),
                display_order=choice.get("display_order") or 0,
                rationale=choice.get("rationale") or "",
            )

    @staticmethod
    def _format_validation_error(exc: ValidationError) -> str:
        """Flattens Django's {field: [messages]} into one readable line."""
        if not hasattr(exc, "message_dict"):
            return "; ".join(exc.messages)
        return "; ".join(f"{field}: {' '.join(messages)}" for field, messages in exc.message_dict.items())

    def _report(self, created, updated, skipped_existing, needs_review, created_taxonomy, errors):
        self.stdout.write(self.style.SUCCESS(f"Imported {created} new question(s)."))
        if updated:
            self.stdout.write(self.style.SUCCESS(f"Updated {updated} existing question(s)."))
        if skipped_existing:
            self.stdout.write(
                f"Skipped {skipped_existing} question(s) that already exist (pass --update to refresh them)."
            )
        if needs_review:
            self.stdout.write(
                self.style.WARNING(
                    f"Skipped {len(needs_review)} question(s) with an unresolved "
                    f"nclex_client_needs_subcategory ({NEEDS_REVIEW_SENTINEL}): {', '.join(needs_review)}"
                )
            )
        if created_taxonomy:
            # dict.fromkeys de-duplicates while preserving first-seen order.
            # Entries can repeat because a row whose transaction later rolls
            # back (a validation failure, or --dry-run) still appended what
            # it attempted to create — the database change is undone, the
            # in-memory note is not. Reporting the distinct set is both
            # honest and readable: for a dry run it answers "what would this
            # file bring into existence", which is exactly the question that
            # catches a typo before it is written.
            distinct = list(dict.fromkeys(created_taxonomy))
            self.stdout.write(
                self.style.WARNING(f"Created {len(distinct)} new taxonomy row(s) — check for typos:")
            )
            for entry in distinct:
                self.stdout.write(f"  {entry}")
        if errors:
            self.stdout.write(self.style.ERROR(f"{len(errors)} row(s) failed validation:"))
            for error in errors:
                self.stdout.write(self.style.ERROR(error))
