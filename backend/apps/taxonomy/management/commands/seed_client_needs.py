from django.core.management.base import BaseCommand
from django.db import transaction

from apps.taxonomy.models import ClientNeedsCategory, ClientNeedsSubcategory, ExamType

# The exact wording UWorld's own live product uses for this subcategory,
# independently confirmed by the client's own Excel content batch — the
# name this command used to seed ("Safety and Infection Control") was
# simply wrong. RENAMED_SUBCATEGORIES below fixes it in place on an
# existing database rather than via the RN_CLIENT_NEEDS dict alone, so
# Question rows already pointing at the old name keep their FK intact
# instead of becoming orphaned by a get_or_create that only ever creates.
RENAMED_SUBCATEGORIES = {
    ("Safe and Effective Care Environment", "Safety and Infection Control"): (
        "Safety and Infection Prevention and Control"
    ),
}

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
# Health Promotion and Maintenance and Psychosocial Integrity each get
# THEMSELVES as their own single subcategory below, rather than an empty
# list. NCSBN genuinely does not subdivide either category further, but
# Question.nclex_client_needs_subcategory is a required FK — this was the
# open NEEDS_REVIEW question from the first content batch (CLAUDE.md,
# "Questions Pending from Content Team" #4), and it's now resolved: UWorld's
# own live product (and the client's own Excel content batch) both use
# exactly this self-naming convention as their filterable "subcategory" for
# these two categories, confirmed independently of each other.
RN_CLIENT_NEEDS = {
    "Safe and Effective Care Environment": [
        "Management of Care",
        "Safety and Infection Prevention and Control",
    ],
    "Health Promotion and Maintenance": ["Health Promotion and Maintenance"],
    "Psychosocial Integrity": ["Psychosocial Integrity"],
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
        renamed_subcategories = 0

        # One transaction for the whole seed: a partially-seeded taxonomy is
        # worse than an unseeded one, because the importer would then accept
        # some rows and reject others for no reason an editor could see.
        with transaction.atomic():
            # Rename existing rows BEFORE the get_or_create loop below, so a
            # database that already has the old "Safety and Infection
            # Control" row gets renamed in place (preserving every Question
            # FK pointing at it) rather than the loop creating a second,
            # differently-named row alongside it. filter().update() is a
            # no-op (0 rows matched) once already renamed, so this stays
            # safe to re-run on every deploy like the rest of the command.
            for (category_name, old_name), new_name in RENAMED_SUBCATEGORIES.items():
                renamed_subcategories += ClientNeedsSubcategory.objects.filter(
                    name=old_name,
                    category__name=category_name,
                    category__exam_type=ExamType.RN,
                ).update(name=new_name)

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

        if renamed_subcategories:
            self.stdout.write(self.style.SUCCESS(f"Renamed {renamed_subcategories} subcategory(ies)."))
        if created_categories or created_subcategories:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Seeded {created_categories} Client Needs category(ies) and "
                    f"{created_subcategories} subcategory(ies)."
                )
            )
        if not (renamed_subcategories or created_categories or created_subcategories):
            self.stdout.write("Client Needs taxonomy already seeded — nothing to do.")
