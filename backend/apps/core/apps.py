from django.apps import AppConfig


class CoreConfig(AppConfig):
    # Dotted path Django uses internally to identify this app (must match
    # the "apps.core" entry in INSTALLED_APPS in config/settings/base.py).
    name = 'apps.core'
