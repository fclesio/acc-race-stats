import json
from pathlib import Path

import pytest

from acc_race_stats import cli, config
from acc_race_stats.report import write
from acc_race_stats.server import Address

EXAMPLE = Path(__file__).parents[1] / "acc-race-stats.example.toml"


def test_the_example_is_valid():
    loaded = config.load(EXAMPLE)
    assert loaded.server == Address("203.0.113.10", 8821, "myuser", "my-ftp-password")
    assert loaded.defaults["lang"] == "pt-br" and loaded.defaults["class_map"] == ["SILVER=PRO-AM"]


def test_no_file_no_settings():
    assert config.load() == config.Config()


def test_file_in_the_current_folder_is_found(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / config.FILE_NAME).write_text('[report]\nleague = "My League"\nroster = "lists/roster.csv"\n')
    loaded = config.load()
    assert loaded.defaults == {"league": "My League", "roster": tmp_path / "lists" / "roster.csv"}


@pytest.mark.parametrize(
    ("text", "error"),
    [
        ("[report]\nleage = 'x'\n", "unknown setting report.leage"),
        ("[report]\nmin_cars = 'two'\n", "wrong type"),
        ("[report]\nmin_cars = true\n", "wrong type"),
        ("[report]\nlanguage = 'de'\n", "must be one of"),
        ("[server]\naddress = 'http://x'\n", "not valid"),
        ("not toml", "Cannot read"),
    ],
)
def test_wrong_files_say_what_is_wrong(tmp_path, text, error):
    path = tmp_path / "c.toml"
    path.write_text(text)
    with pytest.raises(config.ConfigError, match=error):
        config.load(path)


def test_missing_file_given_by_name(tmp_path):
    with pytest.raises(config.ConfigError, match="not found"):
        config.load(tmp_path / "nope.toml")


def test_options_win_over_the_file(fast, tmp_path):
    path = tmp_path / "c.toml"
    path.write_text('[report]\nleague = "From File"\nlanguage = "en"\nopen_folder = false\n')
    cli.main(["--demo", "--config", str(path), "--output", str(tmp_path / "a")])
    race = json.loads((tmp_path / "a" / "2026-03-15-2140-monza-race" / "race.json").read_text())
    assert race["league"] == "From File" and race["text"] == "Race"
    cli.main(["--demo", "--config", str(path), "--league", "Typed", "--output", str(tmp_path / "b")])
    race = json.loads((tmp_path / "b" / "2026-03-15-2140-monza-race" / "race.json").read_text())
    assert race["league"] == "Typed"


def test_guided_run_with_the_server_in_the_file_asks_nothing_about_it(ftp, fast, tmp_path, monkeypatch):
    path = tmp_path / "c.toml"
    path.write_text(
        f'[server]\naddress = "127.0.0.1:{ftp.port}"\nuser = "me"\npassword = "secret"\n'
        '[report]\nlanguage = "en"\nleague = "L"\ndivisions = "none"\n'
    )
    path.chmod(0o600)
    answers = iter(["1", "1"])  # the event and the session
    monkeypatch.setattr("builtins.input", lambda question: next(answers))
    monkeypatch.setattr(cli, "ask_password", lambda: pytest.fail("the password was asked"))
    cli.main(["--config", str(path), "--output", str(tmp_path / "out")])
    assert [p.name for p in (tmp_path / "out").iterdir()] == ["2026-03-15-2140-monza-race"]


def test_a_file_with_a_password_is_made_private(tmp_path):
    path = tmp_path / "c.toml"
    path.write_text("")
    path.chmod(0o644)
    config.make_private(path)
    if cli.sys.platform != "win32":
        assert path.stat().st_mode & 0o777 == 0o600


def test_guided_answers_are_saved_and_not_asked_again(ftp, fast, tmp_path, monkeypatch):
    first = iter(["1", f"127.0.0.1:{ftp.port}", "me", "1", "1", "1", "1", 'Liga "X"', "1"])
    monkeypatch.setattr("builtins.input", lambda question: next(first))
    monkeypatch.setattr(cli, "ask_password", lambda: "secret")
    cli.main(["--output", str(tmp_path / "a")])
    saved = config.load()
    assert saved.path == Path.cwd() / config.FILE_NAME
    assert saved.server == Address("127.0.0.1", ftp.port, "me", "secret")
    assert saved.defaults == {"lang": "pt-br", "league": 'Liga "X"', "divisions": "pro"}

    second = iter(["1", "1"])  # only the event and the session
    monkeypatch.setattr("builtins.input", lambda question: next(second))
    monkeypatch.setattr(cli, "ask_password", lambda: pytest.fail("the password was asked"))
    cli.main(["--output", str(tmp_path / "b")])
    race = json.loads((tmp_path / "b" / "2026-03-15-2140-monza-race" / "race.json").read_text())
    assert race["league"] == 'Liga "X"'


def test_a_changed_password_replaces_the_saved_one(ftp, fast, tmp_path, monkeypatch):
    path = tmp_path / config.FILE_NAME
    config.save(
        Address("127.0.0.1", ftp.port, "me", "old"), {"language": "en", "league": "L", "divisions": "none"}, path
    )
    answers = iter(["1", "1"])
    monkeypatch.setattr("builtins.input", lambda question: next(answers))
    monkeypatch.setattr(cli, "ask_password", lambda: "secret")
    cli.main(["--config", str(path), "--output", str(tmp_path / "out")])
    assert config.load(path).server.password == "secret"


def test_charts_are_next_to_the_summary(tmp_path):
    from acc_race_stats import demo
    from acc_race_stats.i18n import translator
    from acc_race_stats.race import Race

    old = tmp_path / "charts"
    old.mkdir()
    (old / "01-result.png").write_bytes(b"")
    race = Race(demo.weekend()[2])
    images = write(race, tmp_path, translator("en"), "class")
    assert images and all(image.parent == tmp_path for image in images)
    assert (tmp_path / "summary.txt").exists() and not old.exists()
    assert "08-battles.png" in {image.name for image in images}
    battles = json.loads((tmp_path / "race.json").read_text())["battles"]
    assert battles and battles[0]["laps_within_1s"] >= 3
