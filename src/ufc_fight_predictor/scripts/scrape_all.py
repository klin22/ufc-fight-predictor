import logging
from bs4 import BeautifulSoup
from ufc_fight_predictor.data.scraper.browsersession import BrowserSession
from ufc_fight_predictor.data.scraper.events import extract_events

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    browser_session = BrowserSession()
    starting_page = browser_session.starting_page
    starting_html = browser_session.fetch_page(starting_page, 'a[href*="/event-details/"]')
    soup = BeautifulSoup(starting_html, "lxml")
    #get link to all events
    all_link = next(
        (        
            item 
            for item in soup.select(".b-statistics__paginate-link")
            if item.get_text(strip=True).lower() == "all"
                 
        ),
        None,
    )
    if all_link is None:
        raise ValueError("No tab for selecting all events")
    all_url = all_link["href"]
    print(f"all_link: {all_url}")
    all_html = browser_session.fetch_page(all_url, 'a[href*="/event-details/"]')
    print(f"All events page fetched, extracting events...")
    all_events = extract_events(all_html)
    print(f"Events: {all_events}")