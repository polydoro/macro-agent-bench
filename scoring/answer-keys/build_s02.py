"""S02 answer key: German manufacturing orders at constant prices, latest month, per arm.

Inputs are the Bundesbank BBDE1 downloads the agents saved (Destatis data; SDMX-CSV or the web
time-series CSV). Grouped by arm because SDMX-CSV carries no update stamp; the web CSVs all say
'last update 2026-10-06'. All copies must agree cell by cell, within and across arms.
"""
import collections, csv, glob, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import bbk
from build_s01 import yoy, saar3

ARMS = {'pilot-taskwise': 'A1', 'pilot-a2': 'A2', 'pilot-a3': 'A3'}
# role -> concept code, from the series titles: AEA1 total, AEB1 domestic (Inland), AEB5 foreign (Ausland).
# AED1/AED5 are euro-area / non-euro-area only and do not stand for foreign orders.
ROLES = {'total': 'AEA1', 'domestico': 'AEB1', 'externo': 'AEB5'}

obs = collections.defaultdict(dict)  # (arm, series) -> {period: value}
seen = {}
for f in glob.glob('execucoes/pilot-*-s02-*/attempts/*/work/**/*.csv', recursive=True):
    arm = ARMS[f.split('/')[1].rsplit('-s02', 1)[0]]
    for sid, t, v, _ in bbk.read(f):
        old = seen.setdefault((sid, t), v)
        if abs(old - v) > 1e-9:
            raise SystemExit(f'disagreement {sid} {t}: {old} vs {v} ({f})')
        obs[(arm, sid)][t] = v

r = lambda x: '' if x is None else round(x, 2)
rows = []
for arm in ('A1', 'A2', 'A3'):
    for role, concept in ROLES.items():
        sa = obs.get((arm, f'Y.{concept}.A2P300000.C.A'), {})
        ca = obs.get((arm, f'W.{concept}.A2P300000.C.L'), {})
        t = max(sa)
        rows.append({'arm': arm, 'role': role, 'series_sa': f'BBDE1.M.DE.Y.{concept}.A2P300000.F.C.I21.A', 'period': t,
                     'yoy_ca': r(yoy(ca, t)), 'yoy_sa': r(yoy(sa, t)), 'saar3_sa': r(saar3(sa, t)), 'level_sa': r(sa.get(t)),
                     'note': '' if ca else 'no calendar-adjusted-only series saved; YoY on SA only'})
path = Path(__file__).parent / 'S02-key.csv'
with open(path, 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)
print(open(path).read())
