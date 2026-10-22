from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from ufc_fight_predictor.data.database.models import Base
from ufc_fight_predictor.data.database.repository import (
    save_event,
    save_fight,
    save_fight_stats,
    save_fighter,
    save_round_stats,
)
from ufc_fight_predictor.data.scraper.fights import (
    extract_fight,
    extract_fight_stats,
    extract_round_stats,
)
from ufc_fight_predictor.data.scraper.models import Event

FIXTURE_PATH = Path(__file__).parent / "captured_html/test_fight.html"
FIGHT_URL = "http://www.ufcstats.com/fight-details/missing-control"


def replace_stat_values(html: str, value: str, column: str = "ctrl") -> str:
    soup = BeautifulSoup(html, "lxml")
    for table in soup.find_all("table"):
        header = table.select_one(
            "thead.b-fight-details__table-head, thead.b-fight-details__table-head_rnd"
        )
        if header is None:
            continue
        headers = [
            cell.get_text(" ", strip=True).lower().rstrip(".")
            for cell in header.find_all("th")
        ]
        if column not in headers:
            continue
        for row in table.select("tbody tr"):
            cells = row.find_all("td", recursive=False)
            for text in cells[headers.index(column)].select(
                "p.b-fight-details__table-text"
            ):
                text.string = value
    return str(soup)


@pytest.mark.parametrize(
    "column,value,expected",
    [
        ("ctrl", "--", {"control_seconds": None}),
        ("ctrl", "", {"control_seconds": None}),
        ("ctrl", "0:00", {"control_seconds": 0}),
        ("ctrl", "1:23", {"control_seconds": 83}),
        ("kd", "--", {"knockdowns": None}),
        ("kd", "0", {"knockdowns": 0}),
        ("head", "--", {"head_landed": None, "head_attempted": None}),
        ("head", "1 of --", {"head_landed": 1, "head_attempted": None}),
    ],
)
def test_available_and_missing_stats_survive_extraction_and_persistence(
    column, value, expected
):
    html = replace_stat_values(FIXTURE_PATH.read_text(), value, column)
    domain_fight = extract_fight(html, FIGHT_URL)
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    try:
        with Session(engine) as session:
            event = save_event(
                session,
                Event(
                    event_id="missing-control",
                    name="Missing control fixture",
                    date="August 29, 2026",
                    location="Test",
                    url="http://www.ufcstats.com/event-details/missing-control",
                    fights=[],
                ),
            )
            fighters = [domain_fight.fighter_a, domain_fight.fighter_b]
            saved_fighters = [save_fighter(session, fighter) for fighter in fighters]
            fight = save_fight(session, domain_fight, event, *saved_fighters)
            saved_stats = []
            for fighter, saved_fighter in zip(fighters, saved_fighters):
                stats = extract_fight_stats(html, fighter)
                assert all(
                    getattr(stats, field) == value for field, value in expected.items()
                )
                saved_stats.append(
                    save_fight_stats(session, stats, fight, saved_fighter)
                )
                rounds = extract_round_stats(html, fighter)
                assert rounds
                for round_stats in rounds:
                    assert all(
                        getattr(round_stats, field) == value
                        for field, value in expected.items()
                    )
                    saved_stats.append(
                        save_round_stats(session, round_stats, fight, saved_fighter)
                    )
            session.commit()
            session.expire_all()
            assert all(
                getattr(stats, field) == value
                for stats in saved_stats
                for field, value in expected.items()
            )
    finally:
        engine.dispose()


@pytest.mark.parametrize("value", ["unknown", "bad:time"])
@pytest.mark.parametrize("extractor", [extract_fight_stats, extract_round_stats])
def test_malformed_control_times_still_fail(value, extractor):
    html = replace_stat_values(FIXTURE_PATH.read_text(), value)
    fighter = extract_fight(html, FIGHT_URL).fighter_a
    with pytest.raises(ValueError, match="Invalid numeric"):
        extractor(html, fighter)


def test_missing_significant_tables_preserve_totals_and_rounds():
    soup = BeautifulSoup(FIXTURE_PATH.read_text(), "lxml")
    for table in soup.find_all("table"):
        if any(
            cell.get_text(strip=True).lower() == "head" for cell in table.select("th")
        ):
            table.decompose()
    html = str(soup)
    fighter = extract_fight(html, FIGHT_URL).fighter_a
    stats = extract_fight_stats(html, fighter)
    assert stats.sig_strikes_landed == 90
    assert stats.head_landed is None
    rounds = extract_round_stats(html, fighter)
    assert len(rounds) == 3
    assert rounds[0].sig_strikes_landed == 39
    assert rounds[0].head_landed is None


def test_missing_identifying_columns_preserve_other_stats():
    soup = BeautifulSoup(FIXTURE_PATH.read_text(), "lxml")
    for table in soup.find_all("table"):
        header = table.select_one(
            "thead.b-fight-details__table-head, thead.b-fight-details__table-head_rnd"
        )
        if header is None:
            continue
        cells = header.find_all("th")
        headers = [cell.get_text(strip=True).lower() for cell in cells]
        column = "kd" if "kd" in headers else "head"
        index = headers.index(column)
        cells[index].decompose()
        for row in table.select("tbody tr"):
            row.find_all("td", recursive=False)[index].decompose()
    html = str(soup)
    fighter = extract_fight(html, FIGHT_URL).fighter_a
    stats = extract_fight_stats(html, fighter)
    assert stats.knockdowns is None
    assert stats.head_landed is None
    assert stats.sig_strikes_landed == 90
    assert stats.body_landed == 11
    rounds = extract_round_stats(html, fighter)
    assert len(rounds) == 3
    assert rounds[0].knockdowns is None
    assert rounds[0].sig_strikes_landed == 39


def test_all_unavailable_values_do_not_create_empty_stats():
    soup = BeautifulSoup(FIXTURE_PATH.read_text(), "lxml")
    for row in soup.select("table tbody tr"):
        for cell in row.find_all("td", recursive=False)[1:]:
            for text in cell.select("p.b-fight-details__table-text"):
                text.string = "--"
    html = str(soup)
    fighter = extract_fight(html, FIGHT_URL).fighter_a
    assert extract_fight_stats(html, fighter) is None
    assert extract_round_stats(html, fighter) == []
