import pytest
from sandbox.app import handler as sandbox_handler

from api.tests.helpers import fixture_map


@pytest.mark.parametrize("postcode", fixture_map.keys())
def test_example_postcodes_load(mangum_app_client, postcode):
    url = f"/api/v1/sandbox/postcode/{postcode}/"
    response = mangum_app_client(sandbox_handler, url)
    assert response["statusCode"] == 200


def test_missing_postcode(mangum_app_client):
    url = "/api/v1/sandbox/postcode/SW1A1AA/"
    response = mangum_app_client(sandbox_handler, url)
    assert response["statusCode"] == 404
