import uuid

from django.db import models


class UUIDPKMixin(models.Model):
    """Abstract base for models keyed by UUID instead of an auto-increment int."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimeStampedMixin(models.Model):
    """Abstract base adding created_at/updated_at to any model."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
