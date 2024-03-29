# Generated by Django 4.1.2 on 2023-12-05 15:17

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

import api_users.mixins


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="CustomUser",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "password",
                    models.CharField(max_length=128, verbose_name="password"),
                ),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="last login"
                    ),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        max_length=254,
                        unique=True,
                        verbose_name="email address",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="Either your name or an organisation name",
                        max_length=255,
                    ),
                ),
                (
                    "is_staff",
                    models.BooleanField(
                        default=False,
                        help_text="Designates whether the user can log into this admin site.",
                        verbose_name="staff status",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.",
                        verbose_name="active",
                    ),
                ),
                (
                    "date_joined",
                    models.DateTimeField(
                        default=django.utils.timezone.now,
                        verbose_name="date joined",
                    ),
                ),
                (
                    "api_plan",
                    models.CharField(
                        choices=[
                            ("hobbyists", "Hobbyists"),
                            ("standard", "Standard"),
                            ("enterprise", "Enterprise"),
                        ],
                        default="hobbyists",
                        help_text="The plan that this user has paid for",
                        max_length=100,
                        verbose_name="API plan",
                    ),
                ),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "user",
                "verbose_name_plural": "users",
            },
        ),
        migrations.CreateModel(
            name="APIKey",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "updated_at",
                    api_users.mixins.AutoDateTimeField(
                        default=django.utils.timezone.now
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="To help identify your key", max_length=255
                    ),
                ),
                (
                    "usage_reason",
                    models.TextField(
                        help_text="Short description of the usage reason for this key"
                    ),
                ),
                ("key", models.CharField(max_length=255)),
                ("is_active", models.BooleanField(default=True)),
                ("rate_limit_warn", models.BooleanField(default=False)),
                (
                    "api_plan",
                    models.CharField(
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
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="api_keys",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "API key",
                "verbose_name_plural": "API keys",
                "ordering": ["-created_at"],
            },
        ),
    ]
