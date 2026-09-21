from datetime import date
from time import strptime

from sqlalchemy.orm import Session

from ufc_fight_predictor.data.database.models import (
    Event,
    Fight,
    Fighter,
    FightStats,
    RoundStats,
)
from ufc_fight_predictor.data.scraper.models import (
    Event as DomainEvent,
)
from ufc_fight_predictor.data.scraper.models import (
    Fight as DomainFight,
)
from ufc_fight_predictor.data.scraper.models import (
    Fighter as DomainFighter,
)
from ufc_fight_predictor.data.scraper.models import (
    FighterFightStats as DomainFightStats,
)
from ufc_fight_predictor.data.scraper.models import (
    RoundStats as DomainRoundStats,
)

STAT_FIELDS = (
    "knockdowns",
    "sig_strikes_landed",
    "sig_strikes_attempted",
    "head_landed",
    "head_attempted",
    "body_landed",
    "body_attempted",
    "leg_landed",
    "leg_attempted",
    "distance_landed",
    "distance_attempted",
    "clinch_landed",
    "clinch_attempted",
    "ground_landed",
    "ground_attempted",
    "total_strikes_landed",
    "total_strikes_attempted",
    "takedowns_landed",
    "takedowns_attempted",
    "submission_attempts",
    "reversals",
    "control_seconds",
)


def _parse_event_date(value: str) -> date:
    try:
        parsed = strptime(value, "%B %d, %Y")
    except ValueError as error:
        raise ValueError(f"Invalid UFCStats event date: {value!r}") from error
    return date(parsed.tm_year, parsed.tm_mon, parsed.tm_mday)


def _stat_values(
    stats: DomainFightStats | DomainRoundStats,
) -> dict[str, int]:
    return {field: getattr(stats, field) for field in STAT_FIELDS}


def save_event(session: Session, event: DomainEvent) -> Event:
    record = Event(
        ufcstats_id=event.event_id,
        name=event.name,
        event_date=_parse_event_date(event.date),
        location=event.location,
        url=event.url,
    )
    session.add(record)
    session.flush()
    return record


def save_fighter(session: Session, fighter: DomainFighter) -> Fighter:
    record = Fighter(
        ufcstats_id=fighter.ufcstats_id,
        name=fighter.name,
        url=fighter.url,
    )
    session.add(record)
    session.flush()
    return record


def save_fight(
    session: Session,
    fight: DomainFight,
    event: Event,
    fighter_a: Fighter,
    fighter_b: Fighter,
) -> Fight:
    if fighter_a.ufcstats_id != fight.fighter_a.ufcstats_id:
        raise ValueError("fighter_a does not match the domain fight")
    if fighter_b.ufcstats_id != fight.fighter_b.ufcstats_id:
        raise ValueError("fighter_b does not match the domain fight")

    fighters = {
        fighter_a.ufcstats_id: fighter_a,
        fighter_b.ufcstats_id: fighter_b,
    }
    winner = None
    if fight.winner_id is not None:
        winner = fighters.get(fight.winner_id)
        if winner is None:
            raise ValueError("winner_id does not match either fight participant")

    record = Fight(
        ufcstats_id=fight.ufcstats_id,
        url=fight.url,
        event=event,
        fighter_a=fighter_a,
        fighter_b=fighter_b,
        winner=winner,
        weight_class=fight.weight_class,
        method=fight.method,
        end_round=int(fight.end_round),
        end_time=fight.end_time,
        time_format=fight.time_format,
        referee=fight.referee,
    )
    session.add(record)
    session.flush()
    return record


def save_fight_stats(
    session: Session,
    stats: DomainFightStats,
    fight: Fight,
    fighter: Fighter,
) -> FightStats:
    if stats.fighter_id != fighter.ufcstats_id:
        raise ValueError("fighter does not match the fight stats")

    record = FightStats(
        fight=fight,
        fighter=fighter,
        **_stat_values(stats),
    )
    session.add(record)
    session.flush()
    return record


def save_round_stats(
    session: Session,
    stats: DomainRoundStats,
    fight: Fight,
    fighter: Fighter,
) -> RoundStats:
    if stats.fighter_id != fighter.ufcstats_id:
        raise ValueError("fighter does not match the round stats")

    record = RoundStats(
        fight=fight,
        fighter=fighter,
        round_number=stats.round_number,
        **_stat_values(stats),
    )
    session.add(record)
    session.flush()
    return record
