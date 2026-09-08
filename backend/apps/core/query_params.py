"""
Shared parsing for filter query params, used by both apps.quizzes (student
quiz-setup filters) and apps.admin_api (content-team question list filters)
so the two can't quietly diverge on what counts as a valid id — they
previously each carried their own copy with different validation.
"""


def parse_int_csv(values: list[str]) -> list[int]:
    """
    Filters a list of raw query-param strings down to valid non-negative
    integers, silently dropping anything that isn't one — every id in this
    schema is a plain positive-starting AutoField, so this never needs to
    accept a negative value. Matches the "unrecognized input narrows,
    never widens or errors" convention used for filter query params
    throughout this project.
    """
    return [int(v) for v in values if v.strip().isdigit()]


def filter_id_in(qs, field: str, ids: list[int]):
    """
    `qs.filter(**{f"{field}_id__in": ids})`, skipped entirely when `ids` is
    empty (an empty __in filters everything out, not "no filter" — every
    caller here wants the latter). Shared by apps.quizzes.services.
    apply_taxonomy_filters (student quiz-setup filtering) and
    apps.admin_api.services.question_filters (content-team question list
    filtering) specifically for the taxonomy dimensions the two overlap
    on today (nursing_system) — expressing it once means a dimension
    either side adds later is filtered the same way by construction,
    instead of being one more hand-written `.filter(..._id__in=...)` that
    could drift from the other side's version.
    """
    if not ids:
        return qs
    return qs.filter(**{f"{field}_id__in": ids})
