import json
from pathlib import Path
from playwright.sync_api import Error as PlaywrightError


from ufc_fight_predictor.data.scraper.browser import fetch_page
from ufc_fight_predictor.data.scraper.events import extract_events, extract_fight_urls

EVENTS_PAGE = "http://www.ufcstats.com/statistics/events/completed"
OUTPUT_PATH = Path("tests/captured_html/events/van_pantoja/event.html")

event_fight_selector = ".b-statistics__section"
fight_selector = ".b-fight-details__table"
html = fetch_page(EVENTS_PAGE, event_fight_selector)


events = extract_events(html)

van_pantoja = events[0]
van_pantoja_page = fetch_page(events[0].url, fight_selector)

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
with OUTPUT_PATH.open("w") as file:
    json.dump(
        van_pantoja.model_dump(mode="json"),
        file,
        indent=2
    )