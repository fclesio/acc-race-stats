from datetime import datetime

from acc_race_stats.events import find_events
from acc_race_stats.results import Session


def make(name, track="monza", laps=10, kind=None):
    kind = kind or name.split("_")[2].removesuffix(".json")
    data = {"trackName": track, "laps": [{}] * laps, "sessionResult": {"leaderBoardLines": [{}]}}
    return Session(name, kind, data, datetime.strptime(name[:13], "%y%m%d_%H%M%S"))


def grouped(*sessions):
    files = {s.name: s for s in sessions}
    return [[s.name[:11] + s.kind for s in e.sessions] for e in find_events(list(files), files.get)]


def test_race_with_qualifying_and_the_longest_practice():
    assert grouped(
        make("260315_200000_FP.json", laps=90),
        make("260315_202000_FP.json", laps=2),
        make("260315_203000_Q.json"),
        make("260315_214000_R.json"),
    ) == [["260315_2000FP", "260315_2030Q", "260315_2140R"]]


def test_two_races_share_the_qualifying():
    assert grouped(make("260315_203000_Q.json"), make("260315_210000_R.json"), make("260315_220000_R.json")) == [
        ["260315_2030Q", "260315_2200R"],
        ["260315_2030Q", "260315_2100R"],
    ]


def test_practice_after_the_race_is_another_event():
    assert grouped(make("260315_214000_R.json"), make("260315_223000_FP.json")) == [
        ["260315_2230FP"],
        ["260315_2140R"],
    ]


def test_empty_and_other_track_sessions_are_left_out():
    assert grouped(
        make("260314_203000_FP.json", laps=0),
        make("260315_203000_Q.json", track="spa"),
        make("260315_214000_R.json"),
        make("260316_214000_R.json", laps=0),
    ) == [["260315_2140R"]]


def test_small_files_are_not_read():
    files = {s.name: s for s in (make("260314_203000_FP.json"), make("260315_203000_FP.json"))}
    read = []

    def load(name):
        read.append(name)
        return files[name]

    sizes = {"260314_203000_FP.json": 9000, "260315_203000_FP.json": 900}
    assert len(list(find_events(list(files), load, sizes, 8000))) == 1
    assert read == ["260314_203000_FP.json"]
