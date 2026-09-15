from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="documento",
            name="arquivo",
            field=models.FileField(
                blank=True,
                default="",
                max_length=255,
                upload_to="uploads/",
            ),
            preserve_default=False,
        ),
    ]
