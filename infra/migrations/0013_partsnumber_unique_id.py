# Generated by Django 4.2.7 on 2024-09-01 23:48

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("infra", "0012_remove_fullreportdata_unit_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="partsnumber",
            name="unique_id",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
