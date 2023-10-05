# Generated by Django 4.1.2 on 2023-10-06 10:08

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api_users", "0003_apikey_api_plan_customuser_api_plan"),
    ]

    operations = [
        migrations.AlterField(
            model_name="apikey",
            name="api_plan",
            field=models.CharField(
                choices=[
                    ("hobbyists", "Hobbyists"),
                    ("standard", "Standard"),
                    ("enterprise", "Enterprise"),
                ],
                default="hobbyists",
                help_text="The plan for this API key. Only one production key allowed.",
                max_length=100,
                verbose_name="API plan",
            ),
        ),
    ]
