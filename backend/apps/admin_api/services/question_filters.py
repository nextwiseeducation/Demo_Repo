"""
Hand-rolled query-param filtering for the Content Team question table, in
the same style as apps.quizzes.views._parse_facet_query_params — this
project has no django-filter dependency, and five filterable fields plus a
search box is not enough machinery to justify adding one.

Every filter is an explicit whitelist: an unrecognized query param is
silently ignored rather than raising, so a typo in a param name can never
accidentally widen the queryset instead of narrowing it.
"""

from apps.questions.models import ClinicalJudgmentSkill, Difficulty, QuestionType


def _int_list(raw: str) -> list[int]:
    return [int(v) for v in raw.split(",") if v.strip().isdigit()]


def apply_admin_question_filters(queryset, params):
    """params is anything supporting .get(key, default) — a QueryDict in production, a plain dict in tests."""
    if question_type := params.get("question_type"):
        valid = {v for v, _ in QuestionType.choices}
        queryset = queryset.filter(question_type__in=[v for v in question_type.split(",") if v in valid])

    if nursing_system := params.get("nursing_system"):
        queryset = queryset.filter(nursing_system_id__in=_int_list(nursing_system))

    if difficulty := params.get("difficulty"):
        valid = {v for v, _ in Difficulty.choices}
        queryset = queryset.filter(difficulty__in=[v for v in difficulty.split(",") if v in valid])

    if (is_active := params.get("is_active")) is not None and is_active != "":
        queryset = queryset.filter(is_active=is_active.lower() in ("true", "1"))

    if clinical_judgment_skill := params.get("clinical_judgment_skill"):
        valid = {v for v, _ in ClinicalJudgmentSkill.choices}
        queryset = queryset.filter(
            clinical_judgment_skill__in=[v for v in clinical_judgment_skill.split(",") if v in valid]
        )

    if search := params.get("search", "").strip():
        queryset = queryset.filter(stem__icontains=search)

    return queryset
