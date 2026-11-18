"""C05 gold: pass-through of energy to euro-area core inflation (the author 2026-11-17, decision 6).

Reference estimate from the ECB SA indices the C05 agents saved (HICP.M.U2.Y.NRGY00/XEF000.4F0.INX,
read with keys/build_c05_sa.ecb_core, copies ending 2026-09 and 2026-10):
  core m/m_t = a + sum_{k=0..12} b_k energy m/m_{t-k} + sum_{j=1..2} c_j core m/m_{t-j} + e_t,  2005 onward.
Long-run pass-through LR = sum b / (1 - sum c); 12-month cumulative effect of the 2026 energy shock on
core YoY = model-implied core path with actual energy minus the path with energy m/m held at its
2025 average. Newey-West (12 lags) standard errors; delta method for LR.
Also the plain facts: core and energy YoY at the start of the energy upturn and at the latest month.
Writes C05-passthrough.csv.
"""
import csv
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / 'keys'))
import build_c05_sa as S  # noqa: E402

K, J = 12, 2


def series(code, last):
    S.CODE = code
    d = S.ecb_core()[last]
    ps = sorted(d)
    return ps, np.array([d[p] for p in ps])


def nw_cov(X, e, lag=12):
    n = len(e)
    u = X * e[:, None]
    s = u.T @ u
    for k in range(1, lag + 1):
        g = u[k:].T @ u[:-k]
        s += (1 - k / (lag + 1)) * (g + g.T)
    xi = np.linalg.inv(X.T @ X)
    return xi @ s @ xi


def estimate(last):
    pe, e_lvl = series('HICP.M.U2.Y.NRGY00.4F0.INX', last)
    pc, c_lvl = series('HICP.M.U2.Y.XEF000.4F0.INX', last)
    e_lvl = e_lvl[pe.index(pc[0]):]  # core starts 1997-01; align
    pe = pe[pe.index(pc[0]):]
    assert pe == pc
    em, cm = 100 * np.diff(np.log(e_lvl)), 100 * np.diff(np.log(c_lvl))
    months = pe[1:]
    start = months.index('2005-01')
    rows, y = [], []
    for t in range(start, len(months)):
        rows.append([1.0] + [em[t - k] for k in range(K + 1)] + [cm[t - j] for j in range(1, J + 1)])
        y.append(cm[t])
    X, y = np.array(rows), np.array(y)
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    res = y - X @ beta
    V = nw_cov(X, res)
    b, c = beta[1:K + 2], beta[K + 2:]
    lr = b.sum() / (1 - c.sum())
    g = np.zeros(len(beta))
    g[1:K + 2] = 1 / (1 - c.sum())
    g[K + 2:] = b.sum() / (1 - c.sum()) ** 2
    lr_se = float(np.sqrt(g @ V @ g))
    # counterfactual: energy m/m from 2026-01 at its 2025 average
    i26 = months.index('2026-01')
    base = em[months.index('2025-01'):i26].mean()
    em_cf = em.copy()
    em_cf[i26:] = base

    def path(e):
        out = cm[:i26].tolist()
        for t in range(i26, len(months)):
            x = [1.0] + [e[t - k] for k in range(K + 1)] + [out[t - j] for j in range(1, J + 1)]
            out.append(float(np.dot(beta, x)))
        return np.array(out)
    gap = path(em) - path(em_cf)  # core m/m difference attributable to the energy shock
    effect_yoy = float(gap[-12:].sum())  # contribution to core YoY at the latest month, pp (log approx)
    yoy = lambda lvl, p: 100 * (lvl[pe.index(p)] / lvl[pe.index(p) - 12] - 1)
    low = min((p for p in pe if '2025-06' <= p <= pe[-1]), key=lambda p: yoy(e_lvl, p))
    return {'last': last, 'n': len(y), 'sum_b': round(float(b.sum()), 4), 'lr_passthrough': round(float(lr), 4),
            'lr_se': round(lr_se, 4), 'lr_ci95': f'[{lr - 1.96 * lr_se:.3f}, {lr + 1.96 * lr_se:.3f}]',
            'effect_on_core_yoy_pp': round(effect_yoy, 2), 'energy_yoy_trough_month': low,
            'energy_yoy_trough': round(yoy(e_lvl, low), 1), 'core_yoy_at_trough': round(yoy(c_lvl, low), 2),
            'energy_yoy_latest': round(yoy(e_lvl, pe[-1]), 1), 'core_yoy_latest': round(yoy(c_lvl, pe[-1]), 2)}


def main():
    out = [estimate(last) for last in ('2026-09', '2026-10')]
    with (HERE / 'C05-passthrough.csv').open('w', newline='') as handle:
        w = csv.DictWriter(handle, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    for r in out:
        print(r)


if __name__ == '__main__':
    main()
