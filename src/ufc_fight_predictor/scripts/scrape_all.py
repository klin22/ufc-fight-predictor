import argparse
import json
import logging
from pathlib import Path

from bs4 import BeautifulSoup
from sqlalchemy import Column, ForeignKey, String, Table, select
from sqlalchemy.orm import Session

from ufc_fight_predictor.data.database.connection import SessionLocal, engine
from ufc_fight_predictor.data.database.models import Base, Event, Fighter
from ufc_fight_predictor.data.database.repository import (
    save_event,
    save_fight,
    save_fight_stats,
    save_fighter,
    save_fighter_profile,
    save_round_stats,
)
from ufc_fight_predictor.data.scraper.browsersession import BrowserSession
from ufc_fight_predictor.data.scraper.events import extract_events, extract_fight_urls
from ufc_fight_predictor.data.scraper.fighters import extract_fighter_profile
from ufc_fight_predictor.data.scraper.fights import (
    extract_fight,
    extract_fight_stats,
    extract_round_stats,
)

logger = logging.getLogger(__name__)

FAILED_URLS_PATH = Path("data/raw/failed_urls.json")
# Keep progress in the same transaction as the event's data.
COMPLETED_EVENTS = Table(
    "scrape_completed_events",
    Base.metadata,
    Column(
        "event_id",
        String,
        ForeignKey("events.ufcstats_id", ondelete="CASCADE"),
        primary_key=True,
    ),
)
# Marks fighters whose profile page was saved, including pages with no data.
COMPLETED_FIGHTERS = Table(
    "scrape_completed_fighters",
    Base.metadata,
    Column(
        "fighter_id",
        String,
        ForeignKey("fighters.ufcstats_id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


def record_failure(
    failed_urls: list[dict[str, str]],
    url: str,
    page_type: str,
    stage: str,
    error: Exception,
) -> None:
    failed_urls.append(
        {
            "url": url,
            "page_type": page_type,
            "stage": stage,
            "error": f"{type(error).__name__}: {error}",
        }
    )


def scrape_all(*, reset: bool = False, retry_failed: bool = False) -> None:
    """Scrape events and fights, writing a failure report on exit.

    The report is relative to the working directory and replaced on each run.
    Retry mode removes entries only after their data has been committed.
    Database errors abort the run rather than being recorded as scrape failures.
    Completed events are skipped unless reset is explicitly requested.
    """
    if reset and retry_failed:
        raise ValueError("Cannot reset the database while retrying failed URLs")
    failed_urls: list[dict[str, str]] = (
        json.loads(FAILED_URLS_PATH.read_text(encoding="utf-8")) if retry_failed else []
    )
    if retry_failed and any(failure["page_type"] != "fight" for failure in failed_urls):
        raise ValueError(
            "Use normal resume for event or listing failures; retry mode supports fight URLs"
        )
    try:
        if retry_failed:
            retry_fights(failed_urls)
        else:
            scrape_events(failed_urls, reset=reset)
    finally:
        FAILED_URLS_PATH.parent.mkdir(parents=True, exist_ok=True)
        FAILED_URLS_PATH.write_text(
            json.dumps(failed_urls, indent=2) + "\n", encoding="utf-8"
        )
        print(f"Failed URLs: {len(failed_urls)}. Report: {FAILED_URLS_PATH}")


def retry_fights(failed_urls: list[dict[str, str]]) -> None:
    """Retry listed fights; leave event completion markers unchanged."""
    if not failed_urls:
        return
    browser_session = BrowserSession()
    for url in dict.fromkeys(failure["url"] for failure in failed_urls):
        remaining_failures: list[dict[str, str]] = []
        with SessionLocal.begin() as session:
            scrape_fight(browser_session, session, url, remaining_failures)
        failed_urls[:] = [failure for failure in failed_urls if failure["url"] != url]
        failed_urls.extend(remaining_failures)


def scrape_fight(
    browser_session: BrowserSession,
    session: Session,
    url: str,
    failed_urls: list[dict[str, str]],
    event: Event | None = None,
) -> None:
    stage = "fetch"
    try:
        fight_html = browser_session.fetch_page(url, ".b-page")
        stage = "extract"
        fight = extract_fight(fight_html, url)
        if event is None:
            event_link = BeautifulSoup(fight_html, "lxml").select_one(
                '.b-content__title a[href*="/event-details/"]'
            )
            if event_link is None:
                raise ValueError("Missing parent event link")
            event_id = event_link["href"].rstrip("/").split("/")[-1]
    except Exception as error:
        record_failure(failed_urls, url, "fight", stage, error)
        logger.exception("Failed to %s fight page %s", stage, url)
        return

    if event is None:
        event = session.scalar(select(Event).where(Event.ufcstats_id == event_id))
        if event is None:
            raise ValueError(
                f"Parent event {event_id} is not saved; run normal resume first"
            )

    fighter_a = save_fighter(session, fight.fighter_a)
    fighter_b = save_fighter(session, fight.fighter_b)
    saved_fight = save_fight(session, fight, event, fighter_a, fighter_b)
    for fighter, saved_fighter in (
        (fight.fighter_a, fighter_a),
        (fight.fighter_b, fighter_b),
    ):
        try:
            stats = extract_fight_stats(fight_html, fighter)
        except Exception as error:
            record_failure(failed_urls, url, "fight", "extract", error)
            logger.exception("Failed to extract fight stats for %s", url)
        else:
            save_fight_stats(session, stats, saved_fight, saved_fighter)

        try:
            rounds = extract_round_stats(fight_html, fighter)
        except Exception as error:
            record_failure(failed_urls, url, "fight", "extract", error)
            logger.exception("Failed to extract round stats for %s", url)
        else:
            for stats in rounds:
                save_round_stats(session, stats, saved_fight, saved_fighter)


def scrape_fighter_profiles(
    browser_session: BrowserSession,
    session: Session,
    failed_urls: list[dict[str, str]],
) -> None:
    """Save profiles for fighters not yet completed, committing each one."""
    fighters = session.scalars(
        select(Fighter).where(
            Fighter.ufcstats_id.not_in(select(COMPLETED_FIGHTERS.c.fighter_id))
        )
    ).all()
    print(f"Scraping profiles for {len(fighters)} fighters")
    for fighter in fighters:
        stage = "fetch"
        try:
            fighter_html = browser_session.fetch_page(fighter.url, ".b-list__box-list")
            stage = "extract"
            profile = extract_fighter_profile(fighter_html, fighter.ufcstats_id)
        except Exception as error:
            record_failure(failed_urls, fighter.url, "fighter", stage, error)
            logger.exception("Failed to %s fighter page %s", stage, fighter.url)
            continue

        save_fighter_profile(session, profile)
        session.execute(
            COMPLETED_FIGHTERS.insert().values(fighter_id=fighter.ufcstats_id)
        )
        session.commit()


def scrape_events(failed_urls: list[dict[str, str]], *, reset: bool = False) -> None:
    # BrowserSession visits the starting page during initialization.
    url = "http://www.ufcstats.com/statistics/events/completed"
    stage = "fetch"
    try:
        browser_session = BrowserSession()
        url = browser_session.starting_page
        starting_html = browser_session.fetch_page(url, 'a[href*="/event-details/"]')
        stage = "extract"
        soup = BeautifulSoup(starting_html, "lxml")
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
        url = all_link["href"]
        print(f"all_link: {url}")
        stage = "fetch"
        all_html = browser_session.fetch_page(url, 'a[href*="/event-details/"]')
        print("All events page fetched, extracting all events...")
        stage = "extract"
        all_events = extract_events(all_html)
        print(f"First 10 events: {all_events[:10]}")
    except Exception as error:
        record_failure(failed_urls, url, "events_listing", stage, error)
        logger.exception("Failed to %s events listing %s", stage, url)
        raise

    if reset:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as session:
        try:
            completed_events = set(session.scalars(select(COMPLETED_EVENTS.c.event_id)))
            for domainevent in all_events:
                if domainevent.event_id in completed_events:
                    print(f"Skipping completed event {domainevent.name}")
                    continue
                url = domainevent.url
                stage = "fetch"
                try:
                    event_html = browser_session.fetch_page(
                        url, 'a[href*="/fight-details/"]'
                    )
                    stage = "extract"
                    fight_urls = extract_fight_urls(event_html)
                    if not fight_urls:
                        raise ValueError("No fight URLs found for completed event")
                except Exception as error:
                    record_failure(failed_urls, url, "event", stage, error)
                    logger.exception("Failed to %s event page %s", stage, url)
                    continue

                event = save_event(session, domainevent)
                event_failure_count = len(failed_urls)
                for url in fight_urls:
                    scrape_fight(browser_session, session, url, failed_urls, event)
                failure_count = len(
                    {failure["url"] for failure in failed_urls[event_failure_count:]}
                )
                if failure_count == 0:
                    session.execute(
                        COMPLETED_EVENTS.insert().values(event_id=domainevent.event_id)
                    )
                    completed_events.add(domainevent.event_id)
                session.commit()
                print(
                    f"Event {domainevent.name} saved with {failure_count} failed fights"
                )
            scrape_fighter_profiles(browser_session, session, failed_urls)
        except Exception:
            session.rollback()
            logger.exception("Database session failed")
            raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scrape UFCStats, resuming saved progress."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--reset", action="store_true", help="Drop all tables and scrape from scratch."
    )
    mode.add_argument(
        "--retry-failed",
        action="store_true",
        help="Retry only fight URLs in data/raw/failed_urls.json.",
    )
    args = parser.parse_args()
    scrape_all(reset=args.reset, retry_failed=args.retry_failed)
