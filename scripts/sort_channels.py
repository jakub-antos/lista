def sort_channels(input_path, output_path):
    # Parsuj do struktur: [ (group, [kanały]) ]
    with open(input_path, "r", encoding="utf-8") as fin:
        lines = fin.readlines()
    channels = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("#EXTINF"):
            meta = lines[i]
            url = lines[i+1] if (i+1)<len(lines) else ""
            m = re.search(r'group-title="([^"]+)"', meta)
            group = m.group(1) if m else "Rozrywka"
            n = re.search(r',(.+)', meta)
            name = n.group(1).strip() if n else ""
            channels.append( (group, name, meta, url) )
            i += 2
        else:
            i += 1
    # Grupuj wg kolejności GROUP_ORDER
    groups_sorted = {g: [] for g in GROUP_ORDER}
    leftovers = []
    for group, name, meta, url in channels:
        if group in groups_sorted:
            groups_sorted[group].append( (name, meta, url) )
        else:
            leftovers.append( (name, meta, url) )
    # Sortuj Popularne wg priorytetu użytkownika
    popular = groups_sorted["Popularne"]
    def pop_order(x):
        n = x[0].lower()
        for idx, nm in enumerate(POPULARNE_PRIORITY):
            if nm in n:
                return idx
        return 1000  # poza priorytetem
    popular = sorted(popular, key=pop_order)
    groups_sorted["Popularne"] = popular
    # Złóż plik na nowo
    with open(output_path, "w", encoding="utf-8") as fout:
        fout.write("#EXTM3U\n")
        for group in GROUP_ORDER:
            for name, meta, url in groups_sorted[group]:
                fout.write(meta)
                if not meta.endswith("\n"):
                    fout.write("\n")
                fout.write(url)
                if not url.endswith("\n"):
                    fout.write("\n")
        # Reszta
        for name, meta, url in leftovers:
            fout.write(meta)
            if not meta.endswith("\n"):
                fout.write("\n")
            fout.write(url)
            if not url.endswith("\n"):
                fout.write("\n")
