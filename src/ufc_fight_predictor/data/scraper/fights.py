from bs4 import BeautifulSoup

from ufc_fight_predictor.data.outcomes import FightOutcome
from ufc_fight_predictor.data.scraper.models import (
    Fight,
    Fighter,
    FighterFightStats,
    RoundStats,
)

FIGHTER_SELECTOR = "a.b-fight-details__person-link"


def _parse_int(value: str | None, field: str) -> int | None:
    if value is None or value.strip() in {"", "--"}:
        return None
    try:
        return int(value)
    except ValueError as error:
        raise ValueError(f"Invalid {field} value: {value}") from error


def _parse_pair(value: str | None, field: str) -> tuple[int | None, int | None]:
    if value is None or value.strip() in {"", "--"}:
        return None, None
    landed, separator, attempted = value.partition(" of ")
    if not separator:
        raise ValueError(f"Invalid {field} value: {value}")
    return _parse_int(landed, field), _parse_int(attempted, field)


def _parse_control_seconds(value: str | None, field: str) -> int | None:
    # An unavailable control time is distinct from a measured 0:00.
    if value is None or value.strip() in {"", "--"}:
        return None
    minutes, separator, seconds = value.partition(":")
    if not separator:
        raise ValueError(f"Invalid {field} value: {value}")
    try:
        return int(minutes) * 60 + int(seconds)
    except ValueError as error:
        raise ValueError(f"Invalid {field} value: {value}") from error


def _parse_stats(
    totals: dict[str, str | None], significant: dict[str, str | None]
) -> dict[str, int | None]:
    values = {
        name: _parse_int(totals.get(column), column)
        for name, column in (
            ("knockdowns", "kd"),
            ("submission_attempts", "sub. att"),
            ("reversals", "rev"),
        )
    }
    values["control_seconds"] = _parse_control_seconds(totals.get("ctrl"), "ctrl")
    pairs = {
        "sig_strikes": totals.get("sig. str"),
        "total_strikes": totals.get("total str"),
        "takedowns": totals.get("td"),
        **{
            name: significant.get(name)
            for name in ("head", "body", "leg", "distance", "clinch", "ground")
        },
    }
    for name, value in pairs.items():
        values[f"{name}_landed"], values[f"{name}_attempted"] = _parse_pair(value, name)
    return values


def _validate_fighter(soup: BeautifulSoup, fighter: Fighter) -> None:
    if not any(
        link.get("href", "").rstrip("/").split("/")[-1] == fighter.ufcstats_id
        for link in soup.select(FIGHTER_SELECTOR)
    ):
        raise ValueError(f"Fighter {fighter.ufcstats_id} is missing from the page")


def extract_fighters(html: str) -> list[Fighter]:
    soup = BeautifulSoup(html, "lxml")
    fighter_links = soup.select(FIGHTER_SELECTOR)

    fighters = []

    for link in fighter_links:
        url = link["href"]

        fighter = Fighter(
            ufcstats_id=url.rstrip("/").split("/")[-1],
            name=link.get_text(strip=True),
            url=url,
        )

        fighters.append(fighter)

    return fighters


def extract_fight_outcome(html: str) -> tuple[FightOutcome, str | None]:
    """Read both result markers; missing results are not draws or no contests."""
    soup = BeautifulSoup(html, "lxml")
    people = soup.select(".b-fight-details__person")
    if len(people) != 2:
        raise ValueError("Expected exactly two fight participants")

    results = []
    for person in people:
        link = person.select_one("a.b-fight-details__person-link")
        status_el = person.select_one(".b-fight-details__person-status")
        if link is None or status_el is None:
            raise ValueError("Missing fighter link or result marker")
        url = link.get("href")
        if not isinstance(url, str) or not url.rstrip("/"):
            raise ValueError("Missing fighter URL")
        status = status_el.get_text(strip=True).upper()
        results.append((url.rstrip("/").split("/")[-1], status))

    if results[0][0] == results[1][0]:
        raise ValueError("A fight must have two distinct participants")
    statuses = (results[0][1], results[1][1])
    if statuses == ("W", "L"):
        return "winner", results[0][0]
    if statuses == ("L", "W"):
        return "winner", results[1][0]
    if statuses == ("D", "D"):
        return "draw", None
    if statuses == ("NC", "NC"):
        return "no_contest", None
    raise ValueError(f"Invalid or unrecognized fight result markers: {statuses!r}")


def extract_winner_id(html: str) -> str | None:
    """Compatibility wrapper with the same strict result validation."""
    return extract_fight_outcome(html)[1]


# helper
def extract_fight_metadata(html: str) -> tuple[str, str, str, str, str, str]:
    soup = BeautifulSoup(html, "lxml")
    weight_el = soup.select_one(".b-fight-details__fight-title").get_text()
    if weight_el is None:
        raise ValueError("No weight value for this element")

    values = {}
    for item in soup.select(
        ".b-fight-details__text-item_first, .b-fight-details__text-item"
    ):
        text = item.get_text(" ", strip=True)
        key, _separator, value = text.partition(":")
        if key.strip().lower() == "time format":
            value = value.split("(", 1)[0].strip()
        values[key.strip().lower()] = value.strip()

    required = {"method", "round", "time", "time format", "referee"}
    missing = [key for key in required if not values.get(key)]
    if missing:
        raise ValueError(f" Missing metadata: {', '.join(missing)}")

    weight = weight_el.strip().removesuffix(" bout")
    return (
        weight,
        values["method"],
        values["round"],
        values["time"],
        values["time format"],
        values["referee"],
    )


# extracts fight
def extract_fight(html: str, url: str) -> Fight:
    fighters = extract_fighters(html)
    outcome, winner_id = extract_fight_outcome(html)
    weight, method, round, time, time_format, referee = extract_fight_metadata(html)

    return Fight(
        ufcstats_id=url.rstrip("/").split("/")[-1],
        url=url,
        fighter_a=fighters[0],
        fighter_b=fighters[1],
        outcome=outcome,
        winner_id=winner_id,
        weight_class=weight,
        method=method,
        end_round=round,
        end_time=time,
        time_format=time_format,
        referee=referee,
    )


def extract_fight_stats(html: str, fighter: Fighter) -> FighterFightStats | None:
    soup = BeautifulSoup(html, "lxml")
    _validate_fighter(soup, fighter)
    fighter_tables = {}

    for table in soup.find_all("table"):
        header = table.select_one("thead.b-fight-details__table-head")
        body = table.select_one("tbody.b-fight-details__table-body")
        if header is None or body is None:
            continue

        headers = [
            cell.get_text(" ", strip=True).lower().rstrip(".")
            for cell in header.find_all("th")
        ]
        if {"kd", "total str", "ctrl"}.intersection(headers):
            table_name = "totals"
        elif {"head", "body", "leg", "distance", "clinch", "ground"}.intersection(
            headers
        ):
            table_name = "significant"
        else:
            continue

        row = body.find("tr")
        if row is None:
            continue
        cells = row.find_all("td", recursive=False)
        if len(cells) != len(headers):
            raise ValueError(f"Unexpected {table_name} table structure")

        fighter_index = None
        for index, link in enumerate(cells[0].find_all("a")):
            fighter_id = link["href"].rstrip("/").split("/")[-1]
            if fighter_id == fighter.ufcstats_id:
                fighter_index = index
                break
        if fighter_index is None:
            continue

        values = {}
        for column_name, cell in zip(headers, cells):
            fighter_values = cell.select("p.b-fight-details__table-text")
            if fighter_index >= len(fighter_values):
                values[column_name] = None
                continue
            values[column_name] = fighter_values[fighter_index].get_text(
                " ", strip=True
            )
        fighter_tables[table_name] = values

    if not fighter_tables:
        return None

    try:
        values = _parse_stats(
            fighter_tables.get("totals", {}), fighter_tables.get("significant", {})
        )
    except ValueError as error:
        raise ValueError(
            f"Invalid numeric stats for {fighter.ufcstats_id}: {error}"
        ) from error

    if all(value is None for value in values.values()):
        return None
    return FighterFightStats(fighter_id=fighter.ufcstats_id, **values)


def extract_round_stats(html: str, fighter: Fighter) -> list[RoundStats]:
    soup = BeautifulSoup(html, "lxml")
    _validate_fighter(soup, fighter)
    round_tables = {}

    for table in soup.find_all("table"):
        header = table.select_one("thead.b-fight-details__table-head_rnd")
        if header is None:
            continue

        headers = [
            cell.get_text(" ", strip=True).lower().rstrip(".")
            for cell in header.find_all("th")
        ]
        if {"kd", "total str", "ctrl"}.intersection(headers):
            table_name = "totals"
        elif {"head", "body", "leg", "distance", "clinch", "ground"}.intersection(
            headers
        ):
            table_name = "significant"
        else:
            continue

        round_headers = table.select("thead.b-fight-details__table-row_type_head")
        rows = table.select("tbody tr.b-fight-details__table-row")
        if len(round_headers) != len(rows):
            raise ValueError(f"Unexpected per-round {table_name} table structure")

        for round_header, row in zip(round_headers, rows):
            label, separator, number = (
                round_header.get_text(" ", strip=True).lower().partition(" ")
            )
            if label != "round" or not separator:
                raise ValueError("Invalid round heading")
            try:
                round_number = int(number)
            except ValueError as error:
                raise ValueError(f"Invalid round number: {number}") from error

            cells = row.find_all("td", recursive=False)
            if len(cells) != len(headers):
                raise ValueError(
                    f"Unexpected round {round_number} {table_name} structure"
                )

            fighter_index = None
            for index, link in enumerate(cells[0].find_all("a")):
                fighter_id = link["href"].rstrip("/").split("/")[-1]
                if fighter_id == fighter.ufcstats_id:
                    fighter_index = index
                    break
            if fighter_index is None:
                continue

            values = {}
            for column_name, cell in zip(headers, cells):
                fighter_values = cell.select("p.b-fight-details__table-text")
                if fighter_index >= len(fighter_values):
                    values[column_name] = None
                    continue
                value = fighter_values[fighter_index].get_text(" ", strip=True)
                if column_name == "td %" and " of " in value:
                    column_name = "td"
                values[column_name] = value

            round_tables.setdefault(round_number, {})[table_name] = values

    rounds = []
    for round_number, tables in sorted(round_tables.items()):
        try:
            values = _parse_stats(
                tables.get("totals", {}), tables.get("significant", {})
            )
        except ValueError as error:
            raise ValueError(
                f"Invalid numeric round {round_number} stats for {fighter.ufcstats_id}: "
                f"{error}"
            ) from error

        if all(value is None for value in values.values()):
            continue
        rounds.append(
            RoundStats(
                fighter_id=fighter.ufcstats_id,
                round_number=round_number,
                **values,
            )
        )

    return rounds
