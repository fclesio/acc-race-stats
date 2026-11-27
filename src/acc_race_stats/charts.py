"""PNG charts drawn with matplotlib."""

from __future__ import annotations

import logging
import statistics
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.offsetbox import AnnotationBbox, OffsetImage  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from matplotlib.ticker import FuncFormatter, MaxNLocator, MultipleLocator  # noqa: E402

from .gamedata import brand  # noqa: E402
from .i18n import Translate  # noqa: E402
from .palette import driver_palette  # noqa: E402
from .race import Driver, Race  # noqa: E402

logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
BG, CARD, LINE, TEXT, MUTED = "#0a0b0d", "#121418", "#262a31", "#f4f5f7", "#8b929c"
ACCENT = "#f5c542"
GREEN, RED, PURPLE = "#3ddc84", "#ff5d5d", "#c77dff"
STINT_COLORS = ["#3a7bd5", "#7ed321", "#ff8a1f", "#c77dff", "#4fd6e8", "#f5c542"]
# color alone is not enough to tell five crossing lines apart
TOP5_STYLES: list[tuple[str, Any, str]] = [
    ("#4da3ff", "-", "o"), ("#ff8a1f", (0, (6, 2)), "s"), ("#3ddc84", (0, (1, 1.2)), "^"),
    ("#c77dff", (0, (6, 2, 1, 2)), "D"), ("#f5c542", (0, (3, 1, 1, 1, 1, 1)), "v"),
]  # fmt: skip
LOGOS = Path(__file__).parent / "logos"
LOGO_WIDTH = 34  # points, the same for every brand
MONO = ["Menlo", "Consolas", "DejaVu Sans Mono"]
MAX_NAME = 22
BATTLE_SCALE = 4  # seconds above and below 0 in the battle chart
STYLE: Any = {
    "font.family": ["Avenir Next", "Helvetica Neue", "Segoe UI", "Arial", "DejaVu Sans"], "font.size": 12,
    "text.color": TEXT, "axes.facecolor": BG, "figure.facecolor": BG, "savefig.facecolor": BG,
    "axes.edgecolor": LINE, "axes.labelcolor": MUTED, "axes.titlecolor": TEXT, "xtick.color": MUTED,
    "ytick.color": MUTED, "grid.color": LINE, "axes.spines.top": False, "axes.spines.right": False,
    "legend.frameon": False, "axes.axisbelow": True,
    "text.parse_math": False,  # a gamertag with $ is not a formula
}  # fmt: skip


def lap_text(milliseconds: float) -> str:
    """105880 -> '1:45.880'"""
    minutes, rest = divmod(round(milliseconds), 60_000)
    return f"{minutes}:{rest / 1000:06.3f}"


def short(name: str) -> str:
    return name if len(name) <= MAX_NAME else name[: MAX_NAME - 1] + "…"


def whole(ax: Any) -> None:
    """Laps and positions have no decimals."""
    ax.xaxis.set_major_locator(MaxNLocator(nbins=12, integer=True, min_n_ticks=1))


def every(ax: Any, axis: str, step: float, span: float, most: int = 25) -> None:
    """Ticks and grid lines every `step`, or a multiple of it when there would be more than `most` lines."""
    while span / step > most:
        step *= 2
    getattr(ax, f"{axis}axis").set_major_locator(MultipleLocator(step))


def grid_change(grid: int | None, position: int, retired: bool) -> tuple[str, str]:
    """Positions gained from the grid: ▲ green, ▼ red, = grey; nothing without a grid or after retiring."""
    if not grid or retired:
        return "", MUTED
    change = grid - position
    if change > 0:
        return f"▲{change}", GREEN
    if change < 0:
        return f"▼{-change}", RED
    return "=", MUTED


def ink(color: str) -> str:
    """Black or white text, whichever reads better on the color."""
    r, g, b = (int(color[i : i + 2], 16) / 255 for i in (1, 3, 5))
    return BG if 0.299 * r + 0.587 * g + 0.114 * b > 0.5 else "#ffffff"


class Charts:
    def __init__(self, race: Race, out: Path, t: Translate, mode: str, dpi: int = 200) -> None:
        self.race, self.out, self.t, self.mode, self.dpi = race, out, t, mode, dpi
        self.laptime = FuncFormatter(lambda v, _: lap_text(v * 1000))

    # ------------------------------------------------------------ helpers
    def figure(self, title: str, sub: str, width: float, height: float, **grid: Any) -> tuple[Any, Any]:
        fig, axes = plt.subplots(figsize=(width, height), **grid)
        fig.subplots_adjust(top=1 - 1.75 / height, bottom=0.95 / height)
        fig.text(0.035, 1 - 0.4 / height, title, fontsize=24, fontweight="bold", va="top")
        kind = "" if self.race.kind == "R" else self.t(self.race.kind)
        fig.text(
            0.035,
            1 - 0.95 / height,
            "  ·  ".join(x for x in (" · ".join(x for x in (self.race.event, self.race.track) if x), kind, sub) if x),
            fontsize=13,
            color=MUTED,
            va="top",
        )
        if self.race.league:
            league = short(self.race.league).upper()
            style: Any = {"fontsize": 20, "fontweight": "bold", "color": ACCENT, "va": "top", "ha": "right"}
            fig.text(0.965, 1 - 0.4 / height, league, **style)
        fig.text(0.965, 0.15 / height, self.t("source"), fontsize=9, color="#4a5059", ha="right")
        return fig, axes

    def save(self, fig: Any, name: str) -> None:
        fig.savefig(self.out / f"{name}.png", dpi=self.dpi)
        plt.close(fig)

    def legend(self, fig: Any) -> None:
        if self.mode == "class" and len(self.race.classes) > 1:
            handles = []
            for name in self.race.classes:
                own = [d.color for d in self.race.drivers if d.driver_class == name and not d.custom_color]
                if own:
                    handles.append(Patch(color=own[0], label=self.t("class_name", name=name)))
            fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.03, 0), ncol=5, fontsize=11, handlelength=1)

    def names(self, ax: Any, drivers: Sequence[Driver], labels: Sequence[str]) -> None:
        ax.set_yticks(range(len(drivers)), labels, fontsize=11)
        for label, driver in zip(ax.get_yticklabels(), drivers, strict=True):
            label.set_color(driver.color)
        ax.tick_params(axis="y", length=0)

    def bars(
        self, name: str, title: str, sub: str, drivers: Sequence[Driver], value: Callable[[Driver], float],
        text: Callable[[Driver], str], axis: str, room: float = 1.3, count: bool = False,
    ) -> None:  # fmt: skip
        if not drivers:
            return
        values = [value(d) for d in drivers]
        fig, ax = self.figure(title, sub, 16, max(6, 0.45 * len(drivers) + 3))
        fig.subplots_adjust(left=0.2, right=0.95)
        ax.barh(range(len(drivers)), values, color=[d.color for d in drivers], height=0.66)
        top = max(values) or 1
        for y, driver in enumerate(drivers):
            ax.text(values[y] + top * 0.01, y, text(driver), va="center", fontsize=10.5, family=MONO)
        self.names(ax, drivers, [f"P{d.position}  {short(d.name)}" for d in drivers])
        ax.set_ylim(len(drivers) - 0.4, -0.6)
        ax.set_xlim(0, top * room)
        if count:
            whole(ax)
        ax.set_xlabel(axis)
        ax.grid(axis="x", alpha=0.5)
        self.legend(fig)
        self.save(fig, name)

    def table(self, name: str, title: str, sub: str, columns: list[tuple[float, str]], cells: Callable) -> None:
        drivers = self.race.drivers
        fig, ax = self.figure(title, sub, 16, max(6, 0.42 * len(drivers) + 3))
        fig.subplots_adjust(left=0.035, right=0.965)
        ax.axis("off")
        ax.set(xlim=(-0.01, 1.01), ylim=(len(drivers) + 0.5, -0.5))
        for x, label in columns:
            ax.text(x, 0, label, fontsize=10, color=MUTED, va="center", fontweight="bold")
        for y, driver in enumerate(drivers, 1):
            if y % 2:
                ax.add_patch(plt.Rectangle((-0.01, y - 0.5), 1.02, 1, color=CARD, zorder=0))
            place = "DNF" if driver.retired else str(driver.position)
            medal = {1: "#f5c542", 2: "#c9ced6", 3: "#cd7f32"}.get(driver.position, TEXT)
            ax.text(0, y, place, va="center", fontweight="bold", color=medal)
            ax.add_patch(plt.Rectangle((0.036, y - 0.3), 0.005, 0.6, color=driver.color))
            ax.text(0.05, y, short(driver.name), va="center", fontsize=12.5)
            if self.mode == "class":
                box = {"boxstyle": "round,pad=.3", "fc": driver.color, "ec": driver.color}
                ax.text(
                    0.27,
                    y,
                    self.t("class_name", name=driver.driver_class),
                    fontsize=10,
                    va="center",
                    color=ink(driver.color),
                    bbox=box,
                )
            self.logo(ax, 0.376, y, driver.car)
            ax.text(0.398, y, driver.car, fontsize=11.5, va="center")
            for (x, _), (value, color) in zip(columns[-len(cells(driver)) :], cells(driver), strict=True):
                ax.text(x, y, value, va="center", family=MONO, color=color)
        self.save(fig, name)

    def logo(self, ax: Any, x: float, y: float, car: str) -> None:
        name = brand(car)
        if name:
            image = plt.imread(LOGOS / f"{name.lower()}.png")
            box = OffsetImage(image, zoom=LOGO_WIDTH / image.shape[1], dpi_cor=True, interpolation="antialiased")
            ax.add_artist(AnnotationBbox(box, (x, y), frameon=False, pad=0))

    def columns(self, *extra: tuple[float, str]) -> list[tuple[float, str]]:
        middle = [(0.27, self.t("class"))] if self.mode == "class" else []
        return [(0, "#"), (0.05, self.t("driver")), *middle, (0.36, self.t("car")), *extra]

    def best_cell(self, driver: Driver) -> tuple[str, str]:
        return (lap_text(driver.best) if driver.best else "—", PURPLE if driver is self.race.fastest else TEXT)

    # ------------------------------------------------------------ race charts
    def result(self) -> None:
        race, t = self.race, self.t
        winner = race.drivers[0]

        def cells(d: Driver) -> list[tuple[str, str]]:
            behind = winner.laps - d.laps
            if d.retired:
                gap = t("retired")
            elif d is winner:
                gap = lap_text(d.total)
            elif behind > 0:
                gap = t("one_lap") if behind == 1 else t("n_laps", n=behind)
            else:
                gap = f"+{(d.total - winner.total) / 1000:.3f}s"
            change = grid_change(d.grid, d.position, d.retired)
            return [(str(d.laps), TEXT), (gap, TEXT), self.best_cell(d), (str(d.grid or "—"), TEXT), change]

        columns = self.columns((0.6, t("laps")), (0.67, t("time")), (0.8, t("best")), (0.91, t("grid")), (0.95, ""))
        self.table(
            "01-result", t("result"), t("result_sub", cars=len(race.drivers), laps=race.total_laps), columns, cells
        )

    def change(self, name: str, title: str, sub: str, rows: list[tuple[Driver, int]]) -> None:
        if not rows:
            return
        rows.sort(key=lambda row: -row[1])
        fig, ax = self.figure(title, sub, 14, max(6, 0.45 * len(rows) + 3))
        fig.subplots_adjust(left=0.2, right=0.95)
        colors = [GREEN if v > 0 else RED if v < 0 else MUTED for _, v in rows]
        ax.barh(range(len(rows)), [v for _, v in rows], color=colors, height=0.68)
        for y, (_, v) in enumerate(rows):
            side = "left" if v >= 0 else "right"
            ax.text(v + (0.2 if v >= 0 else -0.2), y, f"{v:+d}" if v else "0", va="center", ha=side, fontweight="bold")
        self.names(ax, [d for d, _ in rows], [short(d.name) for d, _ in rows])
        ax.set_ylim(len(rows) - 0.4, -0.6)
        limit = max(abs(v) for _, v in rows) + 2
        ax.set_xlim(-limit, limit)
        ax.axvline(0, color=MUTED, lw=1)
        ax.grid(axis="x")
        whole(ax)
        ax.set_xlabel(self.t("positions"))
        self.legend(fig)
        self.save(fig, name)

    def gained(self) -> None:
        rows = [(d, d.grid - d.position) for d in self.race.drivers if d.grid and not d.retired]
        self.change("02-positions-gained", self.t("gained"), self.t("gained_sub"), rows)

    def start(self) -> None:
        rows = [(d, d.grid - (self.race.position_at(d, 1) or 0)) for d in self.race.drivers if d.grid]
        self.change("03-race-start", self.t("start"), self.t("start_sub"), rows)

    def trace(self) -> None:
        race = self.race
        fig, ax = self.figure(self.t("trace"), self.t("trace_sub", ref=lap_text(race.reference)), 18, 11)
        fig.subplots_adjust(left=0.06, right=0.84)
        labels = []
        low, high = -120.0, 5.0
        for d in reversed(race.drivers):
            gaps = [0.0] + [(n * race.reference - e) / 1000 for n, e in enumerate(d.elapsed, 1)]
            if len(gaps) > 1 and gaps[1] < low:  # never on the same scale as the rest
                continue
            top = d.position <= 6
            ax.plot(range(len(gaps)), gaps, color=d.color, lw=2.6 if top else 1.2, alpha=1 if top else 0.5)
            high = max(high, *gaps)
            if d.position <= 12 and not d.retired and gaps[-1] > low:
                labels.append((gaps[-1], d))
        ax.set_ylim(max(low, ax.get_ylim()[0]), high * 1.15)
        step = (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.03
        last = float("-inf")
        for gap, d in sorted(labels, key=lambda item: item[0]):
            last = max(gap, last + step)
            ax.text(
                race.total_laps + 0.4, last, f"P{d.position} {short(d.name)}", va="center", fontsize=10.5, color=d.color
            )
        ax.set_xlim(0, race.total_laps)
        ax.axhline(0, color=MUTED, lw=1, ls="--")
        every(ax, "x", 3, race.total_laps)
        every(ax, "y", 10, ax.get_ylim()[1] - ax.get_ylim()[0])
        ax.set_xlabel(self.t("lap") + "  ·  " + self.t("trace_note"))
        ax.set_ylabel(self.t("seconds"))
        ax.grid(alpha=0.6)
        self.legend(fig)
        self.save(fig, "04-gap-to-winner")

    def stints(self) -> None:
        drivers = self.race.drivers
        fig, ax = self.figure(self.t("stints"), self.t("stints_sub"), 18, max(6, 0.45 * len(drivers) + 3))
        fig.subplots_adjust(left=0.19, right=0.97)
        for y, d in enumerate(drivers):
            begin = 0
            for k, end in enumerate([*d.pits, d.laps]):
                ax.barh(
                    y, end - begin, left=begin, height=0.62, color=STINT_COLORS[k % len(STINT_COLORS)], edgecolor=BG
                )
                if end - begin >= 2:
                    ax.text((begin + end) / 2, y, str(end - begin), ha="center", va="center", fontsize=10, color=BG)
                begin = end
            for lap in d.served:
                ax.scatter(lap - 0.5, y, marker="X", s=90, color=RED, edgecolor=BG, zorder=4)
        self.names(ax, drivers, [f"P{d.position}  {short(d.name)}" for d in drivers])
        ax.set_ylim(len(drivers) - 0.4, -0.6)
        whole(ax)
        ax.set_xlabel(self.t("lap"))
        ax.grid(axis="x", alpha=0.5)
        most = min(len(STINT_COLORS), max(len(d.pits) + 1 for d in drivers))
        handles: list[Any] = [Patch(color=STINT_COLORS[k], label=self.t("stint", n=k + 1)) for k in range(most)]
        if any(d.served for d in drivers):
            mark = Line2D([], [], marker="X", ls="", ms=10, color=RED, mec=BG, label=self.t("served"))
            handles.append(mark)
        fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.58, 0), ncol=7, fontsize=11, handlelength=1)
        self.legend(fig)
        self.save(fig, "05-stints")

    def top5(self) -> None:
        drivers = [d for d in self.race.drivers if not d.retired and d.clean][:5]
        if not drivers:
            return
        fig, ax = self.figure(self.t("top5"), self.t("clean_sub"), 18, 10)
        fig.subplots_adjust(left=0.07, right=0.97)
        for d, (fixed, dash, marker) in zip(drivers, TOP5_STYLES, strict=False):
            # in class mode several of the top 5 share a color, so the lines get their own
            color = fixed if self.mode == "class" else d.color
            label = f"P{d.position} {short(d.name)} · {d.car}"
            ax.plot(
                [n for n, _ in d.clean],
                [v / 1000 for _, v in d.clean],
                color=color,
                lw=2.2,
                ls=dash,
                marker=marker,
                ms=6,
                label=label,
            )
        ax.yaxis.set_major_formatter(self.laptime)
        whole(ax)
        ax.set_xlabel(self.t("lap"))
        ax.set_ylabel(self.t("lap_time"))
        ax.grid(alpha=0.6)
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.07), ncol=5, fontsize=10, handlelength=4)
        self.save(fig, "06-top5-pace")

    def by_class(self) -> None:
        classes = self.race.classes[:4]
        if self.mode != "class" or len(classes) < 2:
            return
        fig, axes = self.figure(
            self.t("by_class"), self.t("by_class_sub"), 7 * len(classes), 10, ncols=len(classes), sharey=True
        )
        fig.subplots_adjust(left=0.07, right=0.98, wspace=0.06, bottom=0.2)
        for ax, name in zip(axes, classes, strict=True):
            own = [d for d in self.race.drivers if d.driver_class == name]
            for d, dash in zip([d for d in own if d.clean][:3], ("-", "--", ":"), strict=False):
                laps = d.clean
                mean = [statistics.mean(v for _, v in laps[max(0, i - 2) : i + 1]) / 1000 for i in range(len(laps))]
                label = f"P{d.class_position} {short(d.name)} (P{d.position})"
                ax.plot([n for n, _ in laps], mean, color=d.color, ls=dash, lw=2.2, label=label)
            ax.set_title(
                self.t("class_name", name=name), loc="left", fontsize=17, color=own[0].color, fontweight="bold"
            )
            if ax.lines:
                ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.07), fontsize=10.5)
            ax.grid(alpha=0.6)
            whole(ax)
            ax.set_xlabel(self.t("lap"))
        axes[0].yaxis.set_major_formatter(self.laptime)
        self.save(fig, "07-pace-by-class")

    def battles(self) -> None:
        pairs = self.race.battles()
        if not pairs:
            return
        fig, axes = self.figure(
            self.t("battles"),
            self.t("battles_sub", limit=BATTLE_SCALE),
            18,
            3.6 * len(pairs) + 3,
            nrows=len(pairs),
            sharex=True,
            squeeze=False,
        )
        fig.subplots_adjust(left=0.06, right=0.97, hspace=0.75)
        nan = float("nan")
        for ax, (a, b, count) in zip(axes[:, 0], pairs, strict=True):
            skip = self.race.near_stop(a) | self.race.near_stop(b)
            laps = list(range(1, min(len(a.elapsed), len(b.elapsed)) + 1))
            gaps = [nan if n in skip else (self.race.gap(a, b, n) or 0) / 1000 for n in laps]
            # a gap off the scale is drawn on its edge, so the line never leaves the panel
            shown = [g if g != g else max(-BATTLE_SCALE, min(BATTLE_SCALE, g)) for g in gaps]  # g != g: a NaN
            ax.axhspan(-1, 1, color="#1d2a14", zorder=0)
            ax.axhline(0, color=MUTED, lw=1)
            ax.plot(laps, shown, color=a.color, lw=2.4, zorder=3)
            close = [(n, g) for n, g in zip(laps, gaps, strict=True) if abs(g) < 1]
            if close:
                ax.scatter(*zip(*close, strict=True), s=36, color=a.color, zorder=4)
            for side, marker in ((1, "^"), (-1, "v")):
                edge = [n for n, g in zip(laps, gaps, strict=True) if side * g > BATTLE_SCALE]
                if edge:
                    ax.scatter(edge, [side * BATTLE_SCALE] * len(edge), marker=marker, s=60, color=BG,
                               edgecolor=a.color, linewidth=1.6, zorder=4)  # fmt: skip
            ax.set_ylim(-BATTLE_SCALE - 0.8, BATTLE_SCALE + 0.8)
            ax.set_xlim(0.5, self.race.total_laps + 0.5)
            title = f"P{a.position} {short(a.name)}  ×  P{b.position} {short(b.name)}   ·   "
            ax.set_title(title + self.t("battle_laps", n=count), loc="left", fontsize=14)
            ax.grid(alpha=0.5)
            ax.tick_params(labelbottom=True)
            whole(ax)
            ax.set_xlabel(self.t("lap"))
            ax.set_ylabel(self.t("seconds"))
        self.save(fig, "08-battles")

    def pits(self) -> None:
        rows = self.race.pit_effect()
        if not rows:
            return
        fig, (ax, right) = self.figure(
            self.t("pits"),
            self.t("pits_sub"),
            18,
            max(7, 0.45 * len(rows) + 3.4),
            ncols=2,
            sharey=True,
            width_ratios=[3, 2],
        )
        fig.subplots_adjust(left=0.24, right=0.96, wspace=0.08)
        worst = 0.0
        for y, (d, stop, before, after) in enumerate(rows):
            color = GREEN if after < before else RED if after > before else MUTED
            if after != before:
                ax.annotate("", (after, y), (before, y), arrowprops={"arrowstyle": "-|>", "color": color, "lw": 2.2})
            ax.scatter(before, y, s=55, color=BG, edgecolor=TEXT, zorder=3)
            text = f"P{before} → P{after}  ({before - after:+d})" if after != before else f"P{before}  (0)"
            ax.text(max(before, after) + 0.8, y, text, va="center", ha="right", fontsize=10.5, color=color)
            loss = self.race.pit_loss(d, stop)
            if loss is not None:
                worst = max(worst, loss)
                right.barh(y, loss, color=d.color, height=0.6)
                right.text(loss + 0.5, y, f"{loss:.1f} s", va="center", fontsize=10.5, family=MONO)
        self.names(ax, [r[0] for r in rows], [f"{short(r[0].name)} · {self.t('pitted', n=r[1])}" for r in rows])
        ax.set_ylim(len(rows) - 0.4, -0.6)
        last = max(max(r[2], r[3]) for r in rows)
        ax.set_xlim(last + 9, 0.3)
        ticks = [p for p in (1, *range(5, 100, 5)) if p <= last]
        ax.set_xticks(ticks, [f"P{p}" for p in ticks])
        ax.set_title(self.t("pits_pos"), loc="left", fontsize=13)
        right.set_title(self.t("pits_loss"), loc="left", fontsize=13)
        right.set_xlabel(self.t("pits_loss_axis"))
        right.set_xlim(0, (worst or 1) * 1.15)
        for axis in (ax, right):
            axis.grid(axis="x", alpha=0.5)
        right.tick_params(axis="y", length=0)
        self.legend(fig)
        self.save(fig, "09-pit-stops")

    def order(self) -> None:
        """Own color for every driver (cars of a class run together); the dash and the dots show the class."""
        race, drivers = self.race, self.race.drivers
        sub = self.t("order_sub") + (self.t("order_class") if self.mode == "class" else "")
        fig, ax = self.figure(self.t("order"), sub, 20, max(8, 0.5 * len(drivers) + 3))
        fig.subplots_adjust(left=0.16, right=0.83)
        by_class = self.mode == "class"
        dashes: list[Any] = ["-", (0, (5, 1.5)), (0, (1.2, 1)), (0, (5, 1.5, 1, 1.5))]
        # consecutive finishers get distant colors
        for d, own in zip(drivers, driver_palette(len(drivers)), strict=True):
            color = own if by_class else d.color
            dash = dashes[race.classes.index(d.driver_class) % len(dashes)] if by_class else "-"
            points = [(0, d.grid)] if d.grid else []
            points += [(n, p) for n in range(1, len(d.elapsed) + 1) if (p := race.position_at(d, n))]
            if d.laps >= race.total_laps:
                points[-1] = (points[-1][0], d.position)  # penalties after the race change the order
            xs, ys = zip(*points, strict=True)
            z = 100 - d.position
            # the dark edge keeps crossing lines apart
            ax.plot(xs, ys, color=BG, lw=5.5, zorder=z)
            ax.plot(xs, ys, color=color, lw=2.4, ls=dash, zorder=z, solid_joinstyle="round")
            for x, y in (points[0], points[-1]):
                ax.scatter(x, y, s=210, color=d.color, edgecolor=color, linewidth=2, zorder=200)
                ax.text(x, y, str(y), ha="center", va="center_baseline", fontsize=8.5, fontweight="bold",
                        color=ink(d.color), zorder=201)  # fmt: skip
            ax.text(xs[0] - 0.55, ys[0], short(d.name), ha="right", va="center", fontsize=11, color=color)
            if d.retired:
                ax.text(xs[-1], ys[-1] + 0.62, self.t("retired"), ha="center", va="center", fontsize=9, color=color,
                        zorder=202)  # fmt: skip
            elif d.laps < race.total_laps:
                ax.plot([xs[-1], race.total_laps], [ys[-1], d.position], color=color, lw=0.8, alpha=0.35, zorder=1)
            label = f"P{d.position} {short(d.name)}"
            ax.text(race.total_laps + 0.6, d.position, label, va="center", fontsize=11, color=color)
        most = max(len(drivers), *(d.grid or 0 for d in drivers))
        ax.set_ylim(most + 0.7, 0.3)
        ax.set_yticks([])
        ax.spines["left"].set_visible(False)
        ax.set_xlim(-0.35, race.total_laps + 0.35)
        whole(ax)
        ax.set_xlabel(self.t("lap"))
        ax.grid(axis="x", alpha=0.35)
        if by_class:
            handles = []
            for name, dash in zip(race.classes, dashes * 3, strict=False):
                fill = next(d.color for d in drivers if d.driver_class == name)
                handles.append(
                    Line2D([], [], color=MUTED, ls=dash, lw=2.4, marker="o", ms=10, mfc=fill, mec=fill,
                           label=self.t("class_name", name=name))
                )  # fmt: skip
            fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.03, 0), ncol=5, fontsize=11, handlelength=5)
        self.save(fig, "12-lap-by-lap")

    # ------------------------------------------------------------ charts for any session
    def consistency(self) -> None:
        rows = [d for d in self.race.drivers if d.spread is not None and len(d.clean) >= 5]
        rows.sort(key=lambda d: d.spread or 0)
        typical = self.t("typical")
        self.bars("10-consistency", self.t("consistency"), self.t("consistency_sub"), rows, lambda d: d.spread or 0,
                  lambda d: f"± {d.spread:.2f} s   {typical} {lap_text(d.pace or 0)}", self.t("seconds"), 1.4)  # fmt: skip

    def best(self) -> None:
        rows = sorted((d for d in self.race.drivers if d.best), key=lambda d: d.best or 0)
        first = (rows[0].best or 0) if rows else 0
        self.bars("11-best-lap", self.t("best_title"), self.t("best_sub"), rows, lambda d: ((d.best or 0) - first) / 1000,
                  lambda d: f"{lap_text(d.best or 0)}  +{((d.best or 0) - first) / 1000:.3f}", self.t("seconds"))  # fmt: skip

    def ideal(self) -> None:
        rows = sorted((d for d in self.race.drivers if d.ideal and d.best), key=lambda d: d.ideal or 0)
        first = (rows[0].ideal or 0) if rows else 0
        self.bars("13-ideal-lap", self.t("ideal"), self.t("ideal_sub"), rows, lambda d: ((d.ideal or 0) - first) / 1000,
                  lambda d: f"{lap_text(d.ideal or 0)}  Δ {((d.best or 0) - (d.ideal or 0)) / 1000:.3f}",
                  self.t("seconds"))  # fmt: skip

    def limits(self) -> None:
        rows = sorted(self.race.drivers, key=lambda d: -d.invalid)
        if any(d.invalid for d in rows):
            self.bars("14-invalid-laps", self.t("limits"), self.t("limits_sub"), rows, lambda d: d.invalid,
                      lambda d: str(d.invalid), self.t("limits"), 1.1, True)  # fmt: skip

    def sectors(self) -> None:
        found = [(d, s) for d in self.race.drivers if (s := d.sectors)]
        if not found:
            return
        height = max(6, 0.42 * len(found) + 3)
        fig, axes = self.figure(self.t("sectors"), self.t("sectors_sub"), 22, height, ncols=3)
        fig.subplots_adjust(left=0.11, right=0.97, wspace=0.6)
        for k, ax in enumerate(axes):
            rows = sorted(found, key=lambda row: row[1][k])
            gaps = [(s[k] - rows[0][1][k]) / 1000 for _, s in rows]
            top = max(gaps) or 1
            ax.barh(range(len(rows)), gaps, color=[d.color for d, _ in rows], height=0.66)
            for y, (_, s) in enumerate(rows):
                ax.text(gaps[y] + top * 0.02, y, f"{s[k] / 1000:.3f}", va="center", fontsize=10, family=MONO)
            self.names(ax, [d for d, _ in rows], [short(d.name) for d, _ in rows])
            ax.set_ylim(len(rows) - 0.4, -0.6)
            ax.set_xlim(0, top * 1.3)
            ax.set_title(self.t("sector", n=k + 1), loc="left", fontsize=15)
            ax.set_xlabel(self.t("seconds"))
            ax.grid(axis="x", alpha=0.4)
        self.legend(fig)
        self.save(fig, "15-sectors")

    def distribution(self) -> None:
        rows = sorted((d for d in self.race.drivers if len(d.clean) >= 5), key=lambda d: d.pace or 0)
        if not rows:
            return
        fig, ax = self.figure(self.t("spread"), self.t("spread_sub"), 18, max(6, 0.45 * len(rows) + 3))
        fig.subplots_adjust(left=0.18, right=0.96)
        for y, d in enumerate(rows):
            line = {"color": d.color, "lw": 1.6}
            ax.boxplot(
                [[v / 1000 for _, v in d.clean]], orientation="horizontal", positions=[y], widths=0.6, showfliers=False,
                patch_artist=True, manage_ticks=False, whiskerprops=line, capprops=line,
                boxprops={"facecolor": d.color, "edgecolor": d.color}, medianprops={"color": BG, "lw": 2.5},
            )  # fmt: skip
        ax.set_ylim(len(rows) - 0.4, -0.6)
        self.names(ax, rows, [f"P{d.position}  {short(d.name)}" for d in rows])
        ax.xaxis.set_major_formatter(self.laptime)
        every(ax, "x", 1, ax.get_xlim()[1] - ax.get_xlim()[0])
        ax.set_xlabel(self.t("lap_time"))
        ax.grid(axis="x", alpha=0.6)
        self.legend(fig)
        self.save(fig, "16-pace-distribution")

    def timesheet(self) -> None:
        first = self.race.drivers[0]

        def cells(d: Driver) -> list[tuple[str, str]]:
            gap = f"+{(d.best - first.best) / 1000:.3f}" if d.best and first.best and d is not first else "—"
            return [(str(d.laps), TEXT), self.best_cell(d), (gap, TEXT)]

        columns = self.columns((0.6, self.t("laps")), (0.7, self.t("best")), (0.85, self.t("gap")))
        self.table("01-result", self.t("result"), self.t("cars", cars=len(self.race.drivers)), columns, cells)

    def laps_done(self) -> None:
        rows = sorted(self.race.drivers, key=lambda d: -d.laps)
        self.bars(
            "02-laps", self.t("laps_done"), "", rows, lambda d: d.laps, lambda d: str(d.laps), self.t("lap"), 1.1, True
        )

    def draw(self) -> list[Path]:
        if self.race.kind == "R":
            steps = [
                self.result, self.gained, self.start, self.trace, self.stints, self.top5, self.by_class, self.battles,
                self.pits, self.consistency, self.best, self.order, self.ideal, self.limits, self.sectors,
                self.distribution,
            ]  # fmt: skip
        else:
            steps = [self.timesheet, self.best, self.ideal, self.sectors, self.limits]
            if self.race.kind == "FP":
                steps += [self.laps_done, self.consistency, self.distribution]
        self.out.mkdir(parents=True, exist_ok=True)
        with plt.rc_context(STYLE):
            for step in steps:
                step()
        return sorted(self.out.glob("[0-9][0-9]-*.png"))
