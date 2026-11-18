"""Score-vs-time frontier by method, from results/deliveries.csv.

One point per model and method: y = mean total score over the tasks (a run with no delivery counts as 0),
x = median minutes per task. A frontier keeps each point that scores higher than every faster point.

    python analysis/frontier.py          # prints the frontiers for all 16 tasks, simple (11) and complex (5)
"""
import collections
import csv
import os
import random
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, '..', 'results', 'deliveries.csv')
METHODS = ['low_effort', 'high_effort', 'examples', 'self_review', 'external_review']


def load(path=DATA):
    rows = list(csv.DictReader(open(path, newline='')))
    return {(r['suite'], r['task'], r['model'], r['method']): r for r in rows}


CELLS = load()
MODELS = sorted({k[2] for k in CELLS})
TASKS = {s: sorted({k[1] for k in CELLS if k[0] == s}) for s in 'SC'}


def total(r):
    return float(r['total']) if r['total'] else 0.0


def points(tasks):
    out = []
    for m in MODELS:
        for a in METHODS:
            rows = [CELLS[(s, t, m, a)] for s, t in tasks]
            minutes = [float(r['minutes']) for r in rows if r['minutes']]
            out.append((st.median(minutes), st.mean(total(r) for r in rows), m, a))
    return out


def frontier(pts):
    keep, best = [], -1.0
    for p in sorted(pts, key=lambda p: (p[0], -p[1])):
        if p[1] > best + 1e-9:
            keep.append(p)
            best = p[1]
    return keep


def all_tasks():
    return [('S', t) for t in TASKS['S']] + [('C', t) for t in TASKS['C']]


def report(tasks, label):
    pts = points(tasks)
    print(f'\n## {label}')
    print('Overall frontier: ' + ' -> '.join(f'{a} {m} ({t:.1f} min, {s:.1f})' for t, s, m, a in frontier(pts)))
    for a in METHODS:
        print(f'- {a}: ' + '; '.join(f'{m} ({t:.1f}, {s:.1f})' for t, s, m, _ in frontier([p for p in pts if p[3] == a])))


def paired(tasks, a, b, draws=10000, seed=7):
    """Mean score difference a - b over the same tasks (a, b = (model, method)), with a 90% interval from a
    bootstrap over tasks, resampled within simple and complex tasks separately."""
    diff = {k: total(CELLS[(k[0], k[1]) + a]) - total(CELLS[(k[0], k[1]) + b]) for k in tasks}
    strata = [[k for k in tasks if k[0] == s] for s in 'SC']
    strata = [g for g in strata if g]
    rng = random.Random(seed)
    means = sorted(st.mean(diff[rng.choice(g)] for g in strata for _ in g) for _ in range(draws))
    return st.mean(diff.values()), means[int(0.05 * draws)], means[int(0.95 * draws)]


if __name__ == '__main__':
    report(all_tasks(), 'All 16 tasks')
    report([('S', t) for t in TASKS['S']], 'Simple tasks (11)')
    report([('C', t) for t in TASKS['C']], 'Complex tasks (5)')
    print('\n## Top of high effort vs top of examples (paired over tasks, 90% interval)')
    for label, tasks, a, b in [
        ('All 16 tasks', all_tasks(), ('GPT-6 Astra', 'high_effort'), ('Fable 5.1', 'examples')),
        ('Simple tasks', [('S', t) for t in TASKS['S']], ('GPT-6.1 Sol', 'high_effort'), ('Fable 5.1', 'examples')),
    ]:
        d, lo, hi = paired(tasks, a, b)
        print(f'- {label}: {a[0]} {a[1]} minus {b[0]} {b[1]} = {d:+.1f} [{lo:+.1f}, {hi:+.1f}]')
