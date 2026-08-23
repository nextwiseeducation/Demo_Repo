import uuid

from django.db import models


class UUIDPKMixin(models.Model):
    """Abstract base for models keyed by UUID instead of an auto-increment int."""

    # Why UUID instead of Django's default integer id:
    # - Question/response/session IDs are referenced in URLs and (later)
    #   client-side state/API payloads; sequential integers leak how many
    #   rows exist and make IDs guessable (e.g. iterate question_id=1..4000).
    # - UUIDs can be generated client-side or by any service before an
    #   INSERT happens, which matters once there's more than one thing
    #   writing data (e.g. a future import pipeline, or Phase 2 services).
    # - CLAUDE.md's schema spec explicitly calls out UUID PKs for
    #   Question/AnswerChoice/QuizSession/StudentResponseLog.
    # default=uuid.uuid4 (not uuid.uuid4(), no parentheses) — passing the
    # function itself means Django calls it fresh at row-creation time,
    # generating a new UUID per row; calling it here would generate ONE uuid
    # at class-definition time and reuse it as the default for every row.
    # editable=False hides it from admin/forms — it's never meant to be
    # hand-entered or changed after creation.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        # abstract=True means Django does NOT create a database table for
        # UUIDPKMixin itself — it only exists to be inherited. Any model
        # that subclasses it gets its own table with an `id` column defined
        # exactly as above, as if the field had been written directly on
        # that model.
        abstract = True


class TimeStampedMixin(models.Model):
    """Abstract base adding created_at/updated_at to any model."""

    # auto_now_add=True: set once, automatically, the moment the row is
    # first created (INSERT) — never updated again after that, even if the
    # row is saved again later. Not editable via admin/forms.
    created_at = models.DateTimeField(auto_now_add=True)
    # auto_now=True: overwritten automatically on every single .save() call,
    # not just creation — always reflects "last modified at". Also not
    # editable via admin/forms (both fields are effectively read-only and
    # maintained entirely by Django, not application code).
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Same as above: this class produces no table of its own. Models
        # across the project (Question, User, QuizSession, etc.) inherit
        # from this alongside UUIDPKMixin to get both an id and
        # created_at/updated_at for free, consistently, without repeating
        # the field definitions in every app.
        abstract = True
