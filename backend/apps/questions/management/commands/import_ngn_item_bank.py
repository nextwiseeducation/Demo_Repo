"""
Imports the full NGN Item Bank xlsx format: MCQ/SATA/EMR plus every
structural NGN type this project's schema supports (Matrix/Grid, Bow-Tie,
Drag-and-Drop, Cloze, Hot Spot, NGN Case Study).

Separate from import_choice_based_questions.py (JSON-format, MCQ/SATA/EMR
only) deliberately — that command's source file predates the xlsx template
and only ever needs to handle its original shape. This command's source
format (a 6-sheet workbook: Item_Master, Answer_Options, NGN_Cases,
NGN_Components, References, Valid_Values) is now the standard going
forward for every question type, including MCQ/SATA/EMR, since a future
batch has no reason to ever arrive as JSON again.

The actual import logic lives in apps.questions.importer.NgnItemBankImporter
— this command is just the CLI wrapper around it (argument parsing +
rendering the report to stdout), so the admin dashboard's
POST /api/admin/import/ endpoint can run the identical logic without going
through argv/stdout at all.
"""

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.questions.importer import ImportResult, NgnItemBankImporter, write_import_log


class Command(BaseCommand):
    """
    Unlike import_choice_based_questions.py, --file is REQUIRED rather than
    defaulting to a path inside the repo: the template lives outside
    Demo_Repo entirely (an editor's local working copy of client-supplied
    content, not a committed deploy artifact), so there is no single
    canonical path to default to, and each new batch is a genuinely
    different file. Run locally with DATABASE_URL pointed at whichever
    database (dev/production) should receive the import — same mechanism
    already used for the original 12-question batch.

    See apps.questions.importer.NgnItemBankImporter's own docstring for the
    idempotency rules, the case-study-is-atomic rule, and the KNOWN
    LIMITATION around case-study MCQ/SATA sub-items.
    """

    help = "Imports all NGN Item Bank question types from the standard xlsx template."

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True, help="Path to the NGN Item Bank xlsx file.")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate and report without writing anything. Use this to check a new content batch.",
        )
        parser.add_argument(
            "--update",
            action="store_true",
            help="Refresh questions/case studies that already exist (matched on external_id) instead of skipping them.",
        )

    def handle(self, *args, **options):
        path = Path(options["file"])
        if not path.exists():
            raise CommandError(f"{path} not found")

        importer = NgnItemBankImporter(allow_update=options["update"], dry_run=options["dry_run"])
        result = importer.run(path)

        if result.dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — nothing was written."))
        self._report(result)

        # uploaded_by=None: an operator running this from a shell has no
        # request.user — ImportLog.uploaded_by is nullable for exactly this
        # path, and the admin dashboard's Import History tab renders a null
        # uploader as "Command line". write_import_log itself is a no-op
        # for dry runs.
        write_import_log(result, uploaded_by=None, source_filename=path.name)

    def _report(self, result: ImportResult) -> None:
        self.stdout.write(self.style.SUCCESS(f"Imported {result.created} new question(s)."))
        if result.updated:
            self.stdout.write(self.style.SUCCESS(f"Updated {result.updated} existing question(s)."))
        if result.skipped_existing:
            self.stdout.write(
                f"Skipped {result.skipped_existing} question(s) that already exist (pass --update to refresh them)."
            )
        if result.case_studies_created:
            self.stdout.write(
                self.style.SUCCESS(f"Created {result.case_studies_created} new case stud(y/ies).")
            )
        if result.case_studies_updated:
            self.stdout.write(
                self.style.SUCCESS(f"Updated {result.case_studies_updated} existing case stud(y/ies).")
            )
        if result.created_taxonomy:
            distinct = result.distinct_taxonomy
            self.stdout.write(
                self.style.WARNING(f"Created {len(distinct)} new taxonomy row(s) — check for typos:")
            )
            for entry in distinct:
                self.stdout.write(f"  {entry}")
        if result.errors:
            self.stdout.write(self.style.ERROR(f"{len(result.errors)} row(s) failed validation:"))
            for error in result.errors:
                self.stdout.write(self.style.ERROR(error.as_line()))
