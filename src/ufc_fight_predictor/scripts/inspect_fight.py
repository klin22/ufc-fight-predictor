from pathlib import Path

from ufc_fight_predictor.data.scraper.fights import extract_fighters


html = Path(
    "tests/captured_html/test_fight.html"
).read_text(encoding="utf-8")

fighters = extract_fighters(html)

for fighter in fighters:
    print(fighter)