import csv
import logging
from dataclasses import dataclass
from io import StringIO

import boto3
from django.conf import settings

logger = logging.getLogger()


@dataclass
class APIKeyForLogging:
    key: str
    key_name: str
    user_name: str
    email: str
    usage_reason: str

    @property
    def dc_environment(self):
        return getattr(settings, "DC_ENVIRONMENT", None)

    @property
    def file_name(self):
        return f"{self.key[:4]}_{self.key[-4:]}.csv"

    @property
    def prefix(self):
        if self.dc_environment == "production":
            return "api-users/aggregator-api/latest/"

        if self.dc_environment in ("development", "staging"):
            return f"api-users/aggregator-api/{self.dc_environment}/latest/"

        return "api-users/aggregator-api/local-dev/latest/"

    @property
    def bucket(self):
        if self.dc_environment == "production":
            return "dc-monitoring-production-logging"

        if self.dc_environment in ("development", "staging"):
            return "dc-monitoring-dev-logging"

        return "local-dev-logging"

    def upload_to_s3(self):
        # Construct the S3 object key (path)
        s3_key = f"{self.prefix}{self.file_name}"

        # destination for logging info
        destination = f"s3://{self.bucket}/{s3_key}"

        # if not deployed, don't upload to s3
        if self.dc_environment not in ("production", "development", "staging"):
            logger.info(
                f"Not uploading to {destination} because self.dc_environment is not one of (production, development, staging)"
            )
            return destination

        # Create a CSV string with a single row and no header
        csv_buffer = StringIO()
        csv_writer = csv.writer(csv_buffer)
        csv_writer.writerow(
            [
                self.key,
                self.key_name,
                self.user_name,
                self.email,
                self.usage_reason,
            ]
        )

        # Create an S3 client
        s3_client = boto3.client("s3")

        # Upload the CSV to S3
        s3_client.put_object(
            Bucket=self.bucket, Key=s3_key, Body=csv_buffer.getvalue()
        )
        logger.info(f"Uploaded csv to {destination}")
        # return csv destination
        return destination

    @classmethod
    def from_django_model(cls, api_key_model):
        """
        :type api_key_model: frontend.apps.api_users.models.APIKey
        """

        return cls(
            key=api_key_model.key,
            key_name=api_key_model.name,
            user_name=api_key_model.user.name,
            email=api_key_model.user.email,
            usage_reason=api_key_model.usage_reason,
        )
