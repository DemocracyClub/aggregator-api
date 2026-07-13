import json

import pytest
from response_builder.v1.models.base import RootModel
from sandbox.app import handler as sandbox_handler

from tests.helpers import fixture_map, load_sandbox_output


@pytest.mark.parametrize("postcode", fixture_map.keys())
def test_example_postcodes_load(mangum_app_client, postcode):
    url = f"/api/v1/sandbox/postcode/{postcode}/"
    response = mangum_app_client(sandbox_handler, url)
    assert response["statusCode"] == 200


def test_missing_postcode(mangum_app_client):
    url = "/api/v1/sandbox/postcode/SW1A1AA/"
    response = mangum_app_client(sandbox_handler, url)
    assert response["statusCode"] == 404


sandbox_postcodes = [
    "10035187881",
    "10035187882",
    "10035187883",
    "AA11AA",
    "AA12AA",
    "AA12AB",
    "AA13AA",
    "AA14AA",
    "AA15AA",
    "AB12CD",
    "EH11YJ",
]


@pytest.mark.parametrize("postcode", sandbox_postcodes)
def test_validate_sandbox(postcode):
    response = load_sandbox_output(postcode)
    model = RootModel.from_api_response(response)
    assert json.loads(model.json()) == response


# We can't test these as rigorously
# because they have extra properties that aren't in the schema
# and will be stripped when we parse them
# but make sure they at least validate/parse
sandbox_postcodes_with_extras = [
    "AD11DD",
    "CC12CC",
]


@pytest.mark.parametrize("postcode", sandbox_postcodes_with_extras)
def test_validate_sandbox_with_extras(postcode):
    response = load_sandbox_output(postcode)
    model = RootModel.from_api_response(response)
    assert model
