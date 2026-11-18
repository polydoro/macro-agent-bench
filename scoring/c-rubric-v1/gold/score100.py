"""100-point C-task score per delivery: result 50 + method 50 (the author, 2026-11-17).

result  = numbers correct 30 (code check on saved tables, share of N_ questions matched)
        + numbers shown 10 (block D of the method pass, read by Jev, rescaled from 20)
        + gold answer 10 (Jev verdict category vs gold; C03: nowcast accuracy, code)
method  = blocks A, B, C, E of c-rubric-v1-4 (80 points) rescaled to 50.

A4: before = A1 (all seeds byte-identical); the after rows (A4_self_review, A4_external_review) count.
Numbers: code check plus hand-checked overrides (results/manual-overrides-C.json); C04 from gold/c04_check.py. C03 accuracy (results/C03-nowcast-q3.csv): every delivery that nowcasts 2026-Q3 is scored against the Q3 flash
(0.42 q/q); deliveries that nowcast only Q4 (all A2, A3, six A4 self reviews) get 'pending Q4 flash' and their other
90 points rescaled to 100, until the Q4 flash (about 2027-01-30).

usage: python gold/score100.py   -> results/score-100-C-c-gold-provisional-2[-legible-recheck].csv
"""
import csv
import glob
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

HERE = Path(__file__).resolve().parent
RES = HERE.parent / 'results'
VERSION = 'c-gold-provisional-2'  # -1: C03 A1 only; -2: C03 scored on Q3 for every delivery that nowcasts Q3


def nowcast_points(err, naive_err=None):
    """Plain error: 10 within 0.1 pp, linear to 0 at 0.5 pp. Relative: same shape on (|err| - |naive err|)."""
    e = abs(err) if naive_err is None else max(abs(err) - abs(naive_err), 0.0)
    return 10.0 * min(1.0, max(0.0, (0.5 - e) / 0.4))


def legible_d(c, reads):
    """Block D from the blind recheck: 1 per question read as shown with an admitted value, else 0; best-K as in run_pass."""
    import rubric
    t = rubric.TASKS[c['task']]
    k = t['numeric_best_k']
    w = t.get('numeric_points', 20) / k
    got = reads.get(f"{c['task']}|{c['phase']}|{c['model']}", {})
    vals = sorted((w * got.get(q, 0.0) for q in c['references'] if q.startswith('N_')), reverse=True)
    target = 0.0
    if 'target' in t:  # C03 T_target stays as Jev scored it: block D minus Jev's best-K numeric part
        target = statistics.fmean(rep['blocks']['D'] for rep in c['repeats']) - _jev_numeric(c, w, k)
    return sum(vals[:k]) + target


def _jev_numeric(c, w, k):
    import references as R
    out = []
    for rep in c['repeats']:
        v = sorted((w * (rep['choices'].get(q) in R.blind(ref)[1]) for q, ref in c['references'].items()
                    if q.startswith('N_') and not ref.get('fixed')), reverse=True)
        out.append(sum(v[:k]))
    return statistics.fmean(out)


def main(recheck=None):
    reads = json.loads(Path(recheck).read_text()) if recheck else None
    method = {}
    for path in glob.glob(str(RES / 'pass-A*-C0?-c-rubric-v1-4.json')):
        if 'cells' in path:
            continue
        for c in json.loads(Path(path).read_text())['rows']:
            method[(c['task'], c['phase'], c['model'])] = c
    overrides = json.loads((RES / 'manual-overrides-C.json').read_text())
    numbers = {}
    for t in ('C01', 'C02', 'C03', 'C04', 'C05'):
        for c in json.loads((RES / f'code-check-{t}.json').read_text()):
            ok = {o['question'] for o in overrides.get(t, []) if (o['phase'], o['model']) == (c['phase'], c['model']) and o['correct']}
            qs = [{**v, 'correct': v['correct'] or q in ok} for q, v in c['questions'].items()]
            numbers[(t, c['phase'], c['model'])] = 30.0 * sum(q['correct'] for q in qs) / len(qs) if qs else 0.0
    verdict = {}
    for t in ('C01', 'C02', 'C04', 'C05'):
        for c in json.loads((RES / f'verdict-{t}-c-gold-verdict-v1.json').read_text()):
            verdict[(t, c['phase'], c['model'])] = c['points']
    naive = 0.6 - 0.42  # Q2 q/q carried forward against the Q3 flash
    q4_only = set()
    for r in csv.DictReader((RES / 'C03-nowcast-q3.csv').open()):  # Q3 flash 0.42 as the realised value (the author, 2026-11-17)
        k = ('C03', r['phase'], r['model'])
        if r['target'] == '2026-Q4':  # ran after the Q3 flash, nowcasts Q4 only: no accuracy until the Q4 flash
            q4_only.add(k)
            continue
        err = float(r['error_pp']) if r['error_pp'] != '' else None
        verdict[k] = nowcast_points(err) if err is not None else 0.0
        verdict[(*k, 'rel')] = nowcast_points(err, naive) if err is not None else 0.0

    rows = []
    for (t, ph, m), c in sorted(method.items()):
        b = c.get('blocks_mean') or {}
        judged = c['status'] == 'judged'
        meth = 50.0 / 80.0 * sum(b.get(k, 0.0) for k in 'ABCE') if judged else 0.0
        shown = (0.5 * (legible_d(c, reads) if reads is not None else b.get('D', 0.0))) if judged else 0.0
        num = numbers.get((t, ph, m))
        if not judged:
            num = 0.0
        ver = verdict.get((t, ph, m))
        if ver is None and not judged and (t, ph, m) not in q4_only:
            ver = 0.0
        row = {'task': t, 'phase': ph, 'model': m, 'status': c['status'], 'method_50': meth, 'numbers_30': num,
               'shown_10': shown, 'answer_10': ver, 'answer_10_c03_relative': verdict.get((t, ph, m, 'rel'), '')}
        parts = [meth, num, shown, ver]
        row['total_100'] = sum(parts) if None not in parts else None
        if (t, ph, m) in q4_only and judged:  # accuracy not scorable yet: the other 90 points rescaled to 100
            row['total_100'] = (meth + num + shown) * 100 / 90
            row['answer_10'] = 'pending Q4 flash'
        row['old_L'] = c.get('L_mean') if judged else 0.0
        rows.append(row)
    out = RES / f"score-100-C-{VERSION}{'-legible-recheck' if reads is not None else ''}.csv"
    fields = ['task', 'phase', 'model', 'status', 'total_100', 'method_50', 'numbers_30', 'shown_10', 'answer_10',
              'answer_10_c03_relative', 'old_L']
    with out.open('w', newline='') as h:
        w = csv.DictWriter(h, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: (round(v, 2) if isinstance(v, float) else '' if v is None else v) for k, v in r.items()})
    print(out.name, len(rows), 'rows')
    for t in sorted({r['task'] for r in rows}):
        mine = [r for r in rows if r['task'] == t and r['total_100'] is not None]
        if mine:
            print(t, len(mine), 'scored; mean new', round(statistics.fmean(r['total_100'] for r in mine), 1),
                  'old', round(statistics.fmean(r['old_L'] for r in mine), 1),
                  'sd new', round(statistics.pstdev(r['total_100'] for r in mine), 1),
                  'old', round(statistics.pstdev(r['old_L'] for r in mine), 1))
    ok = [r for r in rows if r['total_100'] is not None and r['task'] in ('C01', 'C02', 'C05')]
    for m in sorted({r['model'] for r in ok}, key=lambda m: -statistics.fmean(r['total_100'] for r in ok if r['model'] == m)):
        mine = [r for r in ok if r['model'] == m]
        print(m.ljust(20), round(statistics.fmean(r['total_100'] for r in mine), 1), 'old', round(statistics.fmean(r['old_L'] for r in mine), 1))


if __name__ == '__main__':
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else None)
