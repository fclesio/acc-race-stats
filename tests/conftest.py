"""Fixtures shared by the tests: a fake FTP server, isolated settings and charts that are not drawn."""

import json
import socket
import threading

import pytest

from acc_race_stats import cli, demo
from acc_race_stats import server as server_module
from acc_race_stats.messages import set_language


class FakeFtp(threading.Thread):
    """Just enough FTP for the client: login, MLSD and RETR in passive mode."""

    def __init__(self, files):
        super().__init__(daemon=True)
        self.files = files
        self.drops = 0
        self.sent = 0
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
                if command == "RETR" and self.drops:
                    self.drops -= 1
                    stream.close()
                    connection.shutdown(socket.SHUT_RDWR)
                    return
                say("150 here")
                channel, _ = data.accept()
                if command == "RETR":
                    self.sent += 1
                    body = self.files[argument.rsplit("/", 1)[1]]
                elif argument == "/game/results":
                    body = "".join(f"type=file;size={len(b)}; {n}\r\n" for n, b in self.files.items()).encode()
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
    set_language("en")
    folder = tmp_path_factory.mktemp("settings")
    monkeypatch.setenv("APPDATA", str(folder))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(folder))
    monkeypatch.setattr(server_module, "cache_folder", lambda: folder / "cache")
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
