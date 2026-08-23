#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
# Standard library — os is used to set the settings module env var,
# sys is used to hand the CLI args off to Django's command dispatcher.
import os
import sys


def main():
    """Run administrative tasks."""
    # Tells Django which settings module to load (config/settings/local.py)
    # whenever a management command is run via `python manage.py ...` and
    # DJANGO_SETTINGS_MODULE isn't already set in the environment. This is
    # why `python manage.py runserver` works locally without extra flags —
    # production instead sets DJANGO_SETTINGS_MODULE=config.settings.production
    # directly via the Render environment (see wsgi.py), bypassing this default.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
    try:
        # Imported here (not at module top) so that a missing/broken Django
        # install raises the friendlier ImportError message below instead of
        # a bare traceback the moment this script is run.
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    # Hands sys.argv (e.g. ["manage.py", "migrate"]) to Django, which parses
    # the command name and routes it to the matching management command.
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
