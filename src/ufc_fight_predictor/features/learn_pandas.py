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
query = """
SELECT * 

FROM events e
JOIN fights f ON e.id = f.event_id
JOIN fighters fer ON fer.id = f.fighter_a_id OR fer.id = f.fighter_b_id
JOIN fight_stats fst ON fst.fight_id = f.id AND fst.fighter_id = fer.id
"""
with engine.connect() as connection:
    df = pd.read_sql(query, connection)

df.to_csv("out.csv", index=False)
print(df.columns)
