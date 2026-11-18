"""100-point score per delivery = visual 60 (Jev pass, mean over repeats) + numeric 40 (combine_numeric).

  python build_score100.py      -> results/score-100-A1-A2-A3-S01-S11-provisional-7.csv
  python build_score100.py A4   -> results/score-100-A4-S01-S11-provisional-7.csv  (A4 revisions, after-revision score)
Verified absences score 0.
"""
import csv, json, sys
import rubric

TASKS = sorted(rubric.TASKS)
a4 = sys.argv[1:] == ['A4']
V = rubric.VERSION

if a4:
    rows = json.load(open(f"results/pass-A4-{'-'.join(TASKS)}-{V}.json"))['rows']
    visual = {(r['task'], r['phase'], r['model']): (r.get('L_mean', 0.0) if r['status'] == 'judged' else 0.0) for r in rows}
else:
    visual = {(r['task'], r['phase'], r['model']): float(r['L_mean_of_60'] or 0)
              for r in csv.DictReader(open(f'results/final-A1-A2-A3-S01-S11-{V}.csv'))}

out = []
for t in TASKS:
    for n in csv.DictReader(open(f"results/numeric-combined-{'A4-' if a4 else ''}{t}.csv")):
        v = 0.0 if n['status'] == 'verified_absence' else visual[(t, n['phase'], n['model'])]
        c, l = float(n['N_correct']), float(n['N_legible'])
        out.append({'task': t, 'phase': n['phase'], 'model': n['model'], 'status': n['status'], 'visual_60': round(v, 2),
                    'numeric_correct_30': c, 'numeric_legible_10': l, 'numeric_40': float(n['N_total']),
                    'total_100': round(v + float(n['N_total']), 2), 'code_paths': n.get('code_paths') or ''})
path = f"results/score-100-{'A4-S01-S11' if a4 else 'A1-A2-A3-S01-S11'}-provisional-7.csv"
with open(path, 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0]))
    w.writeheader(); w.writerows(out)
print('wrote', path, len(out), 'rows')
