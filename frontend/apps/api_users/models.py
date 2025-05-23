# Create your models here.
import binascii
import os

from common.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.core.mail import send_mail
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from api_users.logging_helpers import APIKeyForLogging
from api_users.managers import CustomUserManager
from api_users.mixins import TimestampMixin


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom implementation of django User model to use the email for login
    """

    email = models.EmailField(_("email address"), unique=True)
    name = models.CharField(
        max_length=255, help_text=_("Either your name or an organisation name")
    )
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_(
            "Designates whether the user can log into this admin site."
        ),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)
    api_plan = models.CharField(
        choices=[
            (name, plan.label) for name, plan in settings.API_PLANS.items()
        ],
        default="hobbyists",
        max_length=100,
        verbose_name="API plan",
        help_text="The plan that this user has paid for",
    )

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"

    objects = CustomUserManager()

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def clean(self):
        super().clean()
        self.email = CustomUser.objects.normalize_email(self.email)

    def email_user(self, subject, message, from_email=None, **kwargs):
        """
        Email this user.
        """
        send_mail(subject, message, from_email, [self.email], **kwargs)


class APIKey(TimestampMixin, models.Model):
    name = models.CharField(
        max_length=255, help_text="To help identify your key"
    )
    usage_reason = models.TextField(
        help_text="Short description of the usage reason for this key"
    )
    key = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    rate_limit_warn = models.BooleanField(default=False)
    key_type = models.CharField(
        choices=[
            ("development", "Development"),
            ("production", "Production"),
        ],
        max_length=100,
        verbose_name="API plan",
        help_text="The plan for this API key. Only one production key allowed.",
        default="development",
    )
    user: CustomUser = models.ForeignKey(
        to=get_user_model(),
        on_delete=models.CASCADE,
        related_name="api_keys",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "API key"
        verbose_name_plural = "API keys"

    def __str__(self):
        return f"{self.name} ({self.truncated_key})"

    @classmethod
    def _generate_key(self):
        return binascii.hexlify(os.urandom(20)).decode()

    def save(self, *args, **kwargs):
        """
        On initial save generates a key
        """
        if not self.key:
            self.key = self._generate_key()

        from api_users.dynamodb_helpers import DynamoDBClient

        dynamodb_client = DynamoDBClient()

        super().save(*args, **kwargs)
        dynamodb_client.update_key(self)

        key_for_logging = APIKeyForLogging.from_django_model(self)
        key_for_logging.upload_to_s3()

        return self

    def delete(self, using=None, keep_parents=False):
        from api_users.dynamodb_helpers import DynamoDBClient

        dynamodb_client = DynamoDBClient()
        dynamodb_client.delete_key(self)
        return super().delete(using, keep_parents)

    def get_absolute_delete_url(self):
        """
        Build URL to delete the key
        """
        return reverse("api_users:delete-key", kwargs={"pk": self.pk})

    @property
    def label(self):
        if self.user.api_plan == "hobbyists":
            return "Hobbyist"
        return self.key_type.title()

    @property
    def truncated_key(self):
        return f"{self.key[:4]}…{self.key[-4:]}"
