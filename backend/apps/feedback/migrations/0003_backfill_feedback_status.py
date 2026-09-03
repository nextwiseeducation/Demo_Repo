from django.db import migrations


def backfill_status(apps, schema_editor):
    # 0002's AddField already defaults every row to IN_CONSIDERATION at the
    # database level, so this is technically a no-op today — but it's kept
    # as an explicit, separate data migration (matching the
    # accounts/0004+0005 role backfill pattern) so a future field default
    # change doesn't silently skip backfilling existing rows.
    QuizFeedback = apps.get_model("feedback", "QuizFeedback")
    QuizFeedback.objects.filter(status="").update(status="IN_CONSIDERATION")


class Migration(migrations.Migration):
    dependencies = [
        ("feedback", "0002_add_feedback_status_field"),
    ]

    operations = [
        migrations.RunPython(backfill_status, migrations.RunPython.noop),
    ]
