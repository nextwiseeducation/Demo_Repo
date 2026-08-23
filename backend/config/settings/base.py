"""
Base settings shared by local.py and production.py.

Values that differ between environments (or are secret) come from the
environment / .env file via django-environ — see .env.example for the
full list of variables this project reads.
"""

from pathlib import Path

# django-environ — reads typed values (str/bool/int/list/db-url) out of
# environment variables or a .env file, instead of hardcoding secrets or
# per-environment config directly in this file. This is what lets
# SECRET_KEY, DATABASE_URL, and API keys live in Render's environment
# variable dashboard in production and in a local .env file in dev, with
# the exact same settings code reading both.
import environ

# Three .parent calls walk up from this file (config/settings/base.py) to
# config/settings -> config -> the repo's backend/ root, so BASE_DIR always
# points at backend/ regardless of where the process is launched from.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
# Loads backend/.env into the process environment if the file exists (it
# won't in production, where Render injects real environment variables
# directly) — read_env() is a no-op if the path doesn't exist.
environ.Env.read_env(BASE_DIR / ".env")

# No default here on purpose: if SECRET_KEY isn't set, env() raises
# immediately on startup rather than silently booting with an empty/guessable
# key. Required in every environment, including local dev.
SECRET_KEY = env("SECRET_KEY")

# Defaults to False (production-safe default) so DEBUG must be explicitly
# opted into — local.py hardcodes DEBUG = True for dev instead of relying on
# this env var, so this default really only protects production/staging.
DEBUG = env.bool("DEBUG", default=False)

# Empty by default (Django would then reject every Host header) — each
# environment supplies its own list; local.py hardcodes localhost/127.0.0.1.
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

# Used to build links in emails (verification, password reset) that point
# at the React frontend rather than the API itself, and (below) to tell
# CORS which browser origin is allowed to call this API.
FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:5173")


INSTALLED_APPS = [
    # --- Django built-ins ---
    "django.contrib.admin",  # /admin/ site, used as the interim staff UI (see CLAUDE.md — admin.py customization is Milestone 2)
    "django.contrib.auth",  # provides PermissionsMixin/permission machinery our custom User model builds on, plus password hashing/validation
    "django.contrib.contenttypes",  # required by auth's permission system (Permission rows reference a ContentType)
    "django.contrib.sessions",  # backs Django admin's login sessions (the API itself is stateless/JWT — this is admin-only)
    "django.contrib.messages",  # one-time flash messages, required by the admin UI
    "django.contrib.staticfiles",  # collects/serves admin CSS/JS and any app static assets; whitenoise serves what it collects
    # --- Third-party ---
    "corsheaders",  # lets the browser-hosted React frontend (a different Render origin in staging/prod) call this API at all — without it, the browser blocks every cross-origin fetch before it reaches Django. Not needed in local dev, where Vite's proxy (vite.config.ts) makes requests same-origin instead.
    "rest_framework",  # Django REST Framework — turns Django into a JSON API (serializers, viewsets, browsable API)
    "rest_framework_simplejwt.token_blacklist",  # stores blacklisted refresh tokens in the DB; required because SIMPLE_JWT below has BLACKLIST_AFTER_ROTATION=True (logout/rotation needs somewhere to record "this token is now dead")
    "anymail",  # provider-agnostic transactional email backend; lets EMAIL_BACKEND point at SendGrid in prod without SendGrid-specific code elsewhere (see the Email section below)
    # --- Local apps (see apps/<name>/models.py for what each owns) ---
    "apps.core",  # no models of its own yet; home for cross-app abstractions like the UUID-PK/timestamp mixins other apps' models inherit from
    "apps.accounts",  # custom User model, registration/auth/JWT views
    "apps.taxonomy",  # NursingSystem/Topic/Subtopic/ClientNeeds/Tag/CaseStudy — the classification schema questions are tagged against
    "apps.questions",  # Question, AnswerChoice, and the NGN-item-type stub models (Matrix, Bow-Tie, Cloze, etc.)
    "apps.quizzes",  # QuizSession + StudentResponseLog — quiz-taking and the per-answer log Phase 2's AI features will read
    "apps.payments",  # SubscriptionPlan/UserSubscription — Stripe-shaped tables, stubbed and unused until Phase 2
    "apps.feedback",  # QuizFeedback + QuestionIssueReport — end-of-quiz survey and per-question "Report an Issue" flags
]

# Order matters: each request passes down through this list top-to-bottom,
# then the response passes back up bottom-to-top.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",  # HTTPS/HSTS-related headers; several of its behaviors are toggled on in production.py
    "whitenoise.middleware.WhiteNoiseMiddleware",  # serves collected static files directly from the Django/gunicorn process on Render, no separate static file host needed — must sit right after SecurityMiddleware per whitenoise's own docs
    "corsheaders.middleware.CorsMiddleware",  # must sit as high as practical, and specifically before CommonMiddleware, per django-cors-headers' own docs — it needs to attach CORS headers to a request/response before other middleware can short-circuit it
    "django.contrib.sessions.middleware.SessionMiddleware",  # attaches request.session; needed for Django admin login, not used by the JWT API itself
    "django.middleware.common.CommonMiddleware",  # misc conveniences (e.g. APPEND_SLASH)
    "django.middleware.csrf.CsrfViewMiddleware",  # CSRF protection for session-authenticated (cookie-based) requests — i.e. the admin site; the JWT API is exempt in practice since it doesn't use cookies
    "django.contrib.auth.middleware.AuthenticationMiddleware",  # attaches request.user for session-based auth (admin); DRF's JWTAuthentication (see REST_FRAMEWORK below) is what sets request.user for API calls
    "django.contrib.messages.middleware.MessageMiddleware",  # backs django.contrib.messages, used by the admin UI
    "django.middleware.clickjacking.XFrameOptionsMiddleware",  # sends X-Frame-Options to stop the admin site being iframed
]

# Points Django at config/urls.py as the top-level URL dispatch table.
ROOT_URLCONF = "config.urls"

# Only needed because django.contrib.admin renders server-side templates;
# the React frontend never touches this — it only talks to the JSON API.
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
# env.db() parses a single DATABASE_URL string (e.g.
# postgres://user:pass@host:port/dbname) into Django's DATABASES dict shape.
# Render injects this automatically when the web service is linked to the
# managed Postgres instance; locally it comes from .env pointing at the
# user-owned dev Postgres cluster.
DATABASES = {
    "default": env.db("DATABASE_URL"),
}

# Tells Django to use apps.accounts.models.User (email-based, UUID PK)
# instead of the default django.contrib.auth.models.User (username-based,
# integer PK). Must be set before the first migration ever runs — changing
# it later on a live database is a full data migration, not a settings edit.
AUTH_USER_MODEL = "accounts.User"

# Standard Django password strength rules, applied wherever a password is
# set via Django's forms/serializers that call validate_password() —
# registration and password reset both go through this.
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},  # rejects passwords too similar to the user's email/name
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},  # default minimum length is 8
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},  # rejects the ~20,000 most common passwords
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},  # rejects all-digit passwords
]


# Internationalization — not actively used (no i18n content yet) but left at
# Django's own defaults rather than removed, since USE_TZ especially affects
# how every DateTimeField (created_at, current_period_end, etc.) is stored.
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True  # store all datetimes in UTC in the DB; convert to local time only at display time — avoids DST/timezone bugs across environments


# Static files (admin CSS/JS, etc.)
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"  # `collectstatic` gathers every app's static files here; whitenoise serves from this directory
STORAGES = {
    "staticfiles": {
        # Adds a content hash to each filename (cache-busting) and gzip/brotli
        # compresses files at collectstatic time, so whitenoise can serve them
        # with long-lived cache headers safely.
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# User-uploaded files (Question.image). Served by Django itself only when
# DEBUG=True (see config/urls.py) — production would need a real object
# store (e.g. S3) in front of this before question images go live, since
# Render's filesystem isn't persistent/shared across dynos.
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Modern Django default for auto-generated model PKs (BigAutoField instead
# of the older 32-bit AutoField). Doesn't affect this project's models
# directly since every app model here uses an explicit UUID PK mixin
# instead of relying on Django's implicit `id` field — set anyway to
# silence Django's "no default configured" system-check warning.
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Django REST Framework — global API behavior. Individual views/serializers
# can still override these per-endpoint (e.g. AllowAny on registration).
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        # Reads the "Authorization: Bearer <access_token>" header and
        # attaches the corresponding User to request.user. This is what
        # actually authenticates API calls — AuthenticationMiddleware above
        # only covers session/cookie-based auth (the admin site).
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        # Locks every endpoint down by default; individual views (register,
        # login, password reset — anything reachable while logged out) must
        # explicitly opt out with permission_classes = [AllowAny]. Safer
        # default than the alternative of forgetting to lock down a new view.
        "rest_framework.permissions.IsAuthenticated",
    ),
    # Per-view rate limits (via ScopedRateThrottle, set on the auth views
    # that are reachable without being logged in) — keyed by IP for
    # anonymous requests. Prevents mass account creation, login
    # brute-forcing, and using password-reset to spam arbitrary addresses.
    # A view opts into one of these buckets by setting
    # `throttle_scope = "<key>"`, e.g. LoginView uses "login".
    "DEFAULT_THROTTLE_RATES": {
        "register": "5/hour",
        "login": "10/min",
        "password_reset": "5/hour",
        "password_reset_confirm": "10/hour",
    },
}

# Imported here rather than at the top of the file: timedelta is only
# needed for the SIMPLE_JWT block immediately below, and keeping it local
# to where it's used avoids polluting the module namespace / `from .base
# import *` wildcard imports in local.py and production.py with an unrelated
# stdlib symbol. The `# noqa: E402` silences the "import not at top of file"
# lint warning this deliberately triggers.
from datetime import timedelta  # noqa: E402

# djangorestframework-simplejwt configuration — see
# apps/accounts/views.py (LoginView, LogoutView) for how rotation and
# blacklisting are actually exercised.
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),  # short-lived; sent on every API request, so a leaked access token is only useful for 30 minutes
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),  # long-lived; stored client-side to silently obtain new access tokens without re-login ("stay logged in" for 2 weeks)
    "ROTATE_REFRESH_TOKENS": True,  # every refresh call issues a brand-new refresh token instead of reusing the same one — limits how long a stolen refresh token stays valid
    "BLACKLIST_AFTER_ROTATION": True,  # the old refresh token is invalidated the moment it's used to rotate — requires the token_blacklist app (INSTALLED_APPS above) to store the blacklist; also what makes logout actually revoke a refresh token rather than just discarding it client-side
}


# CORS — which browser origins may call this API cross-origin. In local
# dev this setting exists but is never exercised (Vite's proxy makes
# browser requests same-origin instead); in staging/prod the React app is
# deployed as a separate Render static site with its own origin, so
# without this, the browser would block every request before it left the
# frontend.
#
# A separate, explicit list rather than just [FRONTEND_URL]: FRONTEND_URL
# is the one canonical URL used to build email links, but CORS sometimes
# needs to trust more than one origin at once — e.g. both a custom domain
# and the original *.onrender.com URL during DNS cutover, so the site
# doesn't break for anyone still on the old link while DNS propagates.
# Defaults to just FRONTEND_URL when this isn't set separately.
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[FRONTEND_URL])


# Email — SendGrid via Anymail. EMAIL_BACKEND itself is set per-environment
# (console in local.py, Anymail's SendGrid backend in production.py) so
# local dev never needs a real API key.
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="no-reply@nextwiseeducation.com")
ANYMAIL = {
    "SENDGRID_API_KEY": env("SENDGRID_API_KEY", default=""),
}

# Stripe (Phase 2 — stubbed webhook endpoint only, no active integration yet)
# Will be used to verify the signature on incoming Stripe webhook POSTs once
# apps/payments/views.py actually processes events instead of just
# returning 200. Blank default so Phase 1 never needs a real Stripe account.
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET", default="")
