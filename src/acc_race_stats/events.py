"""Groups loose result files into events: a race with its qualifying and practice, or a practice day."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta

from .results import Session, parse_name

WINDOW = timedelta(hours=4)
BREAK = timedelta(hours=2)
MAX_FILES = 12  # files read per kind in one event; servers save many short practice sessions

Loader = Callable[[str], "Session | None"]


@dataclass
class Event:
    sessions: list[Session]  # practice, qualifying, race (the ones that exist)

    @property
    def main(self) -> Session:
        return self.sessions[-1]

    @property
    def cars(self) -> int:
        """Most cars that completed a lap in any session of the event."""
        return max(running_cars(s) for s in self.sessions)

    @property
    def kinds(self) -> list[str]:
        return [s.kind for s in self.sessions]


def running_cars(session: Session) -> int:
    return len({lap["carId"] for lap in session.data.get("laps") or []})


def useful(session: Session | None) -> bool:
    return session is not None and session.cars > 0 and bool(session.data.get("laps"))


def _best(names: list[str], load: Loader, track: str | None, newest: bool) -> Session | None:
    """The newest usable session, or the one with most laps."""
    found: Session | None = None
    for name in names[:MAX_FILES]:
        session = load(name)
        if session is None or not useful(session) or track not in (None, session.track):
            continue
        if newest:
            return session
        if found is None or len(session.data["laps"]) > len(found.data["laps"]):
            found = session
    return found


def find_events(names: list[str], load: Loader) -> Iterator[Event]:
    """Events from newest to oldest, reading files only as they are needed."""
    dated: list[tuple[datetime, str, str]] = []
    for name in names:
        parsed = parse_name(name)
        if parsed:
            dated.append((parsed[0], parsed[1], name))
    dated.sort(reverse=True)
    used: set[str] = set()

    def before(when: datetime, kind: str) -> list[str]:
        return [n for t, k, n in dated if k == kind and timedelta(0) < when - t < WINDOW]

    for position, (when, kind, name) in enumerate(dated):
        if name in used:
            continue
        used.add(name)
        if kind == "R":
            race = load(name)
            if race is None or not useful(race):
                continue
            parts = [
                _best(before(when, "FP"), load, race.track, newest=False),
                _best(before(when, "Q"), load, race.track, newest=True),
                race,
            ]
            previous = next((t for t, k, _ in dated[position + 1 :] if k == "R"), datetime.min)
            used |= {n for t, k, n in dated if k != "R" and max(previous, when - WINDOW) < t < when}
        else:
            block, last = [(kind, name)], when
            for t, k, n in dated[position + 1 :]:
                if k == "R" or last - t > BREAK:
                    break
                block.append((k, n))
                last = t
            # the files of a block with a later race were already used by that race
            block = [(k, n) for k, n in block if n == name or n not in used]
            used |= {n for _, n in block}
            main = _best([n for k, n in block if k == "Q"], load, None, newest=True)
            practice = _best([n for k, n in block if k == "FP"], load, main.track if main else None, newest=False)
            parts = [practice, main]
        sessions = [s for s in parts if s is not None]
        if sessions:
            yield Event(sessions)
