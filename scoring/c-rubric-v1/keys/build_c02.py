"""C02 answer key: euro-area household consumption, per cell (each cell's run start, receipt submitted_at_utc).

Inputs: Eurostat JSON-stat files saved by the C02 agents (Git and release raw-archive-20261116), read
with jsonstat.py; for each series the newest 'updated' stamp not after the cell's start. Copies within
a stamp must agree. Written as long rows (attempt, question, period, label, value, tol) in C02-key.csv.

- Consumption: namq_10_gdp (national concept) P31_S14 or P31_S14_S15, or namq_10_fcs (domestic concept, the
  durability table) P31_S14; no A1 agent saved namq_10_fcs, so A1 uses the oldest later copy
  (2026-10-30), assuming no revision of 2026-Q2 between 10-28 and 10-30 (namq_10_gdp shows none 10-30 to 11-05); chain-linked volumes (CLV20_MEUR),
  SCA, EA21 or EA20: q/q %, q/q annualised and YoY % of the latest quarter (2026-Q2 for every cell:
  the Q3 flash of 2026-10-30 has no expenditure breakdown).
- Retail trade volume (sts_trtu_m, VOL_SLS): G47 or G47_X_G473, EA21 or EA20: YoY on CA (or SCA),
  3m/3m SAAR on SCA. September 2026 first appears in the stamp 2026-11-06 11:00 CET.
- Consumer confidence (ei_bsco_m BS-CSMCI, SA, balance), latest month. A1 ran before Eurostat carried
  October, but two A1 agents quote the DG ECFIN flash of 2026-10-22 (-17.9), so A1's month is
  October with the flash (the author, question 10).
- Household saving rate (nasq_10_ki SRG_S14_S15, SCA), latest quarter.
Tolerances (PR #1): rates 0.15, annualised rates 0.3, balances 0.6.
"""
import collections
import csv
import glob
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE))
import jsonstat  # noqa: E402

RATE, SAAR, BALANCE = 0.15, 0.3, 0.6
DIFF = []
FLASH = {'A1': ('2026-10', -17.9, 'DG ECFIN flash 2026-10-22, quoted by A1 Sonnet and A1 Grok')}


def load(pattern='execucoes/pilot-*-c02-*/attempts/*/work/**/*.json', A4_FILES=False):
    files = glob.glob(str(REPO / pattern), recursive=True) + glob.glob('raw-archive/' + pattern, recursive=True)
    if A4_FILES:  # A4 revisions' saved files (evaluation snapshots), for releases newer than the A1 seed
        task = pattern.split('-*/')[0].split('pilot-*-')[-1].upper()
        ids = {r['attempt'] for r in csv.DictReader((HERE / 'A4-cells.csv').open()) if r['task'] == task}
        files += [f for f in glob.glob(str(REPO / 'execucoes/pilot-a4-*/evaluation-snapshots/*/work/**/*.json'), recursive=True)
                  if f.split('/evaluation-snapshots/')[1].split('/')[0] in ids]
    obs = collections.defaultdict(dict)  # (series key) -> {stamp: {time: value}}
    for f in files:
        try:
            d = json.load(open(f))
            if not (isinstance(d, dict) and 'value' in d and 'dimension' in d):
                continue
            stamp, rows = jsonstat.rows(f)
        except Exception:
            continue
        dataset = ((d.get('extension') or {}).get('id') or '').lower()
        for dims, v in rows:
            if dims.get('geo') not in ('EA21', 'EA20'):
                continue
            key = tuple(sorted([(k, x) for k, x in dims.items() if k not in ('time', 'freq')] + [('dataset', dataset)]))
            series = obs[key].setdefault(stamp, {})
            if dims['time'] in series and abs(series[dims['time']] - v) > 1e-9:
                DIFF.append((key, stamp, dims['time'], series[dims['time']], v, f)); continue
            series[dims['time']] = v
    return obs


def series(obs, cutoff, fallback=False, **want):
    """Newest stamp not after the cutoff. fallback: with no earlier copy, the oldest later one (marked in the stamp)."""
    key = tuple(sorted(want.items()))
    stamps = [s for s in obs.get(key, {}) if s and stamp_utc(s) <= cutoff]
    if stamps:
        best = max(stamps, key=stamp_utc)
        return obs[key][best], best
    later = [s for s in obs.get(key, {}) if s]
    if fallback and later:
        best = min(later, key=stamp_utc)
        return obs[key][best], best + ' (later copy: none saved before the cell ran)'
    return {}, None


def stamp_utc(s):
    from datetime import datetime, timezone
    return datetime.strptime(s, '%Y-%m-%dT%H:%M:%S%z').astimezone(timezone.utc).isoformat()


def cells(task='C02'):
    out = []
    with (REPO / 'harmonization-case-inventory-20261109-v1.csv').open(encoding='utf-8-sig') as handle:
        for r in csv.DictReader(handle):
            if r['task'] == task and r['phase'] in ('A1', 'A2', 'A3'):
                rec = REPO / 'execucoes' / r['source_campaign_id'] / 'attempts' / r['final_attempt_id'] / 'receipt.json'
                out.append((r['phase'], r['final_attempt_id'], json.loads(rec.read_text())['submitted_at_utc']))
    for r in csv.DictReader((HERE / 'A4-cells.csv').open()):  # A4 revisions: run start from the branch state
        if r['task'] == task:
            out.append((r['phase'], r['attempt'], r['start_utc'].replace('+00:00', '')))
    return sorted(set(out))


def pct(a, b):
    return round(100 * (a / b - 1), 2)


def main():
    # A1-A3 keys use only A1-A3 files (unchanged since their pass); A4 keys also read the A4 revisions' files
    obs13, obs4 = load(), load(A4_FILES=True)
    rows = []
    for arm, attempt, start in cells():
        obs = obs4 if arm.startswith('A4') else obs13
        cutoff = start[:19] + '+00:00'
        add = lambda q, period, label, value, tol, stamp: rows.append(
            {'attempt': attempt, 'arm': arm, 'start': start[:19], 'question': q, 'period': period, 'label': label,
             'value': value, 'tol': tol, 'stamp': stamp})
        for geo in ('EA21', 'EA20'):
            for dataset, item in (('namq_10_gdp', 'P31_S14'), ('namq_10_gdp', 'P31_S14_S15'), ('namq_10_fcs', 'P31_S14')):
                s, st = series(obs, cutoff, dataset == 'namq_10_fcs', dataset=dataset, geo=geo, na_item=item, s_adj='SCA', unit='CLV20_MEUR')
                if not s:
                    continue
                t = max(s)
                q = sorted(s)
                i = q.index(t)
                add('N_cons_qoq', t, f'{dataset} {item} {geo}, q/q %', pct(s[t], s[q[i - 1]]), RATE, st)
                add('N_cons_qoq', t, f'{dataset} {item} {geo}, q/q anualizado %', round(100 * ((s[t] / s[q[i - 1]]) ** 4 - 1), 2), SAAR, st)
                add('N_cons_yoy', t, f'{dataset} {item} {geo}, YoY %', pct(s[t], s[q[i - 4]]), RATE, st)
                for unit, qid in (('CLV_PCH_PRE', 'N_cons_qoq'), ('CLV_PCH_SM', 'N_cons_yoy')):  # published rates
                    p, stp = series(obs, cutoff, dataset=dataset, geo=geo, na_item=item, s_adj='SCA', unit=unit)
                    if t in p:
                        add(qid, t, f'{dataset} {item} {geo}, taxa publicada {unit}', p[t], RATE, stp)
            for nace in ('G47', 'G47_X_G473'):
                sa, st = series(obs, cutoff, dataset='sts_trtu_m', geo=geo, indic_bt='VOL_SLS', nace_r2=nace, s_adj='SCA', unit='I21')
                if not sa:
                    continue
                t = max(sa)
                m = sorted(sa)
                i = m.index(t)
                ca, stc = series(obs, cutoff, dataset='sts_trtu_m', geo=geo, indic_bt='VOL_SLS', nace_r2=nace, s_adj='CA', unit='I21')
                if t in ca and m[i - 12] in ca:
                    add('N_ret_yoy', t, f'{nace} {geo}, YoY ajustado por calendário', pct(ca[t], ca[m[i - 12]]), RATE, stc)
                add('N_ret_yoy', t, f'{nace} {geo}, YoY ajustado sazonal e por calendário', pct(sa[t], sa[m[i - 12]]), RATE, st)
                p, stp = series(obs, cutoff, dataset='sts_trtu_m', geo=geo, indic_bt='VOL_SLS', nace_r2=nace, s_adj='CA', unit='PCH_SM')
                if t in p:  # published YoY, calendar adjusted
                    add('N_ret_yoy', t, f'{nace} {geo}, YoY publicado (CA)', p[t], RATE, stp)
                saar = 100 * ((sum(sa[x] for x in m[i - 2:i + 1]) / sum(sa[x] for x in m[i - 5:i - 2])) ** 4 - 1)
                add('N_ret_3m', t, f'{nace} {geo}, 3m/3m SAAR', round(saar, 2), SAAR, st)
            s, st = series(obs, cutoff, dataset='ei_bsco_m', geo=geo, indic='BS-CSMCI', s_adj='SA', unit='BAL')
            if s:
                add('N_conf', max(s), f'confiança do consumidor {geo}, saldo SA', s[max(s)], BALANCE, st)
            s, st = series(obs, cutoff, dataset='nasq_10_ki', geo=geo, sector='S14_S15', na_item='SRG_S14_S15', s_adj='SCA', unit='PC')
            if s:
                add('N_sav', max(s), f'taxa de poupança das famílias {geo}, % SA', s[max(s)], RATE, st)
        if arm in FLASH:
            period, value, note = FLASH[arm]
            add('N_conf', period, 'confiança do consumidor, flash DG ECFIN, saldo', value, BALANCE, note)
    if DIFF:
        print(len(DIFF), 'disagreeing copies within a stamp, e.g.', DIFF[0][:5], DIFF[0][5])
    # keep only the latest period per (attempt, question): an older month is not the latest available
    latest = {}
    for r in rows:
        k = (r['attempt'], r['question'])
        latest[k] = max(latest.get(k, ''), r['period'])
    rows = [r for r in rows if r['period'] == latest[(r['attempt'], r['question'])]]
    with (HERE / 'C02-key.csv').open('w', newline='') as handle:
        w = csv.DictWriter(handle, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    summary = collections.defaultdict(set)
    for r in rows:
        summary[(r['arm'], r['question'], r['period'])].add(r['value'])
    for k in sorted(summary):
        print(k, sorted(summary[k]))
    for a in sorted({(r['arm'], r['attempt'], r['start']) for r in rows}):
        print(a, {r['question']: r['period'] for r in rows if r['attempt'] == a[1]})


if __name__ == '__main__':
    main()
