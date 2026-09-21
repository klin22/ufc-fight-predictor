from sqlalchemy import text

from ufc_fight_predictor.data.database.models import Base

# with engine.connect() as connection:
#     result = connection.execute(text("SELECT 1"))
#     print(result.scalar())


def main() -> None:
    from ufc_fight_predictor.data.database.connection import SessionLocal, engine

    Base.metadata.create_all(engine)

    with SessionLocal() as session:
        result = session.execute(text("SELECT 1"))
        print(result.scalar_one())


if __name__ == "__main__":
    main()
