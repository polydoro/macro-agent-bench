"""Second avenue for S05/S06 3m SAAR (the author 2026-11-17): RMSE over the last 24 months between
the delivery's 3m SAAR (from its saved SA index) and the reference, threshold 1.0 pp.
Reference: S05 = ABS-X13-reference-v3 on Eurostat HICP Italy NSA (I25, 2010-01 onward) of the
arm's vintage; S06 = ECB official SA (HICP.M.U2.Y.*.4F0.INX) of the arm's vintage.
Applies to inconclusive series and to the borderline Italian non-energy-goods failures."""
import csv, glob, math, sys
sys.path.insert(0, './answer-keys')
import jsonstat as J, x13, extract_sa as X
E = './execucoes/'
STAMP = {'A1': '2026-10-16T23:00:00+0200', 'A2': '2026-10-16T23:00:00+0200', 'A3': '2026-11-04T11:00:00+0100'}
IT = {'total': 'TOTAL', 'core': 'TOT_X_NRG_FOOD', 'neig': 'IGD_NNRG', 'serv': 'SERV', 'food': 'FOOD'}
EA = {'total': '000000', 'core': 'XEF000', 'neig': 'IGXE00', 'serv': 'SERV00', 'food': 'FOOD00'}
BORDER = {('A1', 'gpt-6-luna'), ('A2', 'gpt-6-luna'), ('A1', 'kimi-code/k3.1-pro'), ('A2', 'kimi-code/k3.1-pro'), ('A3', 'claude-opus-5-5')}
ARMDIR = {'A1': 'pilot-one-s06', 'A2': 'pilot-a2-s06', 'A3': 'pilot-a3-s06'}


def saar(d):
    ps = sorted(d)
    return {ps[i]: 100 * ((d[ps[i]] / d[ps[i - 3]]) ** 4 - 1) for i in range(3, len(ps))}


def it_nsa(phase, code):
    out = {}
    for p in glob.glob(E + 'pilot-*s05*/attempts/*/work/**/*.json', recursive=True):
        if not J.is_jsonstat(p, 'coicop18'):
            continue
        up, rs = J.rows(p)
        if up != STAMP[phase]:
            continue
        for d, v in rs:
            if d.get('geo') == 'IT' and d.get('unit') == 'I25' and d['coicop18'] == code and d['time'] >= '2010-01':
                out[d['time']] = v
    return out


def ea_sa(phase, code):
    out = {}
    for p in glob.glob(E + ARMDIR[phase] + '*/attempts/*/work/**/*.csv', recursive=True):
        with open(p, errors='ignore') as fh:
            if 'OBS_VALUE' not in fh.readline():
                continue
            fh.seek(0)
            for r in csv.DictReader(fh):
                if r.get('KEY') == f'HICP.M.U2.Y.{code}.4F0.INX':
                    out[r['TIME_PERIOD']] = float(r['OBS_VALUE'])
    return out


rows = list(csv.DictReader(open(sys.argv[1])))
w = csv.writer(open(sys.argv[2], 'w', newline=''))
w.writerow(['phase', 'task', 'model', 'component', 'why', 'months_compared', 'last', 'rmse_pp', 'verdict', 'delivery_latest_3msaar', 'reference_latest_3msaar'])
refcache = {}
for r in rows:
    if r['component'] not in IT:
        continue
    border = r['task'] == 'S05' and r['component'] == 'neig' and r['verdict'] == 'residual seasonality' and (r['phase'], r['model']) in BORDER
    if r['verdict'] != 'inconclusive' and not border:
        continue
    key = (r['phase'], r['task'], r['component'])
    if key not in refcache:
        if r['task'] == 'S05':
            n = it_nsa(r['phase'], IT[r['component']]); ps = sorted(n)
            _, sa = x13.adjust([n[p] for p in ps], ps[0]); refcache[key] = saar(dict(zip(ps, sa)))
        else:
            refcache[key] = saar(ea_sa(r['phase'], EA[r['component']]))
    ref = refcache[key]
    wd = glob.glob(f"{E}*/attempts/*/work")
    inv = [x for x in csv.DictReader(open(E + '../harmonization-case-inventory-20261109-v1.csv', encoding='utf-8-sig'))
           if (x['phase'], x['task'], x['model']) == (r['phase'], r['task'], r['model'])][0]
    got = X.extract(f"{E}{inv['source_campaign_id']}/attempts/{inv['final_attempt_id']}/work")[r['component']]
    mine = saar(got['data']) if got['kind'] == 'sa' else got['data']
    com = [p for p in sorted(mine) if p in ref][-24:]
    rm = math.sqrt(sum((mine[p] - ref[p]) ** 2 for p in com) / len(com))
    w.writerow([r['phase'], r['task'], r['model'], r['component'], 'borderline Italian goods' if border else 'inconclusive',
                len(com), com[-1], round(rm, 2), 'pass' if rm <= 1.0 else 'fail', round(mine[com[-1]], 2), round(ref[com[-1]], 2)])
