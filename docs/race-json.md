# race.json

UTF-8 JSON, one per session. `schema` is 1; it changes when a field changes its meaning or is removed. Times are in
milliseconds unless the name says otherwise. Player ids are never included.

| Field | Type | Content |
|---|---|---|
| `schema` | int | 1 |
| `session` | string | `R` race, `Q` qualifying, `FP` practice |
| `track`, `title` | string | names used in the charts |
| `date` | string or null | from the file name, ISO 8601, server time |
| `laps` | int | laps of the first classified driver |
| `warnings` | list of strings | problems in the data, in the chosen language |
| `drivers` | list | in final order |
| `battles` | list | races only: up to 4 pairs, as in [the battle chart](charts.md#race); empty otherwise |

Each driver:

| Field | Type | Content |
|---|---|---|
| `position`, `class_position` | int | overall and in the category |
| `name`, `number`, `car` | string, int, string | |
| `class`, `color` | string | category and chart color |
| `grid` | int or null | starting position |
| `laps` | int | |
| `total_ms` | int or null | with penalties added after the race |
| `best_ms`, `ideal_ms` | int or null | best valid lap, and sum of the best sectors |
| `pace_ms` | float or null | median of the clean laps |
| `spread_s` | float or null | seconds; see [consistency](charts.md#race) |
| `pit_laps` | list of int | without stops to serve a penalty |
| `invalid_laps` | int | without lap 1 and the laps around the stops |
| `retired` | bool | |
| `lap_times_ms` | list of int | in a race, lap 1 starts at the green light |
| `elapsed_ms` | list of int | time at the end of each lap |
| `penalties` | list | `penalty`, `reason`, `violationInLap`, `clearedInLap`, as in the game |

Each battle:

| Field | Type | Content |
|---|---|---|
| `ahead`, `behind` | string | names, in final order |
| `laps_within_1s` | int | laps as neighbours less than 1 s apart, without the laps around their stops |
