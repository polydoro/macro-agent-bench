"""Read INE (Spain) tempus3 JSON series saved by agents: one series dict or a list of them."""
import json


def series(path):
    """[(cod, name, {period 'YYYY-MM': value})]"""
    try:
        d = json.load(open(path))
    except Exception:
        return []
    items = d if isinstance(d, list) else [d]
    out = []
    for s in items:
        if not (isinstance(s, dict) and 'Data' in s and 'Nombre' in s):
            continue
        pts = {}
        for p in s['Data'] or []:
            if p.get('Valor') is None or not p.get('FK_Periodo') or p['FK_Periodo'] > 12:
                continue
            pts[f"{p['Anyo']:04d}-{p['FK_Periodo']:02d}"] = float(p['Valor'])
        out.append((s.get('COD'), ' '.join(s['Nombre'].split()), pts))
    return out
