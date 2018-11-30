import json
import os
from django.http import HttpRequest
from django.test import TestCase
from api.v1.stitcher import Stitcher


def load_fixture(testname, fixture):
    dirname = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.abspath(
        os.path.join(dirname, f"fixtures/{testname}", f"{fixture}.json")
    )
    return json.load(open(file_path))


def load_sandbox_output(filename):
    dirname = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.abspath(
        os.path.join(dirname, "..", f"sandbox-responses/{filename}.json")
    )
    return json.load(open(file_path))


class StitcherTests(TestCase):
    maxDiff = None

    def test_no_ballots(self):
        s = Stitcher(
            load_fixture("test_no_elections", "wdiv"),
            load_fixture("test_no_elections", "wcivf"),
            HttpRequest(),
        )
        self.assertDictEqual(
            s.make_result_known_response(), load_sandbox_output("AA11AA")
        )

    def test_one_election_station_known_with_candidates(self):
        s = Stitcher(
            load_fixture("test_one_election_station_known_with_candidates", "wdiv"),
            load_fixture("test_one_election_station_known_with_candidates", "wcivf"),
            HttpRequest(),
        )
        self.assertDictEqual(
            s.make_result_known_response(), load_sandbox_output("AA12AA")
        )

    def test_one_election_station_not_known_with_candidates(self):
        s = Stitcher(
            load_fixture("test_one_election_station_not_known_with_candidates", "wdiv"),
            load_fixture(
                "test_one_election_station_not_known_with_candidates", "wcivf"
            ),
            HttpRequest(),
        )
        self.assertDictEqual(
            s.make_result_known_response(), load_sandbox_output("AA12AB")
        )

    def test_address_picker(self):
        request = HttpRequest()
        request.build_absolute_uri = (
            lambda route: f'https://developers.democracyclub.org.uk{route.replace("/api/v1/", "/api/v1/sandbox/")}'
        )
        s = Stitcher(
            load_fixture("test_address_picker", "wdiv"),
            load_fixture("test_address_picker", "wcivf"),
            request,
        )
        self.assertDictEqual(
            s.make_address_picker_response(), load_sandbox_output("AA13AA")
        )

    def test_multiple_elections(self):
        s = Stitcher(
            load_fixture("test_multiple_elections", "wdiv"),
            load_fixture("test_multiple_elections", "wcivf"),
            HttpRequest(),
        )
        self.assertDictEqual(
            s.make_result_known_response(), load_sandbox_output("AA14AA")
        )
