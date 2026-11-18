"""Legibility recheck for the C tasks, step 2: collect the blind readers' result.json files.

shown = 1 if the reader says printed 'yes' and a value it read falls within an admitted variant's tolerance, else 0.
Questions not read stay 0 (no Jev credit and no value found by the code check). Writes
results/legible-recheck-C/reads.json ({"task|phase|model": {qid: 0/1}}) and reads-detail.json (every read, with
Jev's credit), applies results/legible-recheck-C/adjudications.json, and prints removed/added counts. Usage: python gold/legible_collect.py <reader_dir>
"""
import glob
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
RES = HERE.parent / 'results'


def main(src):
    src = Path(src)
    key = json.loads((src / 'key.json').read_text())
    refs = {}
    for path in glob.glob(str(RES / 'pass-A*-C0?-c-rubric-v1-4.json')):
        if 'cells' not in path:
            for r in json.loads(Path(path).read_text())['rows']:
                refs[(r['task'], r['phase'], r['model'])] = r.get('references', {})
    adj = {(a['code'], a['q']): a for a in json.loads((RES / 'legible-recheck-C/adjudications.json').read_text())}
    reads, detail, c, missing = {}, [], Counter(), []
    for code, cell in sorted(key.items()):
        f = src / code / 'result.json'
        if not f.exists():
            missing.append(code)
            continue
        res = {x['id']: x for x in json.loads(f.read_text())}
        ref = refs[(cell['task'], cell['phase'], cell['model'])]
        out = reads.setdefault(f"{cell['task']}|{cell['phase']}|{cell['model']}", {})
        for q, credit in cell['jev_credit'].items():
            x = res.get(q, {'printed': 'missing'})
            vals = [v for v in [x.get('value')] + list(x.get('values') or []) if isinstance(v, (int, float))]
            ok = x['printed'] == 'yes' and any(abs(v - val) <= tol + 1e-9 for v in vals for _, val, tol in ref[q]['variants'])
            if (code, q) in adj:  # hand adjudication of reader inconsistencies (adjudications.json)
                ok = adj[(code, q)]['shown']
            out[q] = 1.0 if ok else 0.0
            c[('credited' if credit else 'uncredited', 'shown' if ok else 'not shown', x['printed'])] += 1
            detail.append({'code': code, **{k: cell[k] for k in ('task', 'phase', 'model')}, 'q': q, 'jev_credit': credit,
                           'printed': x['printed'], 'value': x.get('value'), 'values': x.get('values'), 'where': x.get('where'), 'shown': ok})
    out = RES / 'legible-recheck-C'
    out.mkdir(exist_ok=True)
    (out / 'reads.json').write_text(json.dumps(reads, indent=1, ensure_ascii=False))
    (out / 'reads-detail.json').write_text(json.dumps(detail, indent=1, ensure_ascii=False))
    for k, v in sorted(c.items()):
        print(k, v)
    if missing:
        print('MISSING result.json:', ' '.join(missing))


if __name__ == '__main__':
    main(sys.argv[1])
