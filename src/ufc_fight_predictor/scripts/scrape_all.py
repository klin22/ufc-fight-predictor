import logging

from bs4 import BeautifulSoup
from playwright.sync_api import Error as PlaywrightError

from ufc_fight_predictor.data.database.connection import SessionLocal
from ufc_fight_predictor.data.database.repository import (
    save_event,
    save_fight,
    save_fight_stats,
    save_fighter,
    save_round_stats,
)
from ufc_fight_predictor.data.scraper.browsersession import BrowserSession
from ufc_fight_predictor.data.scraper.events import extract_events, extract_fight_urls
from ufc_fight_predictor.data.scraper.fights import (
    extract_fight,
    extract_fight_stats,
    extract_round_stats,
)
from ufc_fight_predictor.data.database.connection import engine
from ufc_fight_predictor.data.database.models import Base
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
    print("All events page fetched, extracting events...")
    all_events = extract_events(all_html) #list[Event]
    print(f"First 10 events: {all_events[:10]}")

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    try:
        with SessionLocal() as session:
            for domainevent in all_events[:10]:
                event = save_event(session, domainevent)
                url = event.url
                event_html = browser_session.fetch_page(url, 'a[href*="/fight-details/"]')
                fight_urls = extract_fight_urls(event_html)
                fights = []
                for url in fight_urls:
                    #in fight page
                    try:
                        fight_html = browser_session.fetch_page(url, ".b-page")
                    except PlaywrightError:
                        print(f"fight_html: {url} unable to be fetched")
                        continue
                    
                    fight = extract_fight(fight_html, url)
                    fighter_a = fight.fighter_a
                    fighter_b = fight.fighter_b
                    fighter_a_fstats = extract_fight_stats(fight_html, fighter_a)
                    fighter_b_fstats = extract_fight_stats(fight_html, fighter_b)
                    fighter_a_rstats = extract_round_stats(fight_html, fighter_a)
                    fighter_b_rstats = extract_round_stats(fight_html, fighter_b)
            
                    sa_fighter_a = save_fighter(session, fighter_a)
                    sa_fighter_b = save_fighter(session, fighter_b)
                    saved_fight = save_fight(session,
                                            fight,
                                            event,
                                            sa_fighter_a,
                                            sa_fighter_b)
                    sa_fighter_a_fstats = save_fight_stats(session,
                                                            fighter_a_fstats,
                                                            saved_fight,
                                                            sa_fighter_a)
                    sa_fighter_b_fstats = save_fight_stats(session,
                                                            fighter_b_fstats,
                                                            saved_fight,
                                                            sa_fighter_b)
                    for round_stats in fighter_a_rstats:
                        save_round_stats(
                            session,
                            round_stats,
                            saved_fight,
                            sa_fighter_a,
                        )
            
                    for round_stats in fighter_b_rstats:
                        save_round_stats(
                            session,
                            round_stats,
                            saved_fight,
                            sa_fighter_b,
                        )
                print(f"Event {event.name} processed successfully")
            session.commit()
    except Exception:
        logging.exception("Session exception: {Exception}")

