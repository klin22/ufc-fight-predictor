from bs4 import BeautifulSoup

from ufc_fight_predictor.data.scraper.models import Fighter, Fight

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

def extract_fight_metadata(html:str) -> tuple[
    str, str, str, str, str, str]:
    soup = BeautifulSoup(html, "lxml")
    weight_el = soup.select_one(".b-fight-details__fight-title").get_text()
    if weight_el is None:
        raise ValueError("No weight value for this element")

    values = {}
    for item in soup.select(".b-fight-details__text-item_first, " 
                            ".b-fight-details__text-item"):

        text = item.get_text(" ", strip=True)
        key, separator, value = text.partition(":")
        if key.strip().lower() == "time format":
            value = value.split("(", 1)[0].strip()
        values[key.strip().lower()] = value.strip()
    
    required = {"method", "round", "time", "time format", "referee"}
    missing = [key for key in required if values[key] is None]
    if missing:
        raise ValueError(f" Missing metadata: {', '.join(missing)}")

    weight = weight_el.strip().removesuffix(" bout")
    return (
        weight,
        values["method"],
        values["round"],
        values["time"],
        values["time format"],
        values["referee"]
    )

def extract_fight(html:str, url:str) -> Fight:
    fighters = extract_fighters(html)
    winner_id = extract_winner_id(html)
    weight, method, round, time, time_format, referee = (extract_fight_metadata(html))
    url = url

    return Fight(
        fight_id=url.rstrip("/").split("/")[-1],
        url=url,
        fighter_a=fighters[0],
        fighter_b=fighters[1],
        winner_id=winner_id,
        weight=weight,
        method=method,
        round=round,
        time=time,
        time_format=time_format,
        referee=referee
    )



