# Usage

## Guided

The launchers (`ACC-Race-Stats.bat`, `ACC-Race-Stats.command`, `./run.sh` or `make`) ask everything. The first question
is the language; Portuguese is the default. Menus with up to nine options accept the number alone; the others need
Enter. Ctrl-C stops at any point.

The last server (address, port and user) is remembered, so the next run only asks for the password. A
[settings file](#settings-file) can answer the rest. Events where fewer
than two cars completed a lap are hidden; `--min-cars 1` shows them.

## Options

Pass options to the guided run, or skip the questions with a path, `--ftp` or `--demo`.

| System | How |
|---|---|
| Windows | `make --league "My League"` |
| macOS, Linux | `./run.sh --league "My League"` or `make ARGS='--league "My League"'` |
| With [uv](https://docs.astral.sh/uv/) | `uv run acc-race-stats --league "My League"` |

### Where the data comes from

| Option | What it does |
|---|---|
| `path` | a result file, or a folder with result files |
| `--ftp ADDRESS` | IP, `IP:port` or `ftp://user@IP:port` |
| `--port`, `--user` | when they are not in the address |
| `--demo` | an invented race weekend |

The password is asked, or read from the environment variable `ACC_FTP_PASSWORD` or from the
[settings file](#settings-file). With a server in the settings file, `--list` and the filters below work without
`--ftp`.

### Which session

These filters apply without the questions, except `--min-cars`, which is only for the questions.

| Option | What it does |
|---|---|
| `--session race\|practice\|qualifying\|all` | default `race` |
| `--track monza` | name of the track, or part of it |
| `--date 24/11` | within 3 days of it; also `24/11/2026` and `2026-11-24` |
| `--list` | only list the sessions found |
| `--min-cars N` | hide events with fewer cars (default 2) |

Without filters, the newest race is used.

### Categories and colors

| Option | What it does |
|---|---|
| `--divisions none` | one color per driver, no categories |
| `--divisions game` | the categories saved in the file |
| `--divisions pro` | Pro / Pro-Am / Am |
| `--divisions metal` | Gold / Silver / Bronze |
| `--divisions fia` | Platinum / Gold / Silver / Bronze |
| `--divisions numbers` | Division 1, 2, 3 and 4 |
| `--class-map SILVER=PRO-AM` | rename one or more categories |
| `--class-color PRO=#ffffff` | change the color of one or more categories |
| `--color-by auto\|class\|driver` | `auto` uses categories when there is more than one |

The categories of the game are ranked Pro, Pro-Am, Silver, Am, National. The fastest one in the file gets the first
category of the league, and so on. With `pro`, equal names stay together.

### Output

| Option | What it does |
|---|---|
| `--lang en\|pt-br` | questions and charts (default `pt-br`) |
| `--league NAME` | highlighted on every chart |
| `--event NAME` | in the titles, for example "Round 3" |
| `--output FOLDER` | default: `ACC Race Stats` in your Documents folder |
| `--no-open` | do not open the folder at the end |
| `--config FILE` | settings file (default: `acc-race-stats.toml`, if it exists) |

The charts, `summary.txt` and `race.json` of a session are written side by side in one folder,
`<date>-<time>-<track>-<session>`. Running again on the same session replaces them.

## Settings file

A [TOML](https://toml.io) file with the answers, so they are not typed every time. At the end of a guided run without a
settings file, the program offers to write one with the server, password, language, league and categories: in the
project folder, or next to the remembered server when that folder cannot be written. It can also be written by hand
from [acc-race-stats.example.toml](../acc-race-stats.example.toml).

It is looked for in this order; the first one found is used:

1. `--config FILE`;
2. the environment variable `ACC_RACE_STATS_CONFIG`;
3. `acc-race-stats.toml` in the current folder (the project folder, for the launchers);
4. `config.toml` next to the remembered server (see [the files on your computer](troubleshooting.md#files-on-your-computer)).

Options on the command line win over the file, and the file wins over the questions. An unknown setting, a wrong type or
a wrong value stops with a message that names it.

| `[server]` | Content |
|---|---|
| `address` | IP, `IP:port` or `ftp://user@IP:port` |
| `port`, `user` | when they are not in the address |
| `password` | the FTP password; leave it out to be asked |

| `[report]` | Same as |
|---|---|
| `language` | `--lang` |
| `league`, `event` | `--league`, `--event` |
| `divisions`, `color_by` | `--divisions`, `--color-by` |
| `class_map`, `class_color` | `--class-map`, `--class-color`, as a table: `{ SILVER = "PRO-AM" }` |
| `roster`, `grid`, `output` | `--roster`, `--grid`, `--output`; relative to the settings file, `~` allowed |
| `min_cars` | `--min-cars` |
| `open_folder` | `false` is `--no-open` |

**The password is stored in plain text.** `acc-race-stats.toml` is in `.gitignore`. Do not share, commit or send it. On
macOS and Linux the program makes a file with a password readable only by its owner. When the saved password is refused,
the one typed instead replaces it in the file; the rest of the file is kept.

## Driver list

`--roster roster.csv` changes how drivers appear. Only `name` (the in-game name) is required. The separator can be `,` or
`;`, and lines starting with `#` are ignored. Drivers who are not in the list keep the data of the game.

| Column | Content |
|---|---|
| `name` | in-game name |
| `class` | category |
| `color` | like `#1c69d4` |
| `display` | another name for the charts |
| `hide` | `yes` leaves the driver out (a broadcaster, for example) |

See [examples/roster.csv](../examples/roster.csv).

## Starting grid

The grid comes from the last qualifying on the same track in the 4 hours before the race. Without that file, use
`--grid grid.csv`, with in-game names or car numbers. See [examples/grid.csv](../examples/grid.csv).
