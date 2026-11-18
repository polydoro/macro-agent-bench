"""Run code_check over every cell of a task; write results/code-check-<task>.json.
`python run_code_check.py S03 A4` checks the A4 revisions instead (results/code-check-A4-<task>.json):
each release admitted for A4 is checked at its own period, and a value counts if it matches any."""
import json, sys
import code_check as C, references as R
from run_pass import cells, REPO
from a4_cells import a4_cells, seed_cells

task = sys.argv[1]
a4 = sys.argv[2:] == ['A4']
seed = sys.argv[2:] == ['A4seed']  # before-revision seeds that differ from the A1 delivery (A1 key)
RANK = {'auto': 3, 'ambiguous': 2, 'fail': 1, 'none': 0}


def check_a4(task, wd, refs):
    """One check per release (period), merged per question: correct under any release wins."""
    by_period = {}
    for q, r in refs.items():
        for per, vs in r['periods']:
            by_period.setdefault(per, {})[q] = {**r, 'variants': [(f'[{per}]', v, t) for v, t in vs]}
    merged = {}
    for per, rs in by_period.items():
        for q, v in C.check(task, wd, rs, per.replace('-Q', 'Q') if task == 'S08' else per).items():
            old = merged.get(q)
            if old is None or (v['correct'], RANK[v['status']]) > (old['correct'], RANK[old['status']]):
                merged[q] = v
    return merged


out = []
source = a4_cells({task}) if a4 else seed_cells({task}) if seed else cells({'A1', 'A2', 'A3'}, {task})
for row, images in source:
    cell = {k: row[k] for k in ('phase', 'task', 'model', 'final_attempt_id', 'disposition')}
    if row['disposition'] == 'verified_absence':
        out.append({**cell, 'checks': {}}); continue
    refs, fixed = R.references(task, row['phase'], row['model'])
    refs = {q: r for q, r in refs.items() if q not in fixed}
    if a4:
        checks = check_a4(task, row['workdir'], refs)
    else:
        period = next(iter(refs.values()))['period']
        wd = REPO / 'execucoes' / row['source_campaign_id'] / 'attempts' / row['final_attempt_id'] / 'work'
        checks = C.check(task, str(wd), refs, period[:7] if task != 'S11' else period)
    out.append({**cell, 'fixed': list(fixed), 'checks': checks})
json.dump(out, open(f"results/code-check-{'A4-' if a4 else 'A4seed-' if seed else ''}{task}.json", 'w'), ensure_ascii=False, indent=1)
for c in out:
    ch = c['checks']
    print(c['phase'], f"{c['model']:20s}", f"{sum(1 for v in ch.values() if v['correct'])}/{len(ch)}", ' '.join(f"{q[2:]}:{v['status']}" for q, v in ch.items() if v['status'] != 'auto'))
