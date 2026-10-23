from pathlib import Path

from ufc_fight_predictor.data.scraper.fighters import extract_fighter_profile

FIGHTER_FIXTURE_PATH = Path("tests/captured_html/test_fighter.html")
MISSING_FIXTURE_PATH = Path("tests/captured_html/test_fighter_missing.html")


def test_extract_fighter_profile():
    html = FIGHTER_FIXTURE_PATH.read_text(encoding="utf8")
    profile = extract_fighter_profile(html, "c96d9178c9ed9e62")
    assert profile.model_dump() == {
        "ufcstats_id": "c96d9178c9ed9e62",
        "height_in": 67,
        "reach_in": 66,
        "stance": "Southpaw",
        "dob": "Dec 24, 1986",
    }


def test_extract_fighter_profile_missing_values():
    html = MISSING_FIXTURE_PATH.read_text(encoding="utf8")
    profile = extract_fighter_profile(html, "3e03cec9767d37e6")
    assert profile.model_dump() == {
        "ufcstats_id": "3e03cec9767d37e6",
        "height_in": None,
        "reach_in": None,
        "stance": None,
        "dob": None,
    }
