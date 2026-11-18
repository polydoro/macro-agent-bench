"""S02 A4 release: Destatis press release 385 of 2026-11-05 (September 2026 orders).

The A4 revisions ran on 5-7 Nov 2026, after this release, so under "the seed's release or newer" the
September figures are admitted alongside the A1 and A3 (August) keys. The raw Bundesbank downloads of
that vintage were not kept; the levels below come from Fable A4s's saved conversion of them
(entrega/bundesbank_sa_2021eq100.csv, real SA 2021=100), which matches the press release m/m for
every series (its tabela_checagem_comunicado_385.csv) and Kimi A4e's own download (90.3 / 88.8 / 91.3).
Calendar-adjusted YoY for the total, +3.3%, is the release figure (saved by Haiku A4s in
dados/destatis_publicacao_2026-11-05.csv; Kimi A4e has the same). No NSA or calendar-only component
series of this vintage was saved, so those variants are left blank.

Appends arm A4 rows to S02-key.csv and S02-extra-yoy.csv (replacing earlier A4 rows).
"""
import csv, glob, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from build_s01 import yoy, saar3

src = glob.glob(str(HERE.parent / 'execucoes/pilot-a4-*/evaluation-snapshots/*/work/entrega/tabela_checagem_comunicado_385.csv'))
assert len(src) == 1, src
levels = list(csv.DictReader(open(Path(src[0]).with_name('bundesbank_sa_2021eq100.csv'))))
COLS = {'total': ('AEA1', 'Total (real)'), 'domestico': ('AEB1', 'Mercado interno'), 'externo': ('AEB5', 'Exterior')}
T = '2026-09'
r = lambda x: round(x, 2)

key = [row for row in csv.DictReader(open(HERE / 'S02-key.csv')) if row['arm'] != 'A4']
extra = [row for row in csv.DictReader(open(HERE / 'S02-extra-yoy.csv')) if row['arm'] != 'A4']
for role, (concept, col) in COLS.items():
    s = {x['periodo']: float(x[col]) for x in levels if x[col]}
    key.append({'arm': 'A4', 'role': role, 'series_sa': f'BBDE1.M.DE.Y.{concept}.A2P300000.F.C.I21.A', 'period': T,
                'yoy_ca': 3.3 if role == 'total' else '', 'yoy_sa': r(yoy(s, T)), 'saar3_sa': r(saar3(s, T)), 'level_sa': s[T],
                'note': 'Destatis PD 385 of 2026-11-05; levels from Fable A4s saved conversion (raw not kept)'})
    extra.append({'arm': 'A4', 'role': role, 'period': T, 'yoy_ca': '', 'yoy_nsa': '', 'source': 'September release: no NSA or calendar-only series saved'})
for name, rows in (('S02-key.csv', key), ('S02-extra-yoy.csv', extra)):
    with open(HERE / name, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
print(*[k for k in key if k['arm'] == 'A4'], sep='\n')
