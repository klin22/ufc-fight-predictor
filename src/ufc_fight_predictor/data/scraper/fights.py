from bs4 import BeautifulSoup

from ufc_fight_predictor.data.scraper.models import (
    Fight,
    Fighter,
    FighterFightStats,
    RoundStats,
)

FIGHTER_SELECTOR = "a.b-fight-details__person-link"
REQUIRED_TOTAL_COLUMNS = {
    "kd", "sig. str", "total str", "td", "sub. att", "rev", "ctrl"
}
REQUIRED_SIGNIFICANT_COLUMNS = {
    "head", "body", "leg", "distance", "clinch", "ground"
}


def _parse_pair(value: str, field: str) -> tuple[int, int]:
    landed, separator, attempted = value.partition(" of ")
    if not separator:
        raise ValueError(f"Invalid {field} value: {value}")
    try:
        return int(landed), int(attempted)
    except ValueError as error:
        raise ValueError(f"Invalid {field} value: {value}") from error


def _parse_control_seconds(value: str, field: str) -> int:
    minutes, separator, seconds = value.partition(":")
    if not separator:
        raise ValueError(f"Invalid {field} value: {value}")
    try:
        return int(minutes) * 60 + int(seconds)
    except ValueError as error:
        raise ValueError(f"Invalid {field} value: {value}") from error


def extract_fighters(html: str) -> list[Fighter]:
    soup = BeautifulSoup(html, "lxml")
    fighter_links = soup.select(
        FIGHTER_SELECTOR
    )

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

def extract_winner_id(html:str)-> str | None:
    soup = BeautifulSoup(html, "lxml")
    for person in soup.select(".b-fight-details__person"):
        link = person.select_one("a.b-fight-details__person-link")
        status_el = person.select_one(".b-fight-details__person-status")
        if link is None or status_el is None:
            continue
        status = status_el.get_text(strip=True).upper()
        if status == "W":
            url = link["href"]
            return url.rstrip("/").split("/")[-1]
    return None
#helper
def extract_fight_metadata(html:str) -> tuple[
    str, str, str, str, str, str]:
    soup = BeautifulSoup(html, "lxml")
    weight_el = soup.select_one(".b-fight-details__fight-title").get_text()
    if weight_el is None:
        raise ValueError("No weight value for this element")

    values = {}
    for item in soup.select(".b-fight-details__text-item_first, " 
                            ".b-fight-details__text-item"):

        text = item.get_text(" ", strip=True)
        key, separator, value = text.partition(":")
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
        values["referee"]
    )
#extracts fight
def extract_fight(html:str, url:str) -> Fight:
    fighters = extract_fighters(html)
    winner_id = extract_winner_id(html)
    weight, method, round, time, time_format, referee = (extract_fight_metadata(html))

    return Fight(
        ufcstats_id=url.rstrip("/").split("/")[-1],
        url=url,
        fighter_a=fighters[0],
        fighter_b=fighters[1],
        winner_id=winner_id,
        weight_class=weight,
        method=method,
        end_round=round,
        end_time=time,
        time_format=time_format,
        referee=referee
    )
def extract_fight_stats(html: str, fighter: Fighter) -> FighterFightStats:
    soup = BeautifulSoup(html, "lxml")
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
        if "kd" in headers:
            table_name = "totals"
        elif "head" in headers:
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
                raise ValueError(f"Missing {column_name} value for {fighter.ufcstats_id}")
            values[column_name] = fighter_values[fighter_index].get_text(
                " ", strip=True
            )
        fighter_tables[table_name] = values

    missing_tables = {"totals", "significant"} - fighter_tables.keys()
    if missing_tables:
        raise ValueError(
            f"Missing {', '.join(sorted(missing_tables))} stats for "
            f"{fighter.ufcstats_id}"
        )

    totals = fighter_tables["totals"]
    significant = fighter_tables["significant"]

    missing_columns = (
        REQUIRED_TOTAL_COLUMNS - totals.keys()
        | REQUIRED_SIGNIFICANT_COLUMNS - significant.keys()
    )
    if missing_columns:
        raise ValueError(
            f"Missing stat columns: {', '.join(sorted(missing_columns))}"
        )

    sig_landed, sig_attempted = _parse_pair(totals["sig. str"], "sig. str")
    total_landed, total_attempted = _parse_pair(
        totals["total str"], "total str"
    )
    td_landed, td_attempted = _parse_pair(totals["td"], "td")
    head_landed, head_attempted = _parse_pair(significant["head"], "head")
    body_landed, body_attempted = _parse_pair(significant["body"], "body")
    leg_landed, leg_attempted = _parse_pair(significant["leg"], "leg")
    distance_landed, distance_attempted = _parse_pair(
        significant["distance"], "distance"
    )
    clinch_landed, clinch_attempted = _parse_pair(
        significant["clinch"], "clinch"
    )
    ground_landed, ground_attempted = _parse_pair(
        significant["ground"], "ground"
    )

    try:
        control_seconds = _parse_control_seconds(totals["ctrl"], "ctrl")
        knockdowns = int(totals["kd"])
        submission_attempts = int(totals["sub. att"])
        reversals = int(totals["rev"])
    except ValueError as error:
        raise ValueError(f"Invalid numeric stats for {fighter.ufcstats_id}") from error

    return FighterFightStats(
        fighter_id=fighter.ufcstats_id,
        knockdowns=knockdowns,
        sig_strikes_landed=sig_landed,
        sig_strikes_attempted=sig_attempted,
        head_landed=head_landed,
        head_attempted=head_attempted,
        body_landed=body_landed,
        body_attempted=body_attempted,
        leg_landed=leg_landed,
        leg_attempted=leg_attempted,
        distance_landed=distance_landed,
        distance_attempted=distance_attempted,
        clinch_landed=clinch_landed,
        clinch_attempted=clinch_attempted,
        ground_landed=ground_landed,
        ground_attempted=ground_attempted,
        total_strikes_landed=total_landed,
        total_strikes_attempted=total_attempted,
        takedowns_landed=td_landed,
        takedowns_attempted=td_attempted,
        submission_attempts=submission_attempts,
        reversals=reversals,
        control_seconds=control_seconds,
    )


def extract_round_stats(html: str, fighter: Fighter) -> list[RoundStats]:
    soup = BeautifulSoup(html, "lxml")
    round_tables = {}

    for table in soup.find_all("table"):
        header = table.select_one("thead.b-fight-details__table-head_rnd")
        if header is None:
            continue

        headers = [
            cell.get_text(" ", strip=True).lower().rstrip(".")
            for cell in header.find_all("th")
        ]
        if "kd" in headers:
            table_name = "totals"
        elif "head" in headers:
            table_name = "significant"
        else:
            continue

        round_headers = table.select(
            "thead.b-fight-details__table-row_type_head"
        )
        rows = table.select(
            "tbody tr.b-fight-details__table-row"
        )
        if len(round_headers) != len(rows):
            raise ValueError(f"Unexpected per-round {table_name} table structure")

        for round_header, row in zip(round_headers, rows):
            label, separator, number = round_header.get_text(
                " ", strip=True
            ).lower().partition(" ")
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
                    raise ValueError(
                        f"Missing round {round_number} {column_name} value for "
                        f"{fighter.ufcstats_id}"
                    )
                value = fighter_values[
                    fighter_index
                ].get_text(" ", strip=True)
                if column_name == "td %" and " of " in value:
                    column_name = "td"
                values[column_name] = value

            round_tables.setdefault(round_number, {})[table_name] = values

    if not round_tables:
        raise ValueError(f"Missing round stats for {fighter.ufcstats_id}")

    rounds = []
    for round_number, tables in sorted(round_tables.items()):
        missing_tables = {"totals", "significant"} - tables.keys()
        if missing_tables:
            raise ValueError(
                f"Missing round {round_number} "
                f"{', '.join(sorted(missing_tables))} stats for "
                f"{fighter.ufcstats_id}"
            )

        totals = tables["totals"]
        significant = tables["significant"]
        missing_columns = (
            REQUIRED_TOTAL_COLUMNS - totals.keys()
            | REQUIRED_SIGNIFICANT_COLUMNS - significant.keys()
        )
        if missing_columns:
            raise ValueError(
                f"Missing round {round_number} stat columns: "
                f"{', '.join(sorted(missing_columns))}"
            )

        sig_landed, sig_attempted = _parse_pair(
            totals["sig. str"], f"round {round_number} sig. str"
        )
        total_landed, total_attempted = _parse_pair(
            totals["total str"], f"round {round_number} total str"
        )
        td_landed, td_attempted = _parse_pair(
            totals["td"], f"round {round_number} td"
        )
        head_landed, head_attempted = _parse_pair(
            significant["head"], f"round {round_number} head"
        )
        body_landed, body_attempted = _parse_pair(
            significant["body"], f"round {round_number} body"
        )
        leg_landed, leg_attempted = _parse_pair(
            significant["leg"], f"round {round_number} leg"
        )
        distance_landed, distance_attempted = _parse_pair(
            significant["distance"], f"round {round_number} distance"
        )
        clinch_landed, clinch_attempted = _parse_pair(
            significant["clinch"], f"round {round_number} clinch"
        )
        ground_landed, ground_attempted = _parse_pair(
            significant["ground"], f"round {round_number} ground"
        )

        try:
            control_seconds = _parse_control_seconds(
                totals["ctrl"], f"round {round_number} ctrl"
            )
            knockdowns = int(totals["kd"])
            submission_attempts = int(totals["sub. att"])
            reversals = int(totals["rev"])
        except ValueError as error:
            raise ValueError(
                f"Invalid numeric round {round_number} stats for "
                f"{fighter.ufcstats_id}"
            ) from error

        rounds.append(
            RoundStats(
                fighter_id=fighter.ufcstats_id,
                round_number=round_number,
                knockdowns=knockdowns,
                sig_strikes_landed=sig_landed,
                sig_strikes_attempted=sig_attempted,
                head_landed=head_landed,
                head_attempted=head_attempted,
                body_landed=body_landed,
                body_attempted=body_attempted,
                leg_landed=leg_landed,
                leg_attempted=leg_attempted,
                distance_landed=distance_landed,
                distance_attempted=distance_attempted,
                clinch_landed=clinch_landed,
                clinch_attempted=clinch_attempted,
                ground_landed=ground_landed,
                ground_attempted=ground_attempted,
                total_strikes_landed=total_landed,
                total_strikes_attempted=total_attempted,
                takedowns_landed=td_landed,
                takedowns_attempted=td_attempted,
                submission_attempts=submission_attempts,
                reversals=reversals,
                control_seconds=control_seconds,
            )
        )

    return rounds
