"""Draws the step-by-step images of the README from a real run of the program.

uv run python tools/build_tutorial.py

The questions and answers come from the program itself, against the FTP server of the tests and the invented race
weekend, so the images change when the text of the program changes. Typed answers are yellow; the hints in green are
added here. The folder pictures are drawings, not screenshots of a system.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).parent.parent
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests")]

from conftest import FakeFtp  # noqa: E402

from acc_race_stats import cli, demo  # noqa: E402
from acc_race_stats import server as server_module  # noqa: E402
from acc_race_stats.messages import set_language  # noqa: E402

OUT = ROOT / "docs" / "images" / "tutorial"
BG, BAR, TEXT, TYPED, HINT, MUTED = "#0f1115", "#1d2027", "#e8eaed", "#f5c542", "#3ddc84", "#8b929c"
MONO = ["Menlo", "Consolas", "DejaVu Sans Mono"]
SANS = ["Avenir Next", "Helvetica Neue", "Segoe UI", "Arial", "DejaVu Sans"]
ADDRESS = "203.0.113.10:8821"
WRAP = 96  # characters per line of the drawn terminal

# per language: the answers of the first run, each with the hint shown next to it
FIRST = {
    "pt-br": [
        ("1", "digite 1 (português)"),
        (ADDRESS, "copie do painel do servidor (ex.: G-Portal)"),
        ("minhaliga", "usuário do FTP, também do painel"),
        ("secret", "a senha não aparece: só asteriscos"),
        ("1", "o número do evento"),
        ("1", "1 = só a corrida, 4 = tudo"),
        ("1", "sua liga usa categorias?"),
        ("1", "escolha o nome das categorias"),
        ("Minha Liga", "aparece em todos os gráficos"),
        ("1", "1 = salvar: da próxima vez não pergunta"),
    ],
    "en": [
        ("2", "type 2 (English)"),
        (ADDRESS, "copy it from the server panel (e.g. G-Portal)"),
        ("myleague", "FTP user, also from the panel"),
        ("secret", "the password shows only asterisks"),
        ("1", "the number of the event"),
        ("1", "1 = only the race, 4 = everything"),
        ("1", "does your league use categories?"),
        ("1", "choose the names of the categories"),
        ("My League", "shown on every chart"),
        ("1", "1 = save: not asked next time"),
    ],
}
SECOND = {
    "pt-br": [("1", "só escolha o evento"), ("1", "e a sessão: pronto")],
    "en": [("1", "only choose the event"), ("1", "and the session: done")],
}
TEXTS = {
    "pt-br": {
        "folder": "Pasta descompactada", "double": "clique duas vezes", "right": "botão direito → Executar como programa",
        "result": "A pasta que abre no final", "charts": "gráficos", "chat": "texto para o chat da liga",
        "data": "os dados",
    },
    "en": {
        "folder": "Unzipped folder", "double": "double-click", "right": "right-click → Run as a Program",
        "result": "The folder that opens at the end", "charts": "charts", "chat": "text for the league chat",
        "data": "the data",
    },
}  # fmt: skip


def run(language: str, port: int, answers: list[tuple[str, str]], argv: list[str], home: Path) -> list[list[tuple]]:
    """Lines of the terminal, each a list of (text, color) parts."""
    pending = list(answers)
    lines: list[list[tuple]] = []
    out = io.StringIO()

    def flush() -> None:
        text = out.getvalue()
        out.seek(0)
        out.truncate()
        if not text:
            return
        for line in text.removesuffix("\n").split("\n"):
            line = line.replace(str(home), "~")
            while len(line) > WRAP:  # long lines continue below, as in a terminal
                lines.append([(line[:WRAP], TEXT)])
                line = line[WRAP:]
            lines.append([(line, TEXT)])

    def question(prompt: str, *, hidden: bool = False, instant=()) -> str:  # type: ignore[no-untyped-def]
        flush()
        answer, hint = pending.pop(0)
        shown = "*" * len(answer) if hidden else answer
        lines.append([(prompt, TEXT), (shown, TYPED), (f"   ← {hint}", HINT)])
        return f"127.0.0.1:{port}" if answer == ADDRESS else answer

    cli.question = question
    set_language(language)
    with contextlib.redirect_stdout(out):
        cli.main([*argv, "--no-open", "--output", str(home / "Documents" / "ACC Race Stats")])
    flush()
    assert not pending, pending
    return lines


def sections(lines: list[list[tuple]]) -> list[list[list[tuple]]]:
    """Cut before the headers '2.', '3.' and the first chart line."""
    cuts = [0]
    for n, line in enumerate(lines):
        text = line[0][0]
        if text[:2] in ("2.", "3."):
            cuts.append(n)
    cuts.append(len(lines))
    return [trim(lines[a:b]) for a, b in zip(cuts, cuts[1:], strict=False)]


def trim(lines: list[list[tuple]]) -> list[list[tuple]]:
    while lines and lines[0] == [("", TEXT)]:
        lines = lines[1:]
    while lines and lines[-1] == [("", TEXT)]:
        lines = lines[:-1]
    return lines


def terminal(lines: list[list[tuple]], path: Path, title: str = "ACC Race Stats") -> None:
    size, step = 11.5, 0.27  # font size and inches per line
    width = 11.0
    height = 0.75 + step * len(lines) + 0.35
    fig = plt.figure(figsize=(width, height), dpi=150)
    fig.patch.set_alpha(0)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set(xlim=(0, width), ylim=(height, 0))
    ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.08, 0.08), width - 0.16, height - 0.16, boxstyle="round,pad=0,rounding_size=0.14",
                                fc=BG, ec="#2a2e36", lw=1.2))  # fmt: skip
    ax.add_patch(FancyBboxPatch((0.08, 0.08), width - 0.16, 0.42, boxstyle="round,pad=0,rounding_size=0.14",
                                fc=BAR, ec="none"))  # fmt: skip
    ax.add_patch(plt.Rectangle((0.08, 0.36), width - 0.16, 0.14, fc=BAR, ec="none"))
    for k, color in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        ax.add_patch(plt.Circle((0.35 + 0.24 * k, 0.29), 0.075, color=color))
    ax.text(width / 2, 0.29, title, ha="center", va="center", color=MUTED, fontsize=10.5, family=SANS)
    renderer = fig.canvas.get_renderer()
    probe = ax.text(0, 0, "M" * 20, fontsize=size, family=MONO)
    box = probe.get_window_extent(renderer)
    probe.remove()
    char = box.width / 20 / fig.dpi  # inches per character
    for n, parts in enumerate(lines):
        x, y = 0.35, 0.82 + step * n
        for text, color in parts:
            ax.text(x, y, text, color=color, fontsize=size, family=MONO, va="center",
                    fontweight="bold" if color == TYPED else "normal")  # fmt: skip
            x += char * len(text)
    fig.savefig(path)
    plt.close(fig)


def folder(language: str, path: Path) -> None:
    t = TEXTS[language]
    rows = [
        ("📁", "docs", ""), ("📁", "examples", ""), ("📁", "src", ""), ("📁", "tests", ""),
        ("▶", "ACC-Race-Stats.bat", f"Windows: {t['double']}"),
        ("▶", "ACC-Race-Stats.command", f"macOS: {t['double']}"),
        ("▶", "run.sh", f"Linux: {t['right']}"),
        ("·", "README.md", ""), ("·", "pyproject.toml", ""), ("·", "…", ""),
    ]  # fmt: skip
    width, step = 11.0, 0.36
    height = 0.95 + step * len(rows) + 0.2
    fig = plt.figure(figsize=(width, height), dpi=150)
    fig.patch.set_alpha(0)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set(xlim=(0, width), ylim=(height, 0))
    ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.08, 0.08), width - 0.16, height - 0.16, boxstyle="round,pad=0,rounding_size=0.14",
                                fc="#f6f7f9", ec="#c9ced6", lw=1.2))  # fmt: skip
    ax.text(0.35, 0.4, f"{t['folder']}: acc-race-stats-main", fontsize=13, fontweight="bold", va="center",
            family=SANS, color="#1d2027")  # fmt: skip
    for n, (icon, name, hint) in enumerate(rows):
        y = 0.95 + step * n
        launcher = bool(hint)
        if launcher:
            ax.add_patch(FancyBboxPatch((0.25, y - 0.15), 5.0, 0.3, boxstyle="round,pad=0,rounding_size=0.06",
                                        fc="#fff3c4", ec="#e0b000", lw=1.2))  # fmt: skip
        mark = {"📁": "#4a90d9", "▶": "#1a9e4b", "·": "#8b929c"}[icon]
        shape = "s" if icon == "📁" else ">" if icon == "▶" else "o"
        ax.plot(0.48, y, marker=shape, ms=9 if icon != "·" else 4, color=mark)
        ax.text(0.75, y, name, fontsize=12, va="center", family=MONO, color="#1d2027",
                fontweight="bold" if launcher else "normal")  # fmt: skip
        if hint:
            ax.annotate(hint, (5.3, y), (5.75, y), va="center", fontsize=12, family=SANS, color="#1a7f3c",
                        fontweight="bold", arrowprops={"arrowstyle": "-|>", "color": "#1a7f3c", "lw": 1.6})  # fmt: skip
    fig.savefig(path)
    plt.close(fig)


def result(language: str, path: Path) -> None:
    t = TEXTS[language]
    images = ["01-result", "04-gap-to-winner", "08-battles", "09-pit-stops", "12-lap-by-lap", "16-pace-distribution"]
    fig = plt.figure(figsize=(11, 6.6), dpi=150)
    fig.patch.set_facecolor("#f6f7f9")
    fig.text(0.03, 0.95, t["result"] + ":  Documents / ACC Race Stats / 2026-03-15-2140-monza-race", fontsize=13,
             fontweight="bold", family=SANS, color="#1d2027", va="top")  # fmt: skip
    for k, name in enumerate(images):
        ax = fig.add_axes((0.03 + (k % 3) * 0.32, 0.47 - (k // 3) * 0.37, 0.3, 0.33))
        ax.imshow(plt.imread(ROOT / "docs" / "images" / f"{name}.png"))
        ax.set_title(f"{name}.png", fontsize=9.5, family=MONO, color="#1d2027")
        ax.axis("off")
    note = f"01 … 16 .png = {t['charts']}     summary.txt = {t['chat']}     race.json = {t['data']}"
    fig.text(0.03, 0.03, note, fontsize=11, family=MONO, color="#1d2027")
    fig.savefig(path)
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    files = {s.name: json.dumps(s.data).encode("utf-16-le") for s in demo.weekend()}
    ftp = FakeFtp(files)
    try:
        for language in ("pt-br", "en"):
            with tempfile.TemporaryDirectory() as folder_name:
                home = Path(folder_name).resolve()
                project = home / "Downloads" / "acc-race-stats-main"
                project.mkdir(parents=True)
                os.chdir(project)
                os.environ["XDG_CONFIG_HOME"] = os.environ["APPDATA"] = str(home / ".config")
                os.environ.pop("ACC_FTP_PASSWORD", None)
                server_module.cache_folder = lambda home=home: home / "cache"  # type: ignore[assignment]
                cli.open_folder = lambda path: None  # type: ignore[assignment]
                first = sections(run(language, ftp.port, FIRST[language], [], home))
                for n, part in enumerate(first, 1):
                    terminal(part, OUT / f"{language}-step{n}.png")
                second = run(language, ftp.port, SECOND[language], [], home)
                terminal(trim(second), OUT / f"{language}-next-time.png")
            folder(language, OUT / f"{language}-folder.png")
            result(language, OUT / f"{language}-result.png")
    finally:
        os.chdir(ROOT)
        ftp.listener.close()
    print("\n".join(str(p.relative_to(ROOT)) for p in sorted(OUT.glob("*.png"))))


if __name__ == "__main__":
    main()
