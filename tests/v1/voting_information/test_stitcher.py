import datetime as dt

import pytest
from config import QueryParams
from starlette.datastructures import Headers
from starlette.requests import Request
from starlette.testclient import TestClient
from voting_information.app import app
from voting_information.stitcher import (
    CANCELLATION_REASONS,
    Stitcher,
    get_ballot_cancellation_reason_data,
)

from common.query_string import clean_query_params
from tests.helpers import fixture_map, load_fixture, load_sandbox_output


@pytest.fixture(scope="function")
def stitcher_client():
    return TestClient(
        app=app, base_url="https://developers.democracyclub.org.uk/"
    )


@pytest.fixture(scope="function")
def mock_request(stitcher_client):
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


@pytest.mark.time_machine(dt.datetime(2018, 1, 1))
def test_no_ballots(mock_request):
    postcode = "AA11AA"
    s = Stitcher(
        load_fixture(fixture_map[postcode], "wdiv"),
        load_fixture(fixture_map[postcode], "wcivf"),
        mock_request(f"/api/v1/postcode/{postcode}"),
        QueryParams(),
    )
    assert s.make_result_known_response() == load_sandbox_output(postcode)


@pytest.mark.time_machine(dt.datetime(2018, 1, 1))
def test_one_election_station_known_with_candidates(mock_request):
    postcode = "AA12AA"
    wdiv_json = load_fixture(fixture_map[postcode], "wdiv")
    wcivf_json = []
    for ballot in wdiv_json["ballots"]:
        wcivf_json.append(
            load_fixture(fixture_map[postcode], ballot["ballot_paper_id"])
        )

    s = Stitcher(
        wdiv_json,
        wcivf_json,
        mock_request(f"/api/v1/postcode/{postcode}"),
        QueryParams(),
        sandbox=True,
    )
    assert s.make_result_known_response() == load_sandbox_output(postcode)


@pytest.mark.time_machine(dt.datetime(2018, 1, 1))
def test_one_election_station_not_known_with_candidates(mock_request):
    postcode = "AA12AB"
    wdiv_json = load_fixture(fixture_map[postcode], "wdiv")
    wcivf_json = []
    for ballot in wdiv_json["ballots"]:
        wcivf_json.append(
            load_fixture(fixture_map[postcode], ballot["ballot_paper_id"])
        )

    s = Stitcher(
        wdiv_json,
        wcivf_json,
        mock_request(f"/api/v1/postcode/{postcode}"),
        QueryParams(),
        sandbox=True,
    )
    assert s.make_result_known_response() == load_sandbox_output(postcode)


@pytest.mark.time_machine(dt.datetime(2018, 1, 1))
def test_address_picker(mock_request):
    postcode = "AA13AA"
    s = Stitcher(
        load_fixture(fixture_map[postcode], "wdiv"),
        load_fixture(fixture_map[postcode], "wcivf"),
        mock_request(f"/api/v1/postcode/{postcode}"),
        QueryParams(),
        sandbox=True,
    )
    assert s.make_address_picker_response() == load_sandbox_output(postcode)


@pytest.mark.time_machine(dt.datetime(2018, 1, 1))
def test_multiple_elections(mock_request):
    postcode = "AA14AA"
    wdiv_json = load_fixture(fixture_map[postcode], "wdiv")
    wcivf_json = []
    for ballot in wdiv_json["ballots"]:
        wcivf_json.append(
            load_fixture(fixture_map[postcode], ballot["ballot_paper_id"])
        )

    s = Stitcher(
        wdiv_json,
        wcivf_json,
        mock_request(f"/api/v1/postcode/{postcode}"),
        QueryParams(),
        sandbox=True,
    )
    assert s.make_result_known_response() == load_sandbox_output(postcode)


@pytest.mark.time_machine(dt.datetime(2018, 1, 1))
def test_with_accessibility_information():
    postcode = "CC12CC"
    wdiv_json = load_fixture(fixture_map[postcode], "wdiv")
    wcivf_json = []
    for ballot in wdiv_json["ballots"]:
        wcivf_json.append(
            load_fixture(fixture_map[postcode], ballot["ballot_paper_id"])
        )

    request = Request(
        {
            "type": "http",
            "path": f"/api/v1/postcode/{postcode}",
            "server": ("developers.democracyclub.org.uk", 443),
            "scheme": "https",
            "headers": Headers().raw,
            "query_string": "include_accessibility=true",
        }
    )
    query_params = clean_query_params(request, QueryParams)

    s = Stitcher(
        wdiv_json,
        wcivf_json,
        request,
        query_params,
        sandbox=True,
    )
    assert s.make_result_known_response() == load_sandbox_output(postcode)


@pytest.mark.time_machine(dt.datetime(2018, 1, 1))
def test_validate_false_with_mismatched_ballots(mock_request):
    postcode = "AA14AA"
    wdiv_json = load_fixture(fixture_map[postcode], "wdiv")
    wcivf_json = []
    for ballot in wdiv_json["ballots"]:
        wcivf_json.append(
            load_fixture(fixture_map[postcode], ballot["ballot_paper_id"])
        )

    s = Stitcher(
        wdiv_json,
        wcivf_json,
        mock_request(f"/api/v1/postcode/{postcode}"),
        QueryParams(),
        sandbox=True,
    )
    assert s.validate()

    # Remove an election from WCIVF
    wcivf_json.pop(0)

    s = Stitcher(
        load_fixture(fixture_map[postcode], "wdiv"),
        wcivf_json,
        mock_request(f"/api/v1/postcode/{postcode}"),
        QueryParams(),
    )
    assert s.validate() is False


@pytest.mark.parametrize(
    "cancelled, reason_code, reason_dict",
    [
        (True, None, {}),
        (True, "CANDIDATE_DEATH", CANCELLATION_REASONS["CANDIDATE_DEATH"]),
        (False, None, None),
    ],
)
def test_get_ballot_cancellation_reason_data(
    cancelled, reason_code, reason_dict
):
    ballot = {"cancelled": cancelled, "cancellation_reason": reason_code}
    assert get_ballot_cancellation_reason_data(ballot) == reason_dict
