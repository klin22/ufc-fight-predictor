from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    ufcstats_id: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    event_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    location: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    url: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
    )

    fights: Mapped[list[Fight]] = relationship(back_populates="event")


class Fighter(Base):
    __tablename__ = "fighters"

    id: Mapped[int] = mapped_column(primary_key=True)
    ufcstats_id: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    url: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
    )

    fight_stats: Mapped[list[FightStats]] = relationship(
        back_populates="fighter",
    )
    round_stats: Mapped[list[RoundStats]] = relationship(
        back_populates="fighter",
    )


class Fight(Base):
    __tablename__ = "fights"

    id: Mapped[int] = mapped_column(primary_key=True)
    ufcstats_id: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
    )
    url: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
    )
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id"),
        nullable=False,
    )
    fighter_a_id: Mapped[int] = mapped_column(
        ForeignKey("fighters.id"),
        nullable=False,
    )
    fighter_b_id: Mapped[int] = mapped_column(
        ForeignKey("fighters.id"),
        nullable=False,
    )
    winner_id: Mapped[int | None] = mapped_column(
        ForeignKey("fighters.id"),
        nullable=True,
    )
    weight_class: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    method: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    end_round: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    end_time: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    time_format: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    referee: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    event: Mapped[Event] = relationship(back_populates="fights")
    fighter_a: Mapped[Fighter] = relationship(
        foreign_keys=[fighter_a_id],
    )
    fighter_b: Mapped[Fighter] = relationship(
        foreign_keys=[fighter_b_id],
    )
    winner: Mapped[Fighter | None] = relationship(
        foreign_keys=[winner_id],
    )
    stats: Mapped[list[FightStats]] = relationship(back_populates="fight")
    round_stats: Mapped[list[RoundStats]] = relationship(
        back_populates="fight",
    )


class FightStats(Base):
    __tablename__ = "fight_stats"
    __table_args__ = (
        UniqueConstraint(
            "fight_id",
            "fighter_id",
            name="uq_fight_stats_fight_fighter",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    fight_id: Mapped[int] = mapped_column(
        ForeignKey("fights.id"),
        nullable=False,
    )
    fighter_id: Mapped[int] = mapped_column(
        ForeignKey("fighters.id"),
        nullable=False,
    )
    knockdowns: Mapped[int] = mapped_column(Integer, nullable=False)
    sig_strikes_landed: Mapped[int] = mapped_column(Integer, nullable=False)
    sig_strikes_attempted: Mapped[int] = mapped_column(Integer, nullable=False)
    head_landed: Mapped[int] = mapped_column(Integer, nullable=False)
    head_attempted: Mapped[int] = mapped_column(Integer, nullable=False)
    body_landed: Mapped[int] = mapped_column(Integer, nullable=False)
    body_attempted: Mapped[int] = mapped_column(Integer, nullable=False)
    leg_landed: Mapped[int] = mapped_column(Integer, nullable=False)
    leg_attempted: Mapped[int] = mapped_column(Integer, nullable=False)
    distance_landed: Mapped[int] = mapped_column(Integer, nullable=False)
    distance_attempted: Mapped[int] = mapped_column(Integer, nullable=False)
    clinch_landed: Mapped[int] = mapped_column(Integer, nullable=False)
    clinch_attempted: Mapped[int] = mapped_column(Integer, nullable=False)
    ground_landed: Mapped[int] = mapped_column(Integer, nullable=False)
    ground_attempted: Mapped[int] = mapped_column(Integer, nullable=False)
    total_strikes_landed: Mapped[int] = mapped_column(Integer, nullable=False)
    total_strikes_attempted: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    takedowns_landed: Mapped[int] = mapped_column(Integer, nullable=False)
    takedowns_attempted: Mapped[int] = mapped_column(Integer, nullable=False)
    submission_attempts: Mapped[int] = mapped_column(Integer, nullable=False)
    reversals: Mapped[int] = mapped_column(Integer, nullable=False)
    control_seconds: Mapped[int] = mapped_column(Integer, nullable=False)

    fight: Mapped[Fight] = relationship(back_populates="stats")
    fighter: Mapped[Fighter] = relationship(back_populates="fight_stats")


class RoundStats(Base):
    __tablename__ = "round_stats"
    __table_args__ = (
        UniqueConstraint(
            "fight_id",
            "fighter_id",
            "round_number",
            name="uq_round_stats_fight_fighter_round",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    fight_id: Mapped[int] = mapped_column(
        ForeignKey("fights.id"),
        nullable=False,
    )
    fighter_id: Mapped[int] = mapped_column(
        ForeignKey("fighters.id"),
        nullable=False,
    )
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    knockdowns: Mapped[int] = mapped_column(Integer, nullable=False)
    sig_strikes_landed: Mapped[int] = mapped_column(Integer, nullable=False)
    sig_strikes_attempted: Mapped[int] = mapped_column(Integer, nullable=False)
    head_landed: Mapped[int] = mapped_column(Integer, nullable=False)
    head_attempted: Mapped[int] = mapped_column(Integer, nullable=False)
    body_landed: Mapped[int] = mapped_column(Integer, nullable=False)
    body_attempted: Mapped[int] = mapped_column(Integer, nullable=False)
    leg_landed: Mapped[int] = mapped_column(Integer, nullable=False)
    leg_attempted: Mapped[int] = mapped_column(Integer, nullable=False)
    distance_landed: Mapped[int] = mapped_column(Integer, nullable=False)
    distance_attempted: Mapped[int] = mapped_column(Integer, nullable=False)
    clinch_landed: Mapped[int] = mapped_column(Integer, nullable=False)
    clinch_attempted: Mapped[int] = mapped_column(Integer, nullable=False)
    ground_landed: Mapped[int] = mapped_column(Integer, nullable=False)
    ground_attempted: Mapped[int] = mapped_column(Integer, nullable=False)
    total_strikes_landed: Mapped[int] = mapped_column(Integer, nullable=False)
    total_strikes_attempted: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    takedowns_landed: Mapped[int] = mapped_column(Integer, nullable=False)
    takedowns_attempted: Mapped[int] = mapped_column(Integer, nullable=False)
    submission_attempts: Mapped[int] = mapped_column(Integer, nullable=False)
    reversals: Mapped[int] = mapped_column(Integer, nullable=False)
    control_seconds: Mapped[int] = mapped_column(Integer, nullable=False)

    fight: Mapped[Fight] = relationship(back_populates="round_stats")
    fighter: Mapped[Fighter] = relationship(back_populates="round_stats")