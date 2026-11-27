import copy
import json

import pytest

from acc_race_stats import demo
from acc_race_stats.gamedata import BRANDS
from acc_race_stats.i18n import TEXT, translator
from acc_race_stats.palette import apply_colors, driver_palette
from acc_race_stats.race import Race
from acc_race_stats.report import write
from acc_race_stats.results import ResultError, decode, matching_qualifying, parse_name
from acc_race_stats.roster import RosterError, load_grid, load_roster
from acc_race_stats.timing import start_offsets


@pytest.fixture
def weekend():
    return demo.weekend()


def test_start_offsets_follow_the_grid(weekend):
    _, quali, race = weekend
    offsets = start_offsets(race.data)
    grid = [line["car"]["carId"] for line in quali.data["sessionResult"]["leaderBoardLines"]]
    assert [offsets[c] for c in grid] == [250 * n for n in range(1, len(grid) + 1)]


@pytest.mark.parametrize("known_total", [True, False])
def test_wrong_first_lap_is_rebuilt(weekend, known_total):
    data = copy.deepcopy(weekend[2].data)
    before = start_offsets(data)
    car = data["laps"][5]["carId"]
    data["laps"][5]["laptime"] += 1_500_000
    if not known_total:  # a car that reconnected and retired: the total time is no use
        for line in data["sessionResult"]["leaderBoardLines"]:
            if line["car"]["carId"] == car:
                line["timing"]["totalTime"] += 200_000
    assert start_offsets(data)[car] + 1_500_000 == pytest.approx(before[car], abs=1 if known_total else 1_500)


def test_post_race_penalty_is_not_part_of_the_clock(weekend):
    data = copy.deepcopy(weekend[2].data)
    before = start_offsets(data)
    line = data["sessionResult"]["leaderBoardLines"][3]
    car = line["car"]["carId"]
    line["timing"]["totalTime"] += 30_000
    data["post_race_penalties"] = [{"carId": car, "penalty": "PostRaceTime", "penaltyValue": 30}]
    assert start_offsets(data) == before


def test_grid_from_qualifying_and_spectators(weekend):
    _, quali, race = weekend
    assert matching_qualifying(race, weekend) is quali
    race.data["sessionResult"]["leaderBoardLines"][-1]["bIsSpectator"] = True
    model = Race(race, quali)
    assert len(model.drivers) == len(demo.NAMES) - 1
    assert all(d.grid for d in model.drivers)


def test_stops_and_export(weekend):
    model = Race(weekend[2], weekend[1])
    assert all(len(d.pits) == 1 for d in model.drivers)
    exported = json.dumps(model.to_dict())
    assert "playerId" not in exported and "demo1" not in exported


def test_color_modes(weekend):
    model = Race(weekend[2])
    assert apply_colors(model) == "class"
    assert len({d.color for d in model.drivers}) == 3
    assert apply_colors(model, "driver") == "driver"
    assert len({d.color for d in model.drivers}) == len(model.drivers)
    assert apply_colors(Race(demo.weekend(single_class=True)[2])) == "driver"
    assert len(set(driver_palette(40))) == 40


def test_class_map(weekend):
    assert Race(weekend[2], class_map={"AM": "BRONZE"}).classes == ["PRO", "PRO-AM", "BRONZE"]


def test_roster_and_grid_files(tmp_path, weekend):
    roster = tmp_path / "roster.csv"
    roster.write_text("name;class;color;display;hide\nUndercut;GOLD;#112233;Under;\nBoxBox99;;;;yes\n", "utf-8")
    model = Race(weekend[2], roster=load_roster(roster))
    apply_colors(model)
    under = next(d for d in model.drivers if d.name == "Under")
    assert (under.driver_class, under.color) == ("GOLD", "#112233")
    assert "BoxBox99" not in [d.name for d in model.drivers]
    grid = tmp_path / "grid.csv"
    grid.write_text("position,driver\n1,#12\n2,Undercut\n", "utf-8")
    model = Race(weekend[2], grid=load_grid(grid))
    assert {d.name: d.grid for d in model.drivers if d.grid} == {"Kerb_Hunter": 1, "Undercut": 2}
    grid.write_text("position,driver\n1,#12\n1,Undercut\n", "utf-8")
    with pytest.raises(RosterError):
        load_grid(grid)


def test_decode_encodings():
    data = {"sessionResult": {"leaderBoardLines": []}}
    text = json.dumps(data)
    for encoding in ("utf-8", "utf-8-sig", "utf-16", "utf-16-le"):
        assert decode(text.encode(encoding)) == data
    with pytest.raises(ResultError):
        decode(b'{"other": 1}')


def test_names():
    assert parse_name("261124_223000_R.json")[1] == "R"
    assert parse_name("results_261124_213000_Q.json")[1] == "Q"
    assert parse_name("../261124_223000_R.json") is None
    assert parse_name("269999_223000_R.json") is None


def test_every_session_is_drawn(tmp_path, weekend):
    weekend[2].data["sessionResult"]["leaderBoardLines"][0]["currentDriver"]["lastName"] = "<b>$a_1$ & 100%"
    expected = {"R": 16, "Q": 5, "FP": 8}
    for session, lang in zip(weekend, ("pt-br", "en", "pt-br"), strict=True):
        model = Race(session, weekend[1] if session.kind == "R" else None)
        mode = apply_colors(model)
        out = tmp_path / session.kind
        out.mkdir()
        assert len(write(model, out, translator(lang), mode)) == expected[session.kind]
    assert "<b>$a_1$ & 100%" in (tmp_path / "R" / "summary.txt").read_text("utf-8")


def test_translations_have_the_same_fields():
    import re

    for pt, en in TEXT.values():
        assert sorted(re.findall(r"{\w+}", pt)) == sorted(re.findall(r"{\w+}", en))


def test_server_name_is_not_used_in_titles(weekend):
    assert Race(weekend[2]).title == "Monza"
    assert Race(weekend[2], league="My League", event="Round 3").title == "My League · Round 3 · Monza"


def test_every_brand_has_a_logo_of_the_same_size():
    from acc_race_stats.charts import LOGOS, plt

    assert len({plt.imread(LOGOS / f"{name.lower()}.png").shape for name in BRANDS}) == 1


def test_custom_categories_keep_the_order_of_the_league(weekend):
    names = {"PRO": "ELITE", "PRO-AM": "CLUB", "AM": "BEGINNER"}
    assert Race(weekend[2], class_map=names).classes == ["ELITE", "CLUB", "BEGINNER"]


def test_grid_change_marks():
    from acc_race_stats.charts import GREEN, MUTED, RED, grid_change

    assert grid_change(5, 2, False) == ("▲3", GREEN)
    assert grid_change(2, 4, False) == ("▼2", RED)
    assert grid_change(3, 3, False) == ("=", MUTED)
    assert grid_change(None, 3, False) == ("", MUTED)
    assert grid_change(3, 9, True) == ("", MUTED)
