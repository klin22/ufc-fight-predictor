from __future__ import annotations
from pydantic import BaseModel

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
    winner_id: str | None
    weight_class: str
    method: str
    end_round: int
    end_time: str
    time_format:str
    referee: str

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