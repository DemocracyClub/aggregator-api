from api.endpoints.v1.voting_information.stitcher import (
    CANCELLATION_REASONS,
    NotificationsMaker,
)

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

pre_eco = {
    "ballot_paper_id": "local.pre-eco.2018-05-03",
    "cancelled": False,
    "metadata": {"pre_eco": {"detail": "Pre-ECO", "title": "Pre-ECO"}},
}

cancelled = {
    "ballot_paper_id": "local.cancelled.2018-05-03",
    "cancelled": True,
    "cancellation_reason": "CANDIDATE_DEATH",
}


def test_no_notifications():
    ballots = [nometa, nometa]
    nm = NotificationsMaker(ballots)
    assert nm.notifications == []


def test_two_elections_one_cancelled():
    ballots = [nometa, cancelled]
    nm = NotificationsMaker(ballots)
    # if one or more elections are going ahead,
    # we don't notify about the cancelled one
    assert nm.notifications == []


def test_one_cancelled_election():
    ballots = [cancelled]
    nm = NotificationsMaker(ballots)
    notifications = nm.notifications
    assert len(notifications) == 1
    assert notifications[0]["title"] == "Cancelled Election"
    assert notifications[0]["type"] == "cancelled_election"
    assert notifications[0]["url"] is None


def test_multiple_cancelled_elections():
    ballots = [cancelled, cancelled]
    nm = NotificationsMaker(ballots)
    notifications = nm.notifications
    assert len(notifications) == 1
    assert notifications[0]["title"] == "Cancelled Election"
    assert notifications[0]["type"] == "cancelled_election"
    assert len(notifications[0]["cancelled_ballots"]) == 2


def test_cancelled_with_pilot():
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
    # in this case, we want to notify about the cancelled election
    # but the id pilot is irrelevant
    assert len(notifications) == 1
    assert notifications[0]["title"] == "Cancelled Election"
    assert notifications[0]["type"] == "cancelled_election"
    assert (
        notifications[0]["url"]
        == ballots[0]["metadata"]["cancelled_election"]["url"]
    )


def test_id_pilot():
    ballots = [nometa, id_pilot]
    nm = NotificationsMaker(ballots)
    notifications = nm.notifications
    assert len(notifications) == 1
    assert (
        notifications[0]["title"]
        == "You need to show ID to vote at this election"
    )
    assert notifications[0]["type"] == "voter_id"


def test_pre_eco_and_id_pilot():
    ballots = [id_pilot, pre_eco]
    nm = NotificationsMaker(ballots)
    notifications = nm.notifications
    assert len(notifications) == 2
    assert (
        notifications[0]["title"]
        == id_pilot["metadata"]["2019-05-02-id-pilot"]["title"]
    )
    assert notifications[0]["type"] == "voter_id"
    assert notifications[1]["title"] == pre_eco["metadata"]["pre_eco"]["title"]
    assert notifications[1]["type"] == "pre_eco"


def test_northern_ireland():
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
    assert len(notifications) == 1
    assert (
        notifications[0]["title"]
        == "You need to show photographic ID to vote in this election"
    )
    assert notifications[0]["type"] == "voter_id"


def test_generate_cancelled_notification():
    nm = NotificationsMaker([cancelled])
    notifications = nm.notifications
    assert notifications[0].get("type") == "cancelled_election"
    assert notifications[0].get("title") == "Cancelled Election"
    assert notifications[0].get("url") is None
    assert (
        notifications[0].get("detail")
        == "The poll for this election will not take place"
    )
    assert len(notifications[0].get("cancelled_ballots")) == 1
    assert (
        notifications[0]["cancelled_ballots"][0]["ballot_paper_id"]
        == cancelled["ballot_paper_id"]
    )
    assert (
        notifications[0]["cancelled_ballots"][0]["detail"]
        == CANCELLATION_REASONS[nm.ballots[0]["cancellation_reason"]]
    )
