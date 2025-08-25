from django.db import models
from django.utils import timezone


class AutoDateTimeField(models.DateTimeField):
    """
    Field to always set the latest updated time
    """

    def pre_save(self, model_instance, add):
        return timezone.now()


class TimestampMixin(models.Model):
    """
    Adds created and updated timestamps to a model.
    TODO move this elsewhere? Core app?
    """

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = AutoDateTimeField(default=timezone.now)

    class Meta:
        abstract = True
