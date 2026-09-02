from bs4 import BeautifulSoup

from ufc_fight_predictor.data.scraper.models import Fighter

FIGHTER_SELECTOR = "a.b-fight-details__person-link"
def extract_fighters(html):
    soup = BeautifulSoup(html, "lxml")
    fighter_links = soup.select(
        FIGHTER_SELECTOR
    )

    fighters = []

    for link in fighter_links:
        url = link["href"]

        fighter = Fighter(
            ufcstats_id=url.rstrip("/").split("/")[-1],
            name=link.get_text(strip=True),
            url=url,
        )

        fighters.append(fighter)

    return fighters
#how to extract this into sql? 
    #tables for fighters, fights, fight stats, round stats etc
def extract_winner_id(html:str)-> str:
    soup = BeautifulSoup(html, "lxml")
    for person in soup.select(".b-fight-details__person"):
        link = person.select_one("a.b-fight-details__person-link")
        status_el = person.select_one(".b-fight-details__person-status")
        if link is None or status_el is None:
            continue
        status = status_el.get_text(strip=True).upper()
        print(f"link: {link}")
        print(f"status: {status}")
        if status == "W":
            url = link["href"]
            return url.rstrip("/").split("/")[-1]
    return None


