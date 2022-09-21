from dataclasses import dataclass
from typing import TYPE_CHECKING

import boto3

if TYPE_CHECKING:
    from mypy_boto3_dynamodb import DynamoDBServiceResource


def get_dynamodb_table(table_name, region_name="eu-west-2"):
    dynamodb: DynamoDBServiceResource = boto3.resource(
        "dynamodb", region_name=region_name
    )
    return dynamodb.Table(table_name)


class UserDoesNotExist(ValueError):
    pass


@dataclass
class User:
    api_key: str
    user_id: str
    is_active: bool = True
    rate_limit_warn: bool = False

    def save(self):
        table = get_dynamodb_table("users")
        table.put_item(
            Item=self.as_dict(),
        )
        return self.as_dict()

    def delete(self):
        table = get_dynamodb_table("users")
        table.delete_item(Key={"api_key": self.api_key})

    def as_dict(self) -> dict:
        return self.__dict__

    @classmethod
    def from_dynamodb(cls, api_key, region_name="eu-west-2"):
        table = get_dynamodb_table("users", region_name)
        item = table.get_item(Key={"api_key": api_key})
        if "Item" not in item:
            raise UserDoesNotExist
        return cls(**item["Item"])
