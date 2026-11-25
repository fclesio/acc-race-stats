"""Makes the logo tiles in src/acc_race_stats/logos from a folder of Simple Icons SVG files (CC0).

uv run --with svgelements python tools/build_logos.py FOLDER
Brands without an SVG get a tile with their name, in the same size.
"""

import re
import sys
from pathlib import Path

import matplotlib
import svgelements as svg

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, PathPatch
from matplotlib.path import Path as Outline
from matplotlib.transforms import Affine2D

OUT = Path(__file__).parent.parent / "src" / "acc_race_stats" / "logos"
COLORS = {
    "Alpine": "#0055a4", "Aston": "#00665e", "Audi": "#1b1b1b", "BMW": "#1c69d4", "Bentley": "#1f4d3a",
    "Chevrolet": "#b58900", "Ferrari": "#c8102e", "Ford": "#133a7c", "Ginetta": "#333333", "Honda": "#cc0000",
    "Jaguar": "#1e3b2a", "KTM": "#ff6600", "Lamborghini": "#8a7510", "Lexus": "#1b1b1b", "Maserati": "#0c2340",
    "McLaren": "#ff8000", "Mercedes": "#2b2f33", "Nissan": "#8b0000", "Porsche": "#7a5c2c",
}  # fmt: skip
FILES = {"Aston": "astonmartin"}
WIDTH, HEIGHT = 1.5, 1.0


def parse_path(text: str) -> Outline:
    path = svg.Path(text)
    path.approximate_arcs_with_cubics()
    points, codes = [], []
    for part in path:
        if isinstance(part, svg.Move):
            new, kind = [part.end], Outline.MOVETO
        elif isinstance(part, svg.CubicBezier):
            new, kind = [part.control1, part.control2, part.end], Outline.CURVE4
        elif isinstance(part, svg.QuadraticBezier):
            new, kind = [part.control, part.end], Outline.CURVE3
        else:
            new, kind = [part.end], Outline.CLOSEPOLY if isinstance(part, svg.Close) else Outline.LINETO
        points += [(p.x, p.y) for p in new]
        codes += [kind] * len(new)
    return Outline(points, codes)


for brand, color in COLORS.items():
    fig = plt.figure(figsize=(WIDTH, HEIGHT))
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set(xlim=(0, WIDTH), ylim=(0, HEIGHT))
    ax.axis("off")
    tile = FancyBboxPatch((0.16, 0.16), WIDTH - 0.32, HEIGHT - 0.32, boxstyle="round,pad=.14", fc="#f4f5f7", lw=0)
    ax.add_patch(tile)
    source = Path(sys.argv[1]) / f"{FILES.get(brand, brand.lower())}.svg"
    if source.exists():
        path = parse_path(re.search(r'<path[^>]* d="([^"]+)"', source.read_text())[1])
        box = path.get_extents()
        scale = min((WIDTH - 0.28) / box.width, (HEIGHT - 0.24) / box.height)
        move = Affine2D().translate(-(box.x0 + box.x1) / 2, -(box.y0 + box.y1) / 2).scale(scale, -scale)
        move.translate(WIDTH / 2, HEIGHT / 2)
        ax.add_patch(PathPatch(move.transform_path(path), fc=color, lw=0))
    else:
        ax.text(
            WIDTH / 2, HEIGHT / 2, brand.upper(), color=color, ha="center", va="center", fontsize=15, fontweight="bold"
        )
    fig.savefig(OUT / f"{brand.lower()}.png", dpi=128, transparent=True)
    plt.close(fig)
