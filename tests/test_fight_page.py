from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from ufc_fight_predictor.data.scraper.fights import *

#fight page

FIGHT_FIXTURE_PATH = Path("tests/captured_html/test_fight.html")
EVENT_FIGHT_DIR = Path("tests/captured_html/events/nurmagomedov_song")
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


def test_extract_round_stats_uses_table_headers():
    html = load_fight_fixture()
    soup = BeautifulSoup(html, "lxml")

    for table in soup.find_all("table"):
        header = table.select_one("thead.b-fight-details__table-head_rnd")
        if header is None:
            continue
        header_cells = header.find_all("th")
        headers = [
            cell.get_text(" ", strip=True).lower().rstrip(".")
            for cell in header_cells
        ]
        if "kd" in headers:
            source_index = headers.index("total str")
        elif "head" in headers:
            source_index = headers.index("body")
        else:
            continue

        moved_header = header_cells[source_index].extract()
        header_cells[-1].insert_after(moved_header)
        for row in table.select("tbody tr.b-fight-details__table-row"):
            cells = row.find_all("td", recursive=False)
            moved_cell = cells[source_index].extract()
            cells[-1].insert_after(moved_cell)

    fighter = extract_fighters(html)[0]
    assert extract_round_stats(str(soup), fighter) == extract_round_stats(
        html, fighter
    )


def test_extract_round_stats_missing_column():
    html = load_fight_fixture()
    soup = BeautifulSoup(html, "lxml")

    for header in soup.select("thead.b-fight-details__table-head_rnd"):
        for cell in header.find_all("th"):
            if cell.get_text(" ", strip=True).lower() == "body":
                cell.string = "torso"

    fighter = extract_fighters(html)[0]
    with pytest.raises(ValueError, match="body"):
        extract_round_stats(str(soup), fighter)


def test_comprehensive():
    html_paths = sorted(EVENT_FIGHT_DIR.glob("*.html"))
    assert html_paths, f"No fight fixtures found in {EVENT_FIGHT_DIR}"

    paired_fields = (
        "sig_strikes",
        "head",
        "body",
        "leg",
        "distance",
        "clinch",
        "ground",
        "total_strikes",
        "takedowns",
    )

    def assert_stats_are_consistent(stats, context):
        values = stats.model_dump(exclude={"fighter_id", "round_number"})

        for field_name, value in values.items():
            assert value >= 0, f"{context}: {field_name} cannot be negative"

        for field_name in paired_fields:
            landed = values[f"{field_name}_landed"]
            attempted = values[f"{field_name}_attempted"]
            assert landed <= attempted, (
                f"{context}: {field_name} landed ({landed}) exceeds "
                f"attempted ({attempted})"
            )

        for suffix in ("landed", "attempted"):
            significant = values[f"sig_strikes_{suffix}"]
            total = values[f"total_strikes_{suffix}"]
            target_total = sum(
                values[f"{target}_{suffix}"]
                for target in ("head", "body", "leg")
            )
            position_total = sum(
                values[f"{position}_{suffix}"]
                for position in ("distance", "clinch", "ground")
            )

            assert significant <= total, (
                f"{context}: significant strikes {suffix} ({significant}) "
                f"exceeds total strikes {suffix} ({total})"
            )
            assert target_total == significant, (
                f"{context}: head/body/leg {suffix} sum ({target_total}) "
                f"does not equal significant strikes {suffix} ({significant})"
            )
            assert position_total == significant, (
                f"{context}: distance/clinch/ground {suffix} sum "
                f"({position_total}) does not equal significant strikes "
                f"{suffix} ({significant})"
            )

    for html_path in html_paths:
        html = html_path.read_text(encoding="utf-8")
        context = html_path.name
        fight_url = (
            "http://www.ufcstats.com/fight-details/"
            f"{html_path.stem}"
        )
        fight = extract_fight(html, fight_url)
        fighters = (fight.fighter_a, fight.fighter_b)
        fighter_ids = {fighter.ufcstats_id for fighter in fighters}

        assert len(fighter_ids) == 2, f"{context}: expected two distinct fighters"
        if fight.winner_id is not None:
            assert fight.winner_id in fighter_ids, (
                f"{context}: winner is missing or is not one of the fighters"
            )

        for field_name in (
            "weight_class",
            "method",
            "end_round",
            "end_time",
            "time_format",
            "referee",
        ):
            value = getattr(fight, field_name)
            assert value.strip(), f"{context}: {field_name} is empty"

        assert fight.end_round.isdigit(), (
            f"{context}: invalid end round {fight.end_round!r}"
        )
        end_round = int(fight.end_round)
        assert 1 <= end_round <= 5, (
            f"{context}: end round {end_round} is outside 1-5"
        )

        minutes, separator, seconds = fight.end_time.partition(":")
        assert separator and minutes.isdigit() and seconds.isdigit(), (
            f"{context}: invalid end time {fight.end_time!r}"
        )
        end_seconds = int(minutes) * 60 + int(seconds)
        assert 0 <= end_seconds <= 300 and int(seconds) < 60, (
            f"{context}: end time {fight.end_time!r} is outside one round"
        )

        format_parts = fight.time_format.split()
        assert (
            len(format_parts) == 2
            and format_parts[0].isdigit()
            and format_parts[1].lower() == "rnd"
        ), f"{context}: invalid time format {fight.time_format!r}"
        scheduled_rounds = int(format_parts[0])
        assert scheduled_rounds in {3, 5} and end_round <= scheduled_rounds, (
            f"{context}: end round {end_round} is incompatible with "
            f"{fight.time_format!r}"
        )

        for fighter in fighters:
            fighter_context = f"{context} ({fighter.name})"
            totals = extract_fight_stats(html, fighter)
            rounds = extract_round_stats(html, fighter)

            assert_stats_are_consistent(totals, fighter_context)
            assert [stats.round_number for stats in rounds] == list(
                range(1, end_round + 1)
            ), f"{fighter_context}: round rows do not match the fight end round"

            for round_stats in rounds:
                round_context = (
                    f"{fighter_context}, round {round_stats.round_number}"
                )
                assert_stats_are_consistent(round_stats, round_context)
                round_limit = (
                    end_seconds
                    if round_stats.round_number == end_round
                    else 300
                )
                assert round_stats.control_seconds <= round_limit, (
                    f"{round_context}: control time exceeds round duration"
                )

            total_values = totals.model_dump(exclude={"fighter_id"})
            for field_name, expected_total in total_values.items():
                actual_total = sum(
                    getattr(round_stats, field_name)
                    for round_stats in rounds
                )
                assert actual_total == expected_total, (
                    f"{fighter_context}: round {field_name} sum "
                    f"({actual_total}) does not equal fight total "
                    f"({expected_total})"
                )