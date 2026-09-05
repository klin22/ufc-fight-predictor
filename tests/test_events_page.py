from pathlib import Path

from ufc_fight_predictor.data.scraper.browser import fetch_page
from ufc_fight_predictor.data.scraper.events import extract_events, extract_fight_urls
from ufc_fight_predictor.data.scraper.models import Fight
from ufc_fight_predictor.data.scraper.fights import extract_fight

#fight page
completed_events_url = "http://www.ufcstats.com/statistics/events/completed"
fight_page_url = "http://www.ufcstats.com/event-details/9d61d8cb1c354867"
FIXTURE_PATH = Path("tests/captured_html/completed_events.html")
FIXTURE_PATH_FIGHTS = Path("tests/captured_html/event_fights.html")
#0: events_selector, 


def load_completed_events_fixture():
    return FIXTURE_PATH.read_text(encoding="utf_8")

def load_event_fights_fixture():
    return FIXTURE_PATH_FIGHTS.read_text(encoding="utf_8")

def test_extract_events():
    html = load_completed_events_fixture()
    events = extract_events(html)
    assert events[0].name == 'ufc fight night: nurmagomedov vs. song'
    assert events[0].event_id == '9d61d8cb1c354867'

def test_url_uniqueness():
    html = load_completed_events_fixture()
    events = extract_events(html)
    urls = [event.url for event in events]
    unique_urls = set(urls)
    assert len(unique_urls) == len(events)

def test_extract_fight_urls():
    html = load_event_fights_fixture()
    fight_urls = extract_fight_urls(html)
    assert len(fight_urls) > 0
    assert fight_urls[0] == "http://www.ufcstats.com/fight-details/228fefc6923c40a5"

def test_extract_all_events_fights():
    html = fetch_page(completed_events_url, ".b-statistics__sub-tabs-link")
    print(f"completed events html: {html[:500]}")
    events_list = extract_events(html)
    print(f"events list length = {len(events_list)}")
    for event in events_list[:2]:
        event_html = fetch_page(event.url, ".b-content__title-highlight")
        print(f"event_html = {event_html[:10000]}")
        fight_urls = extract_fight_urls(event_html)
        for fight_url in fight_urls:
            fight_html = fetch_page(fight_url, ".b-fight-details__fight-title")
            fight = extract_fight(fight_html, fight_url)
            event.fights.append(fight)
    
    for event in events_list[:2]:
        print(f"Event {event.name} fights: {event.fights}")
        assert len(event.fights) > 0
    
