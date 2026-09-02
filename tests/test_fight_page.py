from ufc_fight_predictor.data.scraper.fights_page import fetch_page
from ufc_fight_predictor.data.scraper.fights import extract_winner_id, extract_fighters
from pathlib import Path

#fight page
test_url = "http://www.ufcstats.com/fight-details/afec383a96893ec5"
output_path = "tests/captured_html/test_fight_page.py"

html = fetch_page(test_url)
html = html.lower()

if "checking your browser" in html:
    print("FAIL: Did not pass browser javascript check")
else:
    print("SUCCESS: You have accessed the ufcstats html")
    #Save the fighter page into an output file
    #only write if test_fight_page doesn't currently exist
    if not output_path.exists():
        output_path.Path("tests/captured_html/test_fight.html").write_text(html, encoding="utf-8")
        print(f"Saved {len(html)} chars to 'tests/captured_html/test_fight_page.html'")
    else:
        print("test_fight_page.py already exists, skipping...")
    print(f"testing extract_winner_id: ")
    fighters = extract_fighters(html)
    extract_winner_id(html, fighters)