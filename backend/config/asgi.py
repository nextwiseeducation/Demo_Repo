"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# NOTE: this project deploys via WSGI/gunicorn (see wsgi.py and render.yaml's
# `gunicorn config.wsgi` start command), not ASGI — this file is Django's
# default scaffolding and is not currently wired into the deployment. It
# would only start mattering if something async-native were added later
# (e.g. websockets, ASGI-only middleware) and the deploy target were switched
# to an ASGI server (uvicorn/daphne).
#
# Kept in sync with wsgi.py rather than left at startproject's default:
# that default pointed at "config.settings" — the settings *package*, which
# contains only base/local/production submodules and no settings of its own,
# so anything importing this module would have failed to boot. Harmless
# while unused, but a trap for whoever first tries to run this under an ASGI
# server. setdefault() still lets an explicit DJANGO_SETTINGS_MODULE env var
# override this.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

application = get_asgi_application()
