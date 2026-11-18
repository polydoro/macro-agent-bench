"""S07 answer key: UK monthly GDP (ONS MGDP, GVA chained volume, SA), latest month, per arm.

Source: ONS MGDP CSV (release date 15-10-2026, August 2026) saved in all three arms; the next
release (12 November) came after A3 ran, so every arm keys August. Every saved copy with that
release date (full dataset or single-series downloads) must agree cell by cell. One A2 agent also
saved the September release (July data), which is older and ignored.
Transforms: YoY on the index; 3m/3m SAAR = 100*((mean(t..t-2)/mean(t-3..t-5))^4-1). ONS's own
3m/3m (ED3H etc.) is not annualised; annualising it (2.83 for the total) is an admitted
variant that agents used, so both values are keyed.
"""
import csv, glob

RELEASE = '15-10-2026'
ROLES = {'total': 'ECY2', 'servicos': 'ECYC', 'producao': 'ECY4', 'construcao': 'ECY9', 'manufatura': 'ECY6'}
ONS_3M = {'total': 'ED3H', 'servicos': 'ED3P', 'producao': 'ED3J', 'construcao': 'ED3O', 'manufatura': 'ED3L'}
ONS_YOY = {'total': 'ED2R', 'servicos': 'ED2Z', 'producao': 'ED2T', 'construcao': 'ED2Y', 'manufatura': 'ED2V'}
MON = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']


def load():
    cells, files = {}, 0
    for f in glob.glob('execucoes/pilot-*-s07-*/attempts/*/work/**/*.csv', recursive=True):
        rows = list(csv.reader(open(f, errors='ignore')))
        if len(rows) < 8 or not rows[0] or rows[0][0] != 'Title':
            continue
        head = {r[0]: r for r in rows[:8] if r}
        rel = head.get('Release Date', head.get('Release date', ['', '']))
        cdid = head.get('CDID')
        if not cdid or rel[1] != RELEASE:
            continue
        files += 1
        for r in rows:
            if r and len(r[0]) == 8 and r[0][5:] in MON:
                p = f'{r[0][:4]}-{MON.index(r[0][5:]) + 1:02d}'
                for j in range(1, min(len(r), len(cdid))):
                    if r[j] in ('', 'x'):
                        continue
                    k = (cdid[j], p)
                    v = float(r[j])
                    if k in cells and cells[k] != v:
                        raise ValueError(f'disagreement {k}: {cells[k]} vs {v} in {f}')
                    cells[k] = v
    return cells, files


def shift(p, k):
    y, m = int(p[:4]), int(p[5:7]) - 1 + k
    return f'{y + m // 12}-{m % 12 + 1:02d}'


if __name__ == '__main__':
    cells, files = load()
    w = csv.writer(open('answer-keys/S07-key.csv', 'w', newline=''))
    w.writerow(['arm', 'role', 'cdid', 'period', 'yoy', 'saar3m3m', 'ons_yoy', 'ons_3m3m_not_annualised', 'ons_3m3m_annualised'])
    for role, cd in ROLES.items():
        s = {p: v for (c, p), v in cells.items() if c == cd}
        t = max(s)
        yoy = 100 * (s[t] / s[shift(t, -12)] - 1)
        a = sum(s[shift(t, -i)] for i in range(3)) / 3
        b = sum(s[shift(t, -i)] for i in range(3, 6)) / 3
        saar = 100 * ((a / b) ** 4 - 1)
        for arm in ('A1', 'A2', 'A3'):
            w.writerow([arm, role, cd, t, round(yoy, 2), round(saar, 2),
                        cells.get((ONS_YOY.get(role), t), ''), g if (g := cells.get((ONS_3M.get(role), t))) is not None else '',
                        round(100 * ((1 + g / 100) ** 4 - 1), 2) if g is not None else ''])
    print(files, 'files agree')
