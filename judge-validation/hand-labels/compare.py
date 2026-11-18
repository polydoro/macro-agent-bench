"""Compare the author's blind hand labels with Jev's stored answers. No API calls.

Usage (from visual-rubric-v1/ on branch claude/project-thread-x7r67z):
  python compare.py <labels_dir>   # labels_dir/labels/Dxx.json, from ArtifactData list with out_dir
Outputs per-question rows (compare-rows.csv) and a summary on stdout.
"""
import csv, json, sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
KEY = json.load(open(HERE / 'sample-key-DO-NOT-SHOW.json'))
VAL = {'ATENDE': 1.0, 'PARCIAL': 0.5, 'NAO_ATENDE': 0.0, 'NAO_MOSTRADO': 0.0}
# Binary comparison: the author flags only problems; anything unflagged in a reviewed delivery is Atende.
sys.path.insert(0, '.')
import rubric


def jev(task, phase, model):
    vis = {(r['phase'], r['model']): r for r in json.load(open(f'results/pass-A1-A2-A3-{task}-visual-rubric-v1-provisional-7.json'))['rows']}[(phase, model)]
    num = {(r['phase'], r['model']): r for r in json.load(open(f'results/numeric-A1-A2-A3-{task}-visual-rubric-v1-provisional-7.json'))['rows']}[(phase, model)]
    out = defaultdict(lambda: {'choices': [], 'value': []})
    for rep in vis['repeats']:
        rec = json.load(open(f"responses/{rep['request_sha256']}/r{rep['repeat']}.json"))
        for q, a in rec['response']['answers'].items():
            out[q]['choices'].append(a['choice'])
            out[q]['value'].append(sum(VAL.get(o, 0) * v for o, v in a['probabilities'].items()))  # same as L: undetermined mass counts 0
    for rep in num['repeats']:
        for q, c in rep['choices'].items():
            ok = c in rep['admitted'].get(q, [])
            out[q]['choices'].append('ATENDE' if ok else c)
            out[q]['value'].append(1.0 if ok else 0.0)
    return out, num['references']


def main(labels_dir):
    rows = []
    for k in KEY:
        f = Path(labels_dir) / 'labels' / f"{k['code']}.json"
        if not f.exists():
            continue
        lab = json.load(open(f)); lab = lab.get('data', lab)
        if not lab.get('done'):
            continue
        ans = lab.get('answers', {})
        j, refs = jev(k['task'], k['phase'], k['model'])
        specs = rubric.questions(k['task'])
        for q, spec in specs.items():
            if q not in j:
                continue
            a = ans.get(q, {})
            human_ok = not (a.get('choice') and a['choice'] != 'ATENDE')  # unflagged = Atende (the author, 2026-11-17)
            ch = j[q]['choices']
            if spec['kind'] == 'numeric':  # human: printed and legible; Jev: chose a value range (shown), band_ok kept apart
                jev_ok = sum(c not in ('NAO_MOSTRADO', 'NAO_VERIFICAVEL') for c in ch) / len(ch)
            else:
                jev_ok = sum(c == 'ATENDE' for c in ch) / len(ch)
            jv = [v for v in j[q]['value'] if v is not None]
            rows.append({**{x: k[x] for x in ('code', 'task', 'phase', 'model')}, 'q': q, 'kind': spec['kind'],
                         'weight': spec['weight'], 'group': spec['group'] or '', 'human_ok': int(human_ok),
                         'jev_ok_share': round(jev_ok, 3), 'jev_choices': '|'.join(ch),
                         'jev_points_share': round(sum(jv) / len(jv), 3) if jv else None})
    with open(HERE / 'compare-rows.csv', 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    def summ(key):
        g = defaultdict(list)
        for r in rows:
            g[key(r)].append(r)
        for name, rs in sorted(g.items()):
            agree = sum((r['jev_ok_share'] >= 0.5) == bool(r['human_ok']) for r in rs) / len(rs)
            bias = sum((r['jev_ok_share'] - r['human_ok']) * r['weight'] for r in rs)
            print(f'{str(name):28s} n={len(rs):3d} agree={agree:.2f} jev-minus-human weighted={bias:+.1f}')
    print('By kind'); summ(lambda r: r['kind'])
    print('By model'); summ(lambda r: r['model'])
    print('By task'); summ(lambda r: r['task'])


if __name__ == '__main__':
    main(sys.argv[1])
