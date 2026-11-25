"""Downloading result files from the game server over FTP."""

from __future__ import annotations

import ftplib
import io
import urllib.parse
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import PurePosixPath

from .results import ResultError, Session, parse_name, session_from_bytes

MAX_FILE = 20_000_000


class ServerError(Exception):
    """A problem the user can act on."""


class LoginError(ServerError):
    """The server answered but refused the user or password."""


@dataclass
class Address:
    host: str
    port: int = 21
    user: str = ""
    password: str = ""


def parse_address(text: str) -> Address:
    """Accepts '1.2.3.4', '1.2.3.4:8821' and 'ftp://user:password@1.2.3.4:8821/'."""
    text = text.strip()
    try:
        url = urllib.parse.urlsplit(text if "://" in text else f"ftp://{text}")
        port = url.port or 21
    except ValueError as error:
        raise ServerError("The address is not valid. Example: 203.0.113.10:8821") from error
    if url.scheme != "ftp" or not url.hostname:
        raise ServerError("The address is not valid. Example: 203.0.113.10:8821")
    return Address(
        url.hostname, port, urllib.parse.unquote(url.username or ""), urllib.parse.unquote(url.password or "")
    )


class Server:
    def __init__(self, address: Address, timeout: float = 30) -> None:
        self.address, self.timeout = address, timeout
        self.folder = ""
        self.names: list[str] = []
        self.connect()

    def connect(self) -> None:
        address = self.address
        where = f"{address.host}:{address.port}"
        self.ftp = ftplib.FTP(timeout=self.timeout)
        try:
            self.ftp.connect(address.host, address.port)
        except (OSError, EOFError, ftplib.Error) as error:
            raise ServerError(
                f"The server {where} did not answer ({type(error).__name__}). The user and password were not tested. "
                "Check that the server is running and that the address and port are right."
            ) from error
        try:
            self.ftp.login(address.user, address.password)
        except ftplib.error_perm as error:
            self.ftp.close()
            raise LoginError("The server answered, but the user or password is wrong.") from error
        except (OSError, EOFError, ftplib.Error) as error:
            self.ftp.close()
            raise ServerError(f"The connection to {where} was lost during login.") from error

    def close(self) -> None:
        self.ftp.close()

    def _list(self, folder: str) -> tuple[list[str], list[str]]:
        try:
            items = list(self.ftp.mlsd(folder))
            files = [n for n, facts in items if facts.get("type") == "file"]
            return files, [n for n, facts in items if facts.get("type") == "dir"]
        except ftplib.error_perm:
            names = [PurePosixPath(n).name for n in self.ftp.nlst(folder)]
            return [n for n in names if "." in n], [n for n in names if "." not in n]

    def find_results(self) -> list[str]:
        """Looks for result files in /results, then up to three levels below the root."""
        queue = ["/results", "/"]
        seen: set[str] = set()
        while queue and len(seen) < 80:
            folder = queue.pop(0)
            if folder in seen:
                continue
            seen.add(folder)
            try:
                files, folders = self._list(folder)
            except ftplib.Error:
                continue
            except (OSError, EOFError) as error:
                raise ServerError("The connection was lost while listing the files.") from error
            names = [n for n in files if parse_name(n)]
            if names:
                self.folder, self.names = folder, sorted(names, key=lambda n: parse_name(n) or ())
                return self.names
            if folder.count("/") <= 3:
                queue += [f"{folder.rstrip('/')}/{n}" for n in sorted(folders, key=lambda n: n != "results")]
        raise ServerError(
            'No result file found on the server. ACC only saves them with "dumpLeaderboards": 1 in settings.json.'
        )

    def download(self, name: str) -> tuple[Session, bytes]:
        try:
            raw = self._fetch(name)
        except (OSError, EOFError, ftplib.error_temp):  # idle servers drop the connection: one more try
            self.close()
            self.connect()
            try:
                raw = self._fetch(name)
            except (OSError, EOFError, ftplib.Error) as error:
                raise ServerError(f"Could not download {name}.") from error
        except ftplib.Error as error:
            raise ResultError(f"{name} cannot be downloaded.") from error
        return session_from_bytes(name, raw), raw

    def _fetch(self, name: str) -> bytes:
        buffer = io.BytesIO()

        def receive(chunk: bytes) -> None:
            buffer.write(chunk)
            if buffer.tell() > MAX_FILE:
                raise ResultError(f"{name} is too big for a result file.")

        self.ftp.retrbinary(f"RETR {self.folder.rstrip('/')}/{name}", receive)
        return buffer.getvalue()

    def search(self, day: date | None, kinds: set[str], margin: int = 3, limit: int = 40) -> list[str]:
        """Newest first: files of these kinds around a day (or the newest ones without a day)."""
        found = []
        for name in reversed(self.names):
            parsed = parse_name(name)
            if not parsed or parsed[1] not in kinds:
                continue
            if day and abs(parsed[0].date() - day) > timedelta(days=margin):
                continue
            found.append(name)
        return found[:limit]

    def try_download(self, name: str) -> tuple[Session, bytes] | None:
        """Like download, but None for a file that is not a usable session."""
        try:
            return self.download(name)
        except ResultError:
            return None
