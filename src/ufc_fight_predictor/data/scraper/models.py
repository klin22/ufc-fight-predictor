from pydantic import BaseModel

class Fighter(BaseModel):
    ufcstats_id: str
    name: str
    url: str 

#class for Fights? 
#how does this get used later? 
#
class Fights(BaseModel):
    fighters: list[Fighter]
    winner: Fighter
    method: str
    weight: str
    round: str