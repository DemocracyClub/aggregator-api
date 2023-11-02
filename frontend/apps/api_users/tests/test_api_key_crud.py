from api_users.management.commands.sync_api_keys import (
    Command as SyncApiKeysCommand,
)
from api_users.models import APIKey, CustomUser
from django.test.utils import override_settings


def test_save_api_key_posts_to_dynamodb(db, dynamodb):
    api_user = CustomUser.objects.create()
    api_key = APIKey(name="test_key", user=api_user)

    table = dynamodb.Table("users")
    assert table.scan()["Items"] == []
    api_key.save()
    assert table.scan()["Items"] == [
        {
            "api_key": api_key.key,
            "api_plan": "hobbyists",
            "is_active": True,
            "rate_limit_warn": False,
            "user_id": "1",
        }
    ]


def test_bulk_create_api_keys(db, dynamodb, settings):
    with override_settings(USE_DYNAMODB=False):
        for i in range(10):
            api_user = CustomUser.objects.create(
                name=i, email=f"{i}@example.com"
            )
            APIKey.objects.create(name=f"test_key_{i}", user=api_user)

    table = dynamodb.Table("users")
    assert table.scan()["Items"] == []
    sync_api_keys = SyncApiKeysCommand()
    sync_api_keys.handle()
    assert len(table.scan()["Items"]) == 10


def test_delete_key_deletes_from_dynamodb(db, dynamodb):
    api_user = CustomUser.objects.create()
    api_key = APIKey(name="test_key", user=api_user)

    table = dynamodb.Table("users")
    assert table.scan()["Items"] == []
    api_key.save()
    assert table.scan()["Items"] == [
        {
            "api_key": api_key.key,
            "api_plan": "hobbyists",
            "is_active": True,
            "rate_limit_warn": False,
            "user_id": "1",
        }
    ]
    api_key.delete()
    assert table.scan()["Items"] == []
