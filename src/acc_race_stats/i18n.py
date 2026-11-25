"""Text shown in charts and reports. Brazilian Portuguese is the default; code and CLI are in English."""

from __future__ import annotations

from collections.abc import Callable

Translate = Callable[..., str]

# key: (pt-br, en)
TEXT: dict[str, tuple[str, str]] = {
    "R": ("Corrida", "Race"),
    "Q": ("Classificação", "Qualifying"),
    "FP": ("Treino livre", "Free practice"),
    "source": ("dados do servidor ACC", "data from the ACC server"),
    "result": ("Resultado", "Result"),
    "result_sub": ("{cars} carros · {laps} voltas", "{cars} cars · {laps} laps"),
    "cars": ("{cars} carros", "{cars} cars"),
    "driver": ("PILOTO", "DRIVER"),
    "class": ("CLASSE", "CLASS"),
    "car": ("CARRO", "CAR"),
    "laps": ("VOLTAS", "LAPS"),
    "time": ("TEMPO / GAP", "TIME / GAP"),
    "best": ("MELHOR VOLTA", "BEST LAP"),
    "grid": ("GRID", "GRID"),
    "gap": ("DIFERENÇA", "GAP"),
    "retired": ("abandono", "retired"),
    "one_lap": ("+1 volta", "+1 lap"),
    "n_laps": ("+{n} voltas", "+{n} laps"),
    "gained": ("Posições ganhas e perdidas", "Positions gained and lost"),
    "gained_sub": ("posição no grid − posição final", "grid position − final position"),
    "start": ("Largada", "Race start"),
    "start_sub": ("posição no grid − posição ao fim da volta 1", "grid position − position at the end of lap 1"),
    "positions": ("posições", "positions"),
    "position": ("posição", "position"),
    "lap": ("volta", "lap"),
    "seconds": ("segundos", "seconds"),
    "lap_time": ("tempo de volta", "lap time"),
    "trace": ("Diferença para o vencedor", "Gap to the winner"),
    "trace_sub": (
        "tempo acumulado − voltas × volta média do vencedor ({ref}) · acima = à frente",
        "race time − laps × winner's average lap ({ref}) · higher = ahead",
    ),
    "trace_note": (
        "nomes: top 12 · linhas grossas: top 6 · cortado em −120 s",
        "names: top 12 · thick lines: top 6 · cut at −120 s",
    ),
    "stints": ("Stints e paradas", "Stints and pit stops"),
    "stints_sub": (
        "cada barra é um stint entre paradas · X = punição cumprida",
        "each bar is a stint between stops · X = penalty served",
    ),
    "top5": ("Ritmo do top 5", "Top 5 pace"),
    "clean_sub": ("voltas limpas, sem largada e paradas", "clean laps, without start and stops"),
    "by_class": ("Ritmo por classe", "Pace by class"),
    "by_class_sub": (
        "top 3 de cada classe · voltas limpas, média móvel de 3 voltas",
        "top 3 of each class · clean laps, 3-lap moving average",
    ),
    "battles": ("Batalhas", "Battles"),
    "battles_sub": (
        "duplas com mais voltas a menos de 1 s · acima de 0: o primeiro nome está à frente",
        "pairs with most laps less than 1 s apart · above 0: the first name is ahead",
    ),
    "battle_laps": ("{n} voltas a menos de 1 s", "{n} laps less than 1 s apart"),
    "pits": ("Paradas no box", "Pit stops"),
    "pits_sub": (
        "primeira parada · de quem mais ganhou para quem mais perdeu posições",
        "first stop · from most positions gained to most lost",
    ),
    "pits_pos": (
        "Posição antes de parar → depois que todos pararam",
        "Position before stopping → after everyone stopped",
    ),
    "pits_loss": ("Tempo perdido na parada", "Time lost in the stop"),
    "pits_loss_axis": (
        "segundos (3 voltas da parada − 3 voltas típicas)",
        "seconds (3 laps of the stop − 3 typical laps)",
    ),
    "pitted": ("parou na volta {n}", "stopped on lap {n}"),
    "consistency": ("Consistência", "Consistency"),
    "consistency_sub": (
        "distância média das voltas limpas para a volta típica do piloto · menor = mais regular",
        "average distance of the clean laps to the driver's typical lap · lower = steadier",
    ),
    "typical": ("volta típica", "typical lap"),
    "best_title": ("Melhor volta", "Best lap"),
    "best_sub": ("diferença para a volta mais rápida", "gap to the fastest lap"),
    "order": ("Posições volta a volta", "Lap by lap positions"),
    "order_sub": (
        "posição na pista ao cruzar a linha · volta 0 = grid · nomes no resultado final",
        "position on track at the line · lap 0 = grid · names in final order",
    ),
    "ideal": ("Volta ideal", "Ideal lap"),
    "ideal_sub": (
        "soma dos melhores setores em voltas válidas · Δ = melhor volta − ideal",
        "sum of the best sectors in valid laps · Δ = best lap − ideal",
    ),
    "limits": ("Voltas invalidadas", "Invalid laps"),
    "limits_sub": ("sem a volta 1 e as voltas em torno das paradas", "without lap 1 and the laps around the stops"),
    "sectors": ("Melhores setores", "Best sectors"),
    "sectors_sub": ("melhor tempo em voltas válidas", "best time in valid laps"),
    "sector": ("Setor {n}", "Sector {n}"),
    "spread": ("Distribuição do ritmo", "Pace distribution"),
    "spread_sub": (
        "voltas limpas · caixa = metade central · traço = mediana",
        "clean laps · box = middle half · line = median",
    ),
    "laps_done": ("Voltas completadas", "Laps completed"),
    "fastest": ("Volta mais rápida", "Fastest lap"),
    "pole": ("Pole", "Pole"),
    "best_pace": ("Melhor ritmo", "Best pace"),
    "steadiest": ("Mais regular", "Steadiest"),
    "climber": ("Maior escalada", "Biggest climb"),
    "battle": ("Disputa da corrida", "Battle of the race"),
    "class_winners": ("Vencedores por classe", "Class winners"),
    "penalties": ("Punições do jogo", "In-game penalties"),
}


def translator(lang: str) -> Translate:
    index = 1 if lang == "en" else 0

    def translate(key: str, **values: object) -> str:
        return TEXT[key][index].format(**values)

    return translate
