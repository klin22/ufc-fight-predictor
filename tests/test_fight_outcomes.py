from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from pydantic import ValidationError

from ufc_fight_predictor.data.scraper.fights import extract_fight, extract_fight_outcome
from ufc_fight_predictor.data.scraper.models import Fight

FIXTURE = Path("tests/captured_html/test_fight.html")
URL = "http://www.ufcstats.com/fight-details/example"


def result_html(status_a: str, status_b: str) -> str:
    """Keep the captured page structure, replacing only its result markers."""
    soup = BeautifulSoup(FIXTURE.read_text(), "lxml")
    markers = soup.select(".b-fight-details__person-status")
    markers[0].string = status_a
    markers[1].string = status_b
    return str(soup)


@pytest.mark.parametrize(
    "statuses,outcome,winner_index",
    [
        (("W", "L"), "winner", 0),
        (("L", "W"), "winner", 1),
        (("D", "D"), "draw", None),
        (("NC", "NC"), "no_contest", None),
        ((" nc ", "nc"), "no_contest", None),
    ],
)
def test_extract_fight_outcomes(statuses, outcome, winner_index):
    fight = extract_fight(result_html(*statuses), URL)
    assert fight.outcome == outcome
    fighters = [fight.fighter_a, fight.fighter_b]
    assert fight.winner_id == (
        None if winner_index is None else fighters[winner_index].ufcstats_id
    )
    assert Fight.model_validate_json(fight.model_dump_json()) == fight


@pytest.mark.parametrize(
    "statuses",
    [
        ("W", "W"),
        ("L", "L"),
        ("W", "D"),
        ("D", "NC"),
        ("NC", "L"),
        ("", ""),
        ("unknown", "unknown"),
    ],
)
def test_invalid_markers_are_not_silently_classified(statuses):
    with pytest.raises(ValueError, match="result markers"):
        extract_fight_outcome(result_html(*statuses))


@pytest.mark.parametrize(
    "selector",
    [
        ".b-fight-details__person-status",
        ".b-fight-details__person-link",
        ".b-fight-details__person",
    ],
)
def test_missing_result_markup_fails(selector):
    soup = BeautifulSoup(result_html("D", "D"), "lxml")
    soup.select_one(selector).decompose()
    with pytest.raises(ValueError):
        extract_fight_outcome(str(soup))


@pytest.mark.parametrize(
    "statuses,method,outcome",
    [
        (("D", "D"), "Decision - Majority", "draw"),
        (("NC", "NC"), "Overturned", "no_contest"),
        (("NC", "NC"), "Could Not Continue", "no_contest"),
        (("L", "W"), "DQ", "winner"),
    ],
)
def test_method_is_independent_of_outcome(statuses, method, outcome):
    html = result_html(*statuses).replace("decision - unanimous", method)
    fight = extract_fight(html, URL)
    assert fight.outcome == outcome
    assert fight.method == method


@pytest.mark.parametrize(
    "outcome,winner",
    [
        ("winner", None),
        ("winner", "unrelated-fighter"),
        ("draw", "participant"),
        ("no_contest", "participant"),
        ("unknown", None),
    ],
)
def test_domain_rejects_inconsistent_results(outcome, winner):
    data = extract_fight(result_html("W", "L"), URL).model_dump()
    data.update(
        outcome=outcome,
        winner_id=(
            data["fighter_a"]["ufcstats_id"] if winner == "participant" else winner
        ),
    )
    with pytest.raises(ValidationError):
        Fight.model_validate(data)


def test_domain_requires_explicit_outcome_for_legacy_json():
    data = extract_fight(result_html("D", "D"), URL).model_dump()
    del data["outcome"]
    with pytest.raises(ValidationError, match="outcome"):
        Fight.model_validate(data)
