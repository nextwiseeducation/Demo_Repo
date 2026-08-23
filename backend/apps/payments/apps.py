from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    # Dotted path Django uses to identify this app; must match the
    # "apps.payments" entry in INSTALLED_APPS (config/settings/base.py).
    name = 'apps.payments'
