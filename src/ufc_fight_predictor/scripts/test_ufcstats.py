from ufc_fight_predictor.data.scraper.browser import fetch_page
from ufc_fight_predictor.data.scraper.fights import extract_winner_id, extract_fighters
from pathlib import Path

test_url = "http://www.ufcstats.com/fight-details/afec383a96893ec5"

html = fetch_page(test_url)
html = html.lower()

if "checking your browser" in html:
    print("FAIL: Did not pass browser javascript check")
else:
    print("SUCCESS: You have accessed the ufcstats html")
    #Save the fighter page into an output file
    # Path("tests/captured_html/test_fight.html").write_text(html, encoding="utf-8")
    # print(f"Saved {len(html)} chars to 'tests/captured_html/test_fight.html'")
    print(f"testing extract_winner_id: ")
    fighters = extract_fighters(html)
    extract_winner_id(html, fighters)