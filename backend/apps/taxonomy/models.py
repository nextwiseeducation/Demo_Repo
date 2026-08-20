from django.db import models


class NursingSystem(models.Model):
    """
    Body-system grouping (Cardiovascular, Respiratory, ...) used for
    student-facing filtering. Not part of the official NCSBN test plan —
    NCSBN organizes the exam around Client Needs categories, not body
    systems — this taxonomy is ours to define. See
    CLIENT_QUESTIONS_taxonomy_and_weighting.md: the actual list of systems
    is still pending client confirmation, so only the schema is built now.
    """

    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Topic(models.Model):
    nursing_system = models.ForeignKey(NursingSystem, on_delete=models.CASCADE, related_name="topics")
    name = models.CharField(max_length=150)

    class Meta:
        ordering = ["nursing_system__name", "name"]
        unique_together = ("nursing_system", "name")

    def __str__(self):
        return f"{self.nursing_system} / {self.name}"


class Subtopic(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="subtopics")
    name = models.CharField(max_length=150)

    class Meta:
        ordering = ["topic__name", "name"]
        unique_together = ("topic", "name")

    def __str__(self):
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

    name = models.CharField(max_length=150)
    exam_type = models.CharField(max_length=2, choices=ExamType.choices, default=ExamType.RN)

    class Meta:
        verbose_name_plural = "Client Needs categories"
        unique_together = ("name", "exam_type")
        ordering = ["exam_type", "name"]

    def __str__(self):
        return f"{self.name} ({self.exam_type})"


class ClientNeedsSubcategory(models.Model):
    category = models.ForeignKey(ClientNeedsCategory, on_delete=models.CASCADE, related_name="subcategories")
    name = models.CharField(max_length=150)

    class Meta:
        verbose_name_plural = "Client Needs subcategories"
        unique_together = ("category", "name")
        ordering = ["category__name", "name"]

    def __str__(self):
        return f"{self.category} / {self.name}"


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class CaseStudy(models.Model):
    """Shared clinical scenario linking a set of sequenced NGN Case Study questions."""

    title = models.CharField(max_length=255)
    shared_scenario = models.TextField()

    def __str__(self):
        return self.title
