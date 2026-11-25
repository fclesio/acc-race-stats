"""Static Assetto Corsa Competizione data: cars, tracks and classes."""

NO_TIME = 2**31 - 1

CARS = {
    0: "Porsche 991 GT3 R",
    1: "Mercedes-AMG GT3",
    2: "Ferrari 488 GT3",
    3: "Audi R8 LMS",
    4: "Lamborghini Huracán GT3",
    5: "McLaren 650S GT3",
    6: "Nissan GT-R Nismo GT3 (2018)",
    7: "BMW M6 GT3",
    8: "Bentley Continental GT3 (2018)",
    9: "Porsche 991 II GT3 Cup",
    10: "Nissan GT-R Nismo GT3 (2017)",
    11: "Bentley Continental GT3 (2016)",
    12: "Aston Martin V12 Vantage GT3",
    13: "Lamborghini Gallardo R-EX",
    14: "Jaguar G3",
    15: "Lexus RC F GT3",
    16: "Lamborghini Huracán Evo",
    17: "Honda NSX GT3",
    18: "Lamborghini Huracán ST",
    19: "Audi R8 LMS Evo",
    20: "Aston Martin V8 Vantage",
    21: "Honda NSX Evo",
    22: "McLaren 720S",
    23: "Porsche 991 II GT3 R",
    24: "Ferrari 488 GT3 Evo",
    25: "Mercedes-AMG GT3 Evo",
    26: "Ferrari 488 Challenge Evo",
    27: "BMW M2 CS Racing",
    28: "Porsche 992 GT3 Cup",
    29: "Lamborghini Huracán ST Evo2",
    30: "BMW M4 GT3",
    31: "Audi R8 LMS Evo II",
    32: "Ferrari 296 GT3",
    33: "Lamborghini Huracán Evo2",
    34: "Porsche 992 GT3 R",
    35: "McLaren 720S Evo",
    36: "Ford Mustang GT3",
    50: "Alpine A110 GT4",
    51: "Aston Martin Vantage GT4",
    52: "Audi R8 LMS GT4",
    53: "BMW M4 GT4",
    55: "Chevrolet Camaro GT4",
    56: "Ginetta G55 GT4",
    57: "KTM X-Bow GT4",
    58: "Maserati MC GT4",
    59: "McLaren 570S GT4",
    60: "Mercedes-AMG GT4",
    61: "Porsche 718 Cayman GT4",
    80: "Audi R8 LMS GT2",
    82: "KTM X-Bow GT2",
    83: "Maserati MC20 GT2",
    84: "Mercedes-AMG GT2",
    85: "Porsche 911 GT2 RS CS Evo",
    86: "Porsche 935",
}

# Console results reuse some ids for other cars; the car group tells them apart.
CONSOLE_GT3 = {26: "BMW M4 GT3"}

BRANDS = {
    "Ferrari": "#c8102e",
    "McLaren": "#ff8000",
    "Porsche": "#8a6d3b",
    "BMW": "#1c69d4",
    "Ford": "#133a7c",
    "Audi": "#6b6f75",
    "Lamborghini": "#9c8a1b",
    "Aston": "#00665e",
    "Honda": "#cc0000",
    "Mercedes": "#3a3f44",
    "Nissan": "#8b0000",
    "Lexus": "#2b2b2b",
    "Bentley": "#1f4d3a",
    "Jaguar": "#2e5e3e",
    "Alpine": "#0055a4",
    "Chevrolet": "#d1a000",
    "Ginetta": "#555",
    "KTM": "#ff6600",
    "Maserati": "#0c2340",
}

TRACKS = {
    "barcelona": "Barcelona",
    "brands_hatch": "Brands Hatch",
    "cota": "COTA",
    "donington": "Donington",
    "hungaroring": "Hungaroring",
    "imola": "Imola",
    "indianapolis": "Indianapolis",
    "kyalami": "Kyalami",
    "laguna_seca": "Laguna Seca",
    "misano": "Misano",
    "monza": "Monza",
    "mount_panorama": "Mount Panorama",
    "nurburgring": "Nürburgring",
    "nurburgring_24h": "Nordschleife",
    "oulton_park": "Oulton Park",
    "paul_ricard": "Paul Ricard",
    "red_bull_ring": "Red Bull Ring",
    "silverstone": "Silverstone",
    "snetterton": "Snetterton",
    "spa": "Spa-Francorchamps",
    "suzuka": "Suzuka",
    "valencia": "Valencia",
    "watkins_glen": "Watkins Glen",
    "zandvoort": "Zandvoort",
    "zolder": "Zolder",
}

CUP_CATEGORIES = {0: "PRO", 1: "PRO-AM", 2: "AM", 3: "SILVER", 4: "NATIONAL"}
CLASS_ORDER = list(CUP_CATEGORIES.values())


def car_name(model: int, group: str = "") -> str:
    if group == "GT3" and model in CONSOLE_GT3:
        return CONSOLE_GT3[model]
    return CARS.get(model, f"car {model}")


def track_name(track_id: str) -> str:
    return TRACKS.get(track_id, track_id.replace("_", " ").title())


def brand_color(car: str) -> str:
    return next((color for brand, color in BRANDS.items() if car.startswith(brand)), "#777777")
