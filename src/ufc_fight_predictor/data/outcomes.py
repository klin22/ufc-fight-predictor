"""Completed-fight outcomes shared by scraping and persistence."""

from typing import Literal

FightOutcome = Literal["winner", "draw", "no_contest"]


def validate_fight_outcome(
    outcome: str,
    winner_id: str | None,
    fighter_a_id: str,
    fighter_b_id: str,
) -> None:
    if not fighter_a_id or not fighter_b_id:
        raise ValueError("Both participants must have fighter IDs")
    if fighter_a_id == fighter_b_id:
        raise ValueError("A fight must have two distinct participants")
    if outcome == "winner":
        if winner_id not in (fighter_a_id, fighter_b_id):
            raise ValueError(
                "A winner outcome requires a winner_id matching a participant"
            )
    elif outcome in ("draw", "no_contest"):
        if winner_id is not None:
            raise ValueError("Draws and no contests must have winner_id=None")
    else:
        raise ValueError(f"Unknown fight outcome: {outcome!r}")
