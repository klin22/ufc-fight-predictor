from __future__ import annotations

from typing import Self

from pydantic import BaseModel, model_validator

from ufc_fight_predictor.data.outcomes import FightOutcome, validate_fight_outcome


class Fighter(BaseModel):
    ufcstats_id: str
    name: str
    url: str


class Fight(BaseModel):
    ufcstats_id: str
    url: str
    event: Event | None = None
    fighter_a: Fighter
    fighter_b: Fighter
    outcome: FightOutcome
    winner_id: str | None
    weight_class: str
    method: str
    end_round: int
    end_time: str
    time_format: str
    referee: str

    @model_validator(mode="after")
    def validate_outcome(self) -> Self:
        validate_fight_outcome(
            self.outcome,
            self.winner_id,
            self.fighter_a.ufcstats_id,
            self.fighter_b.ufcstats_id,
        )
        return self


class FighterFightStats(BaseModel):
    fighter_id: str

    knockdowns: int

    sig_strikes_landed: int
    sig_strikes_attempted: int

    head_landed: int
    head_attempted: int
    body_landed: int
    body_attempted: int
    leg_landed: int
    leg_attempted: int

    distance_landed: int
    distance_attempted: int
    clinch_landed: int
    clinch_attempted: int
    ground_landed: int
    ground_attempted: int

    total_strikes_landed: int
    total_strikes_attempted: int

    takedowns_landed: int
    takedowns_attempted: int

    submission_attempts: int
    reversals: int
    control_seconds: int


class RoundStats(BaseModel):
    fighter_id: str
    round_number: int

    knockdowns: int

    sig_strikes_landed: int
    sig_strikes_attempted: int

    head_landed: int
    head_attempted: int
    body_landed: int
    body_attempted: int
    leg_landed: int
    leg_attempted: int

    distance_landed: int
    distance_attempted: int
    clinch_landed: int
    clinch_attempted: int
    ground_landed: int
    ground_attempted: int

    total_strikes_landed: int
    total_strikes_attempted: int

    takedowns_landed: int
    takedowns_attempted: int

    submission_attempts: int
    reversals: int
    control_seconds: int


class Event(BaseModel):
    event_id: str
    name: str
    date: str
    location: str
    url: str
    fights: list[Fight]


class ScrapedFight(BaseModel):
    fight: Fight
    fighter_a: Fighter
    fighter_b: Fighter
    fighter_a_fstats: FighterFightStats
    fighter_b_fstats: FighterFightStats
    fighter_a_rstats: list[RoundStats]
    fighter_b_rstats: list[RoundStats]
