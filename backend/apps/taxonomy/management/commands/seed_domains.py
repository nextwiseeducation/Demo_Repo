from django.core.management.base import BaseCommand
from django.db import transaction

from apps.taxonomy.models import Domain

# UWorld's "Subjects" facet — a broad nursing-curriculum grouping,
# independent of NursingSystem (UWorld's "Systems" facet, body-system/skill
# based). Like NursingSystem itself, this is this project's own invented
# taxonomy (not an NCSBN standard) — hardcoded here only because it's the
# exact list confirmed against the client's own UWorld reference export, the
# same way seed_client_needs.py hardcodes the official Client Needs list.
DOMAINS = [
    "Adult Health",
    "Child Health",
    "Fundamentals",
    "Leadership & Management",
    "Maternal & Newborn Health",
    "Mental Health",
    "Pharmacology",
]


class Command(BaseCommand):
    """
    Seeds the Domain ("Subjects") taxonomy confirmed against the client's
    UWorld reference export.

    Idempotent and additive only, like seed_client_needs.py — safe to
    re-run on every deploy, and safe to re-run after editing the list above.
    Unlike seed_client_needs.py, there is no rename step here: Domain is a
    brand new field with no existing data to reconcile (Question.domain is
    nullable and unpopulated on every row imported before this command
    existed — see Question.domain's own field comment).
    """

    help = "Creates the Domain ('Subjects') taxonomy values if they don't exist."

    def handle(self, *args, **options):
        created = 0
        with transaction.atomic():
            for name in DOMAINS:
                _, made = Domain.objects.get_or_create(name=name)
                if made:
                    created += 1

        if created:
            self.stdout.write(self.style.SUCCESS(f"Seeded {created} Domain(s)."))
        else:
            self.stdout.write("Domain taxonomy already seeded — nothing to do.")
