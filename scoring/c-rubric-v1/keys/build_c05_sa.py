"""C05 core 3m SAAR: the author's S05/S06 seasonal-adjustment rule, applied per cell.

Same code as PR #1 (answer-keys/extract_sa.py, resid_seas.py, copied here; logic of
run_resid_seasonality.py, run_sa_threshold.py and sa_gate.py):
1. The agent's saved core SA series (or 3m SAAR series) is found in its own CSVs (extract_sa.extract).
2. Equal to the ECB official SA (m/m RMSE <= 0.02 pp over the last 60 months): pass.
3. Otherwise F-test on month dummies of the m/m change, full saved history: p >= 0.05 pass,
   p < 0.01 fail, else inconclusive; fewer than 36 months or no saved series: fail.
4. Inconclusive: RMSE of the 3m SAAR over the last 24 months against the ECB SA 3m SAAR, pass <= 1.0 pp.
3m SAAR as in S06: 100*((SA_t/SA_t-3)^4-1). Reference: ECB HICP.M.U2.Y.XEF000.4F0.INX from the CSVs
the C05 agents saved, the copy ending at the cell's reference month (2026-09 or 2026-10).
Pass: the delivery's own 3m SAAR at the reference month is admitted as an extra value. Fail: the
core 3m SAAR question scores NAO_ATENDE whatever the judge reads. Writes C05-sa-gate.csv.
"""
import csv
import glob
import math
import sys
from pathlib import Path

HERE = Path(__file__).parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE))
import extract_sa as X  # noqa: E402
import resid_seas as RS  # noqa: E402

CODE = 'HICP.M.U2.Y.XEF000.4F0.INX'


def ecb_core():
    """{last month: series} from every saved ECB CSV carrying the core SA index; copies ending in the same month must agree."""
    out = {}
    pats = ['execucoes/pilot-*-c05-*/attempts/*/work/**/*.csv']
    files = [f for p in pats for f in glob.glob(str(REPO / p), recursive=True) + glob.glob('raw-archive/' + p, recursive=True)]
    for f in files:
        try:
            with open(f, errors='ignore') as fh:
                if 'OBS_VALUE' not in fh.readline():
                    continue
                fh.seek(0)
                s = {r['TIME_PERIOD']: float(r['OBS_VALUE']) for r in csv.DictReader(fh)
                     if r.get('KEY') == CODE and r.get('OBS_VALUE') not in (None, '')}
        except Exception:
            continue
        if s:
            last = max(s)
            if last in out:
                common = [p for p in s if p in out[last]]
                if any(abs(s[p] - out[last][p]) > 1e-6 for p in common):
                    print('warning: ECB copies ending', last, 'disagree', f)
                out[last].update(s)
            else:
                out[last] = s
    return out


def mom(d):
    ps = sorted(d)
    return {ps[i]: 100 * (d[ps[i]] / d[ps[i - 1]] - 1) for i in range(1, len(ps)) if d[ps[i - 1]]}


def saar(d):
    ps = sorted(d)
    return {ps[i]: 100 * ((d[ps[i]] / d[ps[i - 3]]) ** 4 - 1) for i in range(3, len(ps))}


def main():
    ref = ecb_core()
    print('ECB core SA copies end in', sorted(ref))
    key = {}
    for r in csv.DictReader((HERE / 'C05-key.csv').open()):
        key[r['attempt']] = r['period']
    rows = []
    with (REPO / 'harmonization-case-inventory-20261109-v1.csv').open(encoding='utf-8-sig') as handle:
        cells = [r for r in csv.DictReader(handle) if r['task'] == 'C05' and r['phase'] in ('A1', 'A2', 'A3')]
    for r in csv.DictReader((HERE / 'A4-cells.csv').open()):  # A4 revisions: gate the revised delivery's own series
        if r['task'] == 'C05':
            camp = next(x for x in csv.DictReader((REPO / 'harmonization-case-inventory-20261109-v1.csv').open(encoding='utf-8-sig'))
                        if x['final_attempt_id'] == r['attempt'])['source_campaign_id']
            cells.append({'final_attempt_id': r['attempt'], 'phase': r['phase'], 'model': r['model'], 'disposition': '',
                          'source_campaign_id': camp, 'work': REPO / 'execucoes' / camp / 'evaluation-snapshots' / r['attempt'] / 'work'})
    for c in cells:
        a = c['final_attempt_id']
        if c['disposition'] == 'verified_absence':
            continue
        period = key[a]
        reference = ref[period]
        work = c.get('work') or REPO / 'execucoes' / c['source_campaign_id'] / 'attempts' / a / 'work'
        got = X.extract(str(work)).get('core')
        row = {'attempt': a, 'phase': c['phase'], 'model': c['model'], 'period': period, 'kind': '', 'file': '', 'column': '',
               'n': '', 'F_p': '', 'official_rmse_mom': '', 'threshold_rmse': '', 'verdict': '', 'sa_pass': False, 'own_3msaar_at_period': '', 'own_3msaar_seed_period': ''}
        if not got:
            row['verdict'] = 'no saved series'
            rows.append(row)
            continue
        d = got['data']
        row.update(kind=got['kind'], file=got['file'], column=got['col'])
        t = RS.test(d, rate=got['kind'] == 'saar')
        row.update(n=t['n'], F_p='' if t['F_p'] is None else round(t['F_p'], 4))
        if t['F_p'] is None or t['n'] < 36:
            v = 'too short'
        elif t['F_p'] < 0.01:
            v = 'residual seasonality'
        elif t['F_p'] >= 0.05:
            v = 'pass'
        else:
            v = 'inconclusive'
        mine = saar(d) if got['kind'] == 'sa' else d
        if got['kind'] == 'sa':
            am, bm = mom(d), mom(reference)
            com = [p for p in am if p in bm][-60:]
            if com:
                off = math.sqrt(sum((am[p] - bm[p]) ** 2 for p in com) / len(com))
                row['official_rmse_mom'] = round(off, 3)
                if off <= 0.02:
                    v = 'official ECB SA'
        if v == 'inconclusive':
            rs = saar(reference)
            com = [p for p in sorted(mine) if p in rs][-24:]
            rm = math.sqrt(sum((mine[p] - rs[p]) ** 2 for p in com) / len(com))
            row['threshold_rmse'] = round(rm, 2)
            v = f"threshold {'pass' if rm <= 1.0 else 'fail'}"
        row['verdict'] = v
        row['sa_pass'] = v in ('pass', 'official ECB SA', 'threshold pass')
        if period in mine:
            row['own_3msaar_at_period'] = round(mine[period], 2)
        if c['phase'].startswith('A4') and '2026-09' in mine:  # seed's month, also admitted for A4 revisions
            row['own_3msaar_seed_period'] = round(mine['2026-09'], 2)
        rows.append(row)
    with (HERE / 'C05-sa-gate.csv').open('w', newline='') as handle:
        w = csv.DictWriter(handle, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(r['phase'], r['model'][:12].ljust(12), r['period'], r['kind'], r['n'], r['F_p'], r['official_rmse_mom'], r['threshold_rmse'],
              r['verdict'], r['sa_pass'], r['own_3msaar_at_period'], r['file'][-40:])


if __name__ == '__main__':
    main()
