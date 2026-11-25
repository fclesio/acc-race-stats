"""Reading ACC result files and finding the sessions of one race weekend."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .messages import tr

FILE_NAME = re.compile(r"^(?:results_)?(\d{6}_\d{6})_(R\d?|Q\d?|FP\d?)\.json$", re.IGNORECASE)


class ResultError(Exception):
    """The result file is missing or is not an ACC session."""


@dataclass
class Session:
    name: str
    kind: str  # R, Q or FP
    data: dict[str, Any]
    when: datetime | None = None

    @property
    def track(self) -> str:
        return str(self.data.get("trackName", ""))

    @property
    def cars(self) -> int:
        return len(self.data["sessionResult"]["leaderBoardLines"])


def parse_name(name: str) -> tuple[datetime, str] | None:
    """'261124_223000_R.json' -> (datetime, 'R')"""
    match = FILE_NAME.match(name)
    if not match:
        return None
    try:
        when = datetime.strptime(match[1], "%y%m%d_%H%M%S")
    except ValueError:
        return None
    return when, match[2].upper().rstrip("0123456789")


def decode(raw: bytes) -> dict[str, Any]:
    """ACC writes UTF-16 LE (usually without BOM); other tools save the files again as UTF-8."""
    if raw[:2] == b"\xff\xfe":
        text = raw.decode("utf-16")
    elif raw[1:2] == b"\x00":
        text = raw.decode("utf-16-le")
    else:
        text = raw.decode("utf-8-sig")
    data = json.loads(text)
    if not isinstance(data, dict) or "leaderBoardLines" not in (data.get("sessionResult") or {}):
        raise ResultError(tr("not an ACC session result"))
    return data


def session_from_bytes(name: str, raw: bytes) -> Session:
    try:
        data = decode(raw)
    except (ValueError, UnicodeDecodeError) as error:
        raise ResultError(tr("{name}: not a valid ACC result file", name=name)) from error
    parsed = parse_name(name)
    kind = str(data.get("sessionType", "")).upper().rstrip("0123456789") or (parsed[1] if parsed else "")
    if kind not in ("R", "Q", "FP"):
        raise ResultError(tr("{name}: unknown session type {kind}", name=name, kind=repr(kind)))
    return Session(name, kind, data, parsed[0] if parsed else None)


def load_path(path: Path) -> list[Session]:
    """Every ACC session in a file or folder; other files are skipped."""
    files = sorted(path.glob("*.json")) if path.is_dir() else [path]
    sessions = []
    for file in files:
        try:
            sessions.append(session_from_bytes(file.name, file.read_bytes()))
        except (ResultError, OSError):
            if not path.is_dir():
                raise
    if not sessions:
        raise ResultError(tr("No ACC result file found in {path}", path=path))
    return sessions


def matching_qualifying(race: Session, sessions: list[Session]) -> Session | None:
    """The last qualifying on the same track in the 4 hours before the race."""
    options = [s for s in sessions if s.kind == "Q" and s.track == race.track]
    if race.when is None:
        return options[-1] if len(options) == 1 else None
    dated = [s for s in options if s.when and timedelta(0) < race.when - s.when < timedelta(hours=4)]
    if dated:
        return max(dated, key=lambda s: s.when or datetime.min)
    undated = [s for s in options if s.when is None]
    return undated[0] if len(undated) == 1 else None
