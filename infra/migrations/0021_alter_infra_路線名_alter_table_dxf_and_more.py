# Generated by Django 5.1 on 2024-10-12 07:46

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("infra", "0020_rename_memo_x_bridgepicture_memo_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="infra",
            name="路線名",
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name="table",
            name="dxf",
            field=models.FileField(upload_to="dxf/", verbose_name="dxfファイル"),
        ),
        migrations.AlterField(
            model_name="uploadedfile",
            name="file",
            field=models.FileField(upload_to="dxf/"),
        ),
        migrations.AddConstraint(
            model_name="bridgepicture",
            constraint=models.UniqueConstraint(
                fields=(
                    "picture_number",
                    "damage_coordinate_x",
                    "damage_coordinate_y",
                    "span_number",
                    "table",
                    "infra",
                    "article",
                ),
                name="unique_bridge_picture",
            ),
        ),
    ]
