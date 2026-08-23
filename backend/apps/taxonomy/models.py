from django.db import models

# Note: unlike apps.core's mixins used elsewhere in the project, these
# taxonomy models use Django's default auto-increment integer PK (no
# UUIDPKMixin) and have no created_at/updated_at (no TimeStampedMixin).
# That's a deliberate difference from Question/User/etc: taxonomy rows are
# reference/lookup data (a few dozen–hundred rows, admin-managed, referenced
# by ForeignKey from many questions) rather than user-facing or
# externally-referenced entities, so the UUID/audit-trail properties those
# other models need don't apply here.


class NursingSystem(models.Model):
    """
    Body-system grouping (Cardiovascular, Respiratory, ...) used for
    student-facing filtering. Not part of the official NCSBN test plan —
    NCSBN organizes the exam around Client Needs categories, not body
    systems — this taxonomy is ours to define. See
    CLIENT_QUESTIONS_taxonomy_and_weighting.md: the actual list of systems
    is still pending client confirmation, so only the schema is built now.
    """

    # unique=True: prevents "Cardiovascular" from being accidentally
    # created twice via the admin — this is a flat, top-level list (unlike
    # Topic/Subtopic below, whose uniqueness only needs to hold within
    # their parent).
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        # Alphabetical everywhere this model is listed (admin dropdowns,
        # any future API) rather than insertion order, which would be
        # meaningless to a content editor or student.
        ordering = ["name"]

    def __str__(self):
        # Controls how this row displays in the admin (dropdowns, list
        # pages, breadcrumbs) and anywhere else Django renders a model
        # instance as text.
        return self.name


class Topic(models.Model):
    # on_delete=CASCADE: deleting a NursingSystem deletes all its Topics too
    # (and transitively, per Subtopic below, their Subtopics) — acceptable
    # here since a system with no topics under it is meaningless, and
    # taxonomy deletion is a rare, deliberate admin action, not something
    # that happens as a side effect of normal use.
    # related_name="topics" is what enables nursing_system.topics.all()
    # from the NursingSystem side.
    nursing_system = models.ForeignKey(NursingSystem, on_delete=models.CASCADE, related_name="topics")
    name = models.CharField(max_length=150)

    class Meta:
        # Sort by parent system name first, then topic name within each
        # system — keeps a flat admin list visually grouped by system even
        # without actual UI grouping.
        ordering = ["nursing_system__name", "name"]
        # Unlike NursingSystem.name (globally unique), Topic names only need
        # to be unique WITHIN a given system — "Assessment" could
        # legitimately exist as a topic under both Cardiovascular and
        # Respiratory.
        unique_together = ("nursing_system", "name")

    def __str__(self):
        # "System / Topic" format makes this topic identifiable on its own
        # (e.g. in a flat admin dropdown) without needing to see it nested
        # under its parent.
        return f"{self.nursing_system} / {self.name}"


class Subtopic(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="subtopics")
    name = models.CharField(max_length=150)

    class Meta:
        ordering = ["topic__name", "name"]
        # Same reasoning as Topic above, one level deeper: unique within
        # its parent Topic, not globally.
        unique_together = ("topic", "name")

    def __str__(self):
        # __str__ on Topic already includes the system name, so this ends
        # up rendering as "System / Topic / Subtopic" — a fully qualified
        # path in a single string.
        return f"{self.topic} / {self.name}"


class ExamType(models.TextChoices):
    RN = "RN", "NCLEX-RN"
    PN = "PN", "NCLEX-PN"


class ClientNeedsCategory(models.Model):
    """
    Official NCSBN Client Needs category. exam_type isn't in the original
    brief's field list — it's the hedge CLIENT_QUESTIONS_taxonomy_and_weighting.md
    recommends: RN and PN use different category names/weights (e.g. RN's
    "Management of Care" vs PN's "Coordinated Care"), so this field lets PN
    categories be added later without a migration, even though only RN rows
    are seeded for Phase 1.
    """

    # No unique=True on name alone — see unique_together below, which
    # constrains the (name, exam_type) pair instead, specifically so RN and
    # PN can each have their own "Management of Care"-equivalent category
    # without colliding.
    name = models.CharField(max_length=150)
    exam_type = models.CharField(max_length=2, choices=ExamType.choices, default=ExamType.RN)

    class Meta:
        # Without this, Django's admin would pluralize "Client Needs
        # category" as "Client Needs categorys" — this overrides that to
        # the grammatically correct plural.
        verbose_name_plural = "Client Needs categories"
        # The actual "RN and PN can reuse the same category name" rule,
        # enforced at the database level, not just convention.
        unique_together = ("name", "exam_type")
        ordering = ["exam_type", "name"]

    def __str__(self):
        return f"{self.name} ({self.exam_type})"


class ClientNeedsSubcategory(models.Model):
    category = models.ForeignKey(ClientNeedsCategory, on_delete=models.CASCADE, related_name="subcategories")
    name = models.CharField(max_length=150)

    class Meta:
        verbose_name_plural = "Client Needs subcategories"
        # Unique within its parent category (which itself is already
        # unique per exam type), so this transitively also can't collide
        # across RN/PN.
        unique_together = ("category", "name")
        ordering = ["category__name", "name"]

    def __str__(self):
        return f"{self.category} / {self.name}"


class Tag(models.Model):
    """
    Free-form labels (ManyToMany from Question) for cross-cutting
    concerns that don't fit the strict system/topic/Client-Needs hierarchy
    — e.g. "pediatric", "med-math", "prioritization" — anything an editor
    wants to filter/group by without it being a formal taxonomy axis.
    """

    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class CaseStudy(models.Model):
    """Shared clinical scenario linking a set of sequenced NGN Case Study questions."""

    title = models.CharField(max_length=255)
    # TextField (not CharField): the scenario is a multi-paragraph clinical
    # vignette, not a short label — no practical length cap makes sense.
    # Referenced from Question via case_study_id + case_study_sequence
    # (apps/questions/models.py), which is how a single CaseStudy row ends
    # up backing multiple ordered Question rows that all share this text.
    shared_scenario = models.TextField()

    def __str__(self):
        return self.title
