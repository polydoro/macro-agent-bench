"""Seasonal adjustment for answer keys: the old evaluator's ABS-X13-reference-v3 policy.

Same spec text, same configuration ladder (first successful fit in fixed order) and the
same success rule as statsmodels 0.15 (no "ERROR" in the .err file). Validated against the
55 cached fits in avaliacao/evaluator/deterministic-allruns-20261110-v1/reference-cache
(see check_cache below). Binary: x13as_html from the PyPI wheel x13binary 1.1.61.
"""
import os
import shutil
import subprocess
import tempfile

LADDER = [  # (name, log, maxiter, outlier)
    ("ABS_default", None, None, True),
    ("ABS_default_iter1000", None, 1000, True),
    ("ABS_default_iter5000", None, 5000, True),
    ("ABS_no_outliers_auto", None, 5000, False),
    ("ABS_no_outliers_additive", False, 5000, False),
    ("ABS_no_outliers_log", True, 5000, False),
]
BINARY = shutil.which("x13as_html") or shutil.which("x13as")


def spec(values, start, log, maxiter, outlier):
    y, m = start.split("-")
    data = "\n".join(str(float(v)) for v in values)
    fn = {None: "auto", True: "log", False: "none"}[log]
    s = (f'Series {{\n        data=({data})\nappendbcst=no\nappendfcst=no\nperiod=12\n'
         f'start={int(y)}.{int(m)}\ntitle="reference"\nname="reference"\n\n        }}\n'
         f'        transform{{function={fn}}}\n')
    if outlier:
        s += "outlier{}\n"
    s += "automdl{\nmaxorder = (2 1)\nmaxdiff = (2 1)\n}\n"
    s += "x11{ save=(d11 d12 d13) \n savelog=(fd8 m7 q)}"
    if maxiter:
        s += f"\nestimate {{ maxiter={maxiter} }}\n"
    return s


def _run(text):
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, "series.spc"), "w").write(text)
        subprocess.run([BINARY, "series", "-g", d], cwd=d, capture_output=True, timeout=90)
        err = open(os.path.join(d, "series.err")).read() if os.path.exists(os.path.join(d, "series.err")) else ""
        err = err[err.find("spc:") + 4:]
        d11 = os.path.join(d, "series.d11")
        if "ERROR" in err or not os.path.exists(d11):
            return None
        out = []
        for line in open(d11):
            t = line.split()
            if len(t) == 2 and t[0].isdigit():
                out.append(float(t[1]))
        return out


def adjust(values, start):
    """Return (config name, SA list) for a monthly NSA series starting at 'YYYY-MM'."""
    for name, log, maxiter, outlier in LADDER:
        sa = _run(spec(values, start, log, maxiter, outlier))
        if sa is not None:
            return name, sa
    raise RuntimeError("no X13 configuration succeeded")


def check_cache(cache_dir):
    """Reproduce every cached reference; return the max abs difference per entry."""
    import csv
    import json
    res = {}
    for h in sorted(os.listdir(cache_dir)):
        p = os.path.join(cache_dir, h)
        inp = json.load(open(os.path.join(p, "input.json")))
        r = json.load(open(os.path.join(p, "result.json")))
        if r.get("state") != "complete":
            res[h] = ("cache-incomplete", None)
            continue
        vals = [float.fromhex(x) for x in inp["float64_hex"]]
        ref = [float(row[2]) for row in list(csv.reader(open(os.path.join(p, "reference.csv"))))[1:]]
        name, sa = adjust(vals, inp["periods"][0])
        want = LADDER[r["selected_step"]][0]
        res[h] = (name == want, max(abs(a - b) for a, b in zip(sa, ref)))
    return res


if __name__ == "__main__":
    import sys
    for h, v in check_cache(sys.argv[1]).items():
        print(h[:8], *v)
