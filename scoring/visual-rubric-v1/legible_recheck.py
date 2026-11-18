"""Legibility recheck (2026-11-17): replace Jev's numeric legibility with a strict "is the value printed?" read.

the author's hand labels showed Jev giving legibility credit for values read off unlabelled bars and line ends,
against the printed-only rule. Blind Sonnet readers (no model names; calibrated on the author's 15 labelled
deliveries, 95/95) re-read every question where Jev gave any legibility credit, and every question where Jev gave
none but the code check found the admitted value in the delivery's saved tables. Rule here: legible = 1 if the
reader found the value printed (digits) and it falls in an admitted band, else 0. Other questions stay 0.
Covers A1-A3, the A4 revisions (A4s, A4e) and the five A4 seeds that differ from A1 (A4seed). the author agreed on
2026-11-17 that these corrected scores replace the published ones; the original files stay for the record.

Input:  results/legible-recheck/reads.json  ([{a4?, task, phase, model, q, printed, value, values, where}]; a4 is
        'A4' or 'A4seed', absent for A1-A3)
Output (originals untouched):
  results/legible-recheck/numeric-combined-[A4-|A4seed-]<task>.csv
  results/score-100-A1-A2-A3-S01-S11-provisional-7-legible-recheck.csv
  results/score-100-A4-S01-S11-provisional-7-legible-recheck.csv
  results/a4-before-after-provisional-7-legible-recheck.csv
"""
import contextlib, csv, io, json, os, statistics
from collections import defaultdict
import combine_numeric as CN
import references as R
import rubric
from a4_cells import a4_cells, seed_cells

OUT = 'results/legible-recheck'
V = rubric.VERSION
TASKS = sorted(rubric.TASKS)
SEED_TASKS = ['S02', 'S05', 'S10']

fix = {}
for r in json.load(open(f'{OUT}/reads.json')):
    new, _ = R.references(r['task'], r['phase'], r['model'])
    vals = [x for x in [r.get('value')] + list(r.get('values') or []) if isinstance(x, (int, float))]
    ok = r['printed'] == 'yes' and any(abs(x - v) <= t + 1e-9 for x in vals for _, v, t in new[r['q']]['variants'])
    fix.setdefault((r.get('a4') or '', r['task'], r['phase'], r['model']), {})[r['q']] = 1.0 if ok else 0.0

orig = CN.jev_legibility
def patched(task, a4=False):
    out = orig(task, a4)
    for key, qs in out.items():
        f = fix.get((a4 or '', task, *key), {})
        for q in qs:
            if q in f:
                qs[q] = f[q]
            elif qs[q] > 0:
                raise SystemExit(f'credited question not re-read: {a4} {task} {key} {q}')
    return out
CN.jev_legibility = patched


def combine(task, a4=False):
    """Run combine_numeric into OUT, restoring the published file byte for byte."""
    name = f"numeric-combined-{a4 + '-' if a4 else ''}{task}.csv"
    pub = f'results/{name}'
    keep = open(pub, 'rb').read()
    with contextlib.redirect_stdout(io.StringIO()):
        CN.main(task, a4)
    os.replace(pub, f'{OUT}/{name}')
    open(pub, 'wb').write(keep)
    return list(csv.DictReader(open(f'{OUT}/{name}')))


def write(path, rows):
    with open(path, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print('wrote', path, len(rows), 'rows')


def rescore(published, a4):
    """Same rows as the published 100-point file; numeric part from the recheck, visual 60 unchanged."""
    score = {(r['task'], r['phase'], r['model']): r for r in csv.DictReader(open(published))}
    rows = []
    for t in TASKS:
        for n in combine(t, a4):
            s = score[(t, n['phase'], n['model'])]
            rows.append({**s, 'numeric_legible_10': float(n['N_legible']), 'numeric_40': float(n['N_total']),
                         'total_100': round(float(s['visual_60']) + float(n['N_total']), 2), 'legible_before': s['numeric_legible_10']})
    return rows


os.makedirs(OUT, exist_ok=True)
a13 = rescore('results/score-100-A1-A2-A3-S01-S11-provisional-7.csv', False)
write('results/score-100-A1-A2-A3-S01-S11-provisional-7-legible-recheck.csv', a13)
a4 = rescore('results/score-100-A4-S01-S11-provisional-7.csv', 'A4')
write('results/score-100-A4-S01-S11-provisional-7-legible-recheck.csv', a4)

# A4 before/after, as build_a4_compare.py, on the rechecked scores.
a1 = {(r['task'], r['model']): r for r in a13 if r['phase'] == 'A1'}
after = {(r['task'], r['phase'], r['model']): r for r in a4}
seed_vis = {(r['task'], r['model']): r.get('L_mean', 0.0) if r['status'] == 'judged' else 0.0
            for r in json.load(open(f'results/pass-A4seed-S02-S05-S10-{V}.json'))['rows']}
seed_num = {(t, r['model']): float(r['N_total']) for t in SEED_TASKS for r in combine(t, 'A4seed')}
differ = {(r['task'], r['model']) for r, _ in seed_cells()}
out = []
for row, _ in a4_cells():
    k = (row['task'], row['model'])
    if k in differ:
        before, src = round(seed_vis[k] + seed_num[k], 2), f"seed {row['before_attempt']} (scored separately)"
    else:
        before, src = float(a1[k]['total_100']), 'A1 delivery'
    a = after[(row['task'], row['phase'], row['model'])]
    out.append({'task': row['task'], 'arm': row['phase'], 'model': row['model'], 'after_status': a['status'],
                'before_100': before, 'after_100': float(a['total_100']), 'delta': round(float(a['total_100']) - before, 2),
                'after_visual_60': a['visual_60'], 'after_numeric_40': a['numeric_40'], 'before_source': src})
write('results/a4-before-after-provisional-7-legible-recheck.csv', out)

g = defaultdict(list)
for r in out:
    g[(r['model'], r['arm'])].append(r)
for (m, arm), rs in sorted(g.items()):
    f = lambda c: statistics.fmean(r[c] for r in rs)
    print(f"{m:22s} {arm} {len(rs):2d} before {f('before_100'):6.1f} after {f('after_100'):6.1f} {f('delta'):+6.1f}")
