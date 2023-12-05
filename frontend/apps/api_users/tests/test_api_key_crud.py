from api_users.forms import APIKeyForm
from api_users.management.commands.sync_api_keys import (
    Command as SyncApiKeysCommand,
)
from api_users.models import APIKey, CustomUser
from api_users.utils import send_new_key_notification
from common.settings import API_PLANS
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
            "key_type": "development",
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
            "user_id": str(api_key.user.pk),
            "key_type": "development",
        }
    ]
    api_key.delete()
    assert table.scan()["Items"] == []


def test_api_key_type_creation(db):
    api_user = CustomUser.objects.create()

    # Hobbyist, can only make one key and that key is a dev key
    form = APIKeyForm(user=api_user)
    assert "api_plan" not in form.fields

    # Standard, user can pick prod or dev
    api_user.api_plan = API_PLANS["standard"].value
    api_user.save()
    form = APIKeyForm(user=api_user)
    assert "key_type" in form.fields
    choices = form.fields["key_type"].choices
    assert choices == [
        ("development", "Development"),
        ("production", "Production key"),
    ]

    # Standard user with a production key can't make another production key
    APIKey.objects.create(user=api_user, key_type="production")
    form = APIKeyForm(user=api_user)
    assert "key_type" not in form.fields

    # Promote this user to an enterprise user
    api_user.api_plan = API_PLANS["enterprise"].value
    api_user.save()
    api_user.refresh_from_db()
    form = APIKeyForm(user=api_user)
    assert "key_type" in form.fields
    choices = form.fields["key_type"].choices
    assert choices == [
        ("development", "Development"),
        ("production", "Production key"),
    ]

    # Demote this user to a standard user
    api_user.api_plan = API_PLANS["standard"].value
    api_user.save()
    api_user.refresh_from_db()
    form = APIKeyForm(user=api_user)
    assert "key_type" not in form.fields


def test_form_validation(db):
    api_user = CustomUser.objects.create(api_plan=API_PLANS["hobbyists"].value)

    basic_form_kwargs = {"name": "Test Key", "usage_reason": "Just for testing"}

    form = APIKeyForm(user=api_user, data=basic_form_kwargs)
    form.is_valid()
    assert form.errors == {}

    # Make a key for the user
    APIKey.objects.create(user=api_user, key_type="development")
    form = APIKeyForm(user=api_user, data=basic_form_kwargs)
    form.is_valid()
    assert form.errors == {"__all__": ["Can't make more than one hobbyist key"]}

    api_user.api_plan = API_PLANS["standard"].value
    api_user.save()
    api_user.refresh_from_db()
    data = basic_form_kwargs.copy()
    data["key_type"] = "production"
    form = APIKeyForm(user=api_user, data=data)
    form.is_valid()
    assert form.errors == {}


def test_standard_users_can_make_n_dev_keys_one_prod(db):
    api_user = CustomUser.objects.create(api_plan=API_PLANS["standard"].value)
    api_user.save()

    basic_form_kwargs = {"name": "Test Key", "usage_reason": "Just for testing"}

    data = basic_form_kwargs.copy()
    data["key_type"] = "production"
    form = APIKeyForm(user=api_user, data=data)
    form.is_valid()
    assert form.errors == {}
    form.save()

    for i in range(5):
        data = basic_form_kwargs.copy()
        data["key_type"] = "development"
        data["name"] = f"Test key {i}"
        form = APIKeyForm(user=api_user, data=data)
        form.is_valid()
        assert form.errors == {}
        form.save()

    assert api_user.api_keys.count() == 6

    # Due to the way we can pass things to Django forms in
    # tests, this looks like it will make a new prod key,
    # however it will actually be a dev key. The prod option isn't
    # resented to the user
    data = basic_form_kwargs.copy()
    data["key_type"] = "production"
    data["name"] = "Second prod key"
    form = APIKeyForm(user=api_user, data=data)
    assert "key_type" not in form.fields
    form.is_valid()
    assert form.errors == {}
    model = form.save()
    assert model.key_type == "development"


def test_email_dc_about_key_api_keys(db, rf, mailoutbox):
    request = rf.get("/")
    api_user = CustomUser.objects.create(
        api_plan=API_PLANS["standard"].value,
        name="Test User",
        email="test@example.com",
    )
    api_key = APIKey.objects.create(
        user=api_user,
        key_type="development",
        name="Test Key",
        usage_reason="Just testing",
    )
    send_new_key_notification(request, api_key)
    assert len(mailoutbox) == 1
    email_message = mailoutbox[0]
    assert email_message.subject == "New API key creation"
    assert "This is a development key." in email_message.body
    assert '> "Just testing"' in email_message.body
    assert (
        "You can contact Test User on test@example.com." in email_message.body
    )
    assert email_message.from_email == "developers@democracyclub.org.uk"
    assert list(email_message.to) == ["hello@democracyclub.org.uk"]
