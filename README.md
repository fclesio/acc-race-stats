# ACC Race Stats

English · [Português (Brasil)](README.pt-BR.md)

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
| ![Pit stops](docs/images/09-pit-stops.png) | ![Battles](docs/images/08-battles.png) |

All images come from the invented race of `make demo`. See [every chart explained](docs/charts.md).

## Quick start

1. [Download this project](https://github.com/fclesio/acc-race-stats/archive/refs/heads/main.zip) and unzip it.
2. Double-click the launcher of your system. A terminal window opens and asks everything step by step.

| System | Double-click | Or, in a terminal in the project folder |
|---|---|---|
| Windows | `ACC-Race-Stats.bat` | `make` (Command Prompt) or `.\make` (PowerShell) |
| macOS | `ACC-Race-Stats.command` | `./run.sh` or `make` |
| Linux | see below | `./run.sh` or `make` |

The first run downloads what it needs ([uv](https://docs.astral.sh/uv/), Python and the libraries) by itself, only
once, and can take a few minutes. There is nothing to install or type by hand: `run.sh` needs only `sh` and `curl`
(or `wget`), so it also works without `make` and on older macOS versions.

- **Windows:** if Windows asks whether to run a file from the internet, choose **Run** (or **More info → Run anyway**).

- **macOS:** the first time, macOS may say the file is from an unidentified developer. Right-click
  `ACC-Race-Stats.command` and choose **Open** (on macOS 15 and later: **System Settings → Privacy & Security → Open
  Anyway**). Next time a double-click is enough.
- **Linux:** the first time, right-click `run.sh` and choose **Run as a Program**. After that, **ACC Race Stats** is in
  the applications menu.
- Open the launcher from the unzipped folder, not from inside the zip file.

| Command | What it does |
|---|---|
| `./run.sh` or `make` | asks the language (Portuguese by default), then everything else |
| `./run.sh en` / `./run.sh pt-br` | same, in English / Portuguese (`make en`, `make pt-br`) |
| `./run.sh demo` | an invented race weekend, no server needed (`make demo`) |

At the end of the questions it offers to save the answers (server, password, league, categories), so the next run only
asks which event to draw. See [settings file](#settings-file).

## How it looks

```text
Idioma / Language
  1  Português (Brasil)
  2  English
Número (aperte Enter para 1): 2

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

The results open at the end. They are in `ACC Race Stats`, in your Documents folder, with one folder per session.
Everything of a session is in that one folder:

| File | Content |
|---|---|
| `01-result.png` … `16-pace-distribution.png` | the charts |
| `summary.txt` | text to paste in the league chat |
| `race.json` | the analysis as data, battles included ([format](docs/race-json.md)) |

## Settings file

The first guided run offers to save your answers in `acc-race-stats.toml`, in the project folder; nothing has to be
written by hand. To change them, open that file in any text editor, or delete it to be asked everything again. It can
also be written from [`acc-race-stats.example.toml`](acc-race-stats.example.toml). Every line is optional: what is in the
file is not asked, and options typed on the command line win.

```toml
[server]
address = "203.0.113.10:8821"
user = "myuser"
password = "my-ftp-password"

[report]
language = "pt-br"
league = "My League"
divisions = "pro"
```

The file holds your FTP password in plain text: do not share it. The program makes it readable only by your user on
macOS and Linux, and it is in `.gitignore`. If the password changes on the server, the program asks for the new one
and updates the file. Leave `password` out to be asked every time. See [all settings](docs/usage.md#settings-file).

## Features

- **Made for league admins.** A double-click launcher, numbered menus, a remembered server, an optional settings file
  and clear errors: it says whether the server did not answer or the password is wrong.
- **Events, not files.** A race is listed together with its qualifying and practice; the grid comes from qualifying.
- **Categories your way.** Pro/Pro-Am/Am, Gold/Silver/Bronze, divisions, your own names, or one color per driver.
- **A correct race clock.** Positions and gaps include the time from the green light to the line, and impossible first
  laps are rebuilt. See [how it works](docs/race-clock.md).
- **Fast on slow servers.** Reads only the files it needs and keeps what it already downloaded.
- **Private.** The password is only kept if you write it in your settings file, and player ids never reach the output.

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

The current version is 0.1.1; see the [changelog](CHANGELOG.md). It was developed and tested on macOS; the CI workflow
runs the same tests and launchers on Windows and Linux. Problems on those systems are the most welcome reports.

## License

[MIT](LICENSE). Brand logos come from [Simple Icons](https://simpleicons.org); see [NOTICE](NOTICE.md). This project is
not affiliated with Kunos Simulazioni, the game server hosts or the car brands.
