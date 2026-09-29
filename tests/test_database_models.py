from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ufc_fight_predictor.data.database.models import (
    Base,
    Event,
    Fight,
    Fighter,
    FightStats,
    RoundStats,
)
from ufc_fight_predictor.data.database.repository import (
    save_event,
    save_fight,
    save_fight_stats,
    save_fighter,
    save_round_stats,
)
from ufc_fight_predictor.data.scraper.fights import (
    extract_fight,
    extract_fight_stats,
    extract_round_stats,
)
from ufc_fight_predictor.data.scraper.models import Event as DomainEvent

FIGHT_FIXTURE_PATH = Path("tests/captured_html/test_fight.html")
FIGHT_URL = "http://www.ufcstats.com/fight-details/fixture-fight"


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def fight_html() -> str:
    return FIGHT_FIXTURE_PATH.read_text(encoding="utf-8")


def make_domain_event(fight) -> DomainEvent:
    return DomainEvent(
        event_id="fixture-event",
        name="Fixture Event",
        date="august 29, 2026",
        location="Abu Dhabi, United Arab Emirates",
        url="http://www.ufcstats.com/event-details/fixture-event",
        fights=[fight],
    )


def save_fight_graph(
    session: Session,
    fight_html: str,
):
    domain_fight = extract_fight(fight_html, FIGHT_URL)
    event = save_event(session, make_domain_event(domain_fight))
    fighter_a = save_fighter(session, domain_fight.fighter_a)
    fighter_b = save_fighter(session, domain_fight.fighter_b)
    fight = save_fight(
        session,
        domain_fight,
        event,
        fighter_a,
        fighter_b,
    )
    return domain_fight, event, fighter_a, fighter_b, fight


def test_domain_objects_persist_with_relationships(
    db_session: Session,
    fight_html: str,
) -> None:
    domain_fight, event, fighter_a, fighter_b, fight = save_fight_graph(
        db_session,
        fight_html,
    )

    save_fight_stats(
        db_session,
        extract_fight_stats(fight_html, domain_fight.fighter_a),
        fight,
        fighter_a,
    )
    save_fight_stats(
        db_session,
        extract_fight_stats(fight_html, domain_fight.fighter_b),
        fight,
        fighter_b,
    )
    save_round_stats(
        db_session,
        extract_round_stats(fight_html, domain_fight.fighter_a)[0],
        fight,
        fighter_a,
    )

    draw = domain_fight.model_copy(
        update={
            "ufcstats_id": "fixture-draw",
            "url": "http://www.ufcstats.com/fight-details/fixture-draw",
            "winner_id": None,
        }
    )
    draw_record = save_fight(
        db_session,
        draw,
        event,
        fighter_a,
        fighter_b,
    )
    db_session.commit()
    db_session.expire_all()

    loaded_fight = db_session.scalar(
        select(Fight).where(Fight.ufcstats_id == domain_fight.ufcstats_id)
    )
    loaded_draw = db_session.scalar(select(Fight).where(Fight.id == draw_record.id))

    assert loaded_fight is not None
    assert loaded_fight.event.ufcstats_id == "fixture-event"
    assert loaded_fight.event.event_date.isoformat() == "2026-08-29"
    assert loaded_fight.fighter_a.ufcstats_id == domain_fight.fighter_a.ufcstats_id
    assert loaded_fight.fighter_b.ufcstats_id == domain_fight.fighter_b.ufcstats_id
    assert loaded_fight.winner is not None
    assert loaded_fight.winner.ufcstats_id == domain_fight.winner_id
    assert loaded_fight.end_round == domain_fight.end_round
    assert len(loaded_fight.stats) == 2
    assert len(loaded_fight.round_stats) == 1
    assert loaded_fight.round_stats[0].round_number == 1
    assert loaded_fight.stats[0].fighter.fight_stats
    assert loaded_fight.round_stats[0].fighter.round_stats
    assert loaded_draw is not None
    assert loaded_draw.winner_id is None
    assert loaded_draw.winner is None


@pytest.mark.parametrize("duplicate_field", ["event_id", "url"])
def test_event_reuses_id_but_rejects_conflicting_url(
    db_session: Session,
    fight_html: str,
    duplicate_field: str,
) -> None:
    domain_fight = extract_fight(fight_html, FIGHT_URL)
    event = make_domain_event(domain_fight)
    original = save_event(db_session, event)
    db_session.commit()

    updates = {
        "event_id": "another-event",
        "url": "http://www.ufcstats.com/event-details/another-event",
    }
    updates[duplicate_field] = getattr(event, duplicate_field)

    duplicate = event.model_copy(update=updates)
    if duplicate_field == "event_id":
        assert save_event(db_session, duplicate) is original
        assert original.url == event.url
    else:
        with pytest.raises(IntegrityError):
            save_event(db_session, duplicate)


@pytest.mark.parametrize("duplicate_field", ["ufcstats_id", "url"])
def test_fighter_reuses_id_but_rejects_conflicting_url(
    db_session: Session,
    fight_html: str,
    duplicate_field: str,
) -> None:
    fighter = extract_fight(fight_html, FIGHT_URL).fighter_a
    original = save_fighter(db_session, fighter)
    db_session.commit()

    updates = {
        "ufcstats_id": "another-fighter",
        "url": "http://www.ufcstats.com/fighter-details/another-fighter",
    }
    updates[duplicate_field] = getattr(fighter, duplicate_field)

    duplicate = fighter.model_copy(update=updates)
    if duplicate_field == "ufcstats_id":
        assert save_fighter(db_session, duplicate) is original
        assert original.url == fighter.url
    else:
        with pytest.raises(IntegrityError):
            save_fighter(db_session, duplicate)


@pytest.mark.parametrize("duplicate_field", ["ufcstats_id", "url"])
def test_fight_reuses_id_but_rejects_conflicting_url(
    db_session: Session,
    fight_html: str,
    duplicate_field: str,
) -> None:
    domain_fight, event, fighter_a, fighter_b, original = save_fight_graph(
        db_session,
        fight_html,
    )
    db_session.commit()

    updates = {
        "ufcstats_id": "another-fight",
        "url": "http://www.ufcstats.com/fight-details/another-fight",
    }
    updates[duplicate_field] = getattr(domain_fight, duplicate_field)

    duplicate = domain_fight.model_copy(update=updates)
    if duplicate_field == "ufcstats_id":
        assert (
            save_fight(db_session, duplicate, event, fighter_a, fighter_b) is original
        )
        assert original.url == domain_fight.url
    else:
        with pytest.raises(IntegrityError):
            save_fight(db_session, duplicate, event, fighter_a, fighter_b)


@pytest.mark.parametrize("commit", [False, True])
def test_fight_stats_reuse_existing_record(
    db_session: Session,
    fight_html: str,
    commit: bool,
) -> None:
    domain_fight, _, fighter_a, _, fight = save_fight_graph(
        db_session,
        fight_html,
    )
    stats = extract_fight_stats(fight_html, domain_fight.fighter_a)
    original = save_fight_stats(db_session, stats, fight, fighter_a)
    if commit:
        db_session.commit()

    changed = stats.model_copy(update={"knockdowns": stats.knockdowns + 1})
    assert save_fight_stats(db_session, changed, fight, fighter_a) is original
    assert original.knockdowns == stats.knockdowns
    assert db_session.scalar(select(func.count()).select_from(FightStats)) == 1


@pytest.mark.parametrize("commit", [False, True])
def test_round_stats_reuse_existing_record(
    db_session: Session,
    fight_html: str,
    commit: bool,
) -> None:
    domain_fight, _, fighter_a, _, fight = save_fight_graph(
        db_session,
        fight_html,
    )
    stats = extract_round_stats(fight_html, domain_fight.fighter_a)[0]
    original = save_round_stats(db_session, stats, fight, fighter_a)
    if commit:
        db_session.commit()

    changed = stats.model_copy(update={"knockdowns": stats.knockdowns + 1})
    assert save_round_stats(db_session, changed, fight, fighter_a) is original
    assert original.knockdowns == stats.knockdowns
    assert db_session.scalar(select(func.count()).select_from(RoundStats)) == 1

    next_round = stats.model_copy(update={"round_number": stats.round_number + 1})
    assert save_round_stats(db_session, next_round, fight, fighter_a) is not original
    assert db_session.scalar(select(func.count()).select_from(RoundStats)) == 2


@pytest.mark.parametrize("commit", [False, True])
def test_saving_fight_graph_twice_reuses_records(
    db_session: Session,
    fight_html: str,
    commit: bool,
) -> None:
    _, *original_records = save_fight_graph(db_session, fight_html)
    original_ids = [record.id for record in original_records]
    if commit:
        db_session.commit()
        # Force the second save to find persisted rows outside the identity map.
        db_session.expunge_all()

    _, *repeated_records = save_fight_graph(db_session, fight_html)
    assert [record.id for record in repeated_records] == original_ids
    if not commit:
        for original, repeated in zip(original_records, repeated_records):
            assert repeated is original

    assert db_session.scalar(select(func.count()).select_from(Event)) == 1
    assert db_session.scalar(select(func.count()).select_from(Fighter)) == 2
    assert db_session.scalar(select(func.count()).select_from(Fight)) == 1
