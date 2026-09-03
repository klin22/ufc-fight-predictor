from ufc_fight_predictor.data.scraper.browser import fetch_page
from ufc_fight_predictor.data.scraper.events import extract_events
from pathlib import Path

#fight page
test_url = "http://www.ufcstats.com/statistics/events/completed"
FIXTURE_PATH = Path("tests/captured_html/completed_events.html")
#0: events_selector, 
selectors = ['a.b-statistics__sub-tabs-link[href$="/completed"]']
html = fetch_page(test_url, selectors[0])
html = html.lower()

if "checking your browser" in html:
    print("FAIL: Did not pass browser javascript check")
else:
    print("SUCCESS: You have accessed the ufcstats html")
    #Save the fighter page into an output file
    #only write if test_fight_page doesn't currently exist
    if not FIXTURE_PATH.exists():
        FIXTURE_PATH.write_text(html, encoding="utf-8")
        print(f"Saved {len(html)} chars to 'tests/captured_html/completed_events.html'")
    else:
        print("completed_events.html already exists, skipping...")
    print("First 5 events in extract_events...")
    extract_events(html)
    events_list = extract_events(html)
    print(f"Events found: {len(events_list)}")
    for event in events_list[:5]:
        print(event)

def load_fixture():
    return FIXTURE_PATH.read_text(encoding="utf_8")

def test_extract_events():
    html = load_fixture()
    events = extract_events(html)
    assert events[0].name == 'ufc fight night: nurmagomedov vs. song'
    assert events[0].event_id == '9d61d8cb1c354867'

def test_url_uniqueness():
    html = load_fixture()
    events = extract_events(html)
    urls = [event.url for event in events]
    unique_urls = set(urls)
    assert len(unique_urls) == len(events)