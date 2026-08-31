from django.core.management.base import BaseCommand
from django.db import transaction

from apps.taxonomy.models import NursingSystem

# UWorld's "Systems" facet — flat, 39 values, mixing real body systems
# (Cardiovascular, Respiratory, ...) with process/skill buckets
# (Assignment/Delegation, Communication, Prioritization, ...). Verbatim from
# the client's own UWorld reference export.
NURSING_SYSTEMS = [
    "Agents to Treat Gout",
    "Analgesics",
    "Antepartum",
    "Assignment/Delegation",
    "Basic Care & Comfort",
    "Cardiovascular",
    "Clinical Judgement in Nursing",
    "Communication",
    "Development Throughout the Life Span",
    "Elimination",
    "Emergency Care",
    "Endocrine",
    "Ethical/Legal",
    "Fluid, Electrolyte, Acid-Base Balance",
    "Gastrointestinal/Nutrition",
    "Growth & Development",
    "Hematological/Oncological",
    "Immune",
    "Infectious Disease",
    "Integumentary",
    "Labor/Delivery",
    "Leadership & Management",
    "Management Concepts",
    "Medication Administration",
    "Mental Health Concepts",
    "Musculoskeletal",
    "Neurologic",
    "Newborn",
    "Perioperative Nursing",
    "Postpartum",
    "Prioritization",
    "Psychiatric Medications",
    "Reproductive",
    "Respiratory",
    "Safety/Infection Control",
    "Safety/Infection Control Skills and Procedures",
    "Skills/Procedures",
    "Urinary/Renal",
    "Visual/Auditory",
]


class Command(BaseCommand):
    """
    Seeds the NursingSystem ("Systems") taxonomy confirmed against the
    client's UWorld reference export.

    Additive only (get_or_create, no rename step) — deliberately, unlike
    seed_client_needs.py's rename fix. The 9 questions already imported use
    ad-hoc NursingSystem values ("Endocrine and Reproductive", "Healthcare
    Management and Law") that don't cleanly match this canonical list
    ("Respiratory" is an exact match already and needs no action). This
    command will NOT guess a mapping for the other two — same rule this
    project applies everywhere else taxonomy is involved (see
    import_choice_based_questions.py's _resolve_client_needs: official/
    canonical categories are never auto-created or auto-remapped from a
    fuzzy match). Reassigning those questions to the correct canonical
    NursingSystem, once one is picked, is a manual admin task — the old
    ad-hoc rows are left in place alongside the new canonical ones rather
    than silently merged or deleted.
    """

    help = "Creates the NursingSystem ('Systems') taxonomy values if they don't exist."

    def handle(self, *args, **options):
        created = 0
        with transaction.atomic():
            for name in NURSING_SYSTEMS:
                _, made = NursingSystem.objects.get_or_create(name=name)
                if made:
                    created += 1

        if created:
            self.stdout.write(self.style.SUCCESS(f"Seeded {created} NursingSystem(s)."))
        else:
            self.stdout.write("NursingSystem taxonomy already seeded — nothing to do.")
