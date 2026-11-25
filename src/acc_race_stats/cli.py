"""Command line: guided questions without arguments, or everything with options."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import unicodedata
from collections.abc import Container, Iterator
from datetime import date, datetime
from functools import cache
from itertools import islice
from pathlib import Path

from . import __version__, demo
from .divisions import PRESETS, found_categories, preset_map
from .events import Event, find_events, useful
from .folders import default_output
from .gamedata import TRACKS, track_name
from .i18n import translator
from .messages import set_language, tr
from .palette import apply_colors
from .race import Race
from .report import write
from .results import ResultError, Session, load_path, matching_qualifying, parse_name
from .roster import RosterError, load_grid, load_roster
from .server import Address, LoginError, Server, ServerError, parse_address
from .settings import load_server, save_server
from .terminal import question

PAGE = 10
# a car with one lap takes at least this in a result file; smaller files are not worth a download
BYTES_PER_CAR = 4000
KINDS = {"race": {"R"}, "practice": {"FP"}, "qualifying": {"Q"}, "all": {"R", "Q", "FP"}}
# names of the output folders
LABEL = {"R": "race", "Q": "qualifying", "FP": "practice"}


def kind_name(kind: str) -> str:
    return {"R": tr("Race"), "Q": tr("Qualifying"), "FP": tr("Practice")}[kind]


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
        raise UserError(tr("Track {text} not found or ambiguous. Options: {hint}", text=repr(text), hint=hint))
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
    raise UserError(tr("Date {text} not understood. Use day/month, like 24/11, or 2026-11-24", text=repr(text)))


def parse_pairs(items: list[str]) -> dict[str, str]:
    pairs = {}
    for item in items:
        key, sep, value = item.partition("=")
        if not sep or not key or not value:
            raise UserError(tr("{item} must look like NAME=VALUE", item=repr(item)))
        pairs[key.strip().upper()] = value.strip()
    return pairs


# ---------------------------------------------------------------- questions
def ask(text: str, default: str = "", instant: Container[str] = ()) -> str:
    hint = tr(" (press Enter for {default})", default=default) if default else ""
    return question(f"{text}{hint}: ", instant=instant).strip() or default


def ask_password() -> str:
    return question(tr("FTP password: "), hidden=True)


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
    # with up to nine options the number is enough, without Enter
    keys = [str(n) for n in range(1, len(options) + 1)] if len(options) < 10 else []
    while True:
        answer = ask(tr("Number"), str(default), keys)
        if answer.isdigit() and 1 <= int(answer) <= len(options):
            return int(answer) - 1
        print(tr("  Type a number from 1 to {last}", last=len(options)))


def ask_connection() -> Server:
    print(tr("\n1. Connection (copy it from your game server panel, for example G-Portal)"))
    saved = load_server()
    address: Address | None = None
    if saved:
        same = tr("{server}, user {user}", server=f"{saved.host}:{saved.port}", user=saved.user)
        if choose(tr("Which server?"), [tr("The same as last time ({same})", same=same), tr("Another one")]) == 0:
            address = saved
    while True:
        if address is None:
            address = ask_until(tr("FTP address (IP, or IP:port)"), parse_address)
            if address.port == 21:
                address.port = ask_until(tr("FTP port"), _port, "21")
        address.user = address.user or ask(tr("FTP user"))
        address.password = address.password or ask_password()
        print(tr("Connecting..."))
        try:
            server = Server(address)
        except LoginError as error:
            print(f"  {error}\n")
            address.password = ""
            if address is not saved:
                address.user = ""
            continue
        except ServerError as error:
            print(f"  {error}")
            if choose(tr("What now?"), [tr("Try again"), tr("Type another address")]) == 1:
                address = None
            continue
        print(tr("Connected."))
        save_server(address)
        return server


def _port(text: str) -> int:
    if not text.isdigit() or not 0 < int(text) < 65536:
        raise UserError(tr("The port is a number, like 21 or 31921"))
    return int(text)


# ---------------------------------------------------------------- picking sessions
def describe(session: Session) -> str:
    when = f"{session.when:%d/%m/%Y %H:%M}" if session.when else session.name
    return f"{when}  {track_name(session.track):<18} {kind_name(session.kind):<14} {session.cars} {tr('cars')}"


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
    print(tr("Reading {count} file(s)...", count=len(names)))
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
    t = translator(a.lang or "en")
    folders = []
    # every session of the event uses the categories of its main one
    pool_main = sessions[-1] if sessions else None
    for session in sessions:
        qualifying = matching_qualifying(session, pool) if session.kind == "R" else None
        found = list(found_categories(pool_main or session))
        class_map = preset_map(a.divisions or "", found) | parse_pairs(a.class_map)
        try:
            race = Race(
                session, qualifying, roster=roster, grid=grid if session.kind == "R" else None,
                class_map=class_map, league=a.league, event=a.event,
            )  # fmt: skip
        except ValueError as error:
            print(tr("Skipped {name}: {error}", name=session.name, error=error))
            continue
        colors = parse_pairs(a.class_color)
        for color in colors.values():
            if not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
                raise UserError(tr("Color {color} must look like #1c69d4", color=color))
        mode = apply_colors(race, "driver" if a.divisions == "none" else a.color_by, colors)
        stamp = f"{session.when:%Y-%m-%d-%H%M}" if session.when else Path(session.name).stem
        out = a.output / re.sub(r"[^A-Za-z0-9_-]", "-", f"{stamp}-{session.track}-{LABEL[session.kind]}")
        out.mkdir(parents=True, exist_ok=True)
        print(tr("Drawing charts: {what}, {track}...", what=kind_name(session.kind), track=race.track))
        images = write(race, out, t, mode)
        print(tr("  {count} charts in {folder}", count=len(images), folder=out))
        if session.kind == "R" and not any(d.grid for d in race.drivers):
            print(tr("  No starting grid: qualifying file not found (or use --grid grid.csv)"))
        for warning in race.warnings:
            print(tr("  Note: {warning}", warning=warning))
        folders.append(out)
    if not folders:
        raise UserError(tr("Nothing to draw in the chosen session."))
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
    what = " + ".join(kind_name(k) for k in reversed(event.kinds))
    return f"{when}   {track_name(event.main.track):<18} {event.cars:>2} {tr('cars')}   {what}"


def choose_event(events: Iterator[Event]) -> Event:
    """Numbered list, ten at a time."""
    shown: list[Event] = []
    while True:
        start = len(shown)
        for event in islice(events, PAGE):
            shown.append(event)
            print(f"  {len(shown):>2}  {event_line(event)}", flush=True)
        if not shown:
            raise UserError(tr("No session with enough cars was found. Use --min-cars 1 to see solo sessions."))
        if len(shown) == start:
            print(tr("  There are no older sessions."))
        more = len(shown) - start == PAGE
        while True:
            prompt = tr("Type the number, or M for older ones") if more else tr("Type the number")
            answer = ask(prompt, "1")
            if answer.isdigit() and 1 <= int(answer) <= len(shown):
                return shown[int(answer) - 1]
            if more and answer.lower() == "m":
                break
            print(tr("  Type a number from 1 to {last}", last=len(shown)))


def choose_sessions(event: Event) -> list[Session]:
    if len(event.sessions) == 1:
        return event.sessions
    sessions = event.sessions[::-1]
    options = [kind_name(s.kind) for s in sessions] + [tr("All of them")]
    picked = choose(tr("What do you want to see?"), options)
    return event.sessions if picked == len(sessions) else [sessions[picked]]


def ask_divisions(a: argparse.Namespace, session: Session) -> None:
    """Categories of the league; nothing is asked when the options already say it."""
    found = found_categories(session)
    if a.divisions or a.class_map or a.color_by == "driver" or a.roster:
        return
    print(tr("Categories saved in the file: ") + ", ".join(f"{name} ({count})" for name, count in found.items()))
    has = choose(
        tr("Does your league use categories?"), [tr("Yes"), tr("No, one color per driver")], 1 if len(found) > 1 else 2
    )
    if has == 1:
        a.divisions = "none"
        return
    options = [
        ("pro", "Pro / Pro-Am / Am"),
        ("metal", tr("Gold / Silver / Bronze")),
        ("fia", tr("Platinum / Gold / Silver / Bronze")),
        ("numbers", tr("Division 1 / 2 / 3 / 4")),
        ("game", tr("Exactly as saved in the file")),
        ("custom", tr("Let me type the names")),
    ]
    a.divisions = options[choose(tr("Which ones?"), [text for _, text in options])][0]
    if a.divisions == "custom":
        a.divisions = "game"
        for name, count in found.items():
            answer = ask(tr("Name for {name} ({count} cars)", name=name, count=count), name)
            a.class_map = [*a.class_map, f"{name}={answer.upper()}"]
    names = preset_map(a.divisions, list(found)) | parse_pairs(a.class_map)
    for name, count in found.items():
        print(
            tr(
                "  {name} -> {new} ({count} cars)",
                name=name,
                new=translator(a.lang or "en")("class_name", name=names.get(name, name)),
                count=count,
            )
        )
    if len(found) == 1:
        print(tr("  The file has only one category, so everyone has the same color."))
        a.color_by = "class"


def guided(a: argparse.Namespace) -> list[Path]:
    print("ACC Race Stats\n" + "=" * 14)
    if not a.lang:
        a.lang = ["en", "pt-br"][choose("Language / Idioma", ["English", "Português (Brasil)"])]
        set_language(a.lang)
    server = ask_connection()
    try:
        print(tr("\n2. Pick one (newest first)"))
        names = server.find_results()
        print(tr("Reading the latest sessions, this can take a minute..."))

        @cache
        def load(name: str) -> Session | None:
            found = server.try_download(name)
            return found[0] if found else None

        found = find_events(names, load, server.sizes, BYTES_PER_CAR * a.min_cars)
        event = choose_event(e for e in found if e.cars >= a.min_cars)
    finally:
        server.close()
    sessions = choose_sessions(event)
    print(tr("\n3. Categories"))
    ask_divisions(a, sessions[-1])
    print(tr("\n4. Charts"))
    a.league = a.league or ask(tr("League name to highlight (empty = none)"))
    return generate(sessions, event.sessions, a)


def direct(a: argparse.Namespace) -> list[Path]:
    track, day = parse_track(a.track), parse_day(a.date)
    if a.ftp:
        address = parse_address(a.ftp)
        address.port = a.port or address.port
        address.user = a.user or address.user or ask(tr("FTP user"))
        address.password = address.password or os.environ.get("ACC_FTP_PASSWORD") or ask_password()
        server = Server(address)
        try:
            server.find_results()
            found = search_server(server, day, track, KINDS[a.session])
            if a.list:
                print("\n".join(describe(s) for s in found) or tr("Nothing found."))
                return []
            if not found:
                raise UserError(tr("No session matches the filters."))
            newest = sorted(found, key=lambda s: s.name)
            anchor = ([s for s in newest if s.kind == "R"] or newest)[-1]
            pool = with_companions(server, anchor)
        finally:
            server.close()
    else:
        pool = demo.weekend(single_class=a.color_by == "driver") if a.demo else load_path(a.path)
        found = filter_sessions(pool, day, track, KINDS[a.session])
        if a.list:
            print("\n".join(describe(s) for s in found) or tr("Nothing found."))
            return []
        if not found:
            raise UserError(tr("No session matches the filters."))
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
    p.add_argument("--min-cars", type=int, default=2, help="hide events with fewer cars in the questions (default: 2)")
    p.add_argument("--list", action="store_true", help="only list the sessions found")
    p.add_argument("--lang", choices=["en", "pt-br"], help="language of the questions and charts (default: en)")
    p.add_argument(
        "--divisions",
        choices=["none", "game", *PRESETS],
        help="categories: none, as in the game file, pro (Pro/Pro-Am/Am), metal (Gold/Silver/Bronze), "
        "fia (Platinum/Gold/Silver/Bronze) or numbers (Division 1, 2...)",
    )
    p.add_argument("--color-by", choices=["auto", "class", "driver"], default="auto",
                   help="auto: by class if the race has several classes, otherwise one color per driver")  # fmt: skip
    p.add_argument("--roster", type=Path, help="CSV with the columns name,class,color,display,hide")
    p.add_argument("--grid", type=Path, help="CSV with the columns position,driver (when there is no qualifying file)")
    p.add_argument("--class-map", nargs="+", default=[], metavar="FROM=TO", help="rename classes: SILVER=PRO-AM")
    p.add_argument("--class-color", nargs="+", default=[], metavar="CLASS=#RRGGBB", help="change class colors")
    p.add_argument("--league", default="", help="league name, highlighted on every chart")
    p.add_argument("--event", default="", help="event name in the titles")
    p.add_argument("--output", type=Path, help="output folder (default: ACC Race Stats in your Documents)")
    p.add_argument("--no-open", action="store_true", help="do not open the folder at the end")
    p.add_argument("--version", action="version", version=__version__)
    return p


def main(argv: list[str] | None = None) -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    parser = build_parser()
    a = parser.parse_args(argv)
    set_language(a.lang or "en")
    if sum(map(bool, (a.path, a.ftp, a.demo))) > 1:
        parser.error("choose only one of: path, --ftp, --demo")
    interactive = not (a.path or a.ftp or a.demo)
    if interactive and a.list:
        parser.error("--list needs a path or --ftp")
    try:
        a.output = a.output or default_output()
        folders = guided(a) if interactive else direct(a)
    except (UserError, ServerError, ResultError, RosterError) as error:
        sys.exit(tr("Error: {error}", error=error))
    except (KeyboardInterrupt, EOFError):
        sys.exit(tr("\nCancelled."))
    if folders and not a.no_open:
        open_folder(folders[0] if len(folders) == 1 else a.output)
