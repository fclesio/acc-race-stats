"""Synthetic race weekend (invented drivers) for the demo and the tests."""

from __future__ import annotations

import random
from datetime import datetime
from typing import Any

from .results import Session

NAMES = [
    "Apex Rabbit", "LateBraker", "Kerb_Hunter", "SlipstreamSam", "Marble Run", "TurnTen", "Undercut", "BoxBox99",
    "GravelTrap", "NightStint", "Delta_Plus", "PurpleSector", "ColdTyres", "LiftAndCoast", "FormationLap", "BlueFlag",
]  # fmt: skip


def weekend(seed: int = 7, single_class: bool = False, laps: int = 24) -> list[Session]:
    rng = random.Random(seed)
    cars: list[dict[str, Any]] = []
    for n, name in enumerate(NAMES):
        who = {"firstName": "", "lastName": name, "shortName": name[:3].upper(), "playerId": f"demo{n}"}
        cars.append({
            "carId": 1001 + n, "raceNumber": 10 + n, "carModel": [32, 30, 34, 35, 25, 8][n % 6], "carGroup": "GT3",
            "cupCategory": 0 if single_class else min(2, n // 6), "drivers": [who],
        })  # fmt: skip
    base = {car["carId"]: 108_000 + n * 220 + rng.randint(-150, 150) for n, car in enumerate(cars)}

    def lap(car: int, time: int, ok: bool) -> dict[str, Any]:
        first, second = round(time * 0.32), round(time * 0.35)
        splits = [first, second, time - first - second]
        return {"carId": car, "driverIndex": 0, "laptime": time, "isValidForBest": ok, "splits": splits}

    def session(kind: str, rows: list[dict[str, Any]], total: dict[int, int], order: list[int]) -> dict[str, Any]:
        by_id = {car["carId"]: car for car in cars}
        lines = []
        for car_id in order:
            own = [r for r in rows if r["carId"] == car_id]
            best = min((r["laptime"] for r in own if r["isValidForBest"]), default=2**31 - 1)
            lines.append({
                "car": by_id[car_id], "currentDriver": by_id[car_id]["drivers"][0], "currentDriverIndex": 0,
                "timing": {"lapCount": len(own), "totalTime": total[car_id], "bestLap": best}, "bIsSpectator": False,
            })  # fmt: skip
        return {
            "sessionType": kind, "trackName": "monza", "serverName": "Demo League", "laps": rows, "penalties": [],
            "post_race_penalties": [], "sessionResult": {"leaderBoardLines": lines},
        }  # fmt: skip

    def practice(kind: str, count: int) -> dict[str, Any]:
        rows = [lap(c, base[c] + int(rng.expovariate(1 / 500)), rng.random() > 0.1) for _ in range(count) for c in base]
        best = {c: min((r["laptime"] for r in rows if r["carId"] == c and r["isValidForBest"]), default=2**31 - 1)
                for c in base}  # fmt: skip
        return session(kind, rows, dict.fromkeys(base, count * 110_000), sorted(base, key=lambda c: best[c]))

    free, quali = practice("FP", 10), practice("Q", 5)
    grid = [line["car"]["carId"] for line in quali["sessionResult"]["leaderBoardLines"]]
    clock = {car: 250 * place for place, car in enumerate(grid, 1)}
    crossings: list[tuple[int, dict[str, Any]]] = []
    for car in grid:
        stop = rng.randint(9, 15)
        for number in range(1, laps + 1):
            time = base[car] + int(rng.gauss(500, 350)) + (7_000 + 350 * grid.index(car) if number == 1 else 0)
            time += 9_000 if number == stop - 1 else 52_000 if number == stop else 0
            clock[car] += time
            crossings.append((clock[car], lap(car, time, rng.random() > 0.08)))
    leader = min(clock.values())
    kept = [(t, r) for t, r in crossings if t - r["laptime"] < leader]
    kept.sort(key=lambda item: item[0])
    rows = [r for _, r in kept]
    total = {car: max(t for t, r in kept if r["carId"] == car) for car in grid}
    count = {car: sum(r["carId"] == car for r in rows) for car in grid}
    race = session("R", rows, total, sorted(grid, key=lambda c: (-count[c], total[c])))
    day = "260315"
    return [
        Session(f"{day}_{hour}_{kind}.json", kind, data, datetime.strptime(f"{day}_{hour}", "%y%m%d_%H%M%S"))
        for hour, kind, data in (("200000", "FP", free), ("203000", "Q", quali), ("214000", "R", race))
    ]  # fmt: skip
