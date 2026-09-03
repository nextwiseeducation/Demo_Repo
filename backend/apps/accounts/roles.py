"""
Role backfill logic, kept in its own module (rather than inline in a
migration) so it is directly unit-testable without a migration executor.

Deliberately hardcodes the role string values instead of importing
UserRole: migrations must never depend on application code that can change
shape later (e.g. an enum rename) without that change silently rewriting
history. This module is imported both by
accounts/migrations/0005_backfill_user_roles.py (via apps.get_model) and by
tests.
"""


def backfill_roles(user_model) -> None:
    """
    One-time backfill from the pre-existing is_staff/is_superuser flags to
    the new role field, run once by migration 0005 immediately after 0004
    adds the column (which defaults every row to "STUDENT").
    """
    user_model.objects.filter(is_superuser=True).update(role="SUPERUSER")
    user_model.objects.filter(is_superuser=False, is_staff=True).update(role="CONTENT_ADMIN")
    # Everyone else already has role="STUDENT" from the 0004 column default
    # — no UPDATE needed for that case.
