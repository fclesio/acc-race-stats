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
| `make` is not recognized in PowerShell | Use `.\make`. |
| The first list is slow | Files are read over the internet, one by one. The next run uses the saved ones. |

## Files on your computer

| What | Windows | macOS | Linux |
|---|---|---|---|
| Results | `Documents\ACC Race Stats` | `~/Documents/ACC Race Stats` | Documents folder, `ACC Race Stats` |
| Last server | `%APPDATA%\acc-race-stats` | `~/.config/acc-race-stats` | `~/.config/acc-race-stats` |
| Downloaded files | `%LOCALAPPDATA%\acc-race-stats` | `~/Library/Caches/acc-race-stats` | `~/.cache/acc-race-stats` |

All of them can be deleted.
