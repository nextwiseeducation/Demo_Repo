from django.core.management.base import BaseCommand
from django.db import transaction

from apps.taxonomy.models import ClientNeedsCategory, ClientNeedsSubcategory, ExamType

# The official NCSBN NCLEX-RN Client Needs structure.
#
# Hardcoded here — unlike NursingSystem/Topic/Subtopic, which are this
# project's own invented taxonomy and stay fully admin-managed — because
# these four categories and their subcategories are a published external
# standard, not an editorial choice. The question bank's claim to mirror the
# real exam's category weighting depends on them being exactly this.
#
# Kept as a re-runnable command rather than a data migration deliberately:
# a migration would freeze the list into migration history, and NCSBN does
# revise the test plan periodically. This can simply be edited and re-run.
#
# Note which categories have NO subcategories. That is not an omission —
# NCSBN genuinely does not subdivide Health Promotion and Maintenance or
# Psychosocial Integrity. It is also the open question behind the
# NEEDS_REVIEW rows in the content file (CLAUDE.md, "Questions Pending from
# Content Team" #4): Question.nclex_client_needs_subcategory is currently a
# required FK, so a question in one of these two categories has nothing
# valid to point at. Resolving that — either by making the field nullable or
# by agreeing a "General" subcategory with the client — is what unblocks
# those rows.
RN_CLIENT_NEEDS = {
    "Safe and Effective Care Environment": [
        "Management of Care",
        "Safety and Infection Control",
    ],
    "Health Promotion and Maintenance": [],
    "Psychosocial Integrity": [],
    "Physiological Integrity": [
        "Basic Care and Comfort",
        "Pharmacological and Parenteral Therapies",
        "Reduction of Risk Potential",
        "Physiological Adaptation",
    ],
}


class Command(BaseCommand):
    """
    Seeds the official NCSBN Client Needs categories and subcategories.

    Required before importing content: the question importer looks these up
    STRICTLY and refuses to create them on the fly, precisely so that a typo
    in a content file cannot quietly invent a new "official" exam category
    and misstate what the bank covers. This command is the deliberate act
    that puts them there.

    Idempotent, like ensure_superuser — safe to run on every deploy, and
    safe to re-run after editing the list above to add newly published
    categories.

    Only NCLEX-RN is seeded. ClientNeedsCategory.exam_type exists so PN
    (which uses different category names, e.g. "Coordinated Care" where RN
    says "Management of Care") can be added later without a migration; PN
    content is not in Phase 1 scope.
    """

    help = "Creates the official NCSBN NCLEX-RN Client Needs categories/subcategories if they don't exist."

    def handle(self, *args, **options):
        created_categories = 0
        created_subcategories = 0

        # One transaction for the whole seed: a partially-seeded taxonomy is
        # worse than an unseeded one, because the importer would then accept
        # some rows and reject others for no reason an editor could see.
        with transaction.atomic():
            for category_name, subcategory_names in RN_CLIENT_NEEDS.items():
                category, made = ClientNeedsCategory.objects.get_or_create(
                    name=category_name, exam_type=ExamType.RN
                )
                if made:
                    created_categories += 1

                for subcategory_name in subcategory_names:
                    _, made = ClientNeedsSubcategory.objects.get_or_create(
                        name=subcategory_name, category=category
                    )
                    if made:
                        created_subcategories += 1

        if created_categories or created_subcategories:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Seeded {created_categories} Client Needs category(ies) and "
                    f"{created_subcategories} subcategory(ies)."
                )
            )
        else:
            self.stdout.write("Client Needs taxonomy already seeded — nothing to do.")
