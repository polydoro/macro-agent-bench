"""A4 before/after, same rubric: after = the revision (the score that counts), before = the seed it started from
(only a check). A seed that is the scored A1 delivery keeps that A1 score; the five that differ were scored
separately (pass-/numeric-A4seed-*); a seed without charts scores 0.
  python build_a4_compare.py  ->  results/a4-before-after-provisional-7.csv, plus means by model and arm.
"""
import csv, json, statistics
from collections import defaultdict
import rubric
from a4_cells import a4_cells, seed_cells

V = rubric.VERSION
a1 = {(r['task'], r['model']): r for r in csv.DictReader(open('results/score-100-A1-A2-A3-S01-S11-provisional-7.csv')) if r['phase'] == 'A1'}
after = {(r['task'], r['phase'], r['model']): r for r in csv.DictReader(open('results/score-100-A4-S01-S11-provisional-7.csv'))}
seed_vis = {(r['task'], r['model']): r.get('L_mean', 0.0) if r['status'] == 'judged' else 0.0
            for r in json.load(open(f'results/pass-A4seed-S02-S05-S10-{V}.json'))['rows']}
seed_num = {}
for t in ('S02', 'S05', 'S10'):
    for r in csv.DictReader(open(f'results/numeric-combined-A4seed-{t}.csv')):
        seed_num[(t, r['model'])] = float(r['N_total'])
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
with open('results/a4-before-after-provisional-7.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0]))
    w.writeheader(); w.writerows(out)

g = defaultdict(list)
for r in out:
    g[(r['model'], r['arm'])].append(r)
print(f"{'model':20s} arm  n  before  after  delta")
for (m, arm), rs in sorted(g.items()):
    f = lambda c: statistics.fmean(r[c] for r in rs)
    print(f"{m:20s} {arm} {len(rs):2d} {f('before_100'):6.1f} {f('after_100'):6.1f} {f('delta'):+6.1f}")
