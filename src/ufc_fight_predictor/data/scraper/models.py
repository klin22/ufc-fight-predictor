from pydantic import BaseModel

class Fighter(BaseModel):
    ufcstats_id: str
    name: str
    url: str 

class Fight(BaseModel):
    fight_id: str
    url: str
    fighter_a: Fighter
    # fighter_a_stats: FightStats
    fighter_b: Fighter
    # fighter_b_stats: FightStats
    winner_id: str
    weight: str
    method: str
    round: str
    time: str
    time_format:str
    referee: str

class FightStats(BaseModel):
    fighter: Fighter
    total_kd: str
    ss_total: str

class Event(BaseModel):
    event_id: str
    name: str
    date: str
    location: str
    url: str
    fights: list[Fight]