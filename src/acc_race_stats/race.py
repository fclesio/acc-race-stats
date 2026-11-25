"""Analysis of one session. Every chart and report reads this model."""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Any

from .gamedata import CLASS_ORDER, CUP_CATEGORIES, NO_TIME, car_name, track_name
from .results import Session
from .roster import Roster
from .timing import start_offsets

PIT_LOSS = 25_000
CLEAN_LIMIT = 1.07


def valid_time(value: int | None) -> bool:
    return value is not None and 0 < value < NO_TIME


@dataclass(eq=False)
class Driver:
    car_id: int
    position: int
    name: str
    number: int
    car: str
    driver_class: str
    laps: int
    total: int
    best: int | None
    lap_times: list[int] = field(default_factory=list)
    valid: list[bool] = field(default_factory=list)
    splits: list[list[int]] = field(default_factory=list)
    stops: list[int] = field(default_factory=list)
    served: set[int] = field(default_factory=set)
    penalties: list[dict[str, Any]] = field(default_factory=list)
    elapsed: list[int] = field(default_factory=list)
    grid: int | None = None
    class_position: int = 0
    retired: bool = False
    color: str = "#ffffff"
    custom_color: str = ""

    @property
    def pits(self) -> list[int]:
        return [lap for lap in self.stops if lap not in self.served]

    @property
    def clean(self) -> list[tuple[int, int]]:
        """(lap number, time) without lap 1, stops, the laps around them and incidents."""
        skip = {1} | {lap + delta for lap in self.stops for delta in (-1, 0, 1)}
        laps = [(n, t) for n, t in enumerate(self.lap_times, 1) if n not in skip and valid_time(t)]
        if not laps:
            return []
        limit = statistics.median(t for _, t in laps) * CLEAN_LIMIT
        return [(n, t) for n, t in laps if t <= limit]

    @property
    def pace(self) -> float | None:
        laps = self.clean
        return statistics.median(t for _, t in laps) if laps else None

    @property
    def spread(self) -> float | None:
        laps, pace = self.clean, self.pace
        if len(laps) < 2 or pace is None:
            return None
        return statistics.mean(abs(t - pace) for _, t in laps) / 1000

    @property
    def invalid(self) -> int:
        skip = {1} | {lap + delta for lap in self.stops for delta in (-1, 0, 1)}
        return sum(not ok for n, ok in enumerate(self.valid, 1) if n not in skip)

    @property
    def sectors(self) -> list[int] | None:
        valid = [s for s, ok in zip(self.splits, self.valid, strict=True) if ok]
        rows = [s for s in valid if len(s) == 3 and all(map(valid_time, s))]
        return [min(column) for column in zip(*rows, strict=True)] if rows else None

    @property
    def ideal(self) -> int | None:
        return sum(self.sectors) if self.sectors else None


class Race:
    """A race, qualifying or practice session with its drivers in finishing order."""

    def __init__(
        self,
        session: Session,
        qualifying: Session | None = None,
        *,
        roster: Roster | None = None,
        grid: dict[str, int] | None = None,
        class_map: dict[str, str] | None = None,
        league: str = "",
        event: str = "",
    ) -> None:
        data = session.data
        self.kind, self.when, self.source = session.kind, session.when, session.name
        self.track = track_name(session.track)
        self.league, self.event = league.strip(), event.strip()
        self.title = " · ".join(part for part in (self.league, self.event, self.track) if part)
        self.warnings: list[str] = []
        self.drivers: list[Driver] = []
        is_race = session.kind == "R"

        laps: dict[int, list[dict[str, Any]]] = {}
        for lap in data.get("laps") or []:
            laps.setdefault(lap["carId"], []).append(lap)
        offsets = start_offsets(data) if is_race else {}
        player_grid: dict[str, int] = {}
        if qualifying:
            for position, line in enumerate(qualifying.data["sessionResult"]["leaderBoardLines"], 1):
                if not line.get("bIsSpectator"):
                    player_grid[line["currentDriver"].get("playerId") or ""] = position
            player_grid.pop("", None)
        unused_grid = set(grid or {})

        for line in data["sessionResult"]["leaderBoardLines"]:
            car, timing, who = line["car"], line["timing"], line["currentDriver"]
            name = (who.get("lastName") or who.get("shortName") or f"#{car['raceNumber']}").strip()
            entry = roster.get(name) if roster else None
            own = laps.get(car["carId"], [])
            if not own or line.get("bIsSpectator"):
                continue
            category = CUP_CATEGORIES.get(car.get("cupCategory", 0), "PRO")
            driver_class = (entry.driver_class if entry else "") or (class_map or {}).get(category, category)
            driver = Driver(
                car["carId"], len(self.drivers) + 1, (entry.display if entry else "") or name, car["raceNumber"],
                car_name(car["carModel"], car.get("carGroup", "")), driver_class, timing["lapCount"],
                timing["totalTime"], timing["bestLap"] if valid_time(timing["bestLap"]) else None,
                custom_color=entry.color if entry else "",
            )  # fmt: skip
            driver.lap_times = [lap["laptime"] for lap in own]
            driver.valid = [bool(lap.get("isValidForBest")) for lap in own]
            driver.splits = [list(lap.get("splits") or []) for lap in own]
            if is_race:
                offset = offsets.get(driver.car_id, 0)
                driver.lap_times[0] += offset
                if abs(offset) > 60_000:
                    self.warnings.append(f"{driver.name}: lap 1 in the file was wrong and was rebuilt")
            clock = 0
            for time in driver.lap_times:
                clock += time
                driver.elapsed.append(clock)
            later = driver.lap_times[1:]
            if later:
                typical = statistics.median(later)
                driver.stops = [n for n, t in enumerate(later, 2) if t > max(typical * 1.07, typical + PIT_LOSS)]
            for key in (f"#{driver.number}", name.casefold()):
                if grid and key in grid:
                    driver.grid = grid[key]
                    unused_grid.discard(key)
            if not grid:
                driver.grid = player_grid.get(who.get("playerId") or "")
            if entry and entry.hidden:
                continue
            self.drivers.append(driver)

        if not self.drivers:
            raise ValueError("No driver completed a lap in this session")
        if unused_grid:
            self.warnings.append("grid: not found in the race: " + ", ".join(sorted(unused_grid)))
        self.by_id = {d.car_id: d for d in self.drivers}
        for item in (data.get("penalties") or []) + (data.get("post_race_penalties") or []):
            target = self.by_id.get(item.get("carId"))
            if target and item.get("penalty", "None") != "None":
                target.penalties.append(item)
                if item.get("clearedInLap"):
                    target.served.add(item["clearedInLap"])
        present = {d.driver_class for d in self.drivers}
        self.classes = [c for c in CLASS_ORDER if c in present] + sorted(present - set(CLASS_ORDER))
        for name in self.classes:
            for position, driver in enumerate((d for d in self.drivers if d.driver_class == name), 1):
                driver.class_position = position
        self.total_laps = self.drivers[0].laps
        self.reference = self.drivers[0].total / max(1, self.total_laps)
        for driver in self.drivers:
            driver.retired = is_race and driver.laps < self.total_laps * 0.75
        longest = max(len(d.elapsed) for d in self.drivers)
        self.order = [
            [d.car_id for d in sorted((d for d in self.drivers if len(d.elapsed) > n), key=lambda d: d.elapsed[n])]
            for n in range(longest)
        ]  # fmt: skip

    def position_at(self, driver: Driver, lap: int) -> int | None:
        if not 1 <= lap <= len(self.order) or driver.car_id not in self.order[lap - 1]:
            return None
        return self.order[lap - 1].index(driver.car_id) + 1

    @property
    def fastest(self) -> Driver | None:
        return min((d for d in self.drivers if d.best), key=lambda d: d.best or 0, default=None)

    def gap(self, a: Driver, b: Driver, lap: int) -> int | None:
        if lap > min(len(a.elapsed), len(b.elapsed)):
            return None
        return b.elapsed[lap - 1] - a.elapsed[lap - 1]

    def battles(self, limit: int = 4) -> list[tuple[Driver, Driver, int]]:
        """Pairs of neighbours less than 1 s apart for the most laps (at least 3)."""
        count: dict[tuple[int, int], int] = {}
        for lap in range(2, len(self.order) + 1):
            order = [self.by_id[c] for c in self.order[lap - 1]]
            for a, b in zip(order, order[1:], strict=False):
                gap = self.gap(a, b, lap)
                if gap is not None and gap < 1000:
                    first, second = sorted((a, b), key=lambda d: d.position)
                    key = (first.car_id, second.car_id)
                    count[key] = count.get(key, 0) + 1
        top = sorted(count.items(), key=lambda item: (-item[1], self.by_id[item[0][0]].position))
        return [(self.by_id[a], self.by_id[b], n) for (a, b), n in top[:limit] if n >= 3]

    def pit_loss(self, driver: Driver, lap: int) -> float | None:
        """Seconds lost in the stop lap and its neighbours (the pit box is before or after the line)."""
        if driver.pace is None or lap < 3 or lap >= len(driver.lap_times):
            return None
        return (sum(driver.lap_times[lap - 2 : lap + 1]) - 3 * driver.pace) / 1000

    def pit_effect(self) -> list[tuple[Driver, int, int, int]]:
        """(driver, lap of the first stop, position before, position after everyone stopped)."""
        firsts = sorted(d.pits[0] for d in self.drivers if d.pits and d.pits[0] > 3)
        if not firsts:
            return []
        cycle_end = firsts[min(len(firsts) - 1, len(firsts) * 4 // 5)]
        out = []
        for d in self.drivers:
            if not d.pits:
                continue
            stop = d.pits[0]
            before = self.position_at(d, stop - 2) if stop > 2 else d.grid or self.position_at(d, 1)
            after = self.position_at(d, min(max(stop, cycle_end) + 2, len(d.elapsed)))
            if before and after:
                out.append((d, stop, before, after))
        return sorted(out, key=lambda row: (row[3] - row[2], row[1]))

    def to_dict(self) -> dict[str, Any]:
        """Canonical, documented export (schema 1). No player ids."""
        return {
            "schema": 1, "session": self.kind, "track": self.track, "title": self.title,
            "date": self.when.isoformat() if self.when else None, "laps": self.total_laps, "warnings": self.warnings,
            "drivers": [
                {
                    "position": d.position, "class_position": d.class_position, "name": d.name, "number": d.number,
                    "car": d.car, "class": d.driver_class, "color": d.color, "grid": d.grid, "laps": d.laps,
                    "total_ms": d.total if valid_time(d.total) else None, "best_ms": d.best, "ideal_ms": d.ideal,
                    "pace_ms": d.pace, "spread_s": d.spread, "pit_laps": d.pits, "invalid_laps": d.invalid,
                    "retired": d.retired, "lap_times_ms": d.lap_times, "elapsed_ms": d.elapsed,
                    "penalties": [{k: p.get(k) for k in ("penalty", "reason", "violationInLap", "clearedInLap")}
                                  for p in d.penalties],
                }
                for d in self.drivers
            ],
        }  # fmt: skip
