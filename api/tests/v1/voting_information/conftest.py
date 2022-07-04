import pytest
from starlette.testclient import TestClient

from voting_information.app import app


@pytest.fixture(scope="function")
def vi_app_client() -> TestClient:
    return TestClient(app=app)
