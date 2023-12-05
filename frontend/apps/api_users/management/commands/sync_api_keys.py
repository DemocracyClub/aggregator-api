from django.core.management.base import BaseCommand

from api_users.dynamodb_helpers import DynamoDBClient


class Command(BaseCommand):
    help = "Creates the DynamoDB API user table"

    def handle(self, **options):
        client = DynamoDBClient()
        client.create_table()
        client.sync_api_keys()
