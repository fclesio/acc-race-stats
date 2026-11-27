# Changelog

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the versions follow
[Semantic Versioning](https://semver.org).

## [Unreleased]

### Changed

- `README.md` is in Portuguese, with a link to the English version in `README.en.md`.
- The step-by-step guide shows where the FTP access is in the server panel.

## [0.1.1] - 2026-11-27

### Added

- Double-click launchers: `ACC-Race-Stats.command` (macOS) and `ACC-Race-Stats.bat` (Windows); on Linux the first run
  adds **ACC Race Stats** to the applications menu.
- `run.sh`, a launcher that needs only `sh` and `curl` or `wget`, without `make`.
- Settings file `acc-race-stats.toml` (or `--config FILE`) with the server, password, language, league, categories and
  other options, so they are not asked. The guided run offers to write it, keeps it private to the user and updates a
  password that changed. See `acc-race-stats.example.toml`.
- The launchers say when they are opened inside the zip file, and when the first run is still preparing.
- `battles` in `race.json`.
- `README.pt-BR.md`, the README in Brazilian Portuguese.
- A step-by-step guide with images at the top of both READMEs, drawn from a real run by `tools/build_tutorial.py`.

### Changed

- Portuguese is the default language, in the questions and with `--lang` left out.
- The charts are saved in the session folder, next to `summary.txt` and `race.json`, not in a `charts` folder.
- The Makefile calls `run.sh` and works with GNU make 3.81 (older macOS) and BSD make.
- Battles leave out the laps around the stops of either driver, as the chart already did.
- The guided run hides the connection, categories and charts headers when the settings file already answers them.

### Fixed

- The first run installed uv with instructions to change the `PATH` and restart the shell, which users followed by hand.
  It is now installed silently in a known folder, without touching the shell profile or the `PATH` of Windows.

- The battle chart lost the line when a gap was more than 4 s; it now draws it on the edge and marks the counted laps.
- A path that does not exist gives an error message instead of a traceback.

## [0.1.0] - 2026-11-25

First version.

### Added

- Guided command line in English and Brazilian Portuguese, with a remembered server and a masked password.
- Download over FTP, with the events of the server listed from the newest, and a local cache.
- Up to 16 charts for races, 5 for qualifying and 8 for practice; chat summary and `race.json`.
- Race clock with the start offset of every car, and impossible first laps rebuilt.
- Categories: Pro/Pro-Am/Am, Gold/Silver/Bronze, Platinum to Bronze, divisions, own names, or one color per driver.
- Driver list, starting grid and league name.
- `make` on macOS and Linux, and `make.bat` on Windows.

[Unreleased]: https://github.com/fclesio/acc-race-stats/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/fclesio/acc-race-stats/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/fclesio/acc-race-stats/releases/tag/v0.1.0
