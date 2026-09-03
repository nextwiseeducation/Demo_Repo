from django.db import migrations

from apps.accounts.roles import backfill_roles


def forwards(apps, schema_editor):
    # apps.get_model gives the historical version of User as it existed at
    # this point in migration history — backfill_roles only touches
    # is_superuser/is_staff/role, all three of which already existed by
    # 0004, so using the historical model here is safe and is the correct
    # pattern regardless.
    User = apps.get_model("accounts", "User")
    backfill_roles(User)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_add_user_role_field"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
