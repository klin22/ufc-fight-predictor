import importlib
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from ufc_fight_predictor.data.database.models import (
    Event,
    Fight,
    FightStats,
    RoundStats,
)
from ufc_fight_predictor.data.scraper.models import Event as DomainEvent

FIGHT_HTML = (Path(__file__).parent / "captured_html/test_fight.html").read_text()
FIGHTER_HTML = (Path(__file__).parent / "captured_html/test_fighter.html").read_text()


@pytest.fixture
def scrape(monkeypatch, tmp_path):
    # Import the script without depending on local PostgreSQL credentials.
    for name, value in {
        "POSTGRES_USER": "test",
        "POSTGRES_PASSWORD": "test",
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_DB": "test",
    }.items():
        monkeypatch.setenv(name, value)
    module = importlib.import_module("ufc_fight_predictor.scripts.scrape_all")
    engine = create_engine("sqlite://")
    sessions = sessionmaker(bind=engine)
    pages = {
        "start": '<a class="b-statistics__paginate-link" href="all">All</a>',
        "all": "events",
        # Profile pages for both fighters in FIGHT_HTML.
        **{
            f"http://www.ufcstats.com/fighter-details/{fighter_id}": FIGHTER_HTML
            for fighter_id in ("c96d9178c9ed9e62", "32ab52e5de93092d")
        },
    }
    events = []

    def fetch(url, selector):
        page = pages[url]
        if isinstance(page, BaseException):
            raise page
        return page

    fetch_page = Mock(side_effect=fetch)
    monkeypatch.setattr(module, "engine", engine)
    monkeypatch.setattr(module, "SessionLocal", sessions)
    monkeypatch.setattr(module, "FAILED_URLS_PATH", tmp_path / "failed_urls.json")
    monkeypatch.setattr(
        module,
        "BrowserSession",
        lambda: SimpleNamespace(starting_page="start", fetch_page=fetch_page),
    )
    monkeypatch.setattr(module, "extract_events", lambda html: list(events))

    def add_event(event_id, fight_count=1):
        event = DomainEvent(
            event_id=event_id,
            name=event_id,
            date="August 29, 2026",
            location="Test",
            url=f"http://www.ufcstats.com/event-details/{event_id}",
            fights=[],
        )
        events.append(event)
        urls = [
            f"http://www.ufcstats.com/fight-details/{event_id}-{i}"
            for i in range(fight_count)
        ]
        pages[event.url] = (
            "<table>"
            + "".join(
                f'<tr class="b-fight-details__table-row" data-link="{url}"></tr>'
                for url in urls
            )
            + "</table>"
        )
        fight_page = BeautifulSoup(FIGHT_HTML, "lxml")
        fight_page.select_one(".b-content__title a")["href"] = event.url
        pages.update(dict.fromkeys(urls, str(fight_page)))
        return event, urls

    def snapshot():
        with sessions() as session:
            return (
                set(session.scalars(select(module.COMPLETED_EVENTS.c.event_id))),
                tuple(
                    session.scalar(select(func.count()).select_from(model))
                    for model in (Event, Fight, FightStats, RoundStats)
                ),
            )

    yield SimpleNamespace(
        module=module,
        pages=pages,
        add_event=add_event,
        snapshot=snapshot,
        fetch=fetch_page,
    )
    engine.dispose()


def test_restart_skips_completed_events_and_processes_new_events(scrape):
    first, first_fights = scrape.add_event("first")
    scrape.module.scrape_all()
    assert scrape.snapshot() == ({"first"}, (1, 1, 2, 6))

    second, _ = scrape.add_event("second")
    scrape.fetch.reset_mock()
    scrape.module.scrape_all()
    fetched = {call.args[0] for call in scrape.fetch.call_args_list}
    assert first.url not in fetched
    assert not fetched.intersection(first_fights)
    assert second.url in fetched
    assert scrape.snapshot() == ({"first", "second"}, (2, 2, 4, 12))


def test_partial_event_is_committed_and_retried_without_duplicates(scrape):
    partial, urls = scrape.add_event("partial", fight_count=2)
    complete, _ = scrape.add_event("complete")
    scrape.pages[urls[1]] = ValueError("fetch failed")
    scrape.module.scrape_all()
    assert scrape.snapshot() == ({"complete"}, (2, 2, 4, 12))
    report = json.loads(scrape.module.FAILED_URLS_PATH.read_text())
    assert [failure["url"] for failure in report] == [urls[1]]

    scrape.pages[urls[1]] = FIGHT_HTML
    scrape.fetch.reset_mock()
    scrape.module.scrape_all()
    fetched = {call.args[0] for call in scrape.fetch.call_args_list}
    assert partial.url in fetched
    assert complete.url not in fetched
    assert scrape.snapshot() == ({"partial", "complete"}, (2, 3, 6, 18))
    assert json.loads(scrape.module.FAILED_URLS_PATH.read_text()) == []


@pytest.mark.parametrize(
    "error", [RuntimeError("database failed"), KeyboardInterrupt()]
)
def test_interruption_preserves_previous_events_and_retries_current_event(
    scrape, monkeypatch, error
):
    first, _ = scrape.add_event("first")
    second, urls = scrape.add_event("second")
    original = scrape.module.save_round_stats

    def fail_on_second(session, stats, fight, fighter):
        if fight.url == urls[0]:
            raise error
        return original(session, stats, fight, fighter)

    with monkeypatch.context() as patch:
        patch.setattr(scrape.module, "save_round_stats", fail_on_second)
        with pytest.raises(type(error)):
            scrape.module.scrape_all()
    # The second event's fight, fighters and stats were never committed.
    assert scrape.snapshot() == ({"first"}, (1, 1, 2, 6))
    assert scrape.module.FAILED_URLS_PATH.exists()

    scrape.fetch.reset_mock()
    scrape.module.scrape_all()
    fetched = {call.args[0] for call in scrape.fetch.call_args_list}
    assert first.url not in fetched
    assert second.url in fetched
    assert scrape.snapshot() == ({"first", "second"}, (2, 2, 4, 12))


@pytest.mark.parametrize("page", ["<table></table>", ValueError("event fetch failed")])
def test_event_page_failure_is_not_marked_complete(scrape, page):
    event, _ = scrape.add_event("event")
    valid_page = scrape.pages[event.url]
    scrape.pages[event.url] = page
    scrape.module.scrape_all()
    assert scrape.snapshot() == (set(), (0, 0, 0, 0))
    assert json.loads(scrape.module.FAILED_URLS_PATH.read_text())[0]["url"] == event.url

    scrape.pages[event.url] = valid_page
    scrape.module.scrape_all()
    assert scrape.snapshot() == ({"event"}, (1, 1, 2, 6))


def test_reset_clears_previous_data_and_checkpoints(scrape, monkeypatch):
    event, _ = scrape.add_event("event")
    scrape.module.scrape_all()
    scrape.add_event("extra")
    scrape.module.scrape_all()
    assert scrape.snapshot()[0] == {"event", "extra"}

    # Simulate an event removed from the listing before explicitly resetting.
    monkeypatch.setattr(scrape.module, "extract_events", lambda html: [event])
    scrape.fetch.reset_mock()
    scrape.module.scrape_all(reset=True)
    assert scrape.snapshot() == ({"event"}, (1, 1, 2, 6))
    assert "http://www.ufcstats.com/fight-details/event-0" in {
        call.args[0] for call in scrape.fetch.call_args_list
    }


@pytest.mark.parametrize(
    "rounds_only,expected_counts", [(False, (1, 1, 0, 0)), (True, (1, 1, 2, 0))]
)
def test_unavailable_stats_preserve_fight_and_complete_event(
    scrape, rounds_only, expected_counts
):
    _, urls = scrape.add_event("event")
    soup = BeautifulSoup(FIGHT_HTML, "lxml")
    for table in soup.find_all("table"):
        if not rounds_only or table.select_one("thead.b-fight-details__table-head_rnd"):
            table.decompose()
    scrape.pages[urls[0]] = str(soup)
    scrape.module.scrape_all()
    assert scrape.snapshot() == ({"event"}, expected_counts)
    assert json.loads(scrape.module.FAILED_URLS_PATH.read_text()) == []


@pytest.mark.parametrize(
    "header_class,expected_counts",
    [
        ("b-fight-details__table-head", (1, 1, 1, 6)),
        ("b-fight-details__table-head_rnd", (1, 1, 2, 3)),
    ],
)
def test_stats_error_preserves_other_data_and_remains_retryable(
    scrape, header_class, expected_counts
):
    _, urls = scrape.add_event("event")
    soup = BeautifulSoup(FIGHT_HTML, "lxml")
    table = soup.select_one(f"thead.{header_class}").find_parent("table")
    headers = [cell.get_text(strip=True).lower() for cell in table.select("th")]
    row = table.select_one("tbody tr")
    row.find_all("td", recursive=False)[headers.index("ctrl")].select_one(
        "p"
    ).string = "invalid"
    scrape.pages[urls[0]] = str(soup)
    scrape.module.scrape_all()
    assert scrape.snapshot() == (set(), expected_counts)
    assert json.loads(scrape.module.FAILED_URLS_PATH.read_text())[0]["url"] == urls[0]

    scrape.pages[urls[0]] = FIGHT_HTML
    scrape.module.scrape_all()
    assert scrape.snapshot() == ({"event"}, (1, 1, 2, 6))


def test_retry_mode_fetches_only_failed_fights_once(scrape):
    _, urls = scrape.add_event("event", fight_count=2)
    valid_page = scrape.pages[urls[1]]
    scrape.pages[urls[1]] = ValueError("fetch failed")
    scrape.module.scrape_all()
    assert scrape.snapshot() == (set(), (1, 1, 2, 6))
    report_path = scrape.module.FAILED_URLS_PATH
    failures = json.loads(report_path.read_text())
    # Multiple statistics errors can report the same fight URL.
    report_path.write_text(json.dumps(failures + failures))

    scrape.pages[urls[1]] = valid_page
    scrape.fetch.reset_mock()
    scrape.module.scrape_all(retry_failed=True)
    assert [call.args[0] for call in scrape.fetch.call_args_list] == [urls[1]]
    assert scrape.snapshot() == (set(), (1, 2, 4, 12))
    assert json.loads(report_path.read_text()) == []


@pytest.mark.parametrize(
    "error", [RuntimeError("database failed"), KeyboardInterrupt()]
)
def test_interrupted_retry_keeps_unfinished_urls_and_committed_fights(
    scrape, monkeypatch, error
):
    _, urls = scrape.add_event("event", fight_count=3)
    valid_pages = {url: scrape.pages[url] for url in urls}
    for url in urls[1:]:
        scrape.pages[url] = ValueError("fetch failed")
    scrape.module.scrape_all()
    scrape.pages.update(valid_pages)
    original = scrape.module.save_round_stats

    def fail_last_retry(session, stats, fight, fighter):
        if fight.url == urls[2]:
            raise error
        return original(session, stats, fight, fighter)

    with monkeypatch.context() as patch:
        patch.setattr(scrape.module, "save_round_stats", fail_last_retry)
        with pytest.raises(type(error)):
            scrape.module.scrape_all(retry_failed=True)
    assert scrape.snapshot() == (set(), (1, 2, 4, 12))
    failures = json.loads(scrape.module.FAILED_URLS_PATH.read_text())
    assert [failure["url"] for failure in failures] == [urls[2]]

    scrape.module.scrape_all(retry_failed=True)
    assert scrape.snapshot() == (set(), (1, 3, 6, 18))
    assert json.loads(scrape.module.FAILED_URLS_PATH.read_text()) == []


def test_failed_retry_remains_in_report(scrape):
    _, urls = scrape.add_event("event")
    scrape.pages[urls[0]] = ValueError("fetch failed")
    scrape.module.scrape_all()
    scrape.pages[urls[0]] = ValueError("still unavailable")
    scrape.module.scrape_all(retry_failed=True)
    failures = json.loads(scrape.module.FAILED_URLS_PATH.read_text())
    assert [failure["url"] for failure in failures] == urls
    assert failures[0]["error"] == "ValueError: still unavailable"


def test_empty_retry_report_fetches_nothing(scrape):
    scrape.module.FAILED_URLS_PATH.write_text("[]")
    scrape.module.scrape_all(retry_failed=True)
    scrape.fetch.assert_not_called()


def test_retry_requires_a_saved_parent_event(scrape):
    _, urls = scrape.add_event("event")
    scrape.module.scrape_all()
    fight_page = BeautifulSoup(scrape.pages[urls[0]], "lxml")
    fight_page.select_one(".b-content__title a")["href"] = (
        "http://www.ufcstats.com/event-details/missing"
    )
    scrape.pages[urls[0]] = str(fight_page)
    failures = [
        {"url": urls[0], "page_type": "fight", "stage": "fetch", "error": "old failure"}
    ]
    scrape.module.FAILED_URLS_PATH.write_text(json.dumps(failures))
    with pytest.raises(ValueError, match="normal resume first"):
        scrape.module.scrape_all(retry_failed=True)
    assert json.loads(scrape.module.FAILED_URLS_PATH.read_text()) == failures
