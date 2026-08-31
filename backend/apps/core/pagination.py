from rest_framework.pagination import PageNumberPagination


class DefaultPagination(PageNumberPagination):
    """
    Project-wide default paging for every DRF list endpoint.

    Wired in as REST_FRAMEWORK["DEFAULT_PAGINATION_CLASS"]
    (config/settings/base.py) rather than set per-view, so a list endpoint
    added later is paginated by default instead of only when someone
    remembers to opt in. That default matters here specifically: the
    question bank is specced at 4,000+ rows immediately (CLAUDE.md), and
    each Question serializes its stem, clinical scenario, and every answer
    choice — an unpaginated list response would be multi-megabyte.

    Lives in apps.core (alongside the shared model mixins) because it is a
    cross-app concern, not something apps.questions owns.
    """

    # Large enough that a typical quiz-builder screen fills in one request,
    # small enough that the response stays well under a megabyte.
    page_size = 50
    # Lets the frontend ask for a bigger page (e.g. a filter dropdown that
    # genuinely wants a lot of rows at once) without needing a separate
    # endpoint...
    page_size_query_param = "page_size"
    # ...but caps how far that can be pushed, so a caller can't reintroduce
    # the unpaginated-response problem by passing page_size=100000.
    max_page_size = 200
