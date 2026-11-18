"""C05 answer key: euro-area HICP energy and core, latest month per cell, from the S06 key (PR #1).

S05-S06-key.csv is copied from PR #1 answer-keys/ (S06 method: Eurostat RCH_A and I25 for YoY, ECB
official SA index for 3m SAAR; energy SA equals NSA). The October 2026 flash came out on 2026-11-04 at
11:00 CET (10:00 UTC). Cells that started before it (A1, A2 except Fable) take the S06 September rows;
cells that started after it (A2 Fable on 2026-11-04 16:15 UTC, all A3) take the S06 October rows
(timeliness by each cell's start, the author, question 19). Writes C05-key.csv in the long format of C02.
"""
import csv
import json
from pathlib import Path

HERE = Path(__file__).parent
REPO = HERE.parent.parent
FLASH_UTC = '2026-11-04T10:00:00'
RATE, SAAR = 0.15, 0.3


def main():
    key = [r for r in csv.DictReader((HERE / 'S05-S06-key.csv').open()) if r['task'] == 'S06']
    by_period = {}
    for r in key:
        by_period.setdefault(r['period'], {})[r['role']] = r
    rows = []
    with (REPO / 'harmonization-case-inventory-20261109-v1.csv').open(encoding='utf-8-sig') as handle:
        cells = [r for r in csv.DictReader(handle) if r['task'] == 'C05' and r['phase'] in ('A1', 'A2', 'A3')]
    starts = {}
    for c in cells:
        rec = REPO / 'execucoes' / c['source_campaign_id'] / 'attempts' / c['final_attempt_id'] / 'receipt.json'
        starts[c['final_attempt_id']] = json.loads(rec.read_text())['submitted_at_utc'][:19] if rec.exists() else ''
    for r in csv.DictReader((HERE / 'A4-cells.csv').open()):  # A4 revisions (6-8 Nov, all after the October flash)
        if r['task'] == 'C05':
            cells.append({'final_attempt_id': r['attempt'], 'phase': r['phase']})
            starts[r['attempt']] = r['start_utc'][:19]
    for c in cells:
        start = starts[c['final_attempt_id']]
        period = '2026-10' if start >= FLASH_UTC else '2026-09'
        k = by_period[period]
        for q, role, cols, tol in (('N_energy_yoy', 'energia', ('yoy_rch_a', 'yoy_calc_i25'), RATE),
                                   ('N_core_yoy', 'nucleo', ('yoy_rch_a', 'yoy_calc_i25'), RATE),
                                   ('N_energy_3m', 'energia', ('saar3_sa', 'saar3_nsa'), SAAR),
                                   ('N_core_3m', 'nucleo', ('saar3_sa',), SAAR)):
            for col in cols:
                rows.append({'attempt': c['final_attempt_id'], 'arm': c['phase'], 'start': start, 'question': q, 'period': period,
                             'label': f'{role} {col}', 'value': k[role][col], 'tol': tol, 'stamp': k[role]['saar3_source']})
    with (HERE / 'C05-key.csv').open('w', newline='') as handle:
        w = csv.DictWriter(handle, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(sorted({(r['arm'], r['attempt'][:28], r['start'][:16], r['period']) for r in rows}))


if __name__ == '__main__':
    main()
