"""Numeric 40 points = correctness in code (default 30) + legibility on the chart by Jev (default 10).

Per question: value = W_CODE * correct + (1 - W_CODE) * legible, where
  correct = code_check found the admitted value in the delivery's saved tables (latest period),
  legible = share of Jev repeats whose chosen range is an admitted band (the chart prints the right value).
S05/S06 3m SAAR questions fixed by the SA criterion score 0 on both parts. Best-K groups pick the
K best components on the combined value. The split is a code-side weight: changing it needs no API call.

Usage: python combine_numeric.py S01 [S02 ...]  ->  results/numeric-combined-<task>.csv
       python combine_numeric.py --a4 S01 [...]   ->  results/numeric-combined-A4-<task>.csv (A4 revisions)
       python combine_numeric.py --a4seed S10     ->  results/numeric-combined-A4seed-<task>.csv (seeds that differ from A1)
"""
import csv
import json
import os
import re
import sys

import aggregate
import references as R
from run_numeric import numeric_questions
import rubric

W_CODE = 0.75


def band_ok(old_ref, choice, new_ref):
    """Is Jev's chosen range (built from the reference sent at the time) inside an admitted band of the
    current reference? Lets a later key correction be applied without a new call."""
    if not choice or not choice.startswith('FAIXA_'):
        return False
    text = R.blind(old_ref)[0][choice]
    lo, hi = (float(x) for x in re.findall(r'entre (-?\d+\.\d+) e (-?\d+\.\d+)', text)[0])
    mid = (lo + hi) / 2
    return any(abs(mid - v) <= t + 1e-9 for _, v, t in new_ref['variants'])


ALL = '-'.join(sorted(rubric.TASKS))


def jev_legibility(task, a4=False):
    path = f'results/numeric-A1-A2-A3-{task}-{rubric.VERSION}.json'
    if a4 == 'A4seed':
        path = f'results/numeric-A4seed-S02-S05-S10-{rubric.VERSION}.json'
    elif a4:  # a per-task rerun (S02, after its September key was added) wins over the all-task pass
        path = f'results/numeric-A4-{task}-{rubric.VERSION}.json'
        if not os.path.exists(path):
            path = f'results/numeric-A4-{ALL}-{rubric.VERSION}.json'
    out = {}
    for r in json.load(open(path))['rows']:
        if r['status'] != 'judged' or r['task'] != task:
            continue
        new, _ = R.references(task, r['phase'], r['model'])
        reps = r['repeats']
        out[(r['phase'], r['model'])] = {q: sum(band_ok(r['references'][q], rep['choices'].get(q), new[q]) for rep in reps) / len(reps)
                                         for q in reps[0]['choices']}
    return out


def overrides(task, a4=False):
    """Manual strict mapping where the automatic check failed, found no table or was ambiguous.
    results/manual-overrides-<task>.json: [{phase, model, question, correct, note}], each with the file, period and value."""
    try:
        return {(o['phase'], o['model'], o['question']): o['correct'] for o in json.load(open(f"results/manual-overrides-{a4 + '-' if a4 else ''}{task}.json"))}
    except FileNotFoundError:
        return {}


def main(task, a4=False):
    pre = f'{a4}-' if a4 else ''
    qs, gs = numeric_questions(task)
    leg = jev_legibility(task, a4)
    manual = overrides(task, a4)
    rows = []
    for c in json.load(open(f'results/code-check-{pre}{task}.json')):
        key = (c['phase'], c['model'])
        if not c['checks']:
            rows.append({'phase': c['phase'], 'task': task, 'model': c['model'], 'status': 'verified_absence',
                         'N_total': 0.0, 'N_correct': 0.0, 'N_legible': 0.0})
            continue
        lg = leg.get(key, {})
        parts = {}
        for q in qs:
            code = 1.0 if c['checks'].get(q, {}).get('correct') else 0.0
            if (c['phase'], c['model'], q) in manual:
                code = 1.0 if manual[(c['phase'], c['model'], q)] else 0.0
                c['checks'].setdefault(q, {})['status'] = 'manual'
            vis = lg.get(q, 0.0)
            if q in c.get('fixed', []):
                code = vis = 0.0
            parts[q] = (code, vis)

        def total(fn):
            ans = {q: {'ATENDE': fn(*v), 'NAO_ATENDE': 1 - fn(*v)} for q, v in parts.items()}
            return aggregate.score(qs, gs, ans)['L']
        rows.append({'phase': c['phase'], 'task': task, 'model': c['model'], 'status': 'scored',
                     'N_total': round(total(lambda a, b: W_CODE * a + (1 - W_CODE) * b), 2),
                     'N_correct': round(W_CODE * total(lambda a, b: a), 2),
                     'N_legible': round((1 - W_CODE) * total(lambda a, b: b), 2),
                     'code_paths': ' '.join(f"{q[2:]}:{v['status']}" for q, v in c['checks'].items() if v['status'] != 'auto')})
    rows.sort(key=lambda r: (r['phase'], r['model']))
    with open(f'results/numeric-combined-{pre}{task}.csv', 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=['phase', 'task', 'model', 'status', 'N_total', 'N_correct', 'N_legible', 'code_paths'])
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(r['phase'], f"{r['model']:20s}", f"{r['N_total']:5.1f} = correct {r['N_correct']:4.1f} + legible {r['N_legible']:4.1f}")


if __name__ == '__main__':
    a4 = 'A4' if '--a4' in sys.argv else 'A4seed' if '--a4seed' in sys.argv else False
    for t in [x for x in sys.argv[1:] if not x.startswith('--')]:
        print('==', t)
        main(t, a4)
