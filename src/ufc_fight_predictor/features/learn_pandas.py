import numpy as np
import pandas as pd
from sqlalchemy import text
from ufc_fight_predictor.data.database.connection import engine
#query into the sqlalchemy database
#what does xgboost need? How do i train features? 

df = pd.DataFrame()
print(df)
print(type(df))
print(engine)

#write query that displays data in 
#eventid, fight_id, fighters_id, fightstats, roundstats
#a digestable way
#what features for logistic? 
query = """
SELECT
    e.id AS event_id,
    e.event_date,
    f.id AS fight_id,
    fer.id AS fighter_id,
    fer.name AS fighter_name,
    f.weight_class,
    f.outcome,
    f.winner_id,
    fst.knockdowns,
    fst.sig_strikes_landed,
    fst.sig_strikes_attempted,
    fst.takedowns_landed,
    fst.takedowns_attempted,
    fst.control_seconds
FROM fights f
JOIN events e ON e.id = f.event_id
JOIN fighters fer
    ON fer.id IN (f.fighter_a_id, f.fighter_b_id)
LEFT JOIN fight_stats fst
    ON fst.fight_id = f.id
    AND fst.fighter_id = fer.id
ORDER BY e.event_date, f.id, fer.id
"""

# ORDER BY date
with engine.connect() as connection:
    df = pd.read_sql(query, connection)

df.to_csv("out.csv", index=False)
print(df.columns)
