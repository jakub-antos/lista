import re
from unidecode import unidecode

# Kolejność wyświetlania grup
GROUP_ORDER = [
    "Popularne", "Sport", "Film", "Muzyka", "Informacje", "Dokumenty", "Dla Dzieci", "Rozrywka"
]

# Specjalne wyjątki od użytkownika
EXACT_OVERRIDES = {
    "nuta tv": "Muzyka",
    "tele5": "Popularne",
    "tlc": "Film",
    "tvp info": "Informacje",
}

# Priorytetowa kolejność w Popularnych (kanal, który ma mieć wyżej, świadomość polskich nazw)
POPULARNE_PRIORITY = ["tvp1", "tvp 1", "tvp2", "tvp 2", "polsat", "tvn"]

# Rozbudowany słownik kanałów i grup (oparty na analizie tematyki kanału)
EXACT_GROUPS = {
    # Sport
    "polsat sport": "Sport", "canal+ sport": "Sport", "canal plus sport": "Sport",
    "eleven sports": "Sport", "eurosport": "Sport", "sportklub": "Sport",
    # Film i rozrywka
    "axn": "Film", "axn spin": "Film", "axn white": "Film",
    "kino polska": "Film", "13 ulica": "Film", "stopklatka": "Film",
    "tvp seriale": "Film", "film box": "Film", "canal+ film": "Film", "hbo": "Film",
    "tlc": "Film", "film europe": "Film", "ale kino+": "Film",
    # Dla dzieci
    "mini mini": "Dla Dzieci", "minimini": "Dla Dzieci",
    "babytv": "Dla Dzieci", "baby tv": "Dla Dzieci", "nickelodeon": "Dla Dzieci", "nick jr": "Dla Dzieci", "cartoon network": "Dla Dzieci",
    "4fun kids": "Dla Dzieci",
    # Muzyka
    "4fun": "Muzyka", "4fun.tv": "Muzyka", "4 fun": "Muzyka",
    "eska tv": "Muzyka", "mtv": "Muzyka", "vox music tv": "Muzyka", "polo tv": "Muzyka",
    "power tv": "Muzyka", "trace urban": "Muzyka", "nuta tv": "Muzyka", "stars.tv": "Muzyka",
    # Informacje
    "tvp info": "Informacje", "tvn24": "Informacje", "polsat news": "Informacje",
    "bbc news": "Informacje", "cnn": "Informacje",
    "al jazeera": "Informacje", "euronews": "Informacje", "wpolsce.pl": "Informacje", "trwam": "Informacje",
    # Dokumenty
    "discovery channel": "Dokumenty", "discovery science": "Dokumenty", "investigation discovery": "Dokumenty",
    "nat geo": "Dokumenty", "national geographic": "Dokumenty",
    "bbc earth": "Dokumenty", "animal planet": "Dokumenty", "focus tv": "Dokumenty", "polsat play": "Dokumenty",
    "planete+": "Dokumenty", "history": "Dokumenty",
    # Popularne i rozrywka
    "tvp1": "Popularne", "tvp 1": "Popularne",
    "tvp2": "Popularne", "tvp 2": "Popularne",
    "polsat": "Popularne", "tvn": "Popularne", "tv4": "Popularne",
    "tv puls": "Popularne", "super polsat": "Popularne", "tele5": "Popularne",
    "wp tv": "Rozrywka", "active family": "Rozrywka", "zoom tv": "Rozrywka", "bbc brit": "Rozrywka",
    "bbc entertainment": "Rozrywka", "paramount network": "Rozrywka", "superstacja": "Rozrywka",
}

# Fallback grupy (szersze dopasowanie po kluczach)
KEYWORD_GROUPS = [
    ("sport", "Sport"),
    ("film", "Film"), ("cinema", "Film"), ("kino", "Film"), ("serial", "Film"),
    ("music", "Muzyka"), ("muzyka", "Muzyka"),
    ("kids", "Dla Dzieci"), ("dzieci", "Dla Dzieci"), ("baby", "Dla Dzieci"),
    ("news", "Informacje"), ("info", "Informacje"),
    ("dokument", "Dokumenty"), ("discovery", "Dokumenty"), ("animal", "Dokumenty"), ("geo", "Dokumenty"),
    ("rozrywka", "Rozrywka"), ("entertainment", "Rozrywka"), ("family", "Rozrywka"),
    ("puls", "Popularne"), ("tvp", "Popularne"), ("tvn", "Popularne"), ("polsat", "Popularne"),
]

def assign_group(ch_name):
    name = unidecode(ch_name.lower().strip())
    # Najpierw najważniejsze wyjątki od użytkownika:
    for k in EXACT_OVERRIDES:
        if k in name:
            return EXACT_OVERRIDES[k]
    # Kanały 4fun: "4fun kids" => Dla Dzieci, "4fun" => Muzyka
    if "4fun" in name and "kids" in name:
        return "Dla Dzieci"
    if "4fun" in name:
        return "Muzyka"
    # Kanały AXN zawsze do Film
    if name.startswith("axn"):
        return "Film"
    # Inne wyjątki precyzyjne:
    for k in EXACT_GROUPS:
        if k in name:
            return EXACT_GROUPS[k]
    # Klucz ogólny po słowie
    for kw, group in KEYWORD_GROUPS:
        if kw in name:
            return group
    # Domyślnie rozrywka
    return "Rozrywka"

with open("IPTV2024.m3u", "r", encoding="utf-8") as fin, open("IPTV2024_grouped.m3u", "w", encoding="utf-8") as fout:
    fout.write("#EXTM3U\n")
    lines = fin.readlines()
    temp_channels = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF"):
            # Nazwa kanału po przecinku
            match = re.search(r",(.*)", line)
            ch_name = match.group(1).strip() if match else ""
            group = assign_group(ch_name)
            # Wyczyść stare group-title, jeśli istnieje
            new_line = re.sub(r'group-title=\"[^\"]*\"', '', line)
            new_line = re.sub(r'\s+,', ',', new_line)
            parts = new_line.split(',', 1)
            parts[0] += f' group-title="{group}"'
            new_line = ','.join(parts)
            # URL, zakładamy standard: po #EXTINF zawsze url w next line
            url = lines[i+1].strip() if (i+1) < len(lines) and lines[i+1].strip() else ""
            temp_channels.append((group, ch_name, new_line, url))
            i += 2
        else:
            i += 1

    # Grupowanie i sortowanie: Popularne wyżej, z priorytetem TVP1, TVP2, Polsat, TVN
    group_map = {g: [] for g in GROUP_ORDER}
    leftovers = []
    for group, name, meta, url in temp_channels:
        if group in group_map:
            group_map[group].append((name, meta, url))
        else:
            leftovers.append((name, meta, url))

    def pop_priority(x):
        n = x[0].lower()
        for idx, pat in enumerate(POPULARNE_PRIORITY):
            if pat == n or pat in n:
                return idx
        return 1000
    popular = sorted(group_map["Popularne"], key=pop_priority)
    group_map["Popularne"] = popular

    # Złóż output
    for group in GROUP_ORDER:
        for name, meta, url in group_map[group]:
            fout.write(f"{meta}\n")
            fout.write(f"{url}\n")
    for name, meta, url in leftovers:
        fout.write(f"{meta}\n")
        fout.write(f"{url}\n")
