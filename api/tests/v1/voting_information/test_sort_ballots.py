from voting_information.stitcher import sort_ballots


def test_sorter():
    initial = [
        {
            "poll_open_date": "2020-02-27",
            "ballots": [
                {
                    "ballot_paper_id": "local.manchester.clayton-openshaw.2020-02-27"
                },
                {"ballot_paper_id": "mayor.greater-manchester-ca.2020-02-27"},
                {"ballot_paper_id": "parl.manchester-central.2020-02-27"},
                {"ballot_paper_id": "parl.manchester-central.by.2020-02-27"},
            ],
        },
        {
            "poll_open_date": "2020-05-07",
            "ballots": [
                {"ballot_paper_id": "gla.a.2020-05-07"},
                {"ballot_paper_id": "gla.c.lambeth-and-southwark.2020-05-07"},
                {"ballot_paper_id": "mayor.london.2020-05-07"},
            ],
        },
    ]
    expected = [
        {
            "poll_open_date": "2020-02-27",
            "ballots": [
                {"ballot_paper_id": "parl.manchester-central.2020-02-27"},
                {"ballot_paper_id": "parl.manchester-central.by.2020-02-27"},
                {"ballot_paper_id": "mayor.greater-manchester-ca.2020-02-27"},
                {
                    "ballot_paper_id": "local.manchester.clayton-openshaw.2020-02-27"
                },
            ],
        },
        {
            "poll_open_date": "2020-05-07",
            "ballots": [
                {"ballot_paper_id": "mayor.london.2020-05-07"},
                {"ballot_paper_id": "gla.c.lambeth-and-southwark.2020-05-07"},
                {"ballot_paper_id": "gla.a.2020-05-07"},
            ],
        },
    ]
    assert sort_ballots(initial, {}) == expected


def test_mayor_types_sorted():
    initial = [
        {
            "poll_open_date": "2020-05-07",
            "ballots": [
                {"ballot_paper_id": "mayor.liverpool.2020-05-07"},
                {"ballot_paper_id": "mayor.liverpool-city-ca.2020-05-07"},
            ],
        }
    ]
    sort_keys = {
        "mayor.liverpool.2020-05-07": "local-authority",
        "mayor.liverpool-city-ca.2020-05-07": "combined-authority",
    }
    expected = [
        {
            "poll_open_date": "2020-05-07",
            "ballots": [
                {"ballot_paper_id": "mayor.liverpool-city-ca.2020-05-07"},
                {"ballot_paper_id": "mayor.liverpool.2020-05-07"},
            ],
        }
    ]
    assert sort_ballots(initial, sort_keys) == expected
