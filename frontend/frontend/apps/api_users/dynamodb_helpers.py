import logging
import os
import sys

import boto3
from common.auth_models import User
from django.conf import settings

from api_users.models import APIKey

logger = logging.getLogger()

logger.setLevel(20)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


class DynamoDBClient:
    def __init__(self):
        self.live_mode = getattr(settings, "USE_DYNAMODB", False)

        if not self.live_mode:
            logger.info("Fake mode (will not post to real DynamoDB)")
        self.table_name = getattr(settings, "DYNAMODB_TABLE_NAME", "users")
        self.aws_region = os.environ.get("AWS_REGION", "eu-west-2")
        if self.live_mode:
            self.create_connection()

    def create_connection(self):
        self.client = boto3.client("dynamodb", region_name=self.aws_region)

    def create_table(self):
        logger.info(f"Creating table {self.table_name}")
        if not self.live_mode:
            return True

        if self.table_name in self.client.list_tables()["TableNames"]:
            logger.info(f"Table {self.table_name} already exists")
            return True
        params = {
            "TableName": self.table_name,
            "KeySchema": [
                {"AttributeName": "partition_key", "KeyType": "HASH"},
            ],
            "AttributeDefinitions": [
                {"AttributeName": "partition_key", "AttributeType": "S"},
            ],
            "BillingMode": "PAY_PER_REQUEST",
        }
        return self.client.create_table(**params)

    def sync_api_keys(self):
        logger.info("Syncing API keys")
        dynamodb = boto3.resource("dynamodb", region_name=self.aws_region)
        table = dynamodb.Table(self.table_name)
        for api_key in APIKey.objects.all():
            self._put_single_key(api_key, table)

    def update_key(self, api_key: APIKey):
        if self.live_mode:
            dynamodb = boto3.resource("dynamodb", region_name=self.aws_region)
            table = dynamodb.Table(self.table_name)
            self._put_single_key(api_key, table)

    def delete_key(self, api_key: APIKey):
        dynamodb = boto3.resource("dynamodb", region_name=self.aws_region)
        table = dynamodb.Table(self.table_name)
        user = User.from_django_model(api_key)
        user.delete(table=table)

    def _put_single_key(self, api_key: APIKey, table):
        if not self.live_mode:
            return
        logging.info(f"Putting key {api_key.key}")

        user = User.from_django_model(api_key)
        user.save(table=table)


if __name__ == "__main__":
    client = DynamoDBClient()
    client.create_table()
