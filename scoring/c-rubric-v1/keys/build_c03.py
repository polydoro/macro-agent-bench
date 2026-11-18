"""C03 answer key: euro-area GDP, last observed quarter and the nowcast target, per cell.

The nowcast itself has no key (the author, question 11: no accuracy score). What is checked:
- the last observed GDP growth the cell could see (namq_10_gdp B1GQ, CLV20_MEUR, SCA, EA21 or EA20;
  newest stamp not after the cell's start; computed q/q, q/q annualised, YoY, plus published
  CLV_PCH_PRE / CLV_PCH_SM): A1 (28 Oct) sees 2026-Q2; A2 and A3 see the Q3 flash of 2026-10-30;
- the target quarter: A1 must nowcast 2026-Q3 as not yet released (Q4 may be added); A2/A3 must treat
  Q3 as observed and nowcast 2026-Q4 (the author, question 12).
Writes C03-key.csv (same long format as C02) and C03-cells.csv (attempt, arm, start, target, observed).
Reuses load/series/cells from build_c02.py.
"""
import csv
from pathlib import Path

import build_c02 as b

HERE = Path(__file__).parent
RATE, SAAR = b.RATE, b.SAAR


def main():
    pattern = 'execucoes/pilot-*-c03-*/attempts/*/work/**/*.json'
    obs13, obs4 = b.load(pattern), b.load(pattern, A4_FILES=True)  # A4 revisions also read their own saved files
    rows, cells = [], []
    for arm, attempt, start in b.cells('C03'):
        obs = obs4 if arm.startswith('A4') else obs13
        cutoff = start[:19] + '+00:00'
        add = lambda q, period, label, value, tol, stamp: rows.append(
            {'attempt': attempt, 'arm': arm, 'start': start[:19], 'question': q, 'period': period, 'label': label,
             'value': value, 'tol': tol, 'stamp': stamp})
        last = ''
        for geo in ('EA21', 'EA20'):
            s, st = b.series(obs, cutoff, dataset='namq_10_gdp', geo=geo, na_item='B1GQ', s_adj='SCA', unit='CLV20_MEUR')
            if not s:
                continue
            t = max(s)
            last = max(last, t)
            q = sorted(s)
            i = q.index(t)
            add('N_last_qoq', t, f'PIB {geo}, q/q %', b.pct(s[t], s[q[i - 1]]), RATE, st)
            add('N_last_qoq', t, f'PIB {geo}, q/q anualizado %', round(100 * ((s[t] / s[q[i - 1]]) ** 4 - 1), 2), SAAR, st)
            add('N_last_yoy', t, f'PIB {geo}, YoY %', b.pct(s[t], s[q[i - 4]]), RATE, st)
            for unit, qid in (('CLV_PCH_PRE', 'N_last_qoq'), ('CLV_PCH_SM', 'N_last_yoy')):
                p, stp = b.series(obs, cutoff, dataset='namq_10_gdp', geo=geo, na_item='B1GQ', s_adj='SCA', unit=unit)
                if t in p:
                    add(qid, t, f'PIB {geo}, taxa publicada {unit}', p[t], RATE, stp)
        latest = {}
        for r in rows:
            if r['attempt'] == attempt:
                latest[r['question']] = max(latest.get(r['question'], ''), r['period'])
        rows = [r for r in rows if r['attempt'] != attempt or r['period'] == latest[r['question']]]
        y, n = int(last[:4]), int(last[-1])
        target = f'{y}-Q{n + 1}' if n < 4 else f'{y + 1}-Q1'
        cells.append({'attempt': attempt, 'arm': arm, 'start': start[:19], 'observed': last, 'target': target})
    for name, data in (('C03-key.csv', rows), ('C03-cells.csv', cells)):
        with (HERE / name).open('w', newline='') as handle:
            w = csv.DictWriter(handle, fieldnames=list(data[0]))
            w.writeheader()
            w.writerows(data)
    import collections
    summary = collections.defaultdict(set)
    for r in rows:
        summary[(r['arm'], r['question'], r['period'])].add(r['value'])
    for k in sorted(summary):
        print(k, sorted(summary[k]))
    print(collections.Counter((c['arm'], c['observed'], c['target']) for c in cells))


if __name__ == '__main__':
    main()
