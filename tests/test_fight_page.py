from pathlib import Path

import pytest

from ufc_fight_predictor.data.scraper.fights import *

#fight page

FIGHT_FIXTURE_PATH = Path("tests/captured_html/test_fight.html")
# FIGHT_URL = 

def load_fight_fixture():
    return FIGHT_FIXTURE_PATH.read_text(encoding="utf8")

def test_extract_fighters():
    html = load_fight_fixture()
    fighters = extract_fighters(html)
    assert len(fighters) == 2


def test_extract_fight_metadata():
    html = load_fight_fixture()
    weight, method, round, time, time_format, referee = (extract_fight_metadata(html))
    assert weight == "flyweight"
    assert method == "decision - unanimous"
    assert round == "3"
    assert time == "5:00"
    assert time_format == "3 rnd"
    assert referee == "lukasz bosacki"

def test_extract_fight():
    html = load_fight_fixture()
    fight = extract_fight(html, "http://www.ufcstats.com/event-details/872b018076f831b0")
    assert fight is not None
    print(f"Fight: {fight}")


def test_extract_fight_stats():
    html = load_fight_fixture()
    fighters = {
        fighter.ufcstats_id: fighter
        for fighter in extract_fighters(html)
    }
    expected_stats = {
        "c96d9178c9ed9e62": {
            "knockdowns": 0,
            "sig_strikes_landed": 90,
            "sig_strikes_attempted": 261,
            "head_landed": 44,
            "head_attempted": 191,
            "body_landed": 11,
            "body_attempted": 27,
            "leg_landed": 35,
            "leg_attempted": 43,
            "distance_landed": 87,
            "distance_attempted": 255,
            "clinch_landed": 3,
            "clinch_attempted": 6,
            "ground_landed": 0,
            "ground_attempted": 0,
            "total_strikes_landed": 93,
            "total_strikes_attempted": 265,
            "takedowns_landed": 2,
            "takedowns_attempted": 11,
            "submission_attempts": 0,
            "reversals": 0,
            "control_seconds": 34,
        },
        "32ab52e5de93092d": {
            "knockdowns": 0,
            "sig_strikes_landed": 136,
            "sig_strikes_attempted": 254,
            "head_landed": 122,
            "head_attempted": 236,
            "body_landed": 14,
            "body_attempted": 18,
            "leg_landed": 0,
            "leg_attempted": 0,
            "distance_landed": 129,
            "distance_attempted": 245,
            "clinch_landed": 7,
            "clinch_attempted": 9,
            "ground_landed": 0,
            "ground_attempted": 0,
            "total_strikes_landed": 136,
            "total_strikes_attempted": 254,
            "takedowns_landed": 1,
            "takedowns_attempted": 3,
            "submission_attempts": 0,
            "reversals": 0,
            "control_seconds": 29,
        },
    }

    for fighter_id, expected in expected_stats.items():
        stats = extract_fight_stats(html, fighters[fighter_id])
        assert stats.model_dump() == {"fighter_id": fighter_id, **expected}


def test_extract_fight_stats_missing_fighter():
    html = load_fight_fixture()
    fighter = Fighter(
        ufcstats_id="missing",
        name="Missing Fighter",
        url="http://www.ufcstats.com/fighter-details/missing",
    )

    with pytest.raises(ValueError, match="missing"):
        extract_fight_stats(html, fighter)


def test_extract_round_stats():
    html = load_fight_fixture()
    fighters = {
        fighter.ufcstats_id: fighter
        for fighter in extract_fighters(html)
    }
    expected_rounds = {
        "c96d9178c9ed9e62": [
            (1, 39, 91, 20, 5, 14, 39, 0, 0, 40, 93, 2, 3, 18),
            (2, 27, 78, 10, 4, 13, 24, 3, 0, 28, 79, 0, 4, 16),
            (3, 24, 92, 14, 2, 8, 24, 0, 0, 25, 93, 0, 4, 0),
        ],
        "32ab52e5de93092d": [
            (1, 24, 55, 21, 3, 0, 21, 3, 0, 24, 55, 0, 0, 0),
            (2, 47, 85, 44, 3, 0, 44, 3, 0, 47, 85, 1, 2, 29),
            (3, 65, 114, 57, 8, 0, 64, 1, 0, 65, 114, 0, 1, 0),
        ],
    }

    for fighter_id, expected in expected_rounds.items():
        fighter = fighters[fighter_id]
        rounds = extract_round_stats(html, fighter)
        actual = [
            (
                stats.round_number,
                stats.sig_strikes_landed,
                stats.sig_strikes_attempted,
                stats.head_landed,
                stats.body_landed,
                stats.leg_landed,
                stats.distance_landed,
                stats.clinch_landed,
                stats.ground_landed,
                stats.total_strikes_landed,
                stats.total_strikes_attempted,
                stats.takedowns_landed,
                stats.takedowns_attempted,
                stats.control_seconds,
            )
            for stats in rounds
        ]
        assert actual == expected

        fight_totals = extract_fight_stats(
            html, fighter
        ).model_dump(exclude={"fighter_id"})
        for field_name, expected_total in fight_totals.items():
            assert sum(
                getattr(round_stats, field_name)
                for round_stats in rounds
            ) == expected_total


def test_extract_round_stats_missing_fighter():
    html = load_fight_fixture()
    fighter = Fighter(
        ufcstats_id="missing",
        name="Missing Fighter",
        url="http://www.ufcstats.com/fighter-details/missing",
    )

    with pytest.raises(ValueError, match="missing"):
        extract_round_stats(html, fighter)