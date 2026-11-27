import json
import socket
from datetime import date

import pytest

from acc_race_stats import cli, demo, folders
from acc_race_stats.divisions import found_categories, preset_map
from acc_race_stats.events import Event
from acc_race_stats.server import Address, LoginError, Server, ServerError, parse_address
from acc_race_stats.settings import load_server, save_server
from acc_race_stats.terminal import collect


def test_guided_flow(ftp, fast, tmp_path, monkeypatch, capsys):
    answers = iter(["2", "not valid:port", f"127.0.0.1:{ftp.port}", "me", "me", "m", "1", "4", "1", "1", "My League"])
    passwords = iter(["wrong", "secret"])
    monkeypatch.setattr("builtins.input", lambda question: next(answers))
    monkeypatch.setattr(cli, "ask_password", lambda: next(passwords))
    cli.main(["--output", str(tmp_path)])
    text = capsys.readouterr().out
    assert "o usuário ou a senha está errado" in text and "Connect" not in text and "secret" not in text
    assert sorted(p.name.rsplit("-", 1)[1] for p in tmp_path.iterdir()) == ["practice", "qualifying", "race"]
    race = json.loads((tmp_path / "2026-03-15-2140-monza-race" / "race.json").read_text())
    assert all(race["grid"]) and race["league"] == "My League" and race["text"] == "Corrida"


def test_direct_ftp(ftp, fast, tmp_path, monkeypatch):
    monkeypatch.setenv("ACC_FTP_PASSWORD", "secret")
    cli.main(["--ftp", f"127.0.0.1:{ftp.port}", "--user", "me", "--lang", "en", "--output", str(tmp_path)])
    assert [p.name for p in tmp_path.iterdir()] == ["2026-03-15-2140-monza-race"]


def test_login_and_connection_errors_are_different(ftp):
    with pytest.raises(LoginError):
        Server(Address("127.0.0.1", ftp.port, "me", "nope"))
    with socket.create_server(("127.0.0.1", 0)) as free:
        port = free.getsockname()[1]
    with pytest.raises(ServerError, match="were not tested"):
        Server(Address("127.0.0.1", port, "me", "x"), timeout=2)


def test_address():
    assert parse_address("ftp://joe:p%40ss@1.2.3.4:8821/") == Address("1.2.3.4", 8821, "joe", "p@ss")
    assert parse_address(" 1.2.3.4 ") == Address("1.2.3.4", 21)
    for wrong in ("", "http://x", "1.2.3.4:abc", "1.2.3.4:99999"):
        with pytest.raises(ServerError):
            parse_address(wrong)


def test_day():
    today = date(2026, 3, 1)
    assert cli.parse_day("24/11", today) == date(2025, 11, 24)
    assert cli.parse_day("01/03", today) == today
    assert cli.parse_day("2026-11-24") == cli.parse_day("24/11/2026") == date(2026, 11, 24)
    assert cli.parse_day("") is None
    with pytest.raises(cli.UserError):
        cli.parse_day("soon")


def test_track():
    assert cli.parse_track("Nürburgring") == "nurburgring"
    assert cli.parse_track("spa") == "spa"
    assert cli.parse_track("monz") == "monza"
    assert cli.parse_track("") is None
    with pytest.raises(cli.UserError):
        cli.parse_track("interlagos")


def test_friendly_errors(tmp_path):
    with pytest.raises(SystemExit, match="No ACC result file"):
        cli.main([str(tmp_path)])
    with pytest.raises(SystemExit, match="No ACC result file"):
        cli.main([str(tmp_path / "missing")])
    bad = tmp_path / "x.json"
    bad.write_text("{}")
    with pytest.raises(SystemExit, match="Error"):
        cli.main([str(bad)])


def test_older_events_are_one_key_away(monkeypatch, capsys):
    events = [Event([s]) for s in demo.weekend() for _ in range(4)]
    answers = iter(["99", "m", "12"])
    monkeypatch.setattr("builtins.input", lambda question: next(answers))
    assert cli.choose_event(iter(events)) is events[11]
    assert "   Monza" in capsys.readouterr().out


def test_last_server_is_remembered_without_the_password(ftp, fast, tmp_path, monkeypatch, settings):
    monkeypatch.setattr(cli, "ask_password", lambda: "secret")
    for answers in (["", f"127.0.0.1:{ftp.port}", "me", "1", "1", "", "", ""], ["", "", "", "", "2", ""]):
        replies = iter(answers)
        monkeypatch.setattr("builtins.input", lambda question, replies=replies: next(replies))
        cli.main(["--output", str(tmp_path)])
    assert json.loads(settings.read_text()) == {"host": "127.0.0.1", "port": ftp.port, "user": "me"}


def test_broken_settings_are_ignored(settings):
    settings.parent.mkdir()
    settings.write_text("[]")
    assert load_server() is None


def test_solo_events_are_hidden(ftp, fast, tmp_path, monkeypatch, capsys):
    replies = iter(["", f"127.0.0.1:{ftp.port}", "me"])
    monkeypatch.setattr("builtins.input", lambda question: next(replies))
    monkeypatch.setattr(cli, "ask_password", lambda: "secret")
    with pytest.raises(SystemExit, match="--min-cars 1"):
        cli.main(["--output", str(tmp_path), "--min-cars", "99"])


def test_division_presets():
    assert preset_map("pro", ["PRO", "SILVER", "AM"]) == {"PRO": "PRO", "AM": "AM", "SILVER": "PRO-AM"}
    assert preset_map("metal", ["PRO", "SILVER", "AM"]) == {"PRO": "GOLD", "SILVER": "SILVER", "AM": "BRONZE"}
    assert preset_map("game", ["PRO"]) == {}
    assert found_categories(demo.weekend()[2]) == {"PRO": 6, "PRO-AM": 6, "AM": 4}


@pytest.mark.parametrize(
    ("answers", "divisions", "names"),
    [
        (["2"], "none", []),
        (["1", "2"], "metal", []),
        (["", "6", "Elite", "", "Rookie"], "game", ["PRO=ELITE", "PRO-AM=PRO-AM", "AM=ROOKIE"]),
    ],
)
def test_category_questions(answers, divisions, names, monkeypatch):
    replies = iter(answers)
    monkeypatch.setattr("builtins.input", lambda question: next(replies))
    options = cli.build_parser().parse_args([])
    cli.ask_divisions(options, demo.weekend()[2])
    assert (options.divisions, options.class_map) == (divisions, names)


def test_default_language_is_english(fast, tmp_path):
    cli.main(["--demo", "--output", str(tmp_path)])
    race = json.loads((tmp_path / "2026-03-15-2140-monza-race" / "race.json").read_text())
    assert race["text"] == "Race"


def test_wrong_password_on_the_remembered_server_only_asks_the_password(ftp, fast, tmp_path, monkeypatch):
    save_server(Address("127.0.0.1", ftp.port, "me"))
    passwords, replies = iter(["wrong", "secret"]), iter(["1", "1", "1", "1", "2", ""])
    monkeypatch.setattr(cli, "ask_password", lambda: next(passwords))
    monkeypatch.setattr("builtins.input", lambda question: next(replies))
    cli.main(["--output", str(tmp_path)])
    assert list(tmp_path.iterdir())


def test_another_server(ftp, fast, tmp_path, monkeypatch):
    save_server(Address("192.0.2.1", 21, "old"))
    replies = iter(["1", "2", f"127.0.0.1:{ftp.port}", "me", "1", "1", "2", ""])
    monkeypatch.setattr(cli, "ask_password", lambda: "secret")
    monkeypatch.setattr("builtins.input", lambda question: next(replies))
    cli.main(["--output", str(tmp_path)])
    assert load_server() == Address("127.0.0.1", ftp.port, "me")


@pytest.mark.parametrize(
    ("keys", "password", "screen"),
    [
        ("abc\r", "abc", "***\n"),
        ("ab\x7f\x7f\x7fç1\n", "ç1", "**\b \b\b \b**\n"),
        ("wrong\x15ok\r", "ok", "*****" + "\b \b" * 5 + "**\n"),
        ("\x1b[200~paste\x1b[201~\x1b[A\r", "paste", "*****\n"),
    ],
)
def test_password_shows_asterisks(keys, password, screen):
    reader, shown = iter(keys), []
    assert collect(lambda: next(reader), shown.append, hidden=True) == password
    assert "".join(shown) == screen


def test_password_can_be_cancelled():
    with pytest.raises(KeyboardInterrupt):
        collect(iter("a\x03").__next__, lambda text: None)
    with pytest.raises(EOFError):
        collect(lambda: "", lambda text: None)


@pytest.mark.parametrize(
    "enter", ["\r", "\n", "\x1bOM", "\x1b[13u", "\x1b[13;1:1u", "\x1b[57414u", "\x1b[27;1;13~"]
)  # fmt: skip
def test_every_kind_of_enter(enter):
    assert collect(iter("ab" + enter).__next__, lambda text: None) == "ab"


def test_keypad_and_extended_keys():
    keys = "\x1bOq\x1b[50u\x1b[57402u\x1b[65;2u\x1b[97;1:3u\x1b[A\r"
    assert collect(iter(keys).__next__, lambda text: None) == "123A"
    with pytest.raises(KeyboardInterrupt):
        collect(iter("\x1b[99;5u").__next__, lambda text: None)


def test_lone_escape_does_not_eat_the_next_key():
    waiting = iter([False])
    assert collect(iter("\x1bab\r").__next__, lambda text: None, waiting=lambda: next(waiting)) == "ab"


def test_menu_number_needs_no_enter():
    assert collect(iter("2").__next__, lambda text: None, instant=["1", "2"]) == "2"


def test_download_survives_a_dropped_connection(ftp):
    server = Server(Address("127.0.0.1", ftp.port, "me", "secret"))
    names = server.find_results()
    ftp.drops = 1
    assert server.download(names[0])[0].kind == "FP"
    ftp.drops = 2
    with pytest.raises(ServerError, match="Could not download"):
        server.download(names[1])


def test_files_are_downloaded_once(ftp):
    for _ in range(2):
        server = Server(Address("127.0.0.1", ftp.port, "me", "secret"))
        name = server.find_results()[0]
        assert server.download(name)[0].kind == "FP"
    assert ftp.sent == 1
    ftp.files[name] += b" \x00"  # another file with the same name
    server = Server(Address("127.0.0.1", ftp.port, "me", "secret"))
    server.find_results()
    server.download(name)
    assert ftp.sent == 2


def test_default_folder(tmp_path, monkeypatch):
    monkeypatch.setattr(folders, "documents", lambda: tmp_path / "Documents")
    assert folders.default_output() == tmp_path / "Documents" / "ACC Race Stats"
    blocked = tmp_path / "file"
    blocked.write_text("")
    monkeypatch.setattr(folders, "documents", lambda: blocked)
    monkeypatch.setattr(folders.Path, "home", lambda: tmp_path)
    assert folders.default_output() == tmp_path / "ACC Race Stats"


def test_moved_documents_folder_on_linux(tmp_path, monkeypatch):
    monkeypatch.setattr(folders.sys, "platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    (tmp_path / "user-dirs.dirs").write_text('XDG_DOCUMENTS_DIR="$HOME/Documentos"\n')
    assert folders.documents() == folders.Path.home() / "Documentos"
