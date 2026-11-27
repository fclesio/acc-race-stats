"""Optional TOML file with the answers (server, password, league...), so nothing has to be typed."""

from __future__ import annotations

import json
import os
import re
import stat
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib

from .messages import tr
from .server import Address, ServerError, parse_address
from .settings import settings_file

FILE_NAME = "acc-race-stats.toml"
ENV_FILE = "ACC_RACE_STATS_CONFIG"

# [report] key: (argparse name, type)
REPORT: dict[str, tuple[str, type]] = {
    "language": ("lang", str),
    "league": ("league", str),
    "event": ("event", str),
    "divisions": ("divisions", str),
    "color_by": ("color_by", str),
    "class_map": ("class_map", dict),
    "class_color": ("class_color", dict),
    "roster": ("roster", Path),
    "grid": ("grid", Path),
    "output": ("output", Path),
    "min_cars": ("min_cars", int),
    "open_folder": ("no_open", bool),
}
SERVER = {"address": str, "port": int, "user": str, "password": str}
CHOICES = {
    "language": ("en", "pt-br"),
    "color_by": ("auto", "class", "driver"),
    "divisions": ("none", "game", "pro", "metal", "fia", "numbers"),
}


class ConfigError(Exception):
    """A config file that cannot be used, shown without a traceback."""


@dataclass
class Config:
    path: Path | None = None
    server: Address | None = None
    defaults: dict[str, Any] = field(default_factory=dict)


def candidates() -> list[Path]:
    """The project folder first (where the launchers run), then the folder of the remembered server."""
    return [Path.cwd() / FILE_NAME, settings_file().with_name("config.toml")]


def find(explicit: Path | None) -> Path | None:
    chosen = explicit or (Path(os.environ[ENV_FILE]) if os.environ.get(ENV_FILE) else None)
    if chosen:
        chosen = chosen.expanduser()
        if not chosen.is_file():
            raise ConfigError(tr("Config file {path} not found", path=chosen))
        return chosen
    return next((p for p in candidates() if p.is_file()), None)


def _check(path: Path, where: str, key: str, value: Any, kind: type) -> Any:
    wanted = str if kind is Path else kind
    if kind is int and isinstance(value, bool) or not isinstance(value, wanted):
        raise ConfigError(tr("{path}: {key} has the wrong type", path=path.name, key=f"{where}.{key}"))
    if key in CHOICES and value not in CHOICES[key]:
        options = ", ".join(CHOICES[key])
        raise ConfigError(tr("{path}: {key} must be one of {options}", path=path.name, key=key, options=options))
    if kind is Path:
        folder = Path(str(value)).expanduser()
        return folder if folder.is_absolute() else path.parent / folder
    if kind is dict:
        table: dict[str, Any] = cast(dict, value)
        return [f"{name}={text}" for name, text in table.items()]
    return value


def load(explicit: Path | None = None) -> Config:
    path = find(explicit)
    if path is None:
        return Config()
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        raise ConfigError(tr("Cannot read {path}: {error}", path=path, error=error)) from error
    unknown = [f"[{k}]" for k in data if k not in ("server", "report")]
    for section, known in (("server", SERVER), ("report", REPORT)):
        unknown += [f"{section}.{k}" for k in data.get(section, {}) if k not in known]
    if unknown:
        raise ConfigError(tr("{path}: unknown setting {names}", path=path.name, names=", ".join(unknown)))

    config = Config(path)
    for key, value in data.get("report", {}).items():
        name, kind = REPORT[key]
        value = _check(path, "report", key, value, kind)
        config.defaults[name] = (not value) if key == "open_folder" else value

    server = {k: _check(path, "server", k, v, SERVER[k]) for k, v in data.get("server", {}).items()}
    if server.get("address"):
        try:
            address = parse_address(server["address"])
        except ServerError as error:
            raise ConfigError(f"{path.name}: {error}") from error
        address.port = server.get("port", address.port)
        address.user = server.get("user", address.user)
        address.password = server.get("password", address.password)
        config.server = address
    return config


def make_private(path: Path) -> None:
    """Only the owner can read a file with a password (POSIX); nothing for the user to do."""
    if sys.platform == "win32":
        return
    try:
        if path.stat().st_mode & (stat.S_IRWXG | stat.S_IRWXO):
            path.chmod(0o600)
    except OSError:
        pass


def save_location() -> Path:
    """Next to the launchers when that folder can be written, otherwise next to the remembered server."""
    here = Path.cwd() / FILE_NAME
    try:
        with open(here, "a", encoding="utf-8"):
            pass
        return here
    except OSError:
        return candidates()[1]


def _text(value: str) -> str:
    """A TOML basic string; JSON escapes are valid TOML."""
    return json.dumps(value, ensure_ascii=False)


def save(address: Address, report: dict[str, Any], path: Path | None = None) -> Path | None:
    """Writes the answers of a guided run. Returns None when nothing could be written."""
    path = path or save_location()
    lines = [
        "# ACC Race Stats: answers saved by the program, so they are not asked again.",
        "# Edit with any text editor, or delete this file to be asked everything again.",
        "# It holds the FTP password: do not share it. See acc-race-stats.example.toml for every setting.",
        "",
        "[server]",
        f"address = {_text(f'{address.host}:{address.port}')}",
        f"user = {_text(address.user)}",
        f"password = {_text(address.password)}",
        "",
        "[report]",
    ]
    for key, value in report.items():
        if isinstance(value, dict):
            pairs = ", ".join(f"{_text(k)} = {_text(v)}" for k, v in value.items())
            lines.append(f"{key} = {{ {pairs} }}")
        elif value not in ("", None, {}):
            lines.append(f"{key} = {_text(str(value))}")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except OSError:
        return None
    make_private(path)
    return path


def update_password(path: Path, password: str) -> None:
    """After a wrong saved password, the one that worked replaces it; the rest of the file is kept."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return
    new, count = re.subn(r"(?m)^(\s*password\s*=).*$", lambda m: f"{m[1]} {_text(password)}", text)
    if count == 1:
        try:
            path.write_text(new, encoding="utf-8")
        except OSError:
            pass
