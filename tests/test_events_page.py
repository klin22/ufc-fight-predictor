from ufc_fight_predictor.data.scraper.events import fetch_page
from ufc_fight_predictor.data.scraper.fights import extract_winner_id, extract_fighters
from pathlib import Path

#fight page
test_url = "http://www.ufcstats.com/statistics/events/completed"
output_path = Path("tests/captured_html/test_event_page.html")

html = fetch_page(test_url)
html = html.lower()

if "checking your browser" in html:
    print("FAIL: Did not pass browser javascript check")
else:
    print("SUCCESS: You have accessed the ufcstats html")
    #Save the fighter page into an output file
    #only write if test_fight_page doesn't currently exist
    if not output_path.exists():
        output_path.write_text(html, encoding="utf-8")
        print(f"Saved {len(html)} chars to 'tests/captured_html/test_event_page.html'")
    else:
        print("test_event_page.html already exists, skipping...")