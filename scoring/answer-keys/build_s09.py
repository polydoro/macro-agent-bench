"""S09 answer key: Norway retail sales volume (SSB table 07129), latest month, per arm.

Source: SSB JSON-stat downloads of table 07129 saved in all three arms. A1 (run 2026-10-26/27) has
the release stamped 2026-09-28 (latest August); A2 and A3 have 2026-10-28 (latest September).
All copies of a stamp must agree cell by cell.
YoY on each adjustment variant (calendar-adjusted, unadjusted, SA; rubric admits any declared);
3m/3m SAAR = 100*((mean(t..t-2)/mean(t-3..t-5))^4-1) on the SA volume index.
"""
import csv, glob, json, sys
sys.path.insert(0, 'answer-keys')
import jsonstat as J

STAMP = {'A1': '2026-09-28T06:00:00Z', 'A2': '2026-10-28T07:00:00Z', 'A3': '2026-10-28T07:00:00Z'}
ARMDIR = {'A1': 'pilot-one', 'A2': 'pilot-a2', 'A3': 'pilot-a3'}
ROLES = {'total': ['47', '47_ub'], 'alimentos': ['47.1', '47.2'], 'combustivel': ['47.3'],
         'equipamentos_domesticos': ['47.4', '47.5'], 'cultura_lazer': ['47.6'], 'outros_bens': ['47.7'],
         'internet': ['47.9']}
ADJ = {'ca': 'VolumInVirkedag', 'nsa': 'VolumUjustert', 'sa': 'VolumSesong'}


def load(arm):
    cells, n = {}, 0
    for p in glob.glob(f'execucoes/{ARMDIR[arm]}-s09-*/attempts/*/work/**/*.json', recursive=True):
        try:
            d = json.load(open(p))
        except Exception:
            continue
        if not (isinstance(d, dict) and d.get('id') == ['NACE', 'ContentsCode', 'Tid'] and d.get('updated') == STAMP[arm]):
            continue
        n += 1
        for dims, v in J.rows(p)[1]:
            k = (dims['NACE'], dims['ContentsCode'], f"{dims['Tid'][:4]}-{dims['Tid'][5:]}")
            if k in cells and cells[k] != v:
                raise ValueError(f'disagreement {arm} {k}: {cells[k]} vs {v}')
            cells[k] = v
    return cells, n


def shift(p, k):
    y, m = int(p[:4]), int(p[5:7]) - 1 + k
    return f'{y + m // 12}-{m % 12 + 1:02d}'


if __name__ == '__main__':
    w = csv.writer(open('answer-keys/S09-key.csv', 'w', newline=''))
    w.writerow(['arm', 'role', 'nace', 'period', 'yoy_ca', 'yoy_nsa', 'yoy_sa', 'saar3m3m_sa'])
    for arm in ('A1', 'A2', 'A3'):
        cells, n = load(arm)
        for role, codes in ROLES.items():
            for c in codes:
                s = {a: {p: v for (cc, ct, p), v in cells.items() if cc == c and ct == code} for a, code in ADJ.items()}
                t = max(s['sa'])
                yoy = {a: round(100 * (s[a][t] / s[a][shift(t, -12)] - 1), 2) for a in ADJ}
                m1 = sum(s['sa'][shift(t, -i)] for i in range(3)) / 3
                m0 = sum(s['sa'][shift(t, -i)] for i in range(3, 6)) / 3
                w.writerow([arm, role, c, t, yoy['ca'], yoy['nsa'], yoy['sa'], round(100 * ((m1 / m0) ** 4 - 1), 2)])
        print(arm, n, 'copies agree')
