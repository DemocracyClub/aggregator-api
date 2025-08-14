import boto3
from django.core.management.base import BaseCommand

from api_users.logging_helpers import APIKeyForLogging
from api_users.models import APIKey

s3_client = boto3.client("s3")


class Command(BaseCommand):
    help = "Writes a onerow csv per api key to S3"

    def handle(self, **options):
        for key in APIKey.objects.all().select_related("user"):
            key_for_logging = APIKeyForLogging.from_django_model(key)
            key_for_logging.upload_to_s3()
