"""SA criterion for A4 S05/S06 deliveries, same rule as sa_gate.py for A1-A3 (the author 2026-11-17).
Residual-seasonality test on the delivery's own saved series; S06 series equal to official ECB SA pass;
inconclusive cases, and S05 non-energy goods for the models that were borderline in A1, go to the
24-month RMSE threshold (1.0 pp) against the reference of the release the series ends in (A1 or A3
vintage); too short or no saved series fails; energy is exempt.
Writes answer-keys/S05-S06-sa-gate-A4.csv (same columns as S05-S06-sa-gate.csv)."""
import csv, math, sys
sys.path.insert(0, './answer-keys')
sys.path.insert(0, './visual-rubric-v1')
sys.argv = [sys.argv[0], '/dev/null', '/dev/null']  # run_sa_threshold reads two paths at import
import extract_sa as X, resid_seas as RS, x13
import run_sa_threshold as T
from run_resid_seasonality import OFF, CODE, mom
from a4_cells import a4_cells

ROLE = {'total': 'total', 'core': 'nucleo', 'neig': 'bens_nao_energeticos', 'serv': 'servicos', 'energy': 'energia', 'food': 'alimentos'}
A3_FIRST = {'S05': '2026-10', 'S06': '2026-10'}  # first month only the A3-vintage release has
BORDER_MODELS = {'gpt-6-luna', 'kimi-code/k3.1-pro'}
refcache = {}


def reference(task, comp, vintage):
    key = (task, comp, vintage)
    if key not in refcache:
        if task == 'S05':
            n = T.it_nsa(vintage, T.IT[comp]); ps = sorted(n)
            _, sa = x13.adjust([n[p] for p in ps], ps[0]); refcache[key] = T.saar(dict(zip(ps, sa)))
        else:
            refcache[key] = T.saar(T.ea_sa(vintage, T.EA[comp]))
    return refcache[key]


def own_latest(g):
    d = g['data']; ps = sorted(d); t = ps[-1]
    if g['kind'] == 'saar':
        return t, d[t]
    return (t, 100 * ((d[t] / d[ps[-4]]) ** 4 - 1)) if len(ps) >= 4 else (t, None)


w = csv.writer(open('S05-S06-sa-gate-A4.csv', 'w', newline=''))
w.writerow(['phase', 'task', 'model', 'role', 'sa_pass', 'reason', 'own_last', 'own_latest_3msaar'])
for row, images in a4_cells({'S05', 'S06'}):
    if not images:
        continue
    task = row['task']
    got = X.extract(row['workdir'])
    for c, role in ROLE.items():
        g = got.get(c)
        last, val = own_latest(g) if g else ('', None)
        if c == 'energy':
            ok, why = True, 'energy exempt'
        elif not g:
            ok, why = False, 'no saved series'
        else:
            d = g['data']; t = RS.test(d, rate=g['kind'] == 'saar')
            v = 'too short' if t['F_p'] is None or t['n'] < 36 else 'residual seasonality' if t['F_p'] < 0.01 else 'pass' if t['F_p'] >= 0.05 else 'inconclusive'
            if task == 'S06' and g['kind'] == 'sa':
                vals = []
                for ds in ('HICP', 'ICP'):
                    if (ds, CODE[c]) in OFF:
                        a, b = mom(d), mom(OFF[(ds, CODE[c])]); com = [p for p in a if p in b][-60:]
                        if com:
                            vals.append(math.sqrt(sum((a[p] - b[p]) ** 2 for p in com) / len(com)))
                if vals and min(vals) <= 0.02:
                    v = 'official ECB SA'
            border = task == 'S05' and c == 'neig' and v == 'residual seasonality' and row['model'] in BORDER_MODELS
            if v == 'inconclusive' or border:
                ref = reference(task, c, 'A3' if max(d) >= A3_FIRST[task] else 'A1')
                mine = T.saar(d) if g['kind'] == 'sa' else d
                com = [p for p in sorted(mine) if p in ref][-24:]
                rm = math.sqrt(sum((mine[p] - ref[p]) ** 2 for p in com) / len(com))
                ok, why = rm <= 1.0, f"threshold {'pass' if rm <= 1.0 else 'fail'}"
            else:
                ok, why = v in ('pass', 'official ECB SA'), v
        w.writerow([row['phase'], task, row['model'], role, ok, why, last, '' if val is None else round(val, 2)])
print(open('S05-S06-sa-gate-A4.csv').read())
