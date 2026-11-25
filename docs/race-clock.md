# The race clock

Positions and gaps on every lap need the time since the green light. A result file has the lap times and the total time
of each car, but adding up the laps does not give the total.

## The problem

1. **The first lap starts at the line.** A car at the back of the grid takes several seconds to reach it. That time is
   not in its lap 1, so the car looks closer to the leader than it was.
2. **Some first laps are impossible.** In a real one-hour race, cars were saved with a first lap of 27 and 52 minutes.
3. **Penalties added after the race** are in the total time but did not happen on track.

## The fix

For each car, `offset = total time − sum of the laps − penalties added after the race`.

- An offset from 0 to 15 s is trusted. In the race used to develop this, it grew along the grid from 0.1 s at the front
  to about 6 s at the back.
- For the others there is a second source: the file lists the laps **in the order the cars crossed the line**. The
  elapsed time of a car must fit between its neighbours in that list.
  - If the raw offset fits in at least 80% of the laps, the first lap was wrong and the total is right: it is used.
  - If it does not (a car that retired, for example), the offset is taken from the range the neighbours allow.
- If fewer than half of the cars are trusted, no correction is made.

The offset is added to lap 1. When it is larger than 60 s, the lap is reported as rebuilt.

The code is in [`timing.py`](../src/acc_race_stats/timing.py).
