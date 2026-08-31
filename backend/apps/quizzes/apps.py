from django.apps import AppConfig


class QuizzesConfig(AppConfig):
    # Dotted path Django uses to identify this app; must match the
    # "apps.quizzes" entry in INSTALLED_APPS (config/settings/base.py).
    name = "apps.quizzes"
