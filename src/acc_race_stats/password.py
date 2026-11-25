"""Password question that shows one asterisk per character. Pasting and Backspace work."""

from __future__ import annotations

import codecs
import getpass
import os
import sys
from collections.abc import Callable

ESCAPE = "\x1b"


def collect(read: Callable[[], str], show: Callable[[str], object]) -> str:
    """Reads one character at a time until Enter."""
    typed: list[str] = []
    while True:
        char = read()
        if char in ("\r", "\n"):
            show("\n")
            return "".join(typed)
        if char == "\x03":
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
        elif char == ESCAPE:  # arrows, and the marks some terminals put around pasted text
            if read() in ("[", "O"):
                while not (final := read()).isalpha() and final not in ("~", ""):
                    pass
        elif char in ("\x00", "\xe0") and sys.platform == "win32":  # arrows and function keys send two codes
            read()
        elif char.isprintable():
            typed.append(char)
            show("*")


def show(text: str) -> None:
    sys.stdout.write(text)
    sys.stdout.flush()


if sys.platform == "win32":
    import msvcrt

    def ask_password(question: str) -> str:
        if not sys.stdin.isatty():
            return getpass.getpass(question)
        show(question)
        return collect(msvcrt.getwch, show)

else:
    import termios

    def ask_password(question: str) -> str:
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            return getpass.getpass(question)
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

        before = termios.tcgetattr(fd)
        mode = termios.tcgetattr(fd)
        mode[3] &= ~(termios.ICANON | termios.ECHO | termios.ISIG)
        show(question)
        try:
            termios.tcsetattr(fd, termios.TCSADRAIN, mode)
            return collect(read, show)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, before)
