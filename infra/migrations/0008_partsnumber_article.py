# Generated by Django 4.2.7 on 2024-08-26 05:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("infra", "0007_table_article"),
    ]

    operations = [
        migrations.AddField(
            model_name="partsnumber",
            name="article",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="infra.article",
            ),
        ),
    ]
