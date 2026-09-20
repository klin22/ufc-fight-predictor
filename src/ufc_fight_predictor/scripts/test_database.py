from sqlalchemy import text
from datetime import date
from ufc_fight_predictor.data.database.connection import engine, SessionLocal
from ufc_fight_predictor.data.database.models import Event, Base
# with engine.connect() as connection:
#     result = connection.execute(text("SELECT 1"))
#     print(result.scalar())

try:
    Base.metadata.create_all(engine)
except:
    print("Base.metadata.create_all failed")

with SessionLocal() as session:
    ufc_america = Event(
        ufcstats_id="12345",
        name="ufc_america",
        event_date=date(2026, 9, 19),
        location="abu dhabi",
        url="https://xyz.com"

    )
    session.add(ufc_america)
    session.commit()
    
