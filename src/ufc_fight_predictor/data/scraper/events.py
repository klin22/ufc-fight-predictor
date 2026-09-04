from bs4 import BeautifulSoup
from ufc_fight_predictor.data.scraper.models import Event


def extract_events(html: str) -> list[Event]:
    print("in extract_events")
    events_list = []
    soup = BeautifulSoup(html, "lxml")
    #iterate over all tags
    for event in soup.select(".b-statistics__table-row"):
        # print(f"event: {event}")
        event_link = event.select_one('a[href*="/event-details/"]')
        date_el = event.select_one(".b-statistics__date")
        location_el = event.select_one(".b-statistics__table-col_style_big-top-padding")

        if event_link is None:
            continue
        if date_el is None or location_el is None:
            raise ValueError("Event row is missing date or location")

        url = event_link["href"]
        event_name = event_link.get_text(strip=True)
        e = Event(
            event_id=url.strip("/").split("/")[-1],
            name=event_name,
            date=date_el.get_text(strip=True),
            location=location_el.get_text(" ", strip=True),
            url=url
        )
        events_list.append(e)
    return events_list

#why do i extract fight urls? We can probably access those pages with playwright
#or some equivalent
def extract_fight_urls(html: str) -> list[str] :
    soup = BeautifulSoup(html, "lxml")
    fight_urls = []
    for row in soup.select("tr.b-fight-details__table-row[data-link]"):
        if row is None:
            print("Empty Fight Row Detected")
            continue
        fight_url = row["data-link"]
        fight_urls.append(fight_url)
    print(f"Number of fight_urls extracted: {len(fight_urls)}")
    print(fight_urls)
    return fight_urls
