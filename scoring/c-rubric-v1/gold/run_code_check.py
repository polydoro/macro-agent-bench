"""Code check of the C numeric questions (gold numbers) on each delivery's saved tables, no Jev.

For every judged cell of a task (A1-A3 and the A4 revisions), reads the agent's own CSV/XLSX under work/
with code_check.py and the same references as the Jev numeric block (references.py; A4: seed's release
or newer). C04 is mapped by hand (revision definitions differ by agent) and is not run here.
Writes results/code-check-<task>.json and prints status counts.
Usage: python gold/run_code_check.py C01
"""
import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import code_check as CC  # noqa: E402
import references as R  # noqa: E402
import run_pass  # noqa: E402

PHASES = {'A1', 'A2', 'A3', 'A4_self_review', 'A4_external_review'}


def main(task):
    out = []
    counts = collections.Counter()
    for row, entrega in run_pass.cells(PHASES, task):
        if row['disposition'] == 'verified_absence' or not entrega.exists():
            continue
        refs = {q: r for q, r in R.references(task, row['final_attempt_id']).items() if q.startswith('N_')}
        by_period = collections.defaultdict(dict)
        for q, r in refs.items():
            by_period[tuple(r.get('periods') or [r['period']])][q] = r
        res = {}
        for periods, group in by_period.items():
            res.update(CC.check(task, entrega.parent, group, set(periods)))
        for q, r in refs.items():
            if r.get('fixed'):  # C05 SA rule decided in code
                res[q] = {**res.get(q, {}), 'status': 'sa_rule', 'correct': False, 'note': r.get('fixed_reason')}
        for v in res.values():
            counts[v['status']] += 1
        out.append({'phase': row['phase'], 'model': row['model'], 'attempt': row['final_attempt_id'], 'questions': res})
        print(row['phase'][:7], row['model'][:12].ljust(12), {q: (v['status'], v['correct']) for q, v in res.items()}, flush=True)
    (HERE.parent / 'results').mkdir(exist_ok=True)
    (HERE.parent / f'results/code-check-{task}.json').write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(task, dict(counts))


if __name__ == '__main__':
    main(sys.argv[1])
