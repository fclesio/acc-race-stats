"""Command line: guided questions without arguments, or everything with options."""

from __future__ import annotations

import argparse
import getpass
import os
import re
import subprocess
import sys
import unicodedata
from collections.abc import Iterator
from datetime import date, datetime
from functools import cache
from itertools import islice
from pathlib import Path

from . import __version__, demo
from .events import Event, find_events, useful
from .gamedata import TRACKS, track_name
from .i18n import translator
from .palette import apply_colors
from .race import Race
from .report import write
from .results import ResultError, Session, load_path, matching_qualifying, parse_name
from .roster import RosterError, load_grid, load_roster
from .server import Address, LoginError, Server, ServerError, parse_address

PAGE = 10
KINDS = {"race": {"R"}, "practice": {"FP"}, "qualifying": {"Q"}, "all": {"R", "Q", "FP"}}
LABEL = {"R": "race", "Q": "qualifying", "FP": "practice"}


class UserError(Exception):
    """Wrong input, shown without a traceback."""


def fold(text: str) -> str:
    plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", plain.lower())


def parse_track(text: str) -> str | None:
    """Track id for a name or part of it; None for any track."""
    wanted = fold(text)
    if not wanted:
        return None
    options = {i for i, name in TRACKS.items() if wanted in (fold(i), fold(name))} or {
        i for i, name in TRACKS.items() if wanted in fold(i) or wanted in fold(name)
    }
    if len(options) != 1:
        hint = ", ".join(sorted(track_name(i) for i in options or TRACKS))
        raise UserError(f"Track {text!r} {'is ambiguous' if options else 'not found'}. Options: {hint}")
    return options.pop()


def parse_day(text: str, today: date | None = None) -> date | None:
    """'24/11/2026', '24/11' (most recent one) or '2026-11-24'; None for any day."""
    text = text.strip()
    if not text:
        return None
    for pattern in ("%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(text, pattern).date()
        except ValueError:
            continue
    today = today or date.today()
    match = re.fullmatch(r"(\d{1,2})/(\d{1,2})", text)
    if match:
        for year in range(today.year, today.year - 5, -1):
            try:
                day = date(year, int(match[2]), int(match[1]))
            except ValueError:
                continue
            if day <= today:
                return day
    raise UserError(f"Date {text!r} not understood. Use day/month, like 24/11, or 2026-11-24")


def parse_pairs(items: list[str]) -> dict[str, str]:
    pairs = {}
    for item in items:
        key, sep, value = item.partition("=")
        if not sep or not key or not value:
            raise UserError(f"{item!r} must look like NAME=VALUE")
        pairs[key.strip().upper()] = value.strip()
    return pairs


# ---------------------------------------------------------------- questions
def ask(question: str, default: str = "") -> str:
    answer = input(f"{question}{f' [{default}]' if default else ''}: ").strip()
    return answer or default


def ask_until(question: str, parse, default: str = ""):  # type: ignore[no-untyped-def]
    while True:
        try:
            return parse(ask(question, default))
        except (UserError, ServerError) as error:
            print(f"  {error}")


def choose(title: str, options: list[str], default: int = 1) -> int:
    print(f"\n{title}")
    for n, option in enumerate(options, 1):
        print(f"  {n}  {option}")
    while True:
        answer = ask("Number", str(default))
        if answer.isdigit() and 1 <= int(answer) <= len(options):
            return int(answer) - 1
        print(f"  Type a number from 1 to {len(options)}")


def ask_connection() -> Server:
    print("\n1. Connection (copy it from your game server panel, for example G-Portal)")
    address: Address | None = None
    while True:
        if address is None:
            address = ask_until("FTP address (IP, or IP:port)", parse_address)
            if address.port == 21:
                address.port = ask_until("FTP port", _port, "21")
        address.user = address.user or ask("FTP user")
        address.password = address.password or getpass.getpass("FTP password (hidden while you type): ")
        print("Connecting...")
        try:
            server = Server(address)
        except LoginError as error:
            print(f"  {error}\n")
            address.user = address.password = ""
            continue
        except ServerError as error:
            print(f"  {error}\n")
            address = None
            continue
        print("Connected.")
        return server


def _port(text: str) -> int:
    if not text.isdigit() or not 0 < int(text) < 65536:
        raise UserError("The port is a number, like 21 or 31921")
    return int(text)


# ---------------------------------------------------------------- picking sessions
def describe(session: Session) -> str:
    when = f"{session.when:%d/%m/%Y %H:%M}" if session.when else session.name
    return f"{when}  {track_name(session.track):<18} {LABEL[session.kind]:<11} {session.cars} cars"


def same_weekend(anchor: Session, sessions: list[Session]) -> list[Session]:
    """The newest session of each kind on the anchor's track in the 4 hours up to the anchor."""
    found: dict[str, Session] = {anchor.kind: anchor}
    for s in sorted(sessions, key=lambda s: s.name):
        if s.kind != anchor.kind and s.track == anchor.track and useful(s):
            if s.when and anchor.when and not 0 <= (anchor.when - s.when).total_seconds() < 4 * 3600:
                continue
            found[s.kind] = s
    return [found[k] for k in ("FP", "Q", "R") if k in found]


def filter_sessions(sessions: list[Session], day: date | None, track: str | None, kinds: set[str]) -> list[Session]:
    """Local sessions; a renamed file has no date and passes the date filter."""
    return [
        s
        for s in sessions
        if useful(s)
        and s.kind in kinds
        and track in (None, s.track)
        and (day is None or s.when is None or abs((s.when.date() - day).days) <= 3)
    ]


def search_server(server: Server, day: date | None, track: str | None, kinds: set[str]) -> list[Session]:
    server.names or server.find_results()
    names = server.search(day, kinds)
    if not names:
        return []
    print(f"Reading {len(names)} file(s)...")
    sessions = [found[0] for name in names if (found := server.try_download(name))]
    return [s for s in sessions if useful(s) and (track is None or s.track == track)]


def with_companions(server: Server, anchor: Session) -> list[Session]:
    """The anchor and the other sessions of its weekend (needed for the grid)."""
    if anchor.when is None:
        return [anchor]
    near = []
    for name in server.names:
        parsed = parse_name(name)
        if parsed and name != anchor.name and 0 <= (anchor.when - parsed[0]).total_seconds() < 4 * 3600:
            found = server.try_download(name)
            if found:
                near.append(found[0])
    return [anchor, *near]


def generate(sessions: list[Session], pool: list[Session], a: argparse.Namespace) -> list[Path]:
    roster = load_roster(a.roster) if a.roster else None
    grid = load_grid(a.grid) if a.grid else None
    t = translator(a.lang)
    folders = []
    for session in sessions:
        qualifying = matching_qualifying(session, pool) if session.kind == "R" else None
        try:
            race = Race(
                session, qualifying, roster=roster, grid=grid if session.kind == "R" else None,
                class_map=parse_pairs(a.class_map), league=a.league, event=a.event,
            )  # fmt: skip
        except ValueError as error:
            print(f"Skipped {session.name}: {error}")
            continue
        colors = parse_pairs(a.class_color)
        for color in colors.values():
            if not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
                raise UserError(f"Color {color!r} must look like #1c69d4")
        mode = apply_colors(race, a.color_by, colors)
        stamp = f"{session.when:%Y-%m-%d-%H%M}" if session.when else Path(session.name).stem
        out = a.output / re.sub(r"[^A-Za-z0-9_-]", "-", f"{stamp}-{session.track}-{LABEL[session.kind]}")
        out.mkdir(parents=True, exist_ok=True)
        print(f"Drawing {LABEL[session.kind]} at {race.track}...")
        images = write(race, out, t, mode)
        print(f"  {len(images)} charts (colors by {mode}) in {out}")
        if session.kind == "R" and not any(d.grid for d in race.drivers):
            print("  No starting grid: qualifying file not found (or use --grid grid.csv)")
        for warning in race.warnings:
            print(f"  Note: {warning}")
        folders.append(out)
    if not folders:
        raise UserError("Nothing to draw in the chosen session.")
    return folders


def open_folder(path: Path) -> None:
    try:
        if sys.platform == "win32":
            os.startfile(path)
        else:
            subprocess.run(["open" if sys.platform == "darwin" else "xdg-open", str(path)], check=False)
    except OSError:
        pass


# ---------------------------------------------------------------- entry points
def event_line(event: Event) -> str:
    when = f"{event.main.when:%d/%m/%Y %H:%M}" if event.main.when else ""
    what = " + ".join(LABEL[k].capitalize() for k in reversed(event.kinds))
    return f"{when}   {track_name(event.main.track):<18} {event.main.cars:>2} cars   {what}"


def choose_event(events: Iterator[Event]) -> Event:
    """Numbered list, ten at a time."""
    shown: list[Event] = []
    while True:
        page = list(islice(events, PAGE))
        if not page:
            if not shown:
                raise UserError("No session with laps was found.")
            print("  There are no older sessions.")
        for number, event in enumerate(page, len(shown) + 1):
            print(f"  {number:>2}  {event_line(event)}")
        shown += page
        more = len(page) == PAGE
        while True:
            answer = ask("Type the number" + (", or M for older ones" if more else ""), "1")
            if answer.isdigit() and 1 <= int(answer) <= len(shown):
                return shown[int(answer) - 1]
            if more and answer.lower() == "m":
                break
            print(f"  Type a number from 1 to {len(shown)}")


def choose_sessions(event: Event) -> list[Session]:
    if len(event.sessions) == 1:
        return event.sessions
    sessions = event.sessions[::-1]
    options = [LABEL[s.kind].capitalize() for s in sessions] + ["All of them"]
    picked = choose("What do you want to see?", options)
    return event.sessions if picked == len(sessions) else [sessions[picked]]


def guided(a: argparse.Namespace) -> list[Path]:
    print("ACC Race Stats\n" + "=" * 14)
    server = ask_connection()
    try:
        print("\n2. Pick one (newest first)")
        names = server.find_results()
        print("Reading the latest sessions, this can take a minute...")

        @cache
        def load(name: str) -> Session | None:
            found = server.try_download(name)
            return found[0] if found else None

        event = choose_event(find_events(names, load))
    finally:
        server.close()
    sessions = choose_sessions(event)
    print("\n3. Titles")
    a.league = a.league or ask("League name to highlight (empty = none)")
    return generate(sessions, event.sessions, a)


def direct(a: argparse.Namespace) -> list[Path]:
    track, day = parse_track(a.track), parse_day(a.date)
    if a.ftp:
        address = parse_address(a.ftp)
        address.port = a.port or address.port
        address.user = a.user or address.user or ask("FTP user")
        address.password = (
            address.password or os.environ.get("ACC_FTP_PASSWORD") or getpass.getpass("FTP password (hidden): ")
        )
        server = Server(address)
        try:
            server.find_results()
            found = search_server(server, day, track, KINDS[a.session])
            if a.list:
                print("\n".join(describe(s) for s in found) or "Nothing found.")
                return []
            if not found:
                raise UserError("No session matches the filters.")
            newest = sorted(found, key=lambda s: s.name)
            anchor = ([s for s in newest if s.kind == "R"] or newest)[-1]
            pool = with_companions(server, anchor)
        finally:
            server.close()
    else:
        pool = demo.weekend(single_class=a.color_by == "driver") if a.demo else load_path(a.path)
        found = filter_sessions(pool, day, track, KINDS[a.session])
        if a.list:
            print("\n".join(describe(s) for s in found) or "Nothing found.")
            return []
        if not found:
            raise UserError("No session matches the filters.")
        newest = sorted(found, key=lambda s: s.name)
        anchor = ([s for s in newest if s.kind == "R"] or newest)[-1]
    return generate(same_weekend(anchor, pool) if a.session == "all" else [anchor], pool, a)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="acc-race-stats", description="Charts from Assetto Corsa Competizione server results. "
        "Run it without a path, --ftp or --demo and it asks everything step by step.",
    )  # fmt: skip
    p.add_argument("path", nargs="?", type=Path, help="result file or folder with result files")
    p.add_argument("--ftp", metavar="ADDRESS", help="server address: IP, IP:port or ftp://user@IP:port")
    p.add_argument("--port", type=int, help="FTP port (default: from the address, or 21)")
    p.add_argument("--user", help="FTP user (the password is asked, or read from ACC_FTP_PASSWORD)")
    p.add_argument("--demo", action="store_true", help="use an invented race weekend")
    p.add_argument("--track", default="", help="only this track (name or part of it)")
    p.add_argument("--date", default="", help="within 3 days of this date: 24/11, 24/11/2026 or 2026-11-24")
    p.add_argument("--session", choices=list(KINDS), default="race", help="what to draw (default: race)")
    p.add_argument("--list", action="store_true", help="only list the sessions found")
    p.add_argument("--lang", choices=["pt-br", "en"], default="pt-br", help="language of the charts (default: pt-br)")
    p.add_argument("--color-by", choices=["auto", "class", "driver"], default="auto",
                   help="auto: by class if the race has several classes, otherwise one color per driver")  # fmt: skip
    p.add_argument("--roster", type=Path, help="CSV with the columns name,class,color,display,hide")
    p.add_argument("--grid", type=Path, help="CSV with the columns position,driver (when there is no qualifying file)")
    p.add_argument("--class-map", nargs="+", default=[], metavar="FROM=TO", help="rename classes: SILVER=PRO-AM")
    p.add_argument("--class-color", nargs="+", default=[], metavar="CLASS=#RRGGBB", help="change class colors")
    p.add_argument("--league", default="", help="league name, highlighted on every chart")
    p.add_argument("--event", default="", help="event name in the titles")
    p.add_argument("--output", type=Path, default=Path("reports"), help="output folder (default: reports)")
    p.add_argument("--no-open", action="store_true", help="do not open the folder at the end")
    p.add_argument("--version", action="version", version=__version__)
    return p


def main(argv: list[str] | None = None) -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    parser = build_parser()
    a = parser.parse_args(argv)
    if sum(map(bool, (a.path, a.ftp, a.demo))) > 1:
        parser.error("choose only one of: path, --ftp, --demo")
    interactive = not (a.path or a.ftp or a.demo)
    if interactive and a.list:
        parser.error("--list needs a path or --ftp")
    try:
        folders = guided(a) if interactive else direct(a)
    except (UserError, ServerError, ResultError, RosterError) as error:
        sys.exit(f"Error: {error}")
    except (KeyboardInterrupt, EOFError):
        sys.exit("\nCancelled.")
    if folders and not a.no_open:
        open_folder(folders[0] if len(folders) == 1 else a.output)
