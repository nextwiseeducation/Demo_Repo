# Pulls in every base.py setting (see local.py for the same pattern);
# `env` is imported explicitly on the next line since it's needed directly
# here (env.int below), not just indirectly through the settings it produced.
from .base import *  # noqa: F401,F403
from .base import env

DEBUG = False  # never show tracebacks/debug pages on a public deployment — leaks source code, settings, and stack traces to visitors

# Anymail's SendGrid backend — same `send_mail()` call sites as the console
# backend in local.py, but this one actually delivers via the SendGrid API
# using ANYMAIL["SENDGRID_API_KEY"] (set in base.py from the env var Render
# injects).
EMAIL_BACKEND = "anymail.backends.sendgrid.EmailBackend"

# --- HTTPS/transport security hardening ---
# Render terminates TLS at its own edge/proxy and forwards plain HTTP to
# this process, so these settings are what make Django itself HTTPS-aware
# and HTTPS-enforcing despite the app server not directly holding a
# certificate.
SECURE_SSL_REDIRECT = True  # any plain-HTTP request is redirected to HTTPS before being processed
SESSION_COOKIE_SECURE = True  # session cookie (admin login) is only ever sent over HTTPS, never plain HTTP
CSRF_COOKIE_SECURE = True  # same, for the CSRF cookie
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=60 * 60 * 24 * 7)  # tells browsers to *refuse* plain-HTTP for this host for 7 days, even if a user types http:// directly; configurable via env in case it needs to be raised later (HSTS preload lists typically want 1 year+)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True  # extends that HSTS enforcement to all subdomains, not just the exact host
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")  # tells Django to trust Render's `X-Forwarded-Proto: https` header as proof the original request was HTTPS, since Django itself only sees the proxy's internal plain-HTTP connection — without this, SECURE_SSL_REDIRECT above would incorrectly redirect-loop every request
