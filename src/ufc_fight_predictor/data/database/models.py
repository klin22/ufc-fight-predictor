from __future__ import annotations

from datetime import date

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
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
    height_in: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reach_in: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stance: Mapped[str | None] = mapped_column(String, nullable=True)
    dob: Mapped[date | None] = mapped_column(Date, nullable=True)

    fight_stats: Mapped[list[FightStats]] = relationship(
        back_populates="fighter",
    )
    round_stats: Mapped[list[RoundStats]] = relationship(
        back_populates="fighter",
    )


class Fight(Base):
    __tablename__ = "fights"
    __table_args__ = (
        CheckConstraint(
            "outcome IN ('winner', 'draw', 'no_contest')",
            name="ck_fights_outcome",
        ),
        CheckConstraint(
            "(outcome = 'winner' AND winner_id IS NOT NULL "
            "AND winner_id IN (fighter_a_id, fighter_b_id)) OR "
            "(outcome IN ('draw', 'no_contest') AND winner_id IS NULL)",
            name="ck_fights_outcome_winner",
        ),
        CheckConstraint(
            "fighter_a_id <> fighter_b_id", name="ck_fights_distinct_participants"
        ),
    )

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
    outcome: Mapped[str] = mapped_column(String, nullable=False)
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
    knockdowns: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sig_strikes_landed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sig_strikes_attempted: Mapped[int | None] = mapped_column(Integer, nullable=True)
    head_landed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    head_attempted: Mapped[int | None] = mapped_column(Integer, nullable=True)
    body_landed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    body_attempted: Mapped[int | None] = mapped_column(Integer, nullable=True)
    leg_landed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    leg_attempted: Mapped[int | None] = mapped_column(Integer, nullable=True)
    distance_landed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    distance_attempted: Mapped[int | None] = mapped_column(Integer, nullable=True)
    clinch_landed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    clinch_attempted: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ground_landed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ground_attempted: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_strikes_landed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_strikes_attempted: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    takedowns_landed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    takedowns_attempted: Mapped[int | None] = mapped_column(Integer, nullable=True)
    submission_attempts: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reversals: Mapped[int | None] = mapped_column(Integer, nullable=True)
    control_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

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
    knockdowns: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sig_strikes_landed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sig_strikes_attempted: Mapped[int | None] = mapped_column(Integer, nullable=True)
    head_landed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    head_attempted: Mapped[int | None] = mapped_column(Integer, nullable=True)
    body_landed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    body_attempted: Mapped[int | None] = mapped_column(Integer, nullable=True)
    leg_landed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    leg_attempted: Mapped[int | None] = mapped_column(Integer, nullable=True)
    distance_landed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    distance_attempted: Mapped[int | None] = mapped_column(Integer, nullable=True)
    clinch_landed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    clinch_attempted: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ground_landed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ground_attempted: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_strikes_landed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_strikes_attempted: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    takedowns_landed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    takedowns_attempted: Mapped[int | None] = mapped_column(Integer, nullable=True)
    submission_attempts: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reversals: Mapped[int | None] = mapped_column(Integer, nullable=True)
    control_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    fight: Mapped[Fight] = relationship(back_populates="round_stats")
    fighter: Mapped[Fighter] = relationship(back_populates="round_stats")
