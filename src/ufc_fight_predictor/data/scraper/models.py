from pydantic import BaseModel

class Fighter(BaseModel):
    ufcstats_id: str
    name: str
    url: str 

class Fights(BaseModel):
    fighters: list[Fighter]
    winner: Fighter
    method: str
    weight: str
    round: str

class Event(BaseModel):
    event_id: str
    name: str
    date: str
    location: str
    url: str