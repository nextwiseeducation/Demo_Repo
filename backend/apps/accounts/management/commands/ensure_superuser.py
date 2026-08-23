import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    """
    Idempotent superuser bootstrap for environments with no interactive
    shell access (Render's free web-service plan doesn't support Shell/SSH
    — see docs/architecture.md). Safe to run on every deploy: unlike
    `createsuperuser --noinput`, it skips instead of erroring if the
    account already exists, so it can live directly in the Render build
    command without breaking every subsequent deploy after the first.

    Reads DJANGO_SUPERUSER_EMAIL / DJANGO_SUPERUSER_PASSWORD from the
    environment rather than command-line args, so no credentials need to
    appear in the build command itself or in Render's build logs.
    """

    help = "Creates a superuser from DJANGO_SUPERUSER_EMAIL/DJANGO_SUPERUSER_PASSWORD env vars, if one doesn't already exist."

    def handle(self, *args, **options):
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

        if not email or not password:
            # Not configured — fine locally/in dev, where this command is
            # never invoked anyway. Exits quietly rather than erroring, so
            # it's still safe to reference from a shared build command.
            self.stdout.write("DJANGO_SUPERUSER_EMAIL / DJANGO_SUPERUSER_PASSWORD not set — skipping.")
            return

        if User.objects.filter(email__iexact=email).exists():
            self.stdout.write(f"Superuser '{email}' already exists — skipping.")
            return

        User.objects.create_superuser(email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f"Created superuser '{email}'."))
