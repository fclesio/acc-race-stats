import json
import socket
import threading
from datetime import date

import pytest

from acc_race_stats import cli, demo
from acc_race_stats.divisions import found_categories, preset_map
from acc_race_stats.events import Event
from acc_race_stats.server import Address, LoginError, Server, ServerError, parse_address
from acc_race_stats.settings import load_server


class FakeFtp(threading.Thread):
    """Just enough FTP for the client: login, MLSD and RETR in passive mode."""

    def __init__(self, files):
        super().__init__(daemon=True)
        self.files = files
        self.listener = socket.create_server(("127.0.0.1", 0))
        self.port = self.listener.getsockname()[1]
        self.start()

    def run(self):
        while True:
            try:
                connection, _ = self.listener.accept()
            except OSError:
                return
            threading.Thread(target=self.serve, args=(connection,), daemon=True).start()

    def serve(self, connection):
        stream = connection.makefile("rwb")

        def say(text):
            stream.write(text.encode() + b"\r\n")
            stream.flush()

        say("220 hi")
        data = None
        for raw in stream:
            command, _, argument = raw.decode().strip().partition(" ")
            if command == "USER":
                say("331 password")
            elif command == "PASS":
                say("230 ok" if argument == "secret" else "530 no")
            elif command in ("EPSV", "PASV"):
                data = socket.create_server(("127.0.0.1", 0))
                port = data.getsockname()[1]
                say(f"229 ok (|||{port}|)" if command == "EPSV" else f"227 ok (127,0,0,1,{port >> 8},{port & 255})")
            elif command in ("MLSD", "RETR"):
                if command == "MLSD" and argument not in ("/", "/game", "/game/results"):
                    say("550 no such folder")
                    continue
                say("150 here")
                channel, _ = data.accept()
                if command == "RETR":
                    body = self.files[argument.rsplit("/", 1)[1]]
                elif argument == "/game/results":
                    body = "".join(f"type=file; {n}\r\n" for n in self.files).encode()
                else:
                    body = f"type=dir; {'game' if argument == '/' else 'results'}\r\n".encode()
                channel.sendall(body)
                channel.close()
                say("226 done")
            elif command == "NLST":
                say("550 no such folder")
            else:
                say("200 ok")


@pytest.fixture
def ftp():
    files = {s.name: json.dumps(s.data).encode("utf-16-le") for s in demo.weekend()}
    files["260316_100000_R.json"] = b"broken"
    server = FakeFtp(files)
    yield server
    server.listener.close()


@pytest.fixture(autouse=True)
def settings(tmp_path_factory, monkeypatch):
    folder = tmp_path_factory.mktemp("settings")
    monkeypatch.setenv("APPDATA", str(folder))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(folder))
    return folder / "acc-race-stats" / "server.json"


@pytest.fixture
def fast(monkeypatch):
    def write(race, out, t, mode):
        (out / "race.json").write_text(
            json.dumps({"grid": [d.grid for d in race.drivers], "league": race.league, "text": t("R")})
        )
        return []

    monkeypatch.setattr(cli, "write", write)
    monkeypatch.setattr(cli, "open_folder", lambda path: None)


def test_guided_flow(ftp, fast, tmp_path, monkeypatch, capsys):
    answers = iter(["not valid:port", f"127.0.0.1:{ftp.port}", "me", "me", "m", "1", "4", "1", "1", "My League", "2"])
    passwords = iter(["wrong", "secret"])
    monkeypatch.setattr("builtins.input", lambda question: next(answers))
    monkeypatch.setattr("getpass.getpass", lambda question: next(passwords))
    cli.main(["--output", str(tmp_path)])
    text = capsys.readouterr().out
    assert "user or password is wrong" in text and "secret" not in text
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
    monkeypatch.setattr("getpass.getpass", lambda question: "secret")
    for answers in ([f"127.0.0.1:{ftp.port}", "me", "1", "1", "", "", "", ""], ["", "", "", "", "2", "", ""]):
        replies = iter(answers)
        monkeypatch.setattr("builtins.input", lambda question, replies=replies: next(replies))
        cli.main(["--output", str(tmp_path)])
    assert json.loads(settings.read_text()) == {"host": "127.0.0.1", "port": ftp.port, "user": "me"}


def test_broken_settings_are_ignored(settings):
    settings.parent.mkdir()
    settings.write_text("[]")
    assert load_server() is None


def test_solo_events_are_hidden(ftp, fast, tmp_path, monkeypatch, capsys):
    replies = iter([f"127.0.0.1:{ftp.port}", "me"])
    monkeypatch.setattr("builtins.input", lambda question: next(replies))
    monkeypatch.setattr("getpass.getpass", lambda question: "secret")
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
