# ACC Race Stats

Charts and a report from Assetto Corsa Competizione server results. Connect to your game server, choose the session,
and get PNG charts and a summary for your league chat. No game mods, no telemetry.

## Quick start

Download this project, unzip it and open a terminal in its folder.

| | Command |
|---|---|
| Windows | `make` (in PowerShell: `.\make`), or double-click `make.bat` |
| macOS, Linux | `make` |

Nothing else to install: the first run downloads Python and the libraries, only once. (A Mac without the Apple command
line tools offers to install them the first time `make` is used.)
Then connect to the server and pick a number from the list.

```
1. Connection (from your game server panel, for example G-Portal)
FTP address (IP, or IP:port): 203.0.113.10:31921
FTP user: myuser
FTP password (hidden while you type):
Connected.

2. Pick one (newest first)
   1  24/11/2026 22:30   Monza              26 cars   Race + Qualifying + Practice
   2  22/11/2026 21:34   Spa-Francorchamps  18 cars   Race + Qualifying
   3  21/11/2026 20:10   Monza              12 cars   Practice
Type the number, or M for older ones [1]: 1

What do you want to see?
  1  Race
  2  Qualifying
  3  Practice
  4  All of them
Number [1]:

3. Categories
Categories saved in the file: PRO (10), SILVER (9), AM (7)

Does your league use categories?
  1  Yes
  2  No, one color per driver
Number [1]: 1

Which ones?
  1  Pro / Pro-Am / Am
  2  Gold / Silver / Bronze
  ...

4. Charts
League name to highlight (empty = none): My League

Language of the charts
  1  English
  2  Português (Brasil)
Number [1]:
```

Results go to `reports/`: `charts/`, `summary.txt` and `race.json`.

Try it without a server: `make demo`

## Options

`make en` and `make pt-br` set the chart language without asking; `make` asks (Enter = English).

Other options on Windows: `make --lang pt-br`. On macOS and Linux: `make ARGS="--lang pt-br"`.

| Option | What it does |
|---|---|
| `path` | result file, or folder with result files |
| `--ftp ADDRESS --port N --user U` | server; the password is asked, or read from `ACC_FTP_PASSWORD` |
| `--track` `--date` `--session race\|practice\|qualifying\|all` | which session; the date matches 3 days either way |
| `--min-cars N` | hide events with fewer cars in the questions (default 2) |
| `--list` | only list the sessions found |
| `--lang en\|pt-br` | chart language (default `en`) |
| `--divisions none\|game\|pro\|metal\|fia\|numbers` | league categories; `none` is one color per driver |
| `--color-by auto\|class\|driver` | `auto` uses classes when the race has more than one |
| `--class-map SILVER=PRO-AM` | rename the game classes |
| `--class-color PRO=#ffffff` | change class colors |
| `--league "My League"` | league name highlighted on every chart (default: none) |
| `--event "Round 3"` | event name in the titles |
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
order in which the laps were written. Rebuilt laps are listed at the end of the run.

## Privacy

The address, port and user of the last server are remembered on your computer. The FTP password is never saved. Plain FTP sends it unencrypted, so do not reuse it elsewhere. Player ids are never
written to the output.

## Development

```bash
make test
make check
```

Commits follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/). License: MIT.

This project is not affiliated with Kunos Simulazioni. The brand logos come from [Simple Icons](https://simpleicons.org)
(CC0); they are trademarks of their owners and only identify the cars.
