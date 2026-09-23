#go from scrapign to having entries in database. scrape one page for now
#Code flow: browser gets page, each event is visited and fighter values populated
#Try with one event first
#How should this look ideally? Shodl be one module that does
#all this. 
#   Open browser -> extracts -> maps to sqlalchemy
#   Extract event -> event
#   getFights -> list[Fight]
#   getFighters -> fighterStats, roundstats, etc

import json
from pathlib import Path
from pydantic import TypeAdapter
from ufc_fight_predictor.data.database.repository import (
    save_event,
    save_fighter,
    save_fight,
    save_fight_stats,
    save_round_stats
)
from ufc_fight_predictor.data.database.connection import SessionLocal
from ufc_fight_predictor.data.database.connection import engine
from ufc_fight_predictor.data.database.models import Base
from ufc_fight_predictor.data.scraper.models import Event, ScrapedFight

def load_event(path):
    with path.open() as file:
        data = json.load(file)
    return data

EVENT_PATH = Path("tests/captured_html/events/van_pantoja/event.html")
FIGHT_PATH = Path("tests/captured_html/events/van_pantoja/fights.html")

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

event_page = load_event(EVENT_PATH)
domainevent = Event.model_validate(event_page)

fights_page = load_event(FIGHT_PATH)
fights_page_adapter = TypeAdapter(list[ScrapedFight])
fights = fights_page_adapter.validate_python(fights_page)

with SessionLocal() as session:
    event = save_event(session, domainevent)
    for scrapedfight in fights:
        fight = scrapedfight.fight
        fighter_a = fight.fighter_a
        fighter_b = fight.fighter_b
        fighter_a_fstats = scrapedfight.fighter_a_fstats
        fighter_b_fstats = scrapedfight.fighter_b_fstats
        fighter_a_rstats = scrapedfight.fighter_a_rstats
        fighter_b_rstats = scrapedfight.fighter_b_rstats

        sa_fighter_a = save_fighter(session, fighter_a)
        sa_fighter_b = save_fighter(session, fighter_b)
        saved_fight = save_fight(session,
                                fight,
                                event,
                                sa_fighter_a,
                                sa_fighter_b)
        sa_fighter_a_fstats = save_fight_stats(session,
                                              fighter_a_fstats,
                                              saved_fight,
                                              sa_fighter_a)
        sa_fighter_b_fstats = save_fight_stats(session,
                                              fighter_b_fstats,
                                              saved_fight,
                                              sa_fighter_b)
        for round_stats in fighter_a_rstats:
            save_round_stats(
                session,
                round_stats,
                saved_fight,
                sa_fighter_a,
            )

        for round_stats in fighter_b_rstats:
            save_round_stats(
                session,
                round_stats,
                saved_fight,
                sa_fighter_b,
            )

    session.commit()


#shoudl populate fights table




