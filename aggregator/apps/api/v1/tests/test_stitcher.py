from django.http import HttpRequest
from django.test import TestCase
from api.v1.stitcher import Stitcher
from api.v1.tests.helpers import load_fixture, load_sandbox_output, fixture_map


class StitcherTests(TestCase):
    maxDiff = None

    def setUp(self):
        self.request = HttpRequest()
        self.request.build_absolute_uri = (
            lambda route: f'https://developers.democracyclub.org.uk{route.replace("/api/v1/", "/api/v1/sandbox/")}'
        )

    def test_no_ballots(self):
        postcode = "AA11AA"
        s = Stitcher(
            load_fixture(fixture_map[postcode], "wdiv"),
            load_fixture(fixture_map[postcode], "wcivf"),
            self.request,
        )
        self.assertDictEqual(
            s.make_result_known_response(), load_sandbox_output(postcode)
        )

    def test_one_election_station_known_with_candidates(self):
        postcode = "AA12AA"
        s = Stitcher(
            load_fixture(fixture_map[postcode], "wdiv"),
            load_fixture(fixture_map[postcode], "wcivf"),
            self.request,
        )
        self.assertDictEqual(
            s.make_result_known_response(), load_sandbox_output(postcode)
        )

    def test_one_election_station_not_known_with_candidates(self):
        postcode = "AA12AB"
        s = Stitcher(
            load_fixture(fixture_map[postcode], "wdiv"),
            load_fixture(fixture_map[postcode], "wcivf"),
            self.request,
        )
        self.assertDictEqual(
            s.make_result_known_response(), load_sandbox_output(postcode)
        )

    def test_address_picker(self):
        postcode = "AA13AA"
        s = Stitcher(
            load_fixture(fixture_map[postcode], "wdiv"),
            load_fixture(fixture_map[postcode], "wcivf"),
            self.request,
        )
        self.assertDictEqual(
            s.make_address_picker_response(), load_sandbox_output(postcode)
        )

    def test_multiple_elections(self):
        postcode = "AA14AA"
        s = Stitcher(
            load_fixture(fixture_map[postcode], "wdiv"),
            load_fixture(fixture_map[postcode], "wcivf"),
            self.request,
        )
        self.assertDictEqual(
            s.make_result_known_response(), load_sandbox_output(postcode)
        )

    def test_validate_false_with_mismatched_balots(self):
        postcode = "AA14AA"
        wcivf = load_fixture(fixture_map[postcode], "wcivf")
        s = Stitcher(load_fixture(fixture_map[postcode], "wdiv"), wcivf, self.request)
        self.assertTrue(s.validate())

        # Remove an election from WCIVF
        wcivf.pop(0)

        s = Stitcher(load_fixture(fixture_map[postcode], "wdiv"), wcivf, self.request)
        self.assertFalse(s.validate())
