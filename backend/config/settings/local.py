# Star-import pulls in every setting from base.py (INSTALLED_APPS, DATABASES,
# REST_FRAMEWORK, SIMPLE_JWT, etc.) so this file only needs to state what's
# *different* for local development, not redefine everything from scratch.
from .base import *  # noqa: F401,F403

# Hardcoded True here (rather than left to the env var default in base.py)
# because local dev should always show full tracebacks/debug pages — there's
# no scenario where you'd run `manage.py runserver` locally and want
# production-style generic error pages.
DEBUG = True

# Django only serves requests whose Host header matches this list; runserver
# is always reached via localhost/127.0.0.1, so nothing else is needed here.
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# No real SendGrid key needed for local dev — emails print to the console.
# This is what lets the registration/password-reset E2E flow be tested
# end-to-end locally (verification links included) without any email
# provider credentials — the runserver terminal output *is* the inbox.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
