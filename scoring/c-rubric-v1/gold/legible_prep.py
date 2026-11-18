"""Legibility recheck for the C tasks, step 1: build blind reader folders (no Jev).

Same method as the S tasks (PR #4, visual-rubric-v1/legible_recheck.py): blind Sonnet readers decide, per question,
whether the delivery shows the value as digits. The C rubric's block D also counts a value written in the report
text, so each question carries the report snippets (about 150 characters around every number that falls within an
admitted variant's tolerance); the reader says whether a snippet or a chart label states that series at that period.

Questions read: every N_ question where Jev gave legibility credit in any repeat, plus uncredited questions where the
code check found the admitted value in the delivery (results/code-check-<task>.json and manual overrides).
Output: <out>/<code>/{questions.json, imgN.png} and <out>/key.json (code -> cell; never shown to readers).
Usage: python gold/legible_prep.py <out_dir>
"""
import glob
import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path[:0] = [str(HERE.parent), str(HERE)]
import judge  # noqa: E402
import references as R  # noqa: E402
import run_pass  # noqa: E402

REPO = HERE.parent.parent
RES = HERE.parent / 'results'
NUM = re.compile(r'(?<![\d.,])[-−–+]?\d{1,3}(?:[.,]\d{1,4})?(?![\d])')


def snippets(text, variants, limit=8):
    """Each line holding a number within an admitted tolerance; a table row comes with its header row."""
    out, lines, header = [], text.splitlines(), None
    for i, line in enumerate(lines):
        st = line.strip()
        if st.startswith('|'):
            if header is None or not (i and lines[i - 1].strip().startswith('|')):
                header = st
        else:
            header = None
        for m in NUM.finditer(line):
            v = float(m.group(0).replace(',', '.').replace('−', '-').replace('–', '-'))
            if any(abs(v - val) <= tol + 1e-9 for _, val, tol in variants):
                if st.startswith('|'):
                    snip = st[:300] if st == header else f'[table header] {header[:250]} [row] {st[:300]}'
                else:
                    snip = ' '.join(line[max(0, m.start() - 200): m.end() + 80].split())
                if snip not in out:
                    out.append(snip)
                break
        if len(out) >= limit:
            break
    return out


def main(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    found = {}
    over = json.loads((RES / 'manual-overrides-C.json').read_text())
    for t in ('C01', 'C02', 'C03', 'C04', 'C05'):
        for c in json.loads((RES / f'code-check-{t}.json').read_text()):
            ok = {o['question'] for o in over.get(t, []) if (o['phase'], o['model']) == (c['phase'], c['model'])}
            for q, v in c['questions'].items():
                if v['correct'] or q in ok:
                    found[(t, c['phase'], c['model'], q)] = True
    entregas = {}
    for t in ('C01', 'C02', 'C03', 'C04', 'C05'):
        for row, e in run_pass.cells({'A1', 'A2', 'A3', 'A4_self_review', 'A4_external_review'}, t):
            entregas[(t, row['phase'], row['model'])] = e
    key, n, qn = {}, 0, 0
    for path in sorted(glob.glob(str(RES / 'pass-A*-C0?-c-rubric-v1-4.json'))):
        if 'cells' in path:
            continue
        for r in json.loads(Path(path).read_text())['rows']:
            if r['status'] != 'judged':
                continue
            cell = (r['task'], r['phase'], r['model'])
            text = judge.report_text(entregas[cell])
            qs = []
            for q, ref in r['references'].items():
                if not q.startswith('N_') or ref.get('fixed'):
                    continue
                adm = R.blind(ref)[1]
                credit = sum(rep['choices'].get(q) in adm for rep in r['repeats']) / len(r['repeats'])
                if not credit and not found.get((*cell, q)):
                    continue
                periods = ref.get('periods') or [ref['period']]
                qs.append({'id': q, 'jev_credit': credit, 'periods': periods, 'unit': ref.get('unit', ''),
                           'admitted_series': [lab for lab, _, _ in ref['variants']],
                           'text_snippets': snippets(text, ref['variants'])})
            if not qs:
                continue
            n += 1
            code = f'L{n:03d}'
            d = out / code
            d.mkdir(exist_ok=True)
            for i, img in enumerate(r['images'], 1):
                shutil.copy(REPO / img, d / f'img{i}{Path(img).suffix.lower()}')
            (d / 'questions.json').write_text(json.dumps(
                [{k: v for k, v in q.items() if k != 'jev_credit'} for q in qs], indent=1, ensure_ascii=False))
            key[code] = {'task': r['task'], 'phase': r['phase'], 'model': r['model'],
                         'jev_credit': {q['id']: q['jev_credit'] for q in qs}}
            qn += len(qs)
    (out / 'key.json').write_text(json.dumps(key, indent=1, ensure_ascii=False))
    print(n, 'folders', qn, 'questions')


if __name__ == '__main__':
    main(sys.argv[1])
