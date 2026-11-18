"""Cohen's kappa of Jev (and of the blind Sonnet readers) against the author's hand labels, by item kind.

Run from visual-rubric-v1/:  python hand-labels/kappa.py  ->  prints the markdown tables.
Inputs: hand-labels/compare-rows.csv (Jev vs the author, 265 questions on 15 deliveries) and
hand-labels/sonnet-calib/Dnn.json (blind Sonnet reads of the numeric questions on the same deliveries).
Binary: Jev ok = majority of 3 repeats Atende (Parcial counts as a problem, as in compare.py); Sonnet ok =
value printed and inside an admitted band. CI: 95% percentile bootstrap, resampling the 15 deliveries
(questions within a delivery are not independent), 5,000 draws; draws where kappa is undefined are dropped.
"""
import csv, json, random, sys
import references as R

KINDS = [('identity', 'identity (I1)'), ('conventions', 'conventions (I2)'), ('coverage', 'coverage'),
         ('legibility', 'legibility (P1)'), ('identification', 'identification (P2)'), ('numeric', 'numeric "printed"')]


def kappa(pairs):
    n = len(pairs)
    po = sum(h == j for h, j in pairs) / n
    ph, pj = sum(h for h, _ in pairs) / n, sum(j for _, j in pairs) / n
    pe = ph * pj + (1 - ph) * (1 - pj)
    return None if pe == 1 else (po - pe) / (1 - pe)


def row(label, items, draws=5000, seed=1):
    """items: [(delivery, human_ok, judge_ok)]"""
    pairs = [(h, j) for _, h, j in items]
    n, k = len(pairs), kappa(pairs)
    codes = sorted({c for c, _, _ in items})
    by = {c: [(h, j) for d, h, j in items if d == c] for c in codes}
    rnd, ks = random.Random(seed), []
    for _ in range(draws):
        s = [p for c in rnd.choices(codes, k=len(codes)) for p in by[c]]
        v = kappa(s)
        if v is not None:
            ks.append(v)
    ks.sort()
    ci = f"[{ks[int(.025 * len(ks))]:.2f}, {ks[int(.975 * len(ks)) - 1]:.2f}]" if len(ks) > 100 else 'n/a'
    pos = [j for h, j in pairs if h]; neg = [j for h, j in pairs if not h]
    fc = f"{sum(neg)}/{len(neg)}" if neg else '0/0'
    fr = f"{len(pos) - sum(pos)}/{len(pos)}" if pos else '0/0'
    hb, jb = sum(h for h, _ in pairs) / n, sum(j for _, j in pairs) / n
    flag = ' ⚠' if min(hb, 1 - hb) < 0.1 or min(jb, 1 - jb) < 0.1 else ''
    ks_ = 'undef.' if k is None else f'{k:.2f}'
    return (f"| {label}{flag} | {n} | {sum(h == j for h, j in pairs) / n:.2f} | {ks_} | {ci} | {fc} | {fr} "
            f"| {hb:.2f} | {jb:.2f} |")


HEAD = ("| Item kind | n | Raw agreement | Cohen's kappa | 95% CI | Judge credits what the author rejected | "
        "Judge rejects what the author credited | the author ok rate | Judge ok rate |\n|---|---:|---:|---:|---|---:|---:|---:|---:|")

rows = list(csv.DictReader(open('hand-labels/compare-rows.csv')))
jev = [(r['code'], int(r['human_ok']), int(float(r['jev_ok_share']) >= 0.5), r['kind']) for r in rows]
print('Jev\n' + HEAD)
for kind, label in KINDS:
    print(row(label, [(c, h, j) for c, h, j, k in jev if k == kind]))
print(row('**all questions**', [(c, h, j) for c, h, j, _ in jev]))
print(row('all excl. numeric', [(c, h, j) for c, h, j, k in jev if k != 'numeric']))

son = []
for r in rows:
    if r['kind'] != 'numeric':
        continue
    rd = {x['id']: x for x in json.load(open(f"hand-labels/sonnet-calib/{r['code']}.json"))}[r['q']]
    new, _ = R.references(r['task'], r['phase'], r['model'])
    vals = [v for v in [rd.get('value')] + list(rd.get('values') or []) if isinstance(v, (int, float))]
    ok = rd['printed'] == 'yes' and any(abs(v - a) <= t + 1e-9 for v in vals for _, a, t in new[r['q']]['variants'])
    son.append((r['code'], int(r['human_ok']), int(ok)))
print('\nSonnet readers (numeric only)\n' + HEAD)
print(row('numeric "printed"', son))
print(row('numeric, Jev on the same rows', [(c, h, j) for c, h, j, k in jev if k == 'numeric']))

# Sensitivity: the author's two D02 labels as originally entered (total YoY / 3m flagged not printed). The chart prints
# them (+2.30% / +1.62%); the author approved correcting them on 2026-11-18 (labels/D02.json "corrections").
SLIP = {('D02', 'N_total_yoy'), ('D02', 'N_total_3m')}
orig = [0 if (r['code'], r['q']) in SLIP else int(r['human_ok']) for r in rows]
jev2 = [(c, h2, j, k) for (c, _, j, k), h2 in zip(jev, orig)]
num_h = [h2 for r, h2 in zip(rows, orig) if r['kind'] == 'numeric']
print('\nWith the two D02 labels as originally entered\n' + HEAD)
print(row('Jev, numeric "printed"', [(c, h, j) for c, h, j, k in jev2 if k == 'numeric']))
print(row('Jev, all questions', [(c, h, j) for c, h, j, _ in jev2]))
print(row('Sonnet, numeric "printed"', [(c, h2, j) for (c, _, j), h2 in zip(son, num_h)]))
