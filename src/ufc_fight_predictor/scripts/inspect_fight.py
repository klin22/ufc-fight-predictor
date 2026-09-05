from pathlib import Path

from ufc_fight_predictor.data.scraper.fights import extract_fighters
from ufc_fight_predictor.data.scraper.browser import fetch_page
inspect_url = ""
selectors = ['a.b-statistics__sub-tabs-link[href$="/completed"]', "tr.b-fight-details__table-row"]
html = fetch_page(inspect_url, selectors[0])


if "checking your browser" in html.lower():
    print("FAIL: Did not pass browser javascript check")
else:
    print("SUCCESS: You have accessed the ufcstats html")
    
    if not FIXTURE_PATH.exists():
        FIXTURE_PATH.write_text(html, encoding="utf-8")
        print(f"Saved {len(html)} chars to 'tests/captured_html/completed_events.html'")
    else:
        print("completed_events.html already exists, skipping...")

    if not FIXTURE_PATH_FIGHTS.exists():
        print(f"Event fights fixture does not exist")

    print("First 5 events in extract_events...")
    extract_events(html)
    events_list = extract_events(html)
    print(f"Events found: {len(events_list)}")
    for event in events_list[:5]:
        print(event)