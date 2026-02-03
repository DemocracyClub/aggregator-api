import json

import polars as pl
import pytest
from boundary_changes.client import BoundaryReviewsApiClient
from boundary_changes.models import (
    BoundaryChangeModel,
    BoundaryReviewModel,
)
from starlette.datastructures import Headers
from starlette.requests import Request


@pytest.fixture(scope="function")
def mock_request():
    def request_factory(path):
        return Request(
            {
                "type": "http",
                "path": path,
                "server": ("developers.democracyclub.org.uk", 443),
                "scheme": "https",
                "headers": Headers().raw,
            }
        )

    return request_factory


@pytest.fixture
def mock_client(mock_request):
    return BoundaryReviewsApiClient(mock_request, postcode="AA1 1AA")


@pytest.fixture
def empty_dataframe():
    return pl.DataFrame()


@pytest.fixture
def non_split_dataframe():
    return pl.DataFrame(
        {
            "uprn": ["100", "200", "300"],
            "address": ["1 Test Street", "2 Test Street", "3 Test Street"],
            "postcode": ["AA1 1AA", "AA1 1AA", "AA1 1AA"],
            "addressbase_source": ["s3://test/", "s3://test/", "s3://test/"],
            "boundary_reviews": [
                ["foo"],
                ["foo"],
                ["foo"],
            ],
            "outcode": ["AA1", "AA1", "AA1"],
        }
    )


@pytest.fixture
def split_dataframe():
    return pl.DataFrame(
        {
            "uprn": ["400", "500"],
            "address": ["10 Split Lane", "12 Split Lane"],
            "postcode": ["AA1 1AA", "AA1 1AA"],
            "addressbase_source": ["s3://test/", "s3://test/"],
            "boundary_reviews": [
                ["foo"],
                ["bar"],
            ],
            "outcode": ["AA1", "AA1"],
        }
    )


def test_is_split_returns_false_for_empty_dataframe(
    mock_client, empty_dataframe
):
    assert mock_client.is_split(empty_dataframe) is False


def test_is_split_returns_false_for_single_boundary_review(
    mock_client, non_split_dataframe
):
    assert mock_client.is_split(non_split_dataframe) is False


def test_is_split_returns_true_for_multiple_boundary_reviews(
    mock_client, split_dataframe
):
    assert mock_client.is_split(split_dataframe) is True


def test_parse_boundary_reviews_returns_empty_list_for_empty_input(mock_client):
    assert mock_client.parse_boundary_reviews([]) == []


def test_parse_boundary_reviews_returns_empty_list_for_none(mock_client):
    assert mock_client.parse_boundary_reviews(None) == []


def test_parse_boundary_reviews_parses_json_strings(mock_client):
    review_json = json.dumps(
        {
            "boundary_review_id": "123",
            "boundary_review_details": {
                "consultation_url": "https://example.com",
                "effective_date": "2025-05-01",
                "legislation_title": "Test Legislation",
                "organisation_name": "Test Council",
                "organisation_official_name": "Test Council Official Name",
                "organisation_gss": "E09000001",
            },
            "changes": [
                {
                    "change_scenario": "no_change",
                    "division_type": "ward",
                    "new_division_official_identifier": "gss:E2",
                    "new_division_slug": "new-ward",
                    "new_divisionset_pmtiles_url": "https://example.com/new.pmtiles",
                    "old_division_official_identifier": "gss:E1",
                    "old_division_slug": "old-ward",
                    "old_divisionset_pmtiles_url": "https://example.com/old.pmtiles",
                }
            ],
        }
    )

    result = mock_client.parse_boundary_reviews([review_json])

    assert len(result) == 1
    expected = [
        BoundaryReviewModel(
            id="123",
            consultation_url="https://example.com",
            effective_date="2025-05-01",
            legislation_title="Test Legislation",
            organisation_name="Test Council",
            organisation_official_name="Test Council Official Name",
            organisation_gss="E09000001",
            boundary_changes=[
                BoundaryChangeModel(
                    change_scenario="no_change",
                    division_type="ward",
                    new_division_official_identifier="gss:E2",
                    new_division_slug="new-ward",
                    new_divisionset_pmtiles_url="https://example.com/new.pmtiles",
                    old_division_official_identifier="gss:E1",
                    old_division_slug="old-ward",
                    old_divisionset_pmtiles_url="https://example.com/old.pmtiles",
                    ballots=[],
                )
            ],
        )
    ]
    assert result == expected


def test_query_to_dict_returns_none_for_empty_dataframe(
    mock_client, empty_dataframe
):
    assert mock_client.query_to_dict(empty_dataframe) is None


def test_query_to_dict_returns_address_picker_when_split(
    mock_client, split_dataframe
):
    mock_client.request.url_for = (
        lambda name,
        **kwargs: f"https://example.com/{name}/{kwargs.get('uprn')}"
    )

    result = mock_client.query_to_dict(split_dataframe)

    assert result["address_picker"] is True
    assert len(result["addresses"]) == 2
    assert result["addresses"][0]["slug"] == "400"
    assert result["addresses"][0]["address"] == "10 Split Lane"


def test_patch_response_adds_boundary_reviews_to_response(mock_client):
    """
    patch_response receives a complete response from Stitcher and should
    add boundary_reviews to it without modifying other fields.
    """
    mock_client.postcode_response = lambda: {
        "address_picker": False,
        "addresses": [],
        "boundary_reviews": [{"id": "123"}],
        "electoral_services": None,
        "registration": None,
    }

    input_response = {
        "address_picker": False,
        "addresses": [],
        "dates": [{"date": "2025-05-01"}],
        "electoral_services": {"council_id": "ABC"},
        "registration": {"email": "test@example.com"},
        "postcode_location": {"type": "Feature"},
        "boundary_reviews": None,
    }

    result = mock_client.patch_response(input_response)

    assert result["boundary_reviews"] == [{"id": "123"}]
    assert result["dates"] == [{"date": "2025-05-01"}]
    assert result["electoral_services"] == {"council_id": "ABC"}
    assert result["registration"] == {"email": "test@example.com"}
    assert result["postcode_location"] == {"type": "Feature"}


def test_patch_response_returns_address_picker_when_boundary_data_is_split(
    mock_client,
):
    """
    When boundary data is split (different addresses have different boundary
    reviews), patch_response should return an address picker response.
    """
    mock_client.request.url_for = (
        lambda name,
        **kwargs: f"https://example.com/{name}/{kwargs.get('uprn')}"
    )
    mock_client.postcode_response = lambda: {
        "address_picker": True,
        "addresses": [
            {
                "slug": "100",
                "address": "1 Test St",
                "postcode": "AA1 1AA",
                "url": "https://example.com/address/100",
            },
            {
                "slug": "200",
                "address": "2 Test St",
                "postcode": "AA1 1AA",
                "url": "https://example.com/address/200",
            },
        ],
        "boundary_reviews": None,
        "electoral_services": None,
        "registration": None,
    }

    input_response = {
        "address_picker": False,
        "addresses": [],
        "dates": [{"date": "2025-05-01"}],
        "electoral_services": {"council_id": "ABC"},
        "registration": {"email": "test@example.com"},
        "postcode_location": {"type": "Feature"},
        "boundary_reviews": None,
    }

    result = mock_client.patch_response(input_response)

    assert result["address_picker"] is True
    assert len(result["addresses"]) == 2
    assert result["postcode_location"] == {"type": "Feature"}
    # dates should NOT be in the result since we're returning an address picker
    assert "dates" not in result or result.get("dates") == []
    # electoral_services and registration should be preserved from input
    assert result["electoral_services"] == {"council_id": "ABC"}
    assert result["registration"] == {"email": "test@example.com"}
