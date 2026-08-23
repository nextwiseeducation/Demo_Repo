from django.apps import AppConfig


class AccountsConfig(AppConfig):
    # Dotted path Django uses to identify this app; must match the
    # "apps.accounts" entry in INSTALLED_APPS (config/settings/base.py).
    name = 'apps.accounts'
