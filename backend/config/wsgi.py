"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Unlike manage.py (which defaults to config.settings.local for dev
# convenience), this file hardcodes production settings as the default,
# since this is the module gunicorn actually imports on Render (see
# Procfile: `gunicorn config.wsgi:application`). setdefault() still lets an
# explicit DJANGO_SETTINGS_MODULE env var override this if ever needed.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

# The actual WSGI callable — this is the object gunicorn calls for every
# incoming HTTP request once the process boots.
application = get_wsgi_application()
