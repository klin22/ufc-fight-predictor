import json
from pathlib import Path
from playwright.sync_api import Error as PlaywrightError

from ufc_fight_predictor.data.scraper.models import (
    Fight,
    Fighter,
    FighterFightStats,
    RoundStats,
    ScrapedFight
)
from ufc_fight_predictor.data.scraper.browser import fetch_page
from ufc_fight_predictor.data.scraper.events import extract_events, extract_fight_urls
from ufc_fight_predictor.data.scraper.fights import (
    extract_fight,
    extract_fight_stats,
    extract_round_stats,
)
EVENTS_PAGE = "http://www.ufcstats.com/statistics/events/completed"
OUTPUT_PATH = Path("tests/captured_html/events/van_pantoja/fights.html")
VAN_PANTOJA = Path("tests/captured_html/events/van_pantoja/event.html")
event_fight_selector = ".b-statistics__section"
fight_selector = ".b-fight-details__table"

def load_event(path):
    with path.open() as file:
        data = json.load(file)
    return data

event = load_event(VAN_PANTOJA)
print(f"Van Pantoja Event from script: {event}")

van_pantoja = fetch_page(event['url'], fight_selector)
print(f"van_pantoja successfully fetched...")
fight_urls = extract_fight_urls(van_pantoja)
print(f"fight_urls successfully fetched...")
#how to store events and fights for mapping? 
#fight, fighter_a, fighter_b, fight_stats_a, fight_stats_b
#round_stats_a, round_stats_b
fights: list[(
    Fight, 
    Fighter, 
    Fighter, 
    FighterFightStats,
    FighterFightStats,
    RoundStats,
    RoundStats) ] = []

for url in fight_urls:
    #in fight page
    try:
        fight_html = fetch_page(url, ".b-page")
    except PlaywrightError:
        print(f"fight_html: {url} unable to be fetched")
        continue
    
    fight = extract_fight(fight_html, url)
    fighter_a = fight.fighter_a
    fighter_b = fight.fighter_b
    fighter_a_fstats = extract_fight_stats(fight_html, fighter_a)
    fighter_b_fstats = extract_fight_stats(fight_html, fighter_b)
    fighter_a_rstats = extract_round_stats(fight_html, fighter_a)
    fighter_b_rstats = extract_round_stats(fight_html, fighter_b)
    scrapedfight = ScrapedFight(
    fight=fight,
    fighter_a=fighter_a,
    fighter_b=fighter_b,
    fighter_a_fstats=fighter_a_fstats,
    fighter_b_fstats=fighter_b_fstats,
    fighter_a_rstats=fighter_a_rstats,
    fighter_b_rstats=fighter_b_rstats
    )
    fights.append(scrapedfight)

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
with OUTPUT_PATH.open("w") as file:
    json.dump(
        [fight.model_dump(mode="json") for fight in fights],
        file,
        indent=2
    )


