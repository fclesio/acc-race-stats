# ACC Race Stats

Charts and a report from Assetto Corsa Competizione server results. Connect to your game server, choose the session,
and get PNG charts, a single-file HTML report and a summary for your league chat. No game mods, no telemetry.

## Quick start (Windows)

1. Download this project and unzip it.
2. Double-click `Run.bat`. The first run installs [uv](https://docs.astral.sh/uv/), which brings Python and everything else.
3. Answer the questions: server connection first, then track, approximate date and session.

On macOS or Linux, with uv installed: `uv run --no-dev acc-race-stats`

```
1. Connection (from your game server panel, for example G-Portal)
FTP address (IP, IP:port or ftp://...): 203.0.113.10:31921
FTP user: myuser
FTP password (hidden while you type):
Connected.

2. What do you want to see?
Track (empty = any): monza
Approximate date, like 24/11 (empty = most recent): 24/11

Session
  1  Race
  2  Free practice
  3  Qualifying
  4  All of them
```

Results go to `reports/`: `report.html`, `charts/`, `summary.txt` and `race.json`.

Try it without a server: `uv run acc-race-stats --demo --session all`

## Options

| Option | What it does |
|---|---|
| `path` | result file, or folder with result files |
| `--ftp ADDRESS --port N --user U` | server; the password is asked, or read from `ACC_FTP_PASSWORD` |
| `--track` `--date` `--session race\|practice\|qualifying\|all` | which session; the date matches 3 days either way |
| `--list` | only list the sessions found |
| `--lang pt-br\|en` | chart language (default `pt-br`) |
| `--color-by auto\|class\|driver` | `auto` uses classes when the race has more than one |
| `--class-map SILVER=PRO-AM` | rename the game classes |
| `--class-color PRO=#ffffff` | change class colors |
| `--roster roster.csv` | optional driver list |
| `--grid grid.csv` | starting grid when there is no qualifying file |

`roster.csv` (only `name` is required; `hide` removes someone, such as a broadcaster):

```csv
name,class,color,display,hide
Some Gamertag,PRO,,,
Race Narrator,,,,yes
```

`grid.csv` takes in-game names or car numbers (quotes are not needed):

```csv
position,driver
1,#84
2,Some Gamertag
```

## How the race clock works

ACC starts the first lap of each car at the line, so adding up lap times ignores the seconds between the green light and
the line. Cars that reconnect can also get an impossible first lap. Both are corrected using the total race time and the
order in which the laps were written. The report lists rebuilt laps.

## Privacy

The FTP password is never saved. Plain FTP sends it unencrypted, so do not reuse it elsewhere. Player ids are never
written to the output.

## Development

```bash
uv sync
uv run pytest
uv run ruff check .
uv run mypy
```

Commits follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/). License: MIT.

This project is not affiliated with Kunos Simulazioni.
