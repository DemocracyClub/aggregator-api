import secrets

import pytest

from common.auth_models import User


@pytest.fixture(scope="function")
def tmp_api_user():
    api_key = secrets.token_urlsafe(16)
    user_id = secrets.token_urlsafe(16)
    user = User(api_key=api_key, user_id=user_id)
    user.save()
    yield user
    user.delete()
