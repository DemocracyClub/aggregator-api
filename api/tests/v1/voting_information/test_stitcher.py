import pytest
from starlette.testclient import TestClient
from tests.helpers import fixture_map, load_fixture, load_sandbox_output
from voting_information.app import app
from voting_information.stitcher import Stitcher


@pytest.fixture(scope="function")
def stitcher_client():
    return TestClient(
        app=app, base_url="https://developers.democracyclub.org.uk/"
    )


def test_no_ballots(stitcher_client):
    postcode = "AA11AA"
    s = Stitcher(
        load_fixture(fixture_map[postcode], "wdiv"),
        load_fixture(fixture_map[postcode], "wcivf"),
        stitcher_client,
    )
    assert s.make_result_known_response() == load_sandbox_output(postcode)


def test_one_election_station_known_with_candidates(stitcher_client):
    postcode = "AA12AA"
    s = Stitcher(
        load_fixture(fixture_map[postcode], "wdiv"),
        load_fixture(fixture_map[postcode], "wcivf"),
        stitcher_client,
        sandbox=True,
    )
    assert s.make_result_known_response() == load_sandbox_output(postcode)


def test_one_election_station_not_known_with_candidates(stitcher_client):
    postcode = "AA12AB"
    s = Stitcher(
        load_fixture(fixture_map[postcode], "wdiv"),
        load_fixture(fixture_map[postcode], "wcivf"),
        stitcher_client,
        sandbox=True,
    )
    assert s.make_result_known_response() == load_sandbox_output(postcode)


def test_address_picker(stitcher_client):
    postcode = "AA13AA"
    s = Stitcher(
        load_fixture(fixture_map[postcode], "wdiv"),
        load_fixture(fixture_map[postcode], "wcivf"),
        stitcher_client,
        sandbox=True,
    )
    assert s.make_address_picker_response() == load_sandbox_output(postcode)


def test_multiple_elections(stitcher_client):
    postcode = "AA14AA"
    s = Stitcher(
        load_fixture(fixture_map[postcode], "wdiv"),
        load_fixture(fixture_map[postcode], "wcivf"),
        stitcher_client,
        sandbox=True,
    )
    assert s.make_result_known_response() == load_sandbox_output(postcode)


def test_validate_false_with_mismatched_ballots(stitcher_client):
    postcode = "AA14AA"
    wcivf = load_fixture(fixture_map[postcode], "wcivf")
    s = Stitcher(
        load_fixture(fixture_map[postcode], "wdiv"), wcivf, stitcher_client
    )
    assert s.validate()

    # Remove an election from WCIVF
    wcivf.pop(0)

    s = Stitcher(
        load_fixture(fixture_map[postcode], "wdiv"), wcivf, stitcher_client
    )
    assert s.validate() is False
