"""Final S05/S06 SA criterion per delivery and component, plus the delivery's own latest 3m SAAR.

Combines S05-S06-residual-seasonality.csv (test) and S05-S06-sa-threshold.csv (second avenue).
Pass: official ECB SA, test pass, or threshold pass. Fail: residual seasonality, threshold fail,
too short, no saved series. Energy is exempt (SA or unadjusted admitted). The delivery's own
3m SAAR at its last saved month is recorded so the numeric question can admit it as a variant.
Writes answer-keys/S05-S06-sa-gate.csv.
"""
import csv, glob, sys
sys.path.insert(0, 'answer-keys')
import extract_sa as X

ROLE = {'total': 'total', 'core': 'nucleo', 'neig': 'bens_nao_energeticos', 'serv': 'servicos', 'energy': 'energia', 'food': 'alimentos'}
test = {(r['phase'], r['task'], r['model'], r['component']): r for r in csv.DictReader(open('answer-keys/S05-S06-residual-seasonality.csv'))}
thr = {(r['phase'], r['task'], r['model'], r['component']): r['verdict'] for r in csv.DictReader(open('answer-keys/S05-S06-sa-threshold.csv'))}
inv = [r for r in csv.DictReader(open('harmonization-case-inventory-20261109-v1.csv', encoding='utf-8-sig'))
       if r['task'] in ('S05', 'S06') and r['phase'] in ('A1', 'A2', 'A3')]


def own_latest(g):
    d = g['data']; ps = sorted(d); t = ps[-1]
    if g['kind'] == 'saar':
        return t, d[t]
    return (t, 100 * ((d[t] / d[ps[-4]]) ** 4 - 1)) if len(ps) >= 4 else (t, None)


w = csv.writer(open('answer-keys/S05-S06-sa-gate.csv', 'w', newline=''))
w.writerow(['phase', 'task', 'model', 'role', 'sa_pass', 'reason', 'own_last', 'own_latest_3msaar'])
for r in inv:
    wd = glob.glob(f"execucoes/{r['source_campaign_id']}/attempts/{r['final_attempt_id']}/work")[0]
    got = X.extract(wd)
    for c, role in ROLE.items():
        k = (r['phase'], r['task'], r['model'], c)
        v = test[k]['verdict']
        if c == 'energy':
            ok, why = True, 'energy exempt'
        elif k in thr:
            ok, why = thr[k] == 'pass', f'threshold {thr[k]}'
        else:
            ok, why = v in ('pass', 'official ECB SA'), v
        last, val = own_latest(got[c]) if c in got else ('', None)
        w.writerow([*k[:3], role, ok, why, last, '' if val is None else round(val, 2)])
