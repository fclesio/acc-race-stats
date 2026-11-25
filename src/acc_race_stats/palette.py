"""Driver colors: by class, or one color per driver."""

from __future__ import annotations

import colorsys

from .race import Race

CLASS_COLORS = {
    "PRO": "#ffffff", "PRO-AM": "#949494", "AM": "#e83323", "PLATINUM": "#7fe3ee", "GOLD": "#f5c542",
    "SILVER": "#b9c6d8", "BRONZE": "#cd7f32", "NATIONAL": "#c77dff",
}  # fmt: skip
FALLBACK = ["#4da3ff", "#ff8a1f", "#3ddc84", "#c77dff", "#f5c542", "#ff5d5d"]
DISTINCT = [
    "#4da3ff", "#ff8a1f", "#3ddc84", "#ff5d5d", "#c77dff", "#f5c542", "#4fd6e8", "#ff7eb6", "#b5e655", "#c8a27c",
]  # fmt: skip


def driver_palette(count: int) -> list[str]:
    """Distinct colors that stay readable on the dark background; the first ten are hand-picked."""
    colors = DISTINCT[:count]
    for n in range(count - len(colors)):
        hue = (0.07 + n * 0.618034) % 1
        red, green, blue = colorsys.hls_to_rgb(hue, (0.62, 0.74, 0.54)[n % 3], (0.75, 0.6, 0.5)[n % 3])
        colors.append(f"#{round(red * 255):02x}{round(green * 255):02x}{round(blue * 255):02x}")
    return colors


def class_color(race: Race, name: str, overrides: dict[str, str] | None = None) -> str:
    unknown = [c for c in race.classes if c not in CLASS_COLORS]
    return (
        (overrides or {}).get(name) or CLASS_COLORS.get(name)
        or FALLBACK[unknown.index(name) % len(FALLBACK)]
    )  # fmt: skip


def apply_colors(race: Race, mode: str = "auto", overrides: dict[str, str] | None = None) -> str:
    """Sets the color of every driver and returns the mode used ('class' or 'driver')."""
    if mode == "auto":
        mode = "class" if len(race.classes) > 1 else "driver"
    for driver, color in zip(race.drivers, driver_palette(len(race.drivers)), strict=True):
        driver.color = driver.custom_color or (
            class_color(race, driver.driver_class, overrides) if mode == "class" else color
        )
    return mode
