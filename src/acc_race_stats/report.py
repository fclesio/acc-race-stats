"""Written output: chat summary, race.json and a single-file HTML page."""

from __future__ import annotations

import base64
import html
import json
from pathlib import Path

from .charts import Charts, lap_text
from .i18n import Translate
from .race import Race


def summary(race: Race, t: Translate, mode: str) -> str:
    drivers = race.drivers
    lines = [f"🏁 *{race.title}* · {t(race.kind)}"]
    for medal, d in zip("🥇🥈🥉", drivers, strict=False):
        gap = ""
        if race.kind == "R" and d is not drivers[0] and d.laps == drivers[0].laps:
            gap = f" +{(d.total - drivers[0].total) / 1000:.3f}s"
        elif race.kind != "R" and d.best:
            gap = f" {lap_text(d.best)}"
        lines.append(f"{medal} {d.name} ({d.car}){gap}")
    if mode == "class" and len(race.classes) > 1:
        lines += ["", f"*{t('class_winners')}*"]
        lines += [f"{n}: {next(d.name for d in drivers if d.driver_class == n)}" for n in race.classes]
    lines.append("")
    if race.kind == "R":
        pole = next((d for d in drivers if d.grid == 1), None)
        if pole:
            lines.append(f"⏱️ {t('pole')}: {pole.name} (P{pole.position})")
    if race.fastest and race.fastest.best:
        lines.append(f"🟣 {t('fastest')}: {race.fastest.name} · {lap_text(race.fastest.best)}")
    if race.kind == "R":
        paced = [d for d in drivers if d.pace and len(d.clean) >= 8]
        if paced:
            quick = min(paced, key=lambda d: d.pace or 0)
            steady = min(paced, key=lambda d: d.spread or 0)
            lines.append(f"⚡ {t('best_pace')}: {quick.name} · {lap_text(quick.pace or 0)}")
            lines.append(f"🎯 {t('steadiest')}: {steady.name} · ± {steady.spread:.2f} s")
        climbers = [d for d in drivers if d.grid and not d.retired and d.grid > d.position]
        if climbers:
            best = max(climbers, key=lambda d: (d.grid or 0) - d.position)
            lines.append(f"🚀 {t('climber')}: {best.name} · P{best.grid} → P{best.position}")
        for a, b, n in race.battles(1):
            lines.append(f"⚔️ {t('battle')}: {a.name} × {b.name} · {t('battle_laps', n=n)}")
        fined = [d.name for d in drivers if d.penalties]
        if fined:
            lines.append(f"⚠️ {t('penalties')}: {', '.join(fined)}")
    return "\n".join(lines) + "\n"


PAGE = """<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>{title}</title><style>
body{{margin:0;background:#0a0b0d;color:#f4f5f7;font:16px/1.5 system-ui,sans-serif}}
main{{max-width:1200px;margin:auto;padding:32px 16px}}h1{{margin:0}}h2{{color:#8b929c;font-size:18px}}
pre{{background:#121418;padding:16px;border-radius:8px;white-space:pre-wrap;font:inherit}}
img{{width:100%;margin:0 0 24px;border-radius:8px}}li{{color:#f5c542}}
</style></head><body><main><h1>{title}</h1><h2>{kind}{date}</h2>{notes}
<h2>{summary_title}</h2><pre>{summary}</pre>{images}</main></body></html>
"""


def page(race: Race, t: Translate, lang: str, text: str, images: list[Path]) -> str:
    notes = ""
    if race.warnings:
        items = "".join(f"<li>{html.escape(w)}</li>" for w in race.warnings)
        notes = f"<h2>{t('notes')}</h2><ul>{items}</ul>"
    pictures = "".join(
        f'<img alt="{html.escape(p.stem)}" src="data:image/png;base64,{base64.b64encode(p.read_bytes()).decode()}">'
        for p in images
    )
    return PAGE.format(
        lang="en" if lang == "en" else "pt-BR", title=html.escape(race.title), kind=t(race.kind),
        date=f" · {race.when:%Y-%m-%d %H:%M}" if race.when else "", notes=notes, summary_title=t("summary"),
        summary=html.escape(text), images=pictures,
    )  # fmt: skip


def write(race: Race, out: Path, t: Translate, lang: str, mode: str) -> list[Path]:
    """Writes charts/, report.html, race.json and summary.txt."""
    charts = out / "charts"
    if charts.exists():  # charts of an earlier run in the same folder
        for old in charts.glob("[0-9][0-9]-*.png"):
            old.unlink()
    images = Charts(race, charts, t, mode).draw()
    text = summary(race, t, mode)
    (out / "summary.txt").write_text(text, encoding="utf-8")
    data = json.dumps(race.to_dict(), ensure_ascii=False, indent=1)
    (out / "race.json").write_text(data, encoding="utf-8")
    (out / "report.html").write_text(page(race, t, lang, text, images), encoding="utf-8")
    return images
