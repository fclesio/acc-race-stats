"""Makes the logos in src/acc_race_stats/logos from a folder of Simple Icons SVG files (CC0).

uv run --with svgelements python tools/build_logos.py FOLDER
Brands without an SVG get their name, in a canvas of the same size.
"""

import re
import sys
from pathlib import Path

import matplotlib
import svgelements as svg

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path as Outline
from matplotlib.transforms import Affine2D

OUT = Path(__file__).parent.parent / "src" / "acc_race_stats" / "logos"
# brand colors that read well on the dark background of the charts
COLORS = {
    "Alpine": "#3a9bff", "Aston": "#00a383", "Audi": "#d5d9de", "BMW": "#2f7fe6", "Bentley": "#5aa47a",
    "Chevrolet": "#e0b21f", "Ferrari": "#ffd400", "Ford": "#3a78d8", "Ginetta": "#d5d9de", "Honda": "#e40521",
    "Jaguar": "#7fb08c", "KTM": "#ff6600", "Lamborghini": "#e0b21f", "Lexus": "#d5d9de", "Maserati": "#6f9fe0",
    "McLaren": "#ff8000", "Mercedes": "#a8b0b8", "Nissan": "#f0244f", "Porsche": "#c9a13b",
}  # fmt: skip
FILES = {"Aston": "astonmartin"}
WIDTH, HEIGHT = 1.7, 1.0


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
    source = Path(sys.argv[1]) / f"{FILES.get(brand, brand.lower())}.svg"
    if source.exists():
        path = parse_path(re.search(r'<path[^>]* d="([^"]+)"', source.read_text())[1])
        box = path.get_extents()
        scale = min((WIDTH - 0.04) / box.width, (HEIGHT - 0.04) / box.height)
        move = Affine2D().translate(-(box.x0 + box.x1) / 2, -(box.y0 + box.y1) / 2).scale(scale, -scale)
        move.translate(WIDTH / 2, HEIGHT / 2)
        ax.add_patch(PathPatch(move.transform_path(path), fc=color, lw=0))
    else:
        ax.text(
            WIDTH / 2, HEIGHT / 2, brand.upper(), color=color, ha="center", va="center", fontsize=19, fontweight="bold"
        )
    fig.savefig(OUT / f"{brand.lower()}.png", dpi=200, transparent=True)
    plt.close(fig)
