"""
Faceted question-pool logic shared by quiz-setup's live counts and actual
quiz-session creation.

Kept as module-level functions (mirroring apps.questions.services' own
reasoning) so the two callers below can never quietly drift apart:

  - QuizFacetCountsView, which needs "how many questions match X" for every
    checkbox on the setup page, live, as other checkboxes change;
  - QuizSessionCreateView, which needs the actual matching Question rows to
    draw a real quiz from.

Both go through apply_taxonomy_filters — the ONE place the filter rules are
expressed — so a rule added there is guaranteed to affect both the count
shown to the student and the pool the quiz is actually drawn from.
"""

from django.db.models import (
    BooleanField,
    Case,
    CharField,
    Count,
    Exists,
    OuterRef,
    Q,
    QuerySet,
    Subquery,
    Value,
    When,
)

from apps.questions.models import Question, QuestionType
from apps.taxonomy.models import ClientNeedsSubcategory, Domain, ExamType, NursingSystem

from .models import Bookmark, QuizSession, StudentResponseLog

# UWorld's "Traditional" vs "Next Gen" split, mapped onto our QuestionType
# enum. Matches the SUPPORTED_QUESTION_TYPES split the frontend already
# uses (MCQ/SATA render today; everything else is an NGN stub) with EMR
# folded in on the Traditional side — it's AnswerChoice-based like MCQ/SATA,
# not one of the NGN structural types.
TRADITIONAL_TYPES = [QuestionType.MCQ, QuestionType.SATA, QuestionType.EMR]
NGN_TYPES = [
    QuestionType.MATRIX,
    QuestionType.BOWTIE,
    QuestionType.DRAG_DROP,
    QuestionType.CLOZE,
    QuestionType.HOTSPOT,
    QuestionType.NGN_CASE,
]

# The 4 mutually-exclusive Question Mode buckets that make up status_bucket
# (Marked is deliberately NOT one of these — see annotate_student_status).
STATUS_BUCKETS = ["UNUSED", "INCORRECT", "OMITTED", "CORRECT"]

# Every dimension apply_taxonomy_filters knows how to apply/exclude. Named
# here once so compute_facet_counts and resolve_question_queryset can't
# typo a dimension name differently from each other.
FACET_DIMENSIONS = frozenset(
    {"question_types", "status_filters", "domains", "nursing_systems", "nclex_client_needs_subcategories"}
)


def annotate_student_status(qs: QuerySet, student) -> QuerySet:
    """
    Adds, per Question row, everything the faceted logic below needs to
    know about THIS student's relationship to that question:

      - format_bucket: "TRADITIONAL" or "NGN", derived from question_type.
      - is_marked: has this student bookmarked it (independent of
        correct/incorrect — see Bookmark's own docstring).
      - status_bucket: "UNUSED" / "INCORRECT" / "OMITTED" / "CORRECT",
        mutually exclusive, derived from the student's StudentResponseLog
        history (most recent attempt wins if answered more than once) and
        from OMITTED eligibility (see below).

    Split into two .annotate() calls because status_bucket's Case/When
    needs to reference has_response/is_omitted_eligible/latest_is_correct
    from the first call — annotations from an earlier .annotate() call are
    safe to reference in a later one, but not within the same call.
    """
    responses = StudentResponseLog.objects.filter(student=student, question=OuterRef("pk"))
    latest_response = responses.order_by("-answered_at")

    qs = qs.annotate(
        format_bucket=Case(
            When(question_type__in=TRADITIONAL_TYPES, then=Value("TRADITIONAL")),
            default=Value("NGN"),
            output_field=CharField(),
        ),
        is_marked=Exists(Bookmark.objects.filter(student=student, question=OuterRef("pk"))),
        has_response=Exists(responses),
        latest_is_correct=Subquery(latest_response.values("is_correct")[:1], output_field=BooleanField()),
        # OMITTED, precisely: no response from this student exists, but the
        # question was served as part of a quiz session this student
        # actually finished. Realistically ~0 today — the live quiz flow
        # has no skip/abandon action, only forced submit-then-next — but
        # defined correctly now so the day that action exists, no further
        # schema/query change is needed here.
        is_omitted_eligible=Exists(
            QuizSession.objects.filter(student=student, is_complete=True, questions=OuterRef("pk"))
        ),
    )
    return qs.annotate(
        status_bucket=Case(
            When(has_response=False, is_omitted_eligible=True, then=Value("OMITTED")),
            When(has_response=False, then=Value("UNUSED")),
            When(latest_is_correct=True, then=Value("CORRECT")),
            default=Value("INCORRECT"),
            output_field=CharField(),
        )
    )


def apply_taxonomy_filters(qs: QuerySet, filters: dict, *, exclude: frozenset = frozenset()) -> QuerySet:
    """
    Applies every filter dimension present in `filters`, except any named in
    `exclude` — the mechanism that makes a facet's own live count reflect
    every OTHER active filter without also filtering itself down to nothing
    (a checked "Cardiovascular" box must not make Cardiovascular's own count
    disappear).

    `qs` must already carry annotate_student_status's annotations —
    status_filters below reads status_bucket/is_marked from it.
    """
    if "question_types" not in exclude and filters.get("question_types"):
        selected_formats = filters["question_types"]
        types: list[str] = []
        if "TRADITIONAL" in selected_formats:
            types += TRADITIONAL_TYPES
        if "NGN" in selected_formats:
            types += NGN_TYPES
        qs = qs.filter(question_type__in=types)

    if "domains" not in exclude and filters.get("domains"):
        qs = qs.filter(domain_id__in=filters["domains"])

    if "nursing_systems" not in exclude and filters.get("nursing_systems"):
        qs = qs.filter(nursing_system_id__in=filters["nursing_systems"])

    if "nclex_client_needs_subcategories" not in exclude and filters.get("nclex_client_needs_subcategories"):
        qs = qs.filter(nclex_client_needs_subcategory_id__in=filters["nclex_client_needs_subcategories"])

    if "status_filters" not in exclude and filters.get("status_filters"):
        selected_statuses = filters["status_filters"]
        status_q = Q(status_bucket__in=[s for s in selected_statuses if s != "MARKED"])
        if "MARKED" in selected_statuses:
            # OR, not AND: Marked overlaps the other buckets (a question can
            # be both Incorrect and Marked) rather than being a 5th
            # mutually-exclusive state.
            status_q |= Q(is_marked=True)
        qs = qs.filter(status_q)

    return qs


def resolve_question_queryset(student, filters: dict) -> QuerySet:
    """
    The fully-filtered, annotated queryset a real quiz is drawn from.

    question_mode="STANDARD" means "unused only", overriding whatever
    status_filters was passed — the Custom tab's checkboxes are the only
    way status_filters should ever carry anything other than ["UNUSED"].
    """
    effective_filters = dict(filters)
    if filters.get("question_mode") == "STANDARD":
        effective_filters["status_filters"] = ["UNUSED"]

    qs = annotate_student_status(Question.objects.filter(is_active=True), student)
    return apply_taxonomy_filters(qs, effective_filters, exclude=frozenset())


def compute_facet_counts(student, filters: dict) -> dict:
    """
    Everything the quiz-setup page's live counts need, in 6 queries total —
    no N+1, no per-row Python loop hitting the database.

    Each facet is computed against a queryset that excludes ONLY that
    facet's own dimension (every other active filter still applies) — see
    apply_taxonomy_filters' docstring for why.
    """
    base = annotate_student_status(Question.objects.filter(is_active=True), student)

    # --- Question Type card: unused/total per format, ignoring the current
    # Question Mode selection entirely (this is UWorld's static-looking
    # "34/1983", not "matches whatever Custom boxes happen to be checked"). ---
    type_rows = apply_taxonomy_filters(base, filters, exclude=frozenset({"question_types"})).values(
        "format_bucket"
    ).annotate(unused=Count("id", filter=Q(status_bucket="UNUSED")), total=Count("id"))
    question_types = {fmt: {"unused": 0, "total": 0} for fmt in ("TRADITIONAL", "NGN")}
    for row in type_rows:
        question_types[row["format_bucket"]] = {"unused": row["unused"], "total": row["total"]}

    # --- Question Mode card: the 4 mutually-exclusive buckets in one
    # group-by, plus Marked as its own overlapping query. ---
    mode_qs = apply_taxonomy_filters(base, filters, exclude=frozenset({"status_filters"}))
    mode_rows = mode_qs.values("status_bucket").annotate(
        count=Count("id"), ngn_count=Count("id", filter=Q(format_bucket="NGN"))
    )
    question_mode = {bucket: {"count": 0, "ngn_count": 0} for bucket in STATUS_BUCKETS}
    for row in mode_rows:
        question_mode[row["status_bucket"]] = {"count": row["count"], "ngn_count": row["ngn_count"]}
    marked_totals = mode_qs.filter(is_marked=True).aggregate(
        count=Count("id"), ngn_count=Count("id", filter=Q(format_bucket="NGN"))
    )
    question_mode["MARKED"] = {
        "count": marked_totals["count"] or 0,
        "ngn_count": marked_totals["ngn_count"] or 0,
    }

    # --- Subjects / Systems / Client Needs cards: counted from the
    # taxonomy-model side (not from Question) so every value in the static
    # checklist is always present, including ones with a real 0 count right
    # now — not just values the current filters happen to already match. ---
    domains_matching = apply_taxonomy_filters(base, filters, exclude=frozenset({"domains"}))
    domains = list(
        Domain.objects.annotate(count=Count("questions", filter=Q(questions__in=domains_matching.values("pk"))))
        .values("id", "name", "count")
        .order_by("name")
    )

    systems_matching = apply_taxonomy_filters(base, filters, exclude=frozenset({"nursing_systems"}))
    nursing_systems = list(
        NursingSystem.objects.annotate(
            count=Count("questions", filter=Q(questions__in=systems_matching.values("pk")))
        )
        .values("id", "name", "count")
        .order_by("name")
    )

    needs_matching = apply_taxonomy_filters(base, filters, exclude=frozenset({"nclex_client_needs_subcategories"}))
    client_needs = list(
        ClientNeedsSubcategory.objects.filter(category__exam_type=ExamType.RN)
        .annotate(count=Count("questions", filter=Q(questions__in=needs_matching.values("pk"))))
        .values("id", "name", "count")
        .order_by("category__name", "name")
    )

    return {
        "question_types": question_types,
        "question_mode": question_mode,
        "domains": domains,
        "nursing_systems": nursing_systems,
        "nclex_client_needs_subcategories": client_needs,
    }
