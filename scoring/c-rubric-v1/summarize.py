"""Write results/summary-<VERSION>.csv from the full passes results/pass-A1-A2-A3-<task>-<VERSION>.json."""
import csv
import glob
import json
from pathlib import Path

import rubric

HERE = Path(__file__).parent


def main():
    rows = []
    for path in sorted(glob.glob(str(HERE / f'results/pass-A1-A2-A3-C0?-{rubric.VERSION}.json'))):
        for c in json.loads(Path(path).read_text())['rows']:
            b = c.get('blocks_mean') or {}
            rows.append({'task': c['task'], 'phase': c['phase'], 'model': c['model'], 'status': c['status'],
                         'L_mean': c.get('L_mean'), 'L_sd': round(c['L_sd'], 2) if c.get('L_sd') is not None else '',
                         **{k: b.get(k, '') for k in 'ABCDE'}})
    rows.sort(key=lambda r: (r['task'], r['phase'], r['model']))
    out = HERE / f'results/summary-{rubric.VERSION}.csv'
    with out.open('w', newline='') as handle:
        w = csv.DictWriter(handle, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(out, len(rows))
    model_means(rows)
    a4_summary()


def model_means(rows):
    """Mean L per model across C tasks and arms, two treatments of cells with no delivery:
    counted as 0 (grok 'verified_absence': CLI failed before any model work; sol 'no_product': model ran, delivered nothing)
    and excluded. Counts let the reader see what each mean rests on."""
    out = []
    for model in sorted({r['model'] for r in rows}):
        mine = [r for r in rows if r['model'] == model]
        judged = [float(r['L_mean']) for r in mine if r['status'] == 'judged']
        absent = [r for r in mine if r['status'] != 'judged']
        out.append({'model': model, 'cells': len(mine), 'delivered': len(judged),
                    'no_product': sum(r['status'] == 'no_product' for r in absent),
                    'verified_absence': sum(r['status'] == 'verified_absence' for r in absent),
                    'L_absent_as_0': round(sum(judged) / len(mine), 1),
                    'L_absent_excluded': round(sum(judged) / len(judged), 1)})
    out.sort(key=lambda r: -r['L_absent_as_0'])
    path = HERE / f'results/model-means-{rubric.VERSION}.csv'
    with path.open('w', newline='') as handle:
        w = csv.DictWriter(handle, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    for r in out:
        print(r)



def a4_summary():
    """Before (A1) vs after (A4 self, external) per task and model; after counts (the author), before is the check."""
    a1 = {}
    for path in glob.glob(str(HERE / f'results/pass-A1-A2-A3-C0?-{rubric.VERSION}.json')):
        for c in json.loads(Path(path).read_text())['rows']:
            if c['phase'] == 'A1':
                a1[(c['task'], c['model'])] = c.get('L_mean')
    cells = {r['attempt']: r for r in csv.DictReader((HERE / 'keys/A4-cells.csv').open())}
    rows = {}
    for path in glob.glob(str(HERE / f'results/pass-A4_external_review-A4_self_review-C0?-{rubric.VERSION}.json')):
        for c in json.loads(Path(path).read_text())['rows']:
            k = (c['task'], c['model'])
            r = rows.setdefault(k, {'task': k[0], 'model': k[1], 'before_A1': round(a1[k], 2)})
            arm = 'self' if c['phase'] == 'A4_self_review' else 'external'
            r[arm] = round(c['L_mean'], 2)
            r[f'{arm}_delta'] = round(c['L_mean'] - a1[k], 2)
            info = cells[c['final_attempt_id']]
            r[f'{arm}_revision'] = info['branch_state'] + (' (seed unchanged)' if info['no_op_snapshot'] == 'True' else '')
    out = sorted(rows.values(), key=lambda r: (r['task'], r['model']))
    path = HERE / f'results/a4-before-after-{rubric.VERSION}.csv'
    with path.open('w', newline='') as handle:
        w = csv.DictWriter(handle, fieldnames=['task', 'model', 'before_A1', 'self', 'self_delta', 'self_revision',
                                               'external', 'external_delta', 'external_revision'])
        w.writeheader()
        w.writerows(out)
    import statistics as st
    for m in sorted({r['model'] for r in out}):
        mine = [r for r in out if r['model'] == m]
        print(m, *(round(st.fmean(r[k] for r in mine), 1) for k in ('before_A1', 'self', 'external')))
    for t in sorted({r['task'] for r in out}):
        mine = [r for r in out if r['task'] == t]
        print(t, *(round(st.fmean(r[k] for r in mine), 1) for k in ('before_A1', 'self', 'external')))
    print('all', *(round(st.fmean(r[k] for r in out), 1) for k in ('before_A1', 'self', 'external')))


if __name__ == '__main__':
    main()
