"""Questions in the terminal, read key by key.

The usual input() depends on how the previous program left the terminal: Enter may arrive as a carriage return, as a
keypad code or as an escape sequence, and the question then never ends. Here all of them work.
"""

from __future__ import annotations

import codecs
import getpass
import os
import re
import sys
from collections.abc import Callable, Container

ENTER = "\n"
CANCEL = "\x03"
KEYPAD = {"M": ENTER, "n": ".", "l": ".", "m": "-", "o": "/"} | {chr(ord("p") + n): str(n) for n in range(10)}


def escape_key(read: Callable[[], str], waiting: Callable[[], bool]) -> str:
    """The key behind an escape sequence, or '' for arrows, paste marks and a lone Esc."""
    if not waiting():
        return ""
    first = read()
    if first == "O":
        return KEYPAD.get(read(), "")
    if first != "[":
        return ""
    sequence = ""
    while True:
        char = read()
        if not char:
            return ""
        sequence += char
        if "@" <= char <= "~":
            break
    # extended keyboard modes: ESC[13u, ESC[99;5u and ESC[27;5;99~
    match = re.fullmatch(r"(\d+)(?::\d+)*(?:;(\d+)(?::(\d+))?)?u", sequence)
    if match:
        code, modifier, released = int(match[1]), int(match[2] or 1), match[3] == "3"
    elif other := re.fullmatch(r"27;(\d+);(\d+)~", sequence):
        code, modifier, released = int(other[2]), int(other[1]), False
    else:
        return ""
    if released:
        return ""
    if (modifier - 1) & 4:  # Ctrl
        return chr(code & 31) if chr(code).isalpha() else ""
    if code in (13, 57414):
        return ENTER
    if 57399 <= code <= 57408:
        return str(code - 57399)
    if code >= 57344:
        return ""
    char = chr(code)
    return char.upper() if (modifier - 1) & 1 else char


def collect(
    read: Callable[[], str],
    show: Callable[[str], object],
    *,
    hidden: bool = False,
    instant: Container[str] = (),
    waiting: Callable[[], bool] = lambda: True,
) -> str:
    """Reads keys until Enter, or a key of 'instant' typed first. Hidden text shows asterisks."""
    typed: list[str] = []
    while True:
        char = read()
        if char == "\x1b":
            char = escape_key(read, waiting)
            if not char:
                continue
        if char in ("\r", "\n"):
            show("\n")
            return "".join(typed)
        if char == CANCEL:
            show("\n")
            raise KeyboardInterrupt
        if char == "" or (char == "\x04" and not typed):
            show("\n")
            raise EOFError
        if char in ("\x7f", "\b"):
            if typed:
                typed.pop()
                show("\b \b")
        elif char == "\x15":  # Ctrl-U clears the line
            show("\b \b" * len(typed))
            typed.clear()
        elif char in ("\x00", "\xe0") and sys.platform == "win32":  # arrows and function keys send two codes
            read()
        elif char.isprintable():
            typed.append(char)
            show("*" if hidden else char)
            if len(typed) == 1 and char in instant:
                show("\n")
                return char


def show(text: str) -> None:
    sys.stdout.write(text)
    sys.stdout.flush()


def plain(question: str, hidden: bool) -> str:
    """Without a terminal (pipes, tests)."""
    return getpass.getpass(question) if hidden else input(question)


if sys.platform == "win32":
    import msvcrt

    def question(text: str, *, hidden: bool = False, instant: Container[str] = ()) -> str:
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            return plain(text, hidden)
        show(text)
        return collect(msvcrt.getwch, show, hidden=hidden, instant=instant, waiting=msvcrt.kbhit)

else:
    import select
    import termios

    def question(text: str, *, hidden: bool = False, instant: Container[str] = ()) -> str:
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            return plain(text, hidden)
        fd = sys.stdin.fileno()
        decoder = codecs.getincrementaldecoder("utf-8")("replace")

        def read() -> str:
            while True:
                raw = os.read(fd, 1)
                if not raw:
                    return ""
                char = decoder.decode(raw)
                if char:
                    return char

        def waiting() -> bool:
            return bool(select.select([fd], [], [], 0.1)[0])

        before = termios.tcgetattr(fd)
        mode = termios.tcgetattr(fd)
        mode[0] &= ~termios.IGNCR
        mode[1] |= termios.OPOST | termios.ONLCR
        mode[3] &= ~(termios.ICANON | termios.ECHO | termios.ISIG)
        mode[6][termios.VMIN], mode[6][termios.VTIME] = 1, 0
        show(text)
        try:
            termios.tcsetattr(fd, termios.TCSADRAIN, mode)
            return collect(read, show, hidden=hidden, instant=instant, waiting=waiting)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, before)
