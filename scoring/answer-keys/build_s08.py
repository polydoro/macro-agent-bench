"""S08 answer key: Swiss real quarterly GDP (SECO), latest quarter, per arm.

Source: SECO quarterly national accounts workbooks saved in all three arms (qna_p_* production
side, qna_e_* expenditure side; csa = seasonally and calendar adjusted, cssa = also sport-event
adjusted). Every copy of each workbook is byte-identical across arms (one vintage), and its latest
quarter is 2026 Q2; the Q3 release came after A3 ran. Sheet real_q: chained volumes (previous-year
prices, reference 2020) with SECO's own q/q change in the next column.
Transforms: YoY = level t / level t-4; q/q = SECO's published change; q/q annualised = (1+q)^4-1.
Both sport-adjusted and unadjusted GDP are admitted totals (rubric).
"""
import csv, glob
import openpyxl

ROLES = {
    'total': ['B1GQ'],
    'consumo_familias': ['P31_S14_S15'],
    'consumo_governo': ['P3_S13'],
    'investimento': ['P51G', 'P5111_N111_112G', 'P5111_N113T117G'],
    'exportacoes': ['P6', 'P61', 'P61XF11', 'P62'],
    'importacoes': ['P7', 'P71', 'P71XF11', 'P72'],
    'industria': ['NOGA 10-33'],
    'servicos': ['NOGA 45-47', 'NOGA 49-53', 'NOGA 55-56', 'NOGA 58-63', 'NOGA 64-66', 'NOGA 68-75; 77-82',
                 'NOGA 84', 'NOGA 85', 'NOGA 86-88', 'NOGA 90-93', 'NOGA 94-96'],
}


def read(path):
    ws = openpyxl.load_workbook(path, read_only=True, data_only=True)['real_q']
    ws.reset_dimensions()
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    code = next(r for r in rows if 'B1GQ' in r)
    out = {}
    for r in rows:
        if isinstance(r[0], int) and isinstance(r[1], int):
            for j, c in enumerate(code):
                if c and j < len(r) and isinstance(r[j], (int, float)):
                    q = r[j + 1] if j + 1 < len(r) and isinstance(r[j + 1], (int, float)) else None
                    out[(c, r[0], r[1])] = (r[j], q)
    return out


if __name__ == '__main__':
    w = csv.writer(open('answer-keys/S08-key.csv', 'w', newline=''))
    w.writerow(['arm', 'role', 'code', 'adjustment', 'period', 'yoy', 'qoq', 'qoq_annualised'])
    for side in ('p', 'e'):
        for adj in ('csa', 'cssa'):
            files = sorted(glob.glob(f'execucoes/pilot-*-s08-*/attempts/*/work/**/qna_{side}_{adj}.xlsx', recursive=True))
            data = read(files[0])
            for f in files[1:]:
                if open(f, 'rb').read() != open(files[0], 'rb').read():
                    raise ValueError(f'different vintage: {f}')
            arms = sorted({f.split('/')[1].split('-')[1] for f in files})
            for role, codes in ROLES.items():
                if role == 'total' and side == 'e':
                    continue
                for c in codes:
                    keys = [k for k in data if k[0] == c]
                    if not keys:
                        continue
                    _, y, q = max(keys, key=lambda k: (k[1], k[2]))
                    lvl, g = data[(c, y, q)]
                    lvl4 = data[(c, y - 1, q)][0]
                    for arm in ('A1', 'A2', 'A3'):
                        w.writerow([arm, role, c, adj, f'{y}Q{q}', round(100 * (lvl / lvl4 - 1), 2),
                                    round(100 * g, 2), round(100 * ((1 + g) ** 4 - 1), 2)])
            print(side, adj, len(files), 'identical copies; arms', arms)
    # Aggregates SECO reports only in the press release of 3 September 2026 (q/q, sport-adjusted)
    for arm in ('A1', 'A2', 'A3'):
        w.writerow([arm, 'servicos', 'services sector (release text)', 'cssa', '2026Q2', '', 0.7, ''])
        w.writerow([arm, 'industria', 'industrial sector (release text)', 'cssa', '2026Q2', '', 3.9, ''])
