"""Real race clock for every car.

ACC starts the first lap of each car when it crosses the line, so adding up lap times ignores the time from the green
light to the line (a few seconds at the back of the grid). Reconnecting cars can also get an impossible first lap.
Both are fixed with two independent sources in the result file: the total race time and the order of the laps, which
are written as the cars cross the line.
"""

from __future__ import annotations

import statistics
from bisect import bisect_left
from itertools import accumulate
from typing import Any

MAX_START_OFFSET = 15_000
TOLERANCE = 1_000


def post_race_seconds(data: dict[str, Any]) -> dict[int, int]:
    extra: dict[int, int] = {}
    for item in data.get("post_race_penalties") or []:
        if item.get("penalty") == "PostRaceTime":
            extra[item["carId"]] = extra.get(item["carId"], 0) + int(item.get("penaltyValue") or 0)
    return extra


def start_offsets(data: dict[str, Any]) -> dict[int, int]:
    """carId -> milliseconds to add to the first lap."""
    laps = data.get("laps") or []
    by_car: dict[int, list[tuple[int, int]]] = {}
    for index, lap in enumerate(laps):
        by_car.setdefault(lap["carId"], []).append((index, lap["laptime"]))
    totals = {line["car"]["carId"]: line["timing"]["totalTime"] for line in data["sessionResult"]["leaderBoardLines"]}
    extra = post_race_seconds(data)
    raw: dict[int, int] = {}
    for car, entries in by_car.items():
        offset = totals.get(car, 0) - sum(time for _, time in entries)
        penalty = extra.get(car, 0) * 1000
        raw[car] = offset - penalty if penalty and offset >= penalty else offset
    trusted = {car: value for car, value in raw.items() if 0 <= value <= MAX_START_OFFSET}
    if len(trusted) < max(2, len(by_car) / 2):
        return dict.fromkeys(by_car, 0)

    crossings: list[tuple[int, int]] = []
    for car, value in trusted.items():
        times = accumulate((time for _, time in by_car[car]), initial=value)
        next(times)
        crossings += [(index, time) for (index, _), time in zip(by_car[car], times, strict=True)]
    crossings.sort()
    indexes = [index for index, _ in crossings]

    def bounds(car: int) -> list[tuple[int | None, int | None]]:
        """Range of offsets allowed by the neighbours in crossing order, lap by lap (without the first lap)."""
        result: list[tuple[int | None, int | None]] = []
        elapsed = 0
        for number, (index, time) in enumerate(by_car[car]):
            elapsed += time
            if number == 0 and len(by_car[car]) > 1:
                continue
            at = bisect_left(indexes, index)
            before = crossings[at - 1][1] - elapsed if at else None
            after = crossings[at][1] - elapsed if at < len(crossings) else None
            result.append((before, after))
        return result

    offsets = dict(trusted)
    typical = int(statistics.median(trusted.values()))
    for car in by_car.keys() - trusted.keys():
        ranges = bounds(car)
        fits = sum(
            (low is None or raw[car] >= low - TOLERANCE) and (high is None or raw[car] <= high + TOLERANCE)
            for low, high in ranges
        )
        if fits >= 0.8 * len(ranges):
            offsets[car] = raw[car]
            continue
        lows = [low for low, _ in ranges if low is not None]
        highs = [high for _, high in ranges if high is not None]
        low = int(max(lows)) if lows else typical
        high = int(min(highs)) if highs else typical
        offsets[car] = min(max(typical, low), high) if low <= high else (low + high) // 2
    return offsets
