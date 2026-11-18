"""Extract each S05/S06 delivery's saved SA index or 3m SAAR series per component.

Reads every CSV the agent wrote (not raw downloads), in any of the shapes found:
pandas two-row headers, long tables (period + series column), wide tables with
'<series>_<measure>' names. Returns {component: {'kind': 'sa'|'saar', 'file', 'col', 'data'}}.
Labels are classified by keyword; the chosen file and column are reported for review.
"""
import csv
import os
import re

csv.field_size_limit(10 ** 9)

COMP = [  # order matters
    ("skip", r"serv(rec|tra|hous|msc|com)|totxnrg(?!_food)|alim_n?p\b|bens \(total\)|\| gd\b|comunica|ex_energia|nucleo_istat|ex-energia(?!.*alim)|food_?n?p\b|foodpr|foodun|process|tot_x_nrg(?!_food)|ex_?energia\b(?!.*alim)|total ex energia|elc|fuel|combust|eletric|gas\b|cp0[1-9]|cp1[0-2]|tot_x_nrg_food_s|supercore|aparada|mediana|domestica|pcci|unprocessed"),
    ("core", r"tot_?x_?nrg_?food|^core$|xef000|n[uú]cleo|core|ex_alim"),
    ("neig", r"igd_?nnrg|^neig$|igxe00|bens.?ind|bine|non.?energy"),
    ("serv", r"serv"),
    ("food", r"food|aliment|^alim$"),
    ("energy", r"nrg|energ"),
    ("total", r"total|cp00|000000|cheio|\bnic\b|ipca|hicp|^00$"),
]
SKIP_MEASURE = r"nsa|fator|factor|mom|yoy|sens|seas7|stl7|inicio|6m|status|flag|resid|compon|bce_oficial|ecoicop1|sa_t_3"


def comp_of(label):
    s = label.lower()
    for c, rx in COMP:
        if re.search(rx, s):
            return None if c == "skip" else c
    return None


def measure_of(label):
    s = label.lower()
    if re.search(r"saar|msaar|3m.?anual|3m_?pct|msaar_3m", s) and not re.search(r"6m|sens|seas7|stl7|inicio|nsa|bce_oficial|ecoicop1", s):
        return "saar"
    if re.search(SKIP_MEASURE, s):
        return None
    if re.search(r"(^|[_ .|-])sa($|[_ .|=-])|indice_sa|idx_sa|index_sa|indice_i15_sa|sa_calendario|dessaz", s):
        return "sa"
    return None


PERIOD = re.compile(r"^(\d{4})-(\d{2})")


def _num(x):
    try:
        v = float(x)
        return v if v == v else None
    except (TypeError, ValueError):
        return None


def records(path):
    """Yield (period 'YYYY-MM', series_label, measure_label, value)."""
    rows = list(csv.reader(open(path, errors="ignore")))
    if len(rows) < 3:
        return
    h0, h1 = rows[0], rows[1]
    # pandas two-row header: row1 has no period in col 0 and row0/row1 both labelled
    if (not any(PERIOD.match(x or "") for x in h1) and not any(_num(x) is not None for x in h1)
            and len(h1) == len(h0) and any(h1[1:])):
        body = [r for r in rows[2:] if r and PERIOD.match(r[0])]
        for r in body:
            p = r[0][:7]
            for j in range(1, min(len(r), len(h0))):
                v = _num(r[j])
                if v is not None:
                    a, b = h0[j], h1[j]
                    # one level is the measure, the other the series
                    if measure_of(a):
                        yield p, b, a, v
                    else:
                        yield p, a, b, v
        return
    hdr = h0
    pcol = next((j for j, h in enumerate(hdr) if re.search(r"^(periodo|data|date|mes|time|time_period|period|período)$", h.strip().lower())), None)
    if pcol is None:
        pcol = next((j for j in range(len(hdr)) if PERIOD.match(rows[1][j] if j < len(rows[1]) else "")), None)
    if pcol is None:
        return
    scols = [j for j, h in enumerate(hdr) if re.search(r"^(codigo|code|abertura|serie|série|indicador|coicop18|coicop|categoria|componente|agregado|item|nome|rotulo|codigo_eurostat|codigo_ecoicop)$", h.strip().lower())]
    mcol = next((j for j, h in enumerate(hdr) if h.strip().lower() == "medida"), None)
    vcol = next((j for j, h in enumerate(hdr) if h.strip().lower() == "valor"), None)
    for r in rows[1:]:
        if len(r) <= pcol or not PERIOD.match(r[pcol]):
            continue
        p = r[pcol][:7]
        series = " | ".join(r[j] for j in scols if j < len(r))
        if mcol is not None and vcol is not None:
            v = _num(r[vcol])
            if v is not None:
                yield p, series, r[mcol], v
            continue
        for j, h in enumerate(hdr):
            if j == pcol or j in scols or j >= len(r):
                continue
            v = _num(r[j])
            if v is not None:
                yield p, series or h, h, v


def series_label(series, measure):
    return series if series and series != measure else measure


def extract(workdir):
    found = {}
    for root, _, fs in os.walk(workdir):
        if re.search(r"/(raw|brutos|bruto)(/|$)", root):
            continue
        for f in sorted(fs):
            if not f.endswith(".csv"):
                continue
            p = os.path.join(root, f)
            with open(p, errors="ignore") as fh:
                if "OBS_VALUE" in fh.readline():
                    continue
            acc = {}
            for per, ser, mea, v in records(p):
                m = measure_of(mea)
                if not m:
                    continue
                c = comp_of(series_label(ser, mea)) or comp_of(mea)
                if not c:
                    continue
                acc.setdefault((c, m, ser, mea), {})[per] = v
            for (c, m, ser, mea), d in acc.items():
                key = (c, m)
                cur = found.get(key)
                if cur is None or len(d) > len(cur["data"]):
                    found[key] = {"kind": m, "file": os.path.relpath(p, workdir), "col": f"{ser} :: {mea}", "data": d}
    out = {}
    for c in ["total", "core", "neig", "serv", "energy", "food"]:
        sa, sr = found.get((c, "sa")), found.get((c, "saar"))
        if sa and len(sa["data"]) >= 37:
            out[c] = sa
        elif sr:
            out[c] = sr
        elif sa:
            out[c] = sa
    return out
