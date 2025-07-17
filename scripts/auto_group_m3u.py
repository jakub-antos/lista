import re
from unidecode import unidecode

GROUP_ORDER = [
    "Popularne", "Sport", "Film", "Muzyka", "Informacje", "Dokumenty", "Dla Dzieci", "Rozrywka"
]

EXACT_OVERRIDES = {
    "nuta tv": "Muzyka",
    "tele5": "Popularne",
    "tlc": "Film",
    "tvp info": "Informacje",
}
POPULARNE_PRIORITY = ["tvp1", "tvp2", "polsat", "tvn"]

EXACT_GROUPS = {
    "polsat sport": "Sport", "canal+ sport": "Sport", "eleven sports": "Sport", "eurosport": "Sport", "sportklub": "Sport",
    "axn": "Film", "axn white": "Film", "axn spin": "Film", "kino polska": "Film", "13 ulica": "Film", "stopklatka": "Film", "tvp seriale": "Film", "film box": "Film", "canal+ film": "Film", "hbo": "Film",
    "mini mini": "Dla Dzieci", "babytv": "Dla Dzieci", "baby tv": "Dla Dzieci", "nickelodeon": "Dla Dzieci", "nick jr": "Dla Dzieci", "cartoon network": "Dla Dzieci", "4fun kids": "Dla Dzieci",
    "4fun": "Muzyka", "eska tv": "Muzyka", "mtv": "Muzyka", "vox music": "Muzyka", "polo tv": "Muzyka", "power tv": "Muzyka", "trace urban": "Muzyka", "nuta tv": "Muzyka",
    "tvp info": "Informacje", "tvn24": "Informacje", "polsat news": "Informacje", "bbc news": "Informacje", "cnn": "Informacje", "al jazeera": "Informacje", "euronews": "Informacje", "wpolsce.pl": "Informacje",
    "discovery channel": "Dokumenty", "discovery science": "Dokumenty", "nat geo": "Dokumenty", "national geographic": "Dokumenty", "bbc earth": "Dokumenty", "animal planet": "Dokumenty", "focus tv": "Dokumenty", "polsat play": "Dokumenty",
    "tvp1": "Popularne", "tvp 1": "Popularne", "tvp2": "Popularne", "tvp 2": "Popularne", "polsat": "Popularne", "tvn": "Popularne", "tv4": "Popularne", "tv puls": "Popularne", "super polsat": "Popularne",
    "bbc brit": "Rozrywka", "bbc entertainment": "Rozrywka", "wp tv": "Rozrywka", "active family": "Rozrywka", "zoom tv": "Rozrywka", "paramount network": "Rozrywka", "tele5": "Popularne",
}
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
    for k in EXACT_OVERRIDES:
        if k in name:
            return EXACT_OVERRIDES[k]
    if "4fun" in name and "kids" in name:
        return "Dla Dzieci"
    if "4fun" in name:
        return "Muzyka"
    if name.startswith("axn"):
        return "Film"
    for k in EXACT_GROUPS:
        if k in name:
            return EXACT_GROUPS[k]
    for kw, group in KEYWORD_GROUPS:
        if kw in name:
            return group
    return "Rozrywka"

with open("IPTV2024.m3u", "r", encoding="utf-8") as fin, open("IPTV2024_grouped.m3u", "w", encoding="utf-8") as fout:
    fout.write("#EXTM3U\n")
    lines = fin.readlines()
    temp_channels = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF"):
            match = re.search(r",(.*)", line)
            ch_name = match.group(1).strip() if match else ""
            group = assign_group(ch_name)
            new_line = re.sub(r'group-title=\"[^\"]*\"', '', line)
            new_line = re.sub(r'\s+,', ',', new_line)
            parts = new_line.split(',', 1)
            parts[0] += f' group-title="{group}"'
            new_line = ','.join(parts)
            url = lines[i+1].strip() if (i+1) < len(lines) and lines[i+1].strip() else ""
            temp_channels.append((group, ch_name, new_line, url))
            i += 2
        else:
            i += 1

    # Grupowanie i sortowanie: Popularne wyżej, a w Popularne TVP1, TVP2, Polsat, TVN na górze
    group_map = {g: [] for g in GROUP_ORDER}
    leftovers = []
    for group, name, meta, url in temp_channels:
        if group in group_map:
            group_map[group].append((name, meta, url))
        else:
            leftovers.append((name, meta, url))

    # Sortuj Popularne wg własnej kolejności, resztę alfabet.
    def pop_priority(x):
        n = x[0].lower()
        for idx, pat in enumerate(POPULARNE_PRIORITY):
