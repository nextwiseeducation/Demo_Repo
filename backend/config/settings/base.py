"""
Base settings shared by local.py and production.py.

Values that differ between environments (or are secret) come from the
environment / .env file via django-environ — see .env.example for the
full list of variables this project reads.
"""

from datetime import timedelta
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
    # /admin/ site, used as the interim staff UI (see CLAUDE.md — admin.py
    # customization is Milestone 2).
    "django.contrib.admin",
    # Provides PermissionsMixin/permission machinery our custom User model
    # builds on, plus password hashing/validation.
    "django.contrib.auth",
    # Required by auth's permission system (Permission rows reference a
    # ContentType).
    "django.contrib.contenttypes",
    # Backs Django admin's login sessions (the API itself is stateless/JWT —
    # this is admin-only).
    "django.contrib.sessions",
    # One-time flash messages, required by the admin UI.
    "django.contrib.messages",
    # Collects/serves admin CSS/JS and any app static assets; whitenoise
    # serves what it collects.
    "django.contrib.staticfiles",
    # --- Third-party ---
    # Lets the browser-hosted React frontend (a different Render origin in
    # staging/prod) call this API at all — without it, the browser blocks
    # every cross-origin fetch before it reaches Django. Not needed in local
    # dev, where Vite's proxy (vite.config.ts) makes requests same-origin.
    "corsheaders",
    # Django REST Framework — turns Django into a JSON API (serializers,
    # viewsets, browsable API).
    "rest_framework",
    # Stores blacklisted refresh tokens in the DB; required because
    # SIMPLE_JWT below has BLACKLIST_AFTER_ROTATION=True (logout, rotation,
    # and password reset all need somewhere to record "this token is now
    # dead").
    "rest_framework_simplejwt.token_blacklist",
    # Provider-agnostic transactional email backend; lets EMAIL_BACKEND
    # point at Resend in prod without Resend-specific code elsewhere (see
    # the Email section below).
    "anymail",
    # --- Local apps (see apps/<name>/models.py for what each owns) ---
    # No models of its own; home for cross-app abstractions like the
    # UUID-PK/timestamp mixins and the shared DRF pagination class.
    "apps.core",
    # Custom User model, registration/auth/JWT views.
    "apps.accounts",
    # NursingSystem/Topic/Subtopic/ClientNeeds/Tag/CaseStudy — the
    # classification schema questions are tagged against.
    "apps.taxonomy",
    # Question, AnswerChoice, and the NGN-item-type stub models (Matrix,
    # Bow-Tie, Cloze, etc.).
    "apps.questions",
    # QuizSession + StudentResponseLog — quiz-taking and the per-answer log
    # Phase 2's AI features will read.
    "apps.quizzes",
    # SubscriptionPlan/UserSubscription — Stripe-shaped tables, stubbed and
    # unused until Phase 2.
    "apps.payments",
    # QuizFeedback + QuestionIssueReport — end-of-quiz survey and
    # per-question "Report an Issue" flags.
    "apps.feedback",
]

# Order matters: each request passes down through this list top-to-bottom,
# then the response passes back up bottom-to-top.
MIDDLEWARE = [
    # HTTPS/HSTS-related headers; several of its behaviors are toggled on in
    # production.py.
    "django.middleware.security.SecurityMiddleware",
    # Serves collected static files directly from the Django/gunicorn
    # process on Render, no separate static file host needed — must sit
    # right after SecurityMiddleware per whitenoise's own docs.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    # Must sit as high as practical, and specifically before
    # CommonMiddleware, per django-cors-headers' own docs — it needs to
    # attach CORS headers to a request/response before other middleware can
    # short-circuit it.
    "corsheaders.middleware.CorsMiddleware",
    # Attaches request.session; needed for Django admin login, not used by
    # the JWT API itself.
    "django.contrib.sessions.middleware.SessionMiddleware",
    # Misc conveniences (e.g. APPEND_SLASH).
    "django.middleware.common.CommonMiddleware",
    # CSRF protection for session-authenticated (cookie-based) requests —
    # i.e. the admin site; the JWT API is exempt in practice since it
    # doesn't use cookies.
    "django.middleware.csrf.CsrfViewMiddleware",
    # Attaches request.user for session-based auth (admin); DRF's
    # JWTAuthentication (see REST_FRAMEWORK below) is what sets request.user
    # for API calls.
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # Backs django.contrib.messages, used by the admin UI.
    "django.contrib.messages.middleware.MessageMiddleware",
    # Sends X-Frame-Options to stop the admin site being iframed.
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
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


# Cache
#
# Backed by a database table rather than Django's default in-memory
# LocMemCache, because this cache is not just an optimization here — it is
# where DRF stores rate-limit counters (see DEFAULT_THROTTLE_RATES below).
#
# LocMemCache is per-process, so under gunicorn's multiple worker processes
# each worker would keep its own independent counter: a "5/hour"
# registration limit would really be 5-per-hour-per-worker, and every deploy
# or worker restart would silently reset every limit to zero. Neither is
# acceptable for controls whose entire job is to bound abuse.
#
# DatabaseCache is shared across workers and survives restarts, and needs no
# extra infrastructure — Render's free tier has no Redis, and the Postgres
# instance is already there. The table it needs is created by
# `manage.py createcachetable` (wired into render.yaml's build command;
# Django's test runner creates it automatically for test databases).
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache",
    },
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
    # Rejects passwords too similar to the user's email/name.
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    # Default minimum length is 8.
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    # Rejects the ~20,000 most common passwords.
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    # Rejects all-digit passwords.
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization — not actively used (no i18n content yet) but left at
# Django's own defaults rather than removed, since USE_TZ especially affects
# how every DateTimeField (created_at, current_period_end, etc.) is stored.
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
# Store all datetimes in UTC in the DB; convert to local time only at
# display time — avoids DST/timezone bugs across environments.
USE_TZ = True


# Static files (admin CSS/JS, etc.)
STATIC_URL = "static/"
# `collectstatic` gathers every app's static files here; whitenoise serves
# from this directory.
STATIC_ROOT = BASE_DIR / "staticfiles"
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

# Upload ceilings. Django's own defaults are 2.5MB in-memory and unlimited
# on disk; these cap the on-disk side too, so a single request can't fill
# Render's (small, non-persistent) filesystem. Question.image additionally
# validates extension and size at the field level — see
# apps/questions/models.py.
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5 MB
# Bounds how many fields one form/multipart POST may contain — the default
# is 1000; the admin's question-with-inline-choices form is the widest form
# in the project and is nowhere near that.
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

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
    # Paginate every list endpoint by default rather than per-view, so a
    # list endpoint added later can't accidentally ship the whole table.
    # See apps/core/pagination.py for the page size and its ceiling.
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.DefaultPagination",
    # Per-view rate limits (via ScopedRateThrottle, set on the views that
    # opt in) — keyed by IP for anonymous requests and by user id for
    # authenticated ones. A view joins one of these buckets by setting
    # `throttle_scope = "<key>"`, e.g. LoginView uses "login".
    #
    # Counters live in the shared database cache configured above, so these
    # limits hold across gunicorn workers and across restarts.
    "DEFAULT_THROTTLE_RATES": {
        # --- Reachable while logged out ---
        # Prevents mass account creation.
        "register": "5/hour",
        # Slows password-guessing without affecting a user who mistypes.
        "login": "10/min",
        # This endpoint emails an address supplied by the caller, so it also
        # needs protecting against being used to spam arbitrary inboxes.
        "password_reset": "5/hour",
        # Guessable-token brute-force territory rather than email-spam
        # territory, hence a separate bucket from the request step.
        "password_reset_confirm": "10/hour",
        # NOTE on the two rates below: both endpoints are reachable without
        # authentication, so ScopedRateThrottle keys them by IP address —
        # and a whole nursing cohort on campus wifi or a hospital network
        # shares ONE public IP. A limit tuned to a single student would
        # therefore lock out an entire class. Both are deliberately set
        # per-cohort rather than per-person for that reason.
        #
        # Verification links are signed with SECRET_KEY and are not
        # realistically guessable, so this is a backstop against blind
        # hammering rather than a defence against a credible attack.
        "verify_email": "100/hour",
        # A refresh token is itself a strong, single-use credential
        # (rotation + blacklisting are on), so brute force is not the threat
        # here; this exists to bound runaway automated abuse. One student
        # refreshing a 30-minute access token generates ~2/hour, so this
        # accommodates a large shared-IP cohort with room to spare.
        "token_refresh": "1000/hour",
        # --- Requires a valid access token ---
        # Grading reveals the per-choice answer key, so this bounds how fast
        # one account can harvest it (see QuestionSubmitView's docstring).
        # Set well above what a real quiz-taker generates.
        "question_submit": "300/hour",
        # Feedback/issue reports accept free text, so an unbounded rate is a
        # cheap way to fill the database.
        "feedback": "20/hour",
    },
}

# djangorestframework-simplejwt configuration — see
# apps/accounts/views.py (LoginView, LogoutView) for how rotation and
# blacklisting are actually exercised.
SIMPLE_JWT = {
    # Short-lived; sent on every API request, so a leaked access token is
    # only useful for 30 minutes.
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    # Long-lived; stored client-side to silently obtain new access tokens
    # without re-login ("stay logged in" for 2 weeks).
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
    # Every refresh call issues a brand-new refresh token instead of reusing
    # the same one — limits how long a stolen refresh token stays valid.
    "ROTATE_REFRESH_TOKENS": True,
    # The old refresh token is invalidated the moment it's used to rotate —
    # requires the token_blacklist app (INSTALLED_APPS above) to store the
    # blacklist. This is also what lets logout and password reset actually
    # revoke tokens rather than just discarding them client-side.
    "BLACKLIST_AFTER_ROTATION": True,
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
# and the original *.onrender.com URL during DNS cutover, or both the apex
# domain and its www. subdomain, so the site doesn't break for anyone
# arriving on the other one. Defaults to just FRONTEND_URL when unset.
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[FRONTEND_URL])


# Email — Resend via Anymail. EMAIL_BACKEND itself is set per-environment
# (console in local.py, Anymail's Resend backend in production.py) so
# local dev never needs a real API key.
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="no-reply@nextwiseeducation.com")
ANYMAIL = {
    "RESEND_API_KEY": env("RESEND_API_KEY", default=""),
}

# Stripe (Phase 2 — stubbed webhook endpoint only, no active integration yet)
# Will be used to verify the signature on incoming Stripe webhook POSTs once
# apps/payments/views.py actually processes events instead of just
# returning 200. Blank default so Phase 1 never needs a real Stripe account.
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET", default="")


# Logging
#
# Without an explicit config, Django's default sends nothing to stdout when
# DEBUG=False, which would make the deliberate swallow-and-log failure
# handling in apps/accounts/emails.py invisible in production: a
# misconfigured or down email provider would look exactly like a working
# one. Render captures a service's stdout/stderr as its logs, so writing to
# the console is all that is needed for these to be visible in the Render
# dashboard.
LOGGING = {
    "version": 1,
    # Django installs its own default handlers before this dict is applied;
    # keeping them would double up every record.
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "{asctime} {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": env("LOG_LEVEL", default="INFO"),
    },
    "loggers": {
        # Django's own logger, including the "django.request" records that
        # carry 4xx/5xx tracebacks. propagate=False stops each record being
        # handled twice (once here, once by root).
        "django": {
            "handlers": ["console"],
            "level": env("DJANGO_LOG_LEVEL", default="INFO"),
            "propagate": False,
        },
    },
}
