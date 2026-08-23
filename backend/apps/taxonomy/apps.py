from django.apps import AppConfig


class TaxonomyConfig(AppConfig):
    # Dotted path Django uses to identify this app; must match the
    # "apps.taxonomy" entry in INSTALLED_APPS (config/settings/base.py).
    name = 'apps.taxonomy'
