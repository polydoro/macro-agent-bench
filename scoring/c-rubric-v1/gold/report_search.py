"""Manual-pass helper: for code-check questions with status 'none' (no candidate in saved tables), look for the
reference value in the delivery's own report text, the same way a reader would.

A value counts if a number within the variant's tolerance appears within 120 characters after a keyword for the
role and the transform. Every hit is printed with its snippet for a hand audit; nothing is written back.
Usage: python gold/report_search.py C02 > /tmp/x.txt
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

NUM = re.compile(r'(?<![\d.,])[-−–+]?\d{1,3}(?:[.,]\d{1,4})?(?![\d])')
KW = {'prod': r'produ|output|industri', 'ord': r'encomend|pedido|order|auftr', 'cons': r'consumo|consumption',
      'ret': r'varej|retail|vendas', 'conf': r'confian', 'sav': r'poupan|saving', 'last': r'pib|gdp',
      'energia': r'energ', 'nucleo': r'n[uú]cleo|core'}


def hits(text, q, ref):
    role, tr = CC.C_TARGETS[q]
    for m in re.finditer(KW[role], text, re.I):
        window = text[m.start(): m.start() + 160]
        if tr != 'native' and not CC.transform_ok({'3me': '3m'}.get(tr, tr), window):
            continue
        for n in NUM.finditer(window[len(m.group(0)):]):
            v = float(n.group(0).replace(',', '.').replace('−', '-').replace('–', '-'))
            for label, val, tol in ref['variants']:
                if abs(v - val) <= max(tol, 0.051):
                    return label, ' '.join(window.split())[:160]
    return None


def main(task):
    cc = {(c['phase'], c['model']): c for c in json.loads((HERE.parent / f'results/code-check-{task}.json').read_text())}
    for row, entrega in run_pass.cells({'A1', 'A2', 'A3', 'A4_self_review', 'A4_external_review'}, task):
        c = cc.get((row['phase'], row['model']))
        if not c:
            continue
        refs = R.references(task, row['final_attempt_id'])
        text = judge.report_text(entrega)
        for q, v in c['questions'].items():
            if v['status'] != 'none':
                continue
            h = hits(text, q, refs[q])
            print(row['phase'][:9], row['model'][:12].ljust(12), q.ljust(13), 'REPORT' if h else 'absent', *(h or ()))


if __name__ == '__main__':
    main(sys.argv[1])
