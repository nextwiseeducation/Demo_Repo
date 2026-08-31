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
    # apps.taxonomy / apps.quizzes have no urls.py yet — their models are
    # complete (Milestone 1 scope) but the REST endpoints to read/write them
    # are Milestone 2/3 scope, so nothing is wired here.
]

if settings.DEBUG:
    # Lets Django's dev server serve uploaded files (Question.image) directly
    # from MEDIA_ROOT when running locally. Never added in production — a
    # real deployment needs a proper file host (e.g. S3) in front of
    # MEDIA_URL, since Django serving media files itself doesn't scale and
    # Render's disk isn't persistent across deploys.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
