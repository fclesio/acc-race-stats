# ACC Race Stats

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776ab)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Conventional Commits](https://img.shields.io/badge/commits-conventional-fe5196)](https://www.conventionalcommits.org/en/v1.0.0/)

**Race charts for Assetto Corsa Competizione leagues, straight from your game server.**

Connect over FTP, pick an event from a list, and get up to 16 charts and a summary for your league chat. No game mods,
no telemetry, no files to move around. Works on Windows, macOS and Linux, in English and Brazilian Portuguese.

![Lap by lap positions](docs/images/12-lap-by-lap.png)

| | |
|---|---|
| ![Result](docs/images/01-result.png) | ![Gap to the winner](docs/images/04-gap-to-winner.png) |
| ![Pit stops](docs/images/09-pit-stops.png) | ![Pace distribution](docs/images/16-pace-distribution.png) |

All images come from the invented race of `make demo`. See [every chart explained](docs/charts.md).

## Quick start

1. Download this project and unzip it.
2. Open a terminal in its folder and run:

| System | Command |
|---|---|
| Windows (Command Prompt) | `make` |
| Windows (PowerShell) | `.\make` |
| Windows (no terminal) | double-click `make.bat` |
| macOS, Linux | `make` |

The first run downloads what it needs (Python and the libraries), only once. On a Mac without the Apple command line
tools, the first `make` offers to install them.

| Target | What it does |
|---|---|
| `make` | asks the language, then everything else |
| `make en` / `make pt-br` | same, in English / Portuguese |
| `make demo` | an invented race weekend, no server needed |

## How it looks

```text
1. Connection (copy it from your game server panel, for example G-Portal)
FTP address (IP, or IP:port): 203.0.113.10:8821
FTP user: myuser
FTP password: ********
Connecting...
Connected.

2. Pick one (newest first)
   1  15/03/2026 21:40   Monza              26 cars   Race + Qualifying + Practice
   2  08/03/2026 21:34   Spa-Francorchamps  18 cars   Race + Qualifying
   3  07/03/2026 20:10   Monza              12 cars   Practice
Type the number (press Enter for 1): 1

What do you want to see?
  1  Race
  2  Qualifying
  3  Practice
  4  All of them
Number (press Enter for 1): 1

3. Categories
Categories saved in the file: PRO (10), SILVER (9), AM (7)

Does your league use categories?
  1  Yes
  2  No, one color per driver
Number (press Enter for 1): 1

4. Charts
League name to highlight (empty = none): My League
```

The results open at the end. They are in `ACC Race Stats`, in your Documents folder, with one folder per session:

| File | Content |
|---|---|
| `charts/` | the PNG charts |
| `summary.txt` | text to paste in the league chat |
| `race.json` | the analysis as data ([format](docs/race-json.md)) |

## Features

- **Made for league admins.** Numbered menus, a remembered server and clear errors: it says whether the server did not
  answer or the password is wrong.
- **Events, not files.** A race is listed together with its qualifying and practice; the grid comes from qualifying.
- **Categories your way.** Pro/Pro-Am/Am, Gold/Silver/Bronze, divisions, your own names, or one color per driver.
- **A correct race clock.** Positions and gaps include the time from the green light to the line, and impossible first
  laps are rebuilt. See [how it works](docs/race-clock.md).
- **Fast on slow servers.** Reads only the files it needs and keeps what it already downloaded.
- **Private.** The password is never saved and player ids never reach the output.

## Documentation

| Page | |
|---|---|
| [Usage](docs/usage.md) | every option, driver lists, starting grids, categories |
| [Charts](docs/charts.md) | what each chart shows and how it is calculated |
| [Race clock](docs/race-clock.md) | why adding up lap times is wrong, and the fix |
| [race.json](docs/race-json.md) | data format |
| [Architecture](docs/architecture.md) | modules and design decisions |
| [Troubleshooting](docs/troubleshooting.md) | common problems |
| [Contributing](CONTRIBUTING.md) | development, commits and versions |
| [Changelog](CHANGELOG.md) | what changed in each version |

## Status

0.1.0 is the first version. It was developed and tested on macOS; the CI workflow runs the same tests and launchers on
Windows and Linux. Problems on those systems are the most welcome reports.

## License

[MIT](LICENSE). Brand logos come from [Simple Icons](https://simpleicons.org); see [NOTICE](NOTICE.md). This project is
not affiliated with Kunos Simulazioni, the game server hosts or the car brands.
