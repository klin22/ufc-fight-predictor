#go from scrapign to having entries in database. scrape one page for now
#Code flow: browser gets page, each event is visited and fighter values populated
#Try with one event first
#How should this look ideally? Shodl be one module that does
#all this. 
#   Open browser -> extracts -> maps to sqlalchemy
#   Extract event -> event
#   getFights -> list[Fight]
#   getFighters -> fighterStats, roundstats, etc
EVENTS_PAGE = "http://www.ufcstats.com/statistics/events/completed"
from playwright.sync_api import Error as PlaywrightError

from ufc_fight_predictor.data.scraper.browser import fetch_page
from ufc_fight_predictor.data.scraper.events import extract_events, extract_fight_urls
from ufc_fight_predictor.data.scraper.fights import (
    extract_fight,
    extract_fight_stats,
    extract_round_stats,
)
from ufc_fight_predictor.data.scraper.models import (
    Fight,
    Fighter,
    FighterFightStats,
    RoundStats,
)

event_fight_selector = ".b-statistics__section"
fight_selector = ".b-fight-details__table"
html = fetch_page(EVENTS_PAGE, event_fight_selector)


events = extract_events(html)


van_pantoja = fetch_page(events[0].url, fight_selector)
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
    fights.append((fight, 
    fighter_a, 
    fighter_b,
    fighter_a_fstats,
    fighter_b_fstats,
    fighter_a_rstats,
    fighter_b_rstats))

print(fights)

