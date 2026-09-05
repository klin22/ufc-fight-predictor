from pathlib import Path

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