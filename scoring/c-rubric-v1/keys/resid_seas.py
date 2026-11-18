"""Residual-seasonality tests for a monthly series (dict 'YYYY-MM' -> value).

F: OLS of the month-on-month % change on an intercept and 11 month dummies; F-test that
the dummies are jointly zero (the 'F-test on seasonal dummies' used in JDemetra+).
KW: Kruskal-Wallis test that the m/m changes have the same distribution in every month.
For a 3m SAAR series (already a rate), pass rate=True: the test runs on its levels.
"""
import numpy as np
from scipy import stats


def _changes(s, rate=False):
    ps = sorted(s)
    if rate:
        return [(p, s[p]) for p in ps]
    return [(ps[i], 100 * (s[ps[i]] / s[ps[i - 1]] - 1)) for i in range(1, len(ps))
            if _next(ps[i - 1]) == ps[i]]


def _next(p):
    y, m = int(p[:4]), int(p[5:7])
    return f"{y + (m == 12)}-{m % 12 + 1:02d}"


def test(s, last=None, rate=False):
    ch = _changes(s, rate)
    if last:
        ch = ch[-last:]
    n = len(ch)
    if n < 24:
        return {"n": n, "F_p": None, "KW_p": None}
    y = np.array([v for _, v in ch])
    mon = np.array([int(p[5:7]) for p, _ in ch])
    X = np.column_stack([np.ones(n)] + [(mon == m).astype(float) for m in range(2, 13)])
    rss_u = np.sum((y - X @ np.linalg.lstsq(X, y, rcond=None)[0]) ** 2)
    rss_r = np.sum((y - y.mean()) ** 2)
    F = ((rss_r - rss_u) / 11) / (rss_u / (n - 12))
    groups = [y[mon == m] for m in range(1, 13) if (mon == m).sum() > 0]
    return {"n": n, "F_p": float(stats.f.sf(F, 11, n - 12)), "KW_p": float(stats.kruskal(*groups).pvalue)}
