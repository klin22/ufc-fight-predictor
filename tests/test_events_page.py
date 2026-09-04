from ufc_fight_predictor.data.scraper.browser import fetch_page
from ufc_fight_predictor.data.scraper.events import extract_events, extract_fight_urls
from pathlib import Path

#fight page
completed_events_url = "http://www.ufcstats.com/statistics/events/completed"
fight_page_url = "http://www.ufcstats.com/event-details/9d61d8cb1c354867"
FIXTURE_PATH = Path("tests/captured_html/completed_events.html")
FIXTURE_PATH_FIGHTS = Path("tests/captured_html/event_fights.html")
#0: events_selector, 
selectors = ['a.b-statistics__sub-tabs-link[href$="/completed"]', "tr.b-fight-details__table-row"]
html = fetch_page(completed_events_url, selectors[0])
html = html.lower()

#event fights
event_fights_html = fetch_page(fight_page_url, selectors[1])

if "checking your browser" in html:
    print("FAIL: Did not pass browser javascript check")
else:
    print("SUCCESS: You have accessed the ufcstats html")
    
    if not FIXTURE_PATH.exists():
        FIXTURE_PATH.write_text(html, encoding="utf-8")
        print(f"Saved {len(html)} chars to 'tests/captured_html/completed_events.html'")
    else:
        print("completed_events.html already exists, skipping...")

    if not FIXTURE_PATH_FIGHTS.exists():
        FIXTURE_PATH_FIGHTS.write_text(event_fights_html, encoding="utf-8")
        print(f"Saved {len(html)} chars to 'tests/captured_html/event_fights.html'")

    else:
        print("event_fights.html already exists, skipping...")

    print("First 5 events in extract_events...")
    extract_events(html)
    events_list = extract_events(html)
    print(f"Events found: {len(events_list)}")
    for event in events_list[:5]:
        print(event)

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
