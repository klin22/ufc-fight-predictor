from bs4 import BeautifulSoup

from ufc_fight_predictor.data.scraper.fights import _parse_int
from ufc_fight_predictor.data.scraper.models import FighterProfile

MISSING = {"", "--"}


def _parse_height(value: str) -> int | None:
    # UFCStats lists height as feet and inches, e.g. 5' 7"
    if value in MISSING:
        return None
    feet, separator, inches = value.partition("'")
    if not separator:
        raise ValueError(f"Invalid height value: {value}")
    return _parse_int(feet, "height") * 12 + _parse_int(
        inches.strip().removesuffix('"'), "height"
    )


def _parse_reach(value: str) -> int | None:
    if value in MISSING:
        return None
    return _parse_int(value.removesuffix('"'), "reach")


def extract_fighter_profile(html: str, ufcstats_id: str) -> FighterProfile:
    soup = BeautifulSoup(html, "lxml")
    # The first list is the profile; later lists hold career averages.
    profile_list = soup.select_one(".b-list__box-list")
    if profile_list is None:
        raise ValueError("No profile list on fighter page")

    values = {}
    for item in profile_list.select(".b-list__box-list-item"):
        key, _separator, value = item.get_text(" ", strip=True).partition(":")
        values[key.strip().lower()] = value.strip()

    required = {"height", "reach", "stance", "dob"}
    missing = [key for key in required if key not in values]
    if missing:
        raise ValueError(f"Missing profile fields: {', '.join(missing)}")

    return FighterProfile(
        ufcstats_id=ufcstats_id,
        height_in=_parse_height(values["height"]),
        reach_in=_parse_reach(values["reach"]),
        stance=None if values["stance"] in MISSING else values["stance"],
        dob=None if values["dob"] in MISSING else values["dob"],
    )
