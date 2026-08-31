# Pulls in every base.py setting (see local.py for the same pattern);
# `env` is imported explicitly on the next line since it's needed directly
# here (env.int below), not just indirectly through the settings it produced.
from .base import *  # noqa: F401,F403
from .base import env

# Never show tracebacks/debug pages on a public deployment — leaks source
# code, settings, and stack traces to visitors.
DEBUG = False

# Anymail's Resend backend — same `send_mail()` call sites as the console
# backend in local.py, but this one actually delivers via the Resend API
# using ANYMAIL["RESEND_API_KEY"] (set in base.py from the env var Render
# injects).
EMAIL_BACKEND = "anymail.backends.resend.EmailBackend"

# --- HTTPS/transport security hardening ---
# Render terminates TLS at its own edge/proxy and forwards plain HTTP to
# this process, so these settings are what make Django itself HTTPS-aware
# and HTTPS-enforcing despite the app server not directly holding a
# certificate.

# Any plain-HTTP request is redirected to HTTPS before being processed.
SECURE_SSL_REDIRECT = True

# Session cookie (admin login) is only ever sent over HTTPS, never plain
# HTTP.
SESSION_COOKIE_SECURE = True

# Same, for the CSRF cookie.
CSRF_COOKIE_SECURE = True

# Tells browsers to *refuse* plain-HTTP for this host, even if a user types
# http:// directly. Defaults to one year: the short 7-day value this
# previously used is below what the HSTS preload list requires, and the
# domain has now been serving HTTPS-only long enough that a long max-age is
# safe. Still env-configurable so it can be dialled back quickly if a
# certificate problem ever makes HTTPS temporarily unavailable.
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=60 * 60 * 24 * 365)

# Extends that HSTS enforcement to all subdomains, not just the exact host.
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# Adds the `preload` directive, making the domain eligible for submission to
# the browser-vendor HSTS preload list (hstspreload.org) — browsers then
# refuse plain HTTP for it even on a user's very first visit, before any
# HSTS header has been seen. Requires the two settings above; submission
# itself is a separate manual step, this only makes the header say the site
# is willing.
SECURE_HSTS_PRELOAD = True

# Tells Django to trust Render's `X-Forwarded-Proto: https` header as proof
# the original request was HTTPS, since Django itself only sees the proxy's
# internal plain-HTTP connection — without this, SECURE_SSL_REDIRECT above
# would incorrectly redirect-loop every request.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
