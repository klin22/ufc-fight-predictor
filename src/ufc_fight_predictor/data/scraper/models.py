from __future__ import annotations

from typing import Self

from pydantic import BaseModel, model_validator

from ufc_fight_predictor.data.outcomes import FightOutcome, validate_fight_outcome


class Fighter(BaseModel):
    ufcstats_id: str
    name: str
    url: str


class FighterProfile(BaseModel):
    ufcstats_id: str
    height_in: int | None
    reach_in: int | None
    stance: str | None
    dob: str | None


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

    knockdowns: int | None

    sig_strikes_landed: int | None
    sig_strikes_attempted: int | None

    head_landed: int | None
    head_attempted: int | None
    body_landed: int | None
    body_attempted: int | None
    leg_landed: int | None
    leg_attempted: int | None

    distance_landed: int | None
    distance_attempted: int | None
    clinch_landed: int | None
    clinch_attempted: int | None
    ground_landed: int | None
    ground_attempted: int | None

    total_strikes_landed: int | None
    total_strikes_attempted: int | None

    takedowns_landed: int | None
    takedowns_attempted: int | None

    submission_attempts: int | None
    reversals: int | None
    control_seconds: int | None


class RoundStats(FighterFightStats):
    round_number: int


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
    fighter_a_fstats: FighterFightStats | None
    fighter_b_fstats: FighterFightStats | None
    fighter_a_rstats: list[RoundStats]
    fighter_b_rstats: list[RoundStats]
