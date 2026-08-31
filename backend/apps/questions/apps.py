from django.apps import AppConfig


class QuestionsConfig(AppConfig):
    # Dotted path Django uses to identify this app; must match the
    # "apps.questions" entry in INSTALLED_APPS (config/settings/base.py).
    name = "apps.questions"
