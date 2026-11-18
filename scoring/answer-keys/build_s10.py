"""S10 answer key: Swedish LFS (SCB AKU) unemployment rate, 15-74, latest month, per arm.

Source: SCB PxWeb JSON-stat (table AKURLBefM / TAB6387, population by labour status and type of
data) saved in all three arms, all stamped 2026-10-16 (latest September 2026; October came after
A3). Copies must agree cell by cell. Admitted versions (rubric): unadjusted, seasonally adjusted,
and SCB's seasonally adjusted and smoothed (trend). The rate stays in percent; change in
percentage points is admitted, so m/m and y/y changes in pp are keyed too.
"""
import csv, glob, json, sys
sys.path.insert(0, 'answer-keys')
import jsonstat as J

TYPES = {'O_DATA': 'nsa', 'SR_DATA': 'sa', 'TC_DATA': 'sa_suavizada'}


def load():
    cells, n = {}, 0
    for p in glob.glob('execucoes/pilot-*-s10-*/attempts/*/work/**/*.json', recursive=True):
        try:
            d = json.load(open(p))
        except Exception:
            continue
        if not (isinstance(d, dict) and d.get('class') == 'dataset' and 'Arbetskraftstillh' in d.get('id', [])
                and 'TypData' in d['id'] and 'Tid' in d['id']
                and set(d['id']) <= {'Arbetskraftstillh', 'TypData', 'Kon', 'Alder', 'ContentsCode', 'Tid'}):
            continue
        used = False
        for dims, v in J.rows(p)[1]:
            if dims['Arbetskraftstillh'] != 'ALÖSP' or dims.get('Kon', '1+2') != '1+2' or dims.get('Alder', 'tot15-74') != 'tot15-74':
                continue
            if 'M' not in dims['Tid'] or dims['TypData'] not in TYPES:
                continue
            k = (dims['TypData'], f"{dims['Tid'][:4]}-{dims['Tid'][5:]}")
            if k in cells and abs(cells[k] - v) > 1e-9:
                raise ValueError(f'disagreement {k}: {cells[k]} vs {v} in {p}')
            cells[k] = v
            used = True
        n += used
    return cells, n


def shift(p, k):
    y, m = int(p[:4]), int(p[5:7]) - 1 + k
    return f'{y + m // 12}-{m % 12 + 1:02d}'


if __name__ == '__main__':
    cells, n = load()
    with open('answer-keys/S10-key.csv', 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['arm', 'role', 'version', 'period', 'rate', 'change_1m_pp', 'change_12m_pp'])
        for code, name in TYPES.items():
            s = {p: v for (c, p), v in cells.items() if c == code}
            t = max(s)
            for arm in ('A1', 'A2', 'A3'):
                w.writerow([arm, 'total', name, t, s[t], round(s[t] - s[shift(t, -1)], 2), round(s[t] - s[shift(t, -12)], 2)])
    print(n, 'files agree')
