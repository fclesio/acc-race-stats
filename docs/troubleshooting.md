# Troubleshooting

| Message or problem | What to do |
|---|---|
| The server … did not answer | The server may be off, or the address or port may be wrong (the FTP port is not the game port). Compare with the panel of your host. A firewall or network can also block it: try another network. |
| The user or password is wrong | Copy them from the panel again. The FTP password is not always the one of the panel. |
| No result file found on the server | ACC only saves results with `"dumpLeaderboards": 1` in `settings.json`. |
| No session with enough cars was found | `--min-cars 1` shows sessions with one car. |
| No starting grid | There is no qualifying on that track in the 4 hours before the race. Use [`--grid`](usage.md#starting-grid). |
| Lap 1 in the file was wrong and was rebuilt | Nothing to do: see [race clock](race-clock.md). |
| A car appears as `car 99` | It is not in `gamedata.py` yet. Open an issue with its name. |
| `make` is not recognized in PowerShell | Use `.\make`, or double-click `ACC-Race-Stats.bat`. |
| `make` is missing, or fails on an older Mac | Use `./run.sh` or double-click `ACC-Race-Stats.command`: they need no `make`. |
| macOS: "cannot be opened because it is from an unidentified developer" | Right-click `ACC-Race-Stats.command` → **Open**. On macOS 15 and later: **System Settings → Privacy & Security → Open Anyway**. |
| Linux: a double-click opens `run.sh` in a text editor | Right-click → **Run as a Program**. After the first run, use **ACC Race Stats** in the applications menu. |
| "Unzip the whole project folder first" | The launcher was opened inside the zip file. Unzip it (right-click → **Extract All** on Windows) and open it from the new folder. |
| Windows asks whether to run a file from the internet | Choose **Run**, or **More info → Run anyway**. |
| `Permission denied` on `./run.sh` | Run `sh run.sh`, or `chmod +x run.sh ACC-Race-Stats.command` once. |
| An error names `acc-race-stats.toml` | Fix the setting it names; see [settings file](usage.md#settings-file). |
| The first list is slow | Files are read over the internet, one by one. The next run uses the saved ones. |

## Files on your computer

| What | Windows | macOS | Linux |
|---|---|---|---|
| Results | `Documents\ACC Race Stats` | `~/Documents/ACC Race Stats` | Documents folder, `ACC Race Stats` |
| Last server, `config.toml` | `%APPDATA%\acc-race-stats` | `~/.config/acc-race-stats` | `~/.config/acc-race-stats` |
| Downloaded files | `%LOCALAPPDATA%\acc-race-stats` | `~/Library/Caches/acc-race-stats` | `~/.cache/acc-race-stats` |

All of them can be deleted. Results of 0.1.0 have their charts in a `charts` folder; a new run on the same session removes
it and saves the charts next to `summary.txt`.
