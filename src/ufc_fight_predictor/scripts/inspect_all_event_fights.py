from pathlib import Path

from ufc_fight_predictor.data.scraper.browser import fetch_page
from ufc_fight_predictor.data.scraper.events import extract_fight_urls
from ufc_fight_predictor.data.scraper.fights import extract_fight

event_url = "http://www.ufcstats.com/event-details/9d61d8cb1c354867"
output_dir = Path("tests/captured_html/events/nurmagomedov_song")
event_fight_selector = ".b-fight-details__table-col"
fight_selector = ".b-fight-details__fight-title"


if not output_dir.exists():
    print(f"output_dir {output_dir} does not exist")

#extract each fight into an html

html = fetch_page(event_url, event_fight_selector)
fight_urls = extract_fight_urls(html)

for fight_url in fight_urls:
    fight_html = fetch_page(fight_url, fight_selector)
    fight = extract_fight(fight_html, fight_url)
    fighter_a = fight.fighter_a
    fighter_b = fight.fighter_b
    fighter_a_name = "".join(fighter_a.name.split())
    fighter_b_name = "".join(fighter_b.name.split())
    output_path = (output_dir) / f"{fighter_a_name}_{fighter_b_name}.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(fight_html, encoding="utf-8")
    print(f"Wrote {len(fight_html)} chars to: {output_path}")