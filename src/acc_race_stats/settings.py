"""The last server used, so only the password is typed next time. The password is never stored."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from .server import Address


def settings_file() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / "acc-race-stats" / "server.json"


def load_server() -> Address | None:
    try:
        data = json.loads(settings_file().read_text(encoding="utf-8"))
        return Address(str(data["host"]), int(data["port"]), str(data["user"]))
    except (OSError, ValueError, KeyError, TypeError):
        return None


def save_server(address: Address) -> None:
    """A convenience: a read-only disk must not stop the report."""
    path = settings_file()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"host": address.host, "port": address.port, "user": address.user}), encoding="utf-8"
        )
    except OSError:
        pass
