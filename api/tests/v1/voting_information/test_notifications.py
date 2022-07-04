from django.test import TestCase
from voting_information.stitcher import NotificationsMaker

nometa = {
    "ballot_paper_id": "local.nometa.2018-05-03",
    "cancelled": False,
    "metadata": None,
}

id_pilot = {
    "ballot_paper_id": "local.id-pilot.2018-05-03",
    "cancelled": False,
    "metadata": {
        "2019-05-02-id-pilot": {
            "detail": "Voters in Woking will be required to show photo ID before they can vote.",
            "title": "You need to show ID to vote at this election",
            "url": "https://www.woking.gov.uk/voterid",
        }
    },
}

cancelled = {
    "ballot_paper_id": "local.cancelled.2018-05-03",
    "cancelled": True,
    "metadata": {
        "cancelled_election": {
            "detail": "This election was cancelled due to death of a candidate.",
            "title": "Cancelled Election",
            "url": "https://foo.bar/baz",
        }
    },
}


class NotificationsMakerTests(TestCase):
    def test_no_notifications(self):
        ballots = [nometa, nometa]
        nm = NotificationsMaker(ballots)
        self.assertEqual([], nm.notifications)

    def test_two_elections_one_cancelled(self):
        ballots = [nometa, cancelled]
        nm = NotificationsMaker(ballots)
        # if one or more elections are going ahead,
        # we don't notify about the cancelled one
        self.assertEqual([], nm.notifications)

    def test_one_cancelled_election(self):
        ballots = [cancelled]
        nm = NotificationsMaker(ballots)
        notifications = nm.notifications
        self.assertEqual(1, len(notifications))
        self.assertEqual("Cancelled Election", notifications[0]["title"])
        self.assertEqual("cancelled_election", notifications[0]["type"])

    def test_multiple_cancelled_elections(self):
        ballots = [cancelled, cancelled]
        nm = NotificationsMaker(ballots)
        notifications = nm.notifications
        self.assertEqual(1, len(notifications))
        self.assertEqual("Cancelled Election", notifications[0]["title"])
        self.assertEqual("cancelled_election", notifications[0]["type"])

    def test_cancelled_with_pilot(self):
        ballots = [
            {
                "ballot_paper_id": "local.cancelled.2018-05-03",
                "cancelled": True,
                "metadata": {
                    "2019-05-02-id-pilot": {
                        "detail": "Voters in Woking will be required to show photo ID before they can vote.",
                        "title": "You need to show ID to vote at this election",
                        "url": "https://www.woking.gov.uk/voterid",
                    },
                    "cancelled_election": {
                        "detail": "This election was cancelled due to death of a candidate.",
                        "title": "Cancelled Election",
                        "url": "https://foo.bar/baz",
                    },
                },
            }
        ]
        nm = NotificationsMaker(ballots)
        notifications = nm.notifications
        self.assertEqual(1, len(notifications))
        # in this case, we want to notify about the cancelled election
        # but the id pilot is irrelevant
        self.assertEqual("Cancelled Election", notifications[0]["title"])
        self.assertEqual("cancelled_election", notifications[0]["type"])

    def test_id_pilot(self):
        ballots = [nometa, id_pilot]
        nm = NotificationsMaker(ballots)
        notifications = nm.notifications
        self.assertEqual(1, len(notifications))
        self.assertEqual(
            "You need to show ID to vote at this election", notifications[0]["title"]
        )
        self.assertEqual("voter_id", notifications[0]["type"])

    def test_northern_ireland(self):
        ballots = [
            {
                "ballot_paper_id": "local.northern-ireland.2018-05-03",
                "cancelled": False,
                "metadata": {
                    "ni-voter-id": {
                        "url": "http://www.eoni.org.uk/Vote/Voting-at-a-polling-place",
                        "title": "You need to show photographic ID to vote in this election",
                        "detail": "Voters in Northern Ireland are required to show one form of photo ID, like a passport or driving licence.",
                    }
                },
            }
        ]
        nm = NotificationsMaker(ballots)
        notifications = nm.notifications
        self.assertEqual(1, len(notifications))
        self.assertEqual(
            "You need to show photographic ID to vote in this election",
            notifications[0]["title"],
        )
        self.assertEqual("voter_id", notifications[0]["type"])
