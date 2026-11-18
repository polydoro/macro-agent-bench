"""Manual-review helper: print latest-period rows of a delivery's saved tables (raw downloads excluded)."""
import sys, json
import code_check as C, references as R
from run_pass import cells, REPO
task, who = sys.argv[1], sys.argv[2:]  # who: phase:model
res = {(c['phase'], c['model']): c for c in json.load(open(f'results/code-check-{task}.json'))}
for row, _ in cells({'A1', 'A2', 'A3'}, {task}):
    if f"{row['phase']}:{row['model']}" not in who:
        continue
    refs, _ = R.references(task, row['phase'], row['model'])
    per = next(iter(refs.values()))['period']
    want = {'2026Q4', '2026Q3'} if task == 'S11' else {per[:7]}
    wd = REPO / 'execucoes' / row['source_campaign_id'] / 'attempts' / row['final_attempt_id'] / 'work'
    print('#####', row['phase'], row['model'], {q[2:]: v['status'] for q, v in res[(row['phase'], row['model'])]['checks'].items() if v['status'] in ('fail', 'none')})
    for path, rel in C.candidate_files(str(wd)):
        try:
            gs = list(C.grids(path))
        except Exception:
            continue
        for g in gs:
            if not g: continue
            hdr = [str(x)[:22] for x in g[0]]
            hits = [r for r in g[1:] if C.period_ok(C.periods(' '.join(str(y) for y in r if C.num(y) is None and y not in (None, ''))), want, 'Q' in per)]
            if not hits and len(g) < 40:
                hits = g[1:]
            if not hits: continue
            print('  --', rel, '|', ' ; '.join(hdr)[:600])
            for r in hits[:12]:
                print('     ', ' ; '.join(str(x)[:25] for x in r)[:600])
