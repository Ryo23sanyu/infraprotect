# Generated by Django 4.2.7 on 2024-08-06 01:09

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_alter_customuser_groups_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customuser",
            name="username",
            field=models.CharField(
                error_messages={"unique": "このユーザー名はすでに使用されています。"},
                max_length=150,
                unique=True,
                validators=[
                    django.core.validators.RegexValidator(
                        message="ユーザー名には、アルファベット、数字、@/./+/-/_/ひらがな/カタカナ/漢字しか使用できません。",
                        regex="^[\\w.@+-ぁ-ヶ一-龥々ー\\\\s]*$",
                    )
                ],
            ),
        ),
    ]
