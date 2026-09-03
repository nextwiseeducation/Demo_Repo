from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

# Top-level URL table. Everything the API exposes is namespaced under
# /api/<app>/ and delegates to that app's own urls.py — this file only
# decides the top-level prefixes, not individual endpoint paths.
urlpatterns = [
    # Django admin — the interim staff UI (content-team question entry is
    # Milestone 2's custom admin work).
    path("admin/", admin.site.urls),
    # register/login/logout/verify-email/password-reset/me
    path("api/auth/", include("apps.accounts.urls")),
    # Stripe webhook endpoint (stubbed, Phase 2).
    path("api/payments/", include("apps.payments.urls")),
    # End-of-quiz survey + per-question issue reports.
    path("api/feedback/", include("apps.feedback.urls")),
    # Minimal read + grade endpoints so the quiz UI can use real content;
    # full filtering/search is still Milestone 2/3 scope.
    path("api/questions/", include("apps.questions.urls")),
    # Real quiz-session creation/answering, live facet counts, bookmarks.
    path("api/quizzes/", include("apps.quizzes.urls")),
    # apps.taxonomy has no urls.py of its own yet — every taxonomy value the
    # frontend needs (Domain/NursingSystem/ClientNeedsSubcategory ids+names)
    # is exposed via apps.quizzes' facet-counts endpoint instead, so a
    # separate read API for these models isn't needed yet.
    #
    # The custom admin dashboard (role-gated: analytics, content
    # management, bulk import, feedback triage). "api/admin/" does not
    # collide with "admin/" above — that's the Django admin *site*, this is
    # a JSON API namespace — but it reads like a typo, hence this note.
    path("api/admin/", include("apps.admin_api.urls")),
]

if settings.DEBUG:
    # Lets Django's dev server serve uploaded files (Question.image) directly
    # from MEDIA_ROOT when running locally. Never added in production — a
    # real deployment needs a proper file host (e.g. S3) in front of
    # MEDIA_URL, since Django serving media files itself doesn't scale and
    # Render's disk isn't persistent across deploys.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
