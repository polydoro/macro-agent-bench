"""C04 gold: is the mean revision of German GDP growth different from zero? (the author 2026-11-17, decision 5:
if not significant, "no clear bias" is also admitted.)

Same revisions as keys/build_c04.py (BBKRT, genuine first estimates from 2005). Mean revision with a
Newey-West (Bartlett) standard error: revisions at horizon h overlap across quarters, so the lag is
h-1 quarters (short 1, one year 3, two years 7, three years 11, latest 8), at least the usual rule
floor(4 (n/100)^(2/9)). Two-sided test at 5%. Writes C04-significance.csv.
"""
import csv
import math
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / 'keys'))
import build_c04 as B  # noqa: E402

LAGS = {'short': 1, 'one_year': 3, 'two_years': 7, 'three_years': 11, 'latest': 8}


def nw(x, lag):
    n = len(x)
    m = sum(x) / n
    e = [v - m for v in x]
    s = sum(v * v for v in e) / n
    for k in range(1, lag + 1):
        s += 2 * (1 - k / (lag + 1)) * sum(e[t] * e[t - k] for t in range(k, n)) / n
    return m, math.sqrt(max(s, 0) / n)


def main():
    levels, _ = B.merged_matrix()
    rows = []
    for last in ('2026-09-30', '2026-10-30'):
        visible = levels.loc[:, levels.columns <= last].dropna(axis=1, how='all')
        for measure, lag in B.MEASURES.items():
            rev = B.revisions(visible, lag)
            for sample, keep in B.SAMPLES.items():
                for horizon, group in B.HORIZON_GROUP.items():
                    x = rev.loc[rev['year'].map(keep), horizon].dropna().astype(float).round(2).tolist()
                    if len(x) < 10:
                        continue
                    L = max(LAGS[group], math.floor(4 * (len(x) / 100) ** (2 / 9)))
                    m, se = nw(x, L)
                    t = m / se if se else float('nan')
                    rows.append({'last_vintage': last, 'measure': measure, 'sample': sample, 'horizon': horizon,
                                 'horizon_group': group, 'n': len(x), 'mean': round(m, 4), 'nw_se': round(se, 4),
                                 'nw_lag': L, 't': round(t, 2), 'significant_5pct': abs(t) > 1.96})
    with (HERE / 'C04-significance.csv').open('w', newline='') as handle:
        w = csv.DictWriter(handle, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        if r['last_vintage'] == '2026-10-30':
            print(r['measure'], r['sample'][:22].ljust(22), r['horizon'].ljust(13), r['n'], r['mean'], r['nw_se'], r['t'], r['significant_5pct'])


if __name__ == '__main__':
    main()
