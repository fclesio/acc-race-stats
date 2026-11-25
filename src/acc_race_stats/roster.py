"""Optional files written by the user: driver list and starting grid."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path


class RosterError(Exception):
    """The driver list or grid file cannot be used."""


@dataclass
class RosterEntry:
    driver_class: str = ""
    color: str = ""
    display: str = ""
    hidden: bool = False


@dataclass
class Roster:
    entries: dict[str, RosterEntry] = field(default_factory=dict)

    def get(self, name: str) -> RosterEntry | None:
        return self.entries.get(name.casefold())


def _rows(path: Path) -> list[dict[str, str]]:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as error:
        raise RosterError(f"Cannot read {path}") from error
    except UnicodeDecodeError:
        text = path.read_text(encoding="cp1252")
    lines = [line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    if not lines:
        raise RosterError(f"{path} is empty")
    reader = csv.DictReader(lines, delimiter=";" if ";" in lines[0] else ",")
    return [{(k or "").strip().lower(): (v or "").strip() for k, v in row.items() if k} for row in reader]


def load_roster(path: Path) -> Roster:
    """CSV with a header: name,class,color,display,hide (only name is required)."""
    import re

    roster = Roster()
    for row in _rows(path):
        name = row.get("name", "")
        if not name:
            raise RosterError(f"{path}: every line needs a value in the 'name' column")
        color = row.get("color", "")
        if color and not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
            raise RosterError(f"{path}: color {color!r} of {name} must look like #1c69d4")
        hidden = row.get("hide", "").lower() in ("yes", "y", "1", "true", "x")
        roster.entries[name.casefold()] = RosterEntry(
            row.get("class", "").upper(), color, row.get("display", ""), hidden
        )
    return roster


def load_grid(path: Path) -> dict[str, int]:
    """CSV with a header: position,driver. Driver is the in-game name or '#' and the car number."""
    grid: dict[str, int] = {}
    for row in _rows(path):
        driver, position = row.get("driver", ""), row.get("position", "")
        if not driver or not position.isdigit():
            raise RosterError(f"{path}: every line needs 'position' (a number) and 'driver'")
        if int(position) in grid.values() or driver.casefold() in grid:
            raise RosterError(f"{path}: position {position} or driver {driver} is repeated")
        grid[driver.casefold()] = int(position)
    return grid
