"""Where things are saved on each system."""

from __future__ import annotations

import os
import sys
from pathlib import Path

NAME = "ACC Race Stats"


def documents() -> Path:
    """The Documents folder of the user, also when it was moved (OneDrive, another disk, another language)."""
    home = Path.home()
    if sys.platform == "win32":
        import ctypes

        buffer = ctypes.create_unicode_buffer(260)
        if ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buffer) == 0 and buffer.value:
            return Path(buffer.value)
        return home / "Documents"
    if sys.platform != "darwin":
        config = Path(os.environ.get("XDG_CONFIG_HOME") or home / ".config") / "user-dirs.dirs"
        try:
            for line in config.read_text(encoding="utf-8").splitlines():
                if line.startswith("XDG_DOCUMENTS_DIR="):
                    return Path(line.split("=", 1)[1].strip().strip('"').replace("$HOME", str(home)))
        except (OSError, UnicodeDecodeError):
            pass
    return home / "Documents"


def writable(folder: Path) -> bool:
    try:
        folder.mkdir(parents=True, exist_ok=True)
        test = folder / ".write-test"
        test.touch()
        test.unlink()
    except OSError:
        return False
    return True


def default_output() -> Path:
    """Documents/ACC Race Stats, or a folder in the user's home when Documents cannot be written."""
    return next((f for f in (documents() / NAME, Path.home() / NAME) if writable(f)), Path.cwd() / "reports")


def cache_folder() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Caches"
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    return base / "acc-race-stats"
