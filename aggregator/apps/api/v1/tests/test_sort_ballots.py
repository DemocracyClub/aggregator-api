from django.test import TestCase
from api.v1.stitcher import sort_ballots


class SortBallotsTests(TestCase):
    def test_sorter(self):
        initial = [
            {"ballot_paper_id": "local.manchester.clayton-openshaw.2020-02-27"},
            {"ballot_paper_id": "mayor.greater-manchester-ca.2020-05-07"},
            {"ballot_paper_id": "parl.manchester-central.2019-12-12"},
            {"ballot_paper_id": "parl.manchester-central.by.2019-12-12"},
        ]
        expected = [
            {"ballot_paper_id": "parl.manchester-central.2019-12-12"},
            {"ballot_paper_id": "parl.manchester-central.by.2019-12-12"},
            {"ballot_paper_id": "mayor.greater-manchester-ca.2020-05-07"},
            {"ballot_paper_id": "local.manchester.clayton-openshaw.2020-02-27"},
        ]
        self.assertEqual(expected, sort_ballots(initial))
