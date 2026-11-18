"""C04 numbers: mean revisions by horizon, read from each delivery's saved summary tables (no Jev).

A candidate is a cell in a 'mean' column (media, mean, revisao_media...) of a small table (at most 40 rows), on a row
whose label names a horizon. Horizons map to the key's groups: short (second release, ~3 months, first quarterly
revision), one_year, two_years, three_years, latest (current or final vintage). Measure is yoy if the row, header or
file name says so, else qoq. A question is correct if any candidate matches any admitted variant of the key
(references._c04: BBKRT samples 2005-2019, 2005-latest, ex 2020-21; q/q also annualised). Where the delivery shows
no candidate for a question, the report text is searched the same way (gold/report_search.py logic is not reused:
here the label and the number must sit in one table row of the report).
Writes results/code-check-C04.json in the same shape as run_code_check.py.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path[:0] = [str(HERE.parent), str(HERE)]
import code_check as CC  # noqa: E402
import judge  # noqa: E402
import references as R  # noqa: E402
import run_pass  # noqa: E402

PHASES = {'A1', 'A2', 'A3', 'A4_self_review', 'A4_external_review'}
MEAN = re.compile(r'^(m[eé]dia|mean|revis[aã]o[ _]m[eé]dia|mean[ _]rev\w*|m[eé]dia[ _]revis\w*)([ _]?\(?p\.?p\.?\)?|[ _]pp)?$', re.I)
HORIZON = [  # order matters: first match wins
    ('latest', r'quarta revis[aã]o anual|atual|vigente|[uú]ltim|latest|final|current'),
    ('three_years', r'terceira revis[aã]o anual|\b3\s*a(nos)?\b|3 years|3ª revis[aã]o anual|\bh12\b|r12|\+3 anos|36\s*m'),
    ('two_years', r'segunda revis[aã]o anual|\b2\s*a(nos)?\b|2 years|2ª revis[aã]o anual|\bh8\b|r8|\+2 anos|24\s*m'),
    ('one_year', r'primeira revis[aã]o anual|\b1\s*a(no)?\b|1 year|1ª revis[aã]o anual|\bh4\b|r4|\+1 ano|12\s*m|cerca de 1 ano'),
    ('short', r'segund|2ª publica|second|next|\b3\s*m\b|1ª revis[aã]o trimestral|detalhad|t\+55|\+1 trimestre|\bh1\b|primeira revis[aã]o trimestral'),
]
YOY = re.compile(r'yoy|a/a|anual(?!iz)|vorjahr|year.?on.?year', re.I)


def horizon(label):
    s = label.lower()
    if re.search(r'4 anos|\+4|h16|5 anos', s) and not re.search(r'quarta revis', s):
        return None
    return next((g for g, rx in HORIZON if re.search(rx, s)), None)


def candidates(entrega):
    for path, rel in CC.candidate_files(entrega.parent):
        try:
            grids = list(CC.grids(path))
        except Exception:
            continue
        for g in grids:
            if not g or len(g) > 41:
                continue
            head = [str(c or '').strip() for c in g[0]]
            cols = [j for j, h in enumerate(head) if MEAN.match(h)]
            for r in g[1:]:
                if re.match(r'^(meses|months)$', head[0], re.I) and CC.num(r[0]) is not None:
                    r = [f'{int(CC.num(r[0]))} m'] + list(r[1:])
                label = ' '.join(str(c) for c in r if c not in (None, '') and CC.num(c) is None)
                h = horizon(label)
                if not h:
                    continue
                measure = 'yoy' if re.search(r'revis[aã]o (trimestral|anual)', label, re.I) or YOY.search(f'{label} {rel}') and not re.search(r'qoq|q/q|t/t', label, re.I) else 'qoq'
                for j in cols:
                    v = CC.num(r[j]) if j < len(r) else None
                    if v is not None:
                        yield f'N_{measure}_{h}', v, {'file': rel, 'header': head[j], 'row': label[:100], 'value': round(v, 4)}


def main():
    out = []
    for row, entrega in run_pass.cells(PHASES, 'C04'):
        if row['disposition'] == 'verified_absence' or not entrega.exists():
            continue
        refs = {q: r for q, r in R.references('C04', row['final_attempt_id']).items() if q.startswith('N_')}
        res = {q: {'status': 'none', 'correct': False, 'evidence': [], 'conflicts': []} for q in refs}
        for q, v, ev in candidates(entrega):
            if q not in refs:
                continue
            hit = next((lab for lab, val, tol in refs[q]['variants'] if abs(v - val) <= tol + 1e-9), None)
            (res[q]['evidence'] if hit else res[q]['conflicts']).append({**ev, 'variant': hit})
        for q, r in res.items():
            r['correct'] = bool(r['evidence'])
            r['status'] = 'none' if not (r['evidence'] or r['conflicts']) else 'auto' if r['evidence'] and not r['conflicts'] else 'ambiguous' if r['evidence'] else 'fail'
            r['evidence'], r['conflicts'] = r['evidence'][:3], r['conflicts'][:3]
        out.append({'phase': row['phase'], 'model': row['model'], 'attempt': row['final_attempt_id'], 'questions': res})
        print(row['phase'][:9], row['model'][:12].ljust(12), ''.join('Y' if r['correct'] else '.' if r['status'] == 'none' else 'x' for r in res.values()))
    (HERE.parent / 'results/code-check-C04.json').write_text(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
