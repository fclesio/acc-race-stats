"""Categories: from the ones saved by the game to the ones the league uses."""

from __future__ import annotations

from collections import Counter

from .gamedata import CUP_CATEGORIES
from .results import Session

# from the fastest to the slowest
RANK = ["PRO", "PRO-AM", "SILVER", "AM", "NATIONAL"]
PRESETS: dict[str, list[str]] = {
    "pro": ["PRO", "PRO-AM", "AM"],
    "metal": ["GOLD", "SILVER", "BRONZE"],
    "fia": ["PLATINUM", "GOLD", "SILVER", "BRONZE"],
    "numbers": ["DIVISION 1", "DIVISION 2", "DIVISION 3", "DIVISION 4"],
}


def found_categories(session: Session) -> dict[str, int]:
    """Game categories in the session and how many cars have each, from the fastest to the slowest."""
    running = {lap["carId"] for lap in session.data.get("laps") or []}
    count = Counter(
        CUP_CATEGORIES.get(line["car"].get("cupCategory", 0), "PRO")
        for line in session.data["sessionResult"]["leaderBoardLines"]
        if line["car"]["carId"] in running and not line.get("bIsSpectator")
    )
    return {name: count[name] for name in RANK if count[name]}


def preset_map(preset: str, found: list[str]) -> dict[str, str]:
    """Game category -> league category. Equal names stay together; the rest fill the free places in order."""
    if preset not in PRESETS:
        return {}
    wanted = PRESETS[preset]
    keep = {name: name for name in found if preset == "pro" and name in wanted}
    free = [name for name in wanted if name not in keep]
    rest = [name for name in found if name not in keep]
    return keep | dict(zip(rest, free, strict=False))
