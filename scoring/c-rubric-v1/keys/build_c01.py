"""C01 answer key: German industrial production and orders at the latest month each cell could see.

Production: Eurostat sts_inpr_m JSON-stat files saved by S01 and C01 agents (Git and release
raw-archive-20261116), read with jsonstat.py from PR #1. Per arm, the newest 'updated' stamp before
the arm's first C01 run; copies within a stamp must agree. Latest month 2026-08 in all arms
(Destatis published September production on 2026-11-07, after every C01 run). Totals admitted:
B-D, B-D_F, B_C (Destatis "Industrie") and C (manufacturing) as headline.

Orders: A1 and A2 reuse S02-key.csv (latest 2026-08). Destatis published September orders on
2026-11-05 at 08:00 CET, and every A3 C01 run started after that (09:50-11:10 UTC), so A3's latest
month is 2026-09. That row is computed here from BBDE1 total orders (volume, SA, vintage
"last update 2026-11-05 08:05"), as saved by two A3 agents; the copies must agree. Calendar-adjusted
and unadjusted YoY come from Destatis GENESIS 42151-0004 (X13JDKB, WERTORG; WZ08-C, Insgesamt) as
saved by A3 Kimi; its SA level for September (90.3) matches BBDE1, so it is the same release.

Writes C01-production.csv and C01-orders-A3.csv.
"""
import csv
from pathlib import Path

HERE = Path(__file__).parent
RAW = Path('execucoes/pilot-a3-c01-low-normal-20261105-v1/attempts')  # release raw-archive-20261116 A3-part01
SOURCES = [RAW / 'a3-c01-claude-opus-primary/work/raw/orders.csv',
           RAW / 'a3-c01-grok-low-normal-primary/work/dados/bruto/ord_AEA1_Y_A2P300000.csv']


def read(path):
    out = {}
    for row in csv.reader(path.read_text(encoding='utf-8-sig').splitlines()):
        if len(row) > 1 and len(row[0]) == 7 and row[0][4] == '-' and row[1] not in ('', '.'):
            out[row[0]] = float(row[1])
    return out


PRODUCTION = {'total_BD': 'B-D', 'total_BDF': 'B-D_F', 'industria_BC_destatis': 'B_C', 'manufatura_C': 'C'}
CUTOFF = {'A1': '2026-10-28T12:00:00+0000', 'A2': '2026-10-31T00:00:00+0000', 'A3': '2026-11-05T09:00:00+0000',
          # A4 revisions (keys/A4-cells.csv): non-Anthropic models ran 6 Nov 01-02 UTC, Anthropic models from 7 Nov 18 UTC
          'A4-early': '2026-11-06T01:00:00+0000', 'A4-late': '2026-11-07T18:00:00+0000'}


GENESIS = RAW / 'a3-c01-kimi-pro-low-normal-primary/work/entrega/dados/brutos/42151-0004.json'


def genesis_yoy(adjustment, year=2026, month=9):
    import json
    d = json.loads(GENESIS.read_text())['data'][0]
    idx = {k: d['dimension'][k]['category']['index'] for k in d['id']}
    want = {'ABSATZ': 'INSGESAMT', 'WERT03': adjustment, 'WZ08Y1': 'WZ08-C', 'MONAT': f'MONAT{month:02d}'}

    def get(y):
        pos = 0
        for k, n in zip(d['id'], d['size']):
            pos = pos * n + idx[k][dict(want, JAHR=str(y)).get(k, next(iter(idx[k])))]
        return d['value'][pos]
    return round(100 * (get(year) / get(year - 1) - 1), 2)


def production():
    import collections, glob, sys
    sys.path.insert(0, str(HERE))
    import jsonstat
    repo = HERE.parent.parent
    files = glob.glob(str(repo / 'execucoes/pilot-*-s01-*/attempts/*/work/**/*.json'), recursive=True)
    files += glob.glob(str(repo / 'execucoes/pilot-*-c01-*/attempts/*/work/**/*.json'), recursive=True)
    files += glob.glob('execucoes/pilot-*-c01-*/attempts/*/work/**/*.json', recursive=True)
    files += glob.glob(str(repo / 'execucoes/pilot-a4-*/evaluation-snapshots/*/work/**/*.json'), recursive=True)
    obs = collections.defaultdict(dict)
    used = 0
    for f in files:
        try:
            if not jsonstat.is_jsonstat(f, 'nace_r2'):
                continue
            up, rs = jsonstat.rows(f)
        except Exception:
            continue
        used += 1
        for dims, v in rs:
            if dims.get('geo') != 'DE' or dims.get('unit') != 'I21' or dims.get('indic_bt', 'PRD') != 'PRD':
                continue
            key, t = (up, dims['nace_r2'], dims['s_adj']), dims['time']
            if t in obs[key] and abs(obs[key][t] - v) > 1e-9:
                raise SystemExit(f'disagreement {key} {t}')
            obs[key][t] = v
    out = []
    for arm, cutoff in CUTOFF.items():
        for role, nace in PRODUCTION.items():
            pick = lambda adj: max((k for k in obs if k[1] == nace and k[2] == adj and k[0] <= cutoff), default=None)
            kca, ksa = pick('CA'), pick('SCA')
            sa, ca = obs.get(ksa, {}), obs.get(kca, {})
            t = max(sa)
            months = sorted(sa)
            i = months.index(t)
            yoy = lambda s: round(100 * (s[t] / s[months[i - 12]] - 1), 2) if t in s and months[i - 12] in s else ''
            saar = round(100 * ((sum(sa[m] for m in months[i - 2:i + 1]) / sum(sa[m] for m in months[i - 5:i - 2])) ** 4 - 1), 2)
            out.append({'arm': arm, 'role': role, 'nace': nace, 'period': t, 'yoy_ca': yoy(ca), 'yoy_sca': yoy(sa),
                        'saar3_sca': saar, 'stamp_ca': kca[0] if kca else '', 'stamp_sca': ksa[0]})
    with (HERE / 'C01-production.csv').open('w', newline='') as handle:
        w = csv.DictWriter(handle, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    print(used, 'JSON-stat files;', *(f"{r['arm']} {r['nace']} {r['period']} yoy_ca={r['yoy_ca']} saar={r['saar3_sca']} [{r['stamp_sca']}]" for r in out), sep='\n')


def main():
    production()
    series = [read(p) for p in SOURCES]
    if series[0] != series[1]:
        raise SystemExit('saved BBDE1 copies disagree')
    s = series[0]
    months = sorted(s)
    t = months[-1]
    i = months.index(t)
    yoy = 100 * (s[t] / s[months[i - 12]] - 1)
    m3 = sum(s[m] for m in months[i - 2:i + 1]) / 3
    p3 = sum(s[m] for m in months[i - 5:i - 2]) / 3
    saar = 100 * ((m3 / p3) ** 4 - 1)
    row = {'arm': 'A3', 'role': 'total', 'series_sa': 'BBDE1.M.DE.Y.AEA1.A2P300000.F.C.I21.A', 'period': t,
           'yoy_ca': genesis_yoy('X13JDKB'), 'yoy_nsa': genesis_yoy('WERTORG'), 'yoy_sa': round(yoy, 2), 'saar3_sa': round(saar, 2), 'level_sa': s[t],
           'note': 'vintage 2026-11-05; two BBDE1 copies agree; CA and NSA YoY from GENESIS 42151-0004 (Kimi A3)'}
    with (HERE / 'C01-orders-A3.csv').open('w', newline='') as handle:
        w = csv.DictWriter(handle, fieldnames=list(row))
        w.writeheader()
        w.writerow(row)
    print(row)


if __name__ == '__main__':
    main()
