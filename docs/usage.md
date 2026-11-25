# Usage

## Guided

`make` asks everything. Menus with up to nine options accept the number alone; the others need Enter. Ctrl-C stops at any
point.

The last server (address, port and user) is remembered, so the next run only asks for the password. Events where fewer
than two cars completed a lap are hidden; `--min-cars 1` shows them.

## Options

Pass options to the guided run, or skip the questions with a path, `--ftp` or `--demo`.

| System | How |
|---|---|
| Windows | `make --league "My League"` |
| macOS, Linux | `make ARGS='--league "My League"'` |
| With [uv](https://docs.astral.sh/uv/) | `uv run acc-race-stats --league "My League"` |

### Where the data comes from

| Option | What it does |
|---|---|
| `path` | a result file, or a folder with result files |
| `--ftp ADDRESS` | IP, `IP:port` or `ftp://user@IP:port` |
| `--port`, `--user` | when they are not in the address |
| `--demo` | an invented race weekend |

The password is asked, or read from the environment variable `ACC_FTP_PASSWORD`.

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
| `--lang en\|pt-br` | questions and charts (default `en`) |
| `--league NAME` | highlighted on every chart |
| `--event NAME` | in the titles, for example "Round 3" |
| `--output FOLDER` | default: `ACC Race Stats` in your Documents folder |
| `--no-open` | do not open the folder at the end |

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
