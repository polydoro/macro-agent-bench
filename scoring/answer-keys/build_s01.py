"""S01 answer key: German industrial production, latest month, per Eurostat vintage.

Inputs are the Eurostat JSON-stat files the agents saved (sts_inpr_m, sts_copr_m). Within one
'updated' stamp every agent's copy agrees cell by cell; the script checks that again and stops
if not. Values are computed here, not taken from agent calculations.
"""
import collections, csv, glob, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import jsonstat

SERIES = {'total_BD': 'B-D', 'total_BDF': 'B-D_F', 'intermediarios': 'MIG_ING', 'capital': 'MIG_CAG',
          'consumo': 'MIG_COG', 'energia': 'MIG_NRG', 'construcao': 'F', 'energia_D': 'D', 'industria_BC_destatis': 'B_C',
          'consumo_duraveis': 'MIG_DCOG', 'consumo_nao_duraveis': 'MIG_NDCOG'}  # admitted shown separately


def load(pattern):
    obs = collections.defaultdict(dict)  # (updated, nace, s_adj) -> {period: value}
    for f in glob.glob(pattern, recursive=True):
        if not jsonstat.is_jsonstat(f, 'nace_r2'):
            continue
        up, rs = jsonstat.rows(f)
        for dims, v in rs:
            if dims.get('geo') != 'DE' or dims.get('unit') != 'I21' or dims.get('indic_bt', 'PRD') != 'PRD':
                continue
            key, t = (up, dims['nace_r2'], dims['s_adj']), dims['time']
            old = obs[key].get(t)
            if old is not None and abs(old - v) > 1e-9:
                raise SystemExit(f'disagreement {key} {t}: {old} vs {v}')
            obs[key][t] = v
    return obs


def shift(period, months):
    y, m = map(int, period.split('-'))
    m += months
    y, m = y + (m - 1) // 12, (m - 1) % 12 + 1
    return f'{y:04d}-{m:02d}'


def yoy(s, t):
    return 100 * (s[t] / s[shift(t, -12)] - 1) if t in s and shift(t, -12) in s else None


def saar3(s, t):
    a = [s.get(shift(t, -i)) for i in range(6)]
    if None in a:
        return None
    return 100 * ((sum(a[:3]) / sum(a[3:])) ** 4 - 1)


def latest_series(obs, nace, adj, as_of):
    """Series for nace/adj from the newest 'updated' stamp not after as_of."""
    cands = [k for k in obs if k[1] == nace and k[2] == adj and k[0] <= as_of]
    return (max(cands), obs[max(cands)]) if cands else (None, {})


def mig_energy(arm):
    """MIG energy is not in the Eurostat downloads; Bundesbank BBDE1 A2P500000 (Destatis 'Energie')
    was saved by A2 and taskwise runs. Same release (August 2026) as every arm's latest month;
    all copies agree. W = calendar adjusted, Y = calendar and seasonally adjusted."""
    import glob, sys
    sys.path.insert(0, str(Path(__file__).parent))
    import bbk
    series = {}
    for p in glob.glob('execucoes/pilot-*-s01-*/attempts/*/work/**/*.csv', recursive=True):
        try:
            rows = bbk.read(p)
        except Exception:
            continue
        for sid, t, v, _ in rows:
            if '.A2P500000.' in sid and sid[0] in 'WY':
                d = series.setdefault(sid[0], {})
                if t in d and abs(d[t] - v) > 1e-9:
                    raise ValueError(f'Bundesbank disagreement {sid} {t}')
                d[t] = v
    ca, sa = series['W'], series['Y']
    t = max(sa)
    r = lambda x: round(x, 2)
    return {'arm': arm, 'role': 'energia', 'nace': 'MIG_NRG', 'period': t, 'yoy_ca': r(yoy(ca, t)), 'yoy_sca': r(yoy(sa, t)),
            'saar3_sca': r(saar3(sa, t)), 'level_sca': r(sa[t]), 'eurostat_updated_ca': '', 'eurostat_updated_sca': '',
            'note': 'Bundesbank BBDE1 A2P500000 (Destatis Energie), not in Eurostat downloads'}


if __name__ == '__main__':
    obs = load('execucoes/pilot-*-s01-*/attempts/*/work/**/*.json')
    vintages = {'A1': '2026-10-27T23:59:59+0000', 'A2': '2026-10-29T23:59:59+0100', 'A3': '2026-11-04T23:59:59+0100'}
    out = []
    for arm, as_of in vintages.items():
        for role, nace in SERIES.items():
            up_ca, ca = latest_series(obs, nace, 'CA', as_of)
            up_sa, sa = latest_series(obs, nace, 'SCA', as_of)
            t = max(sa) if sa else (max(ca) if ca else None)
            if t is None and role == 'energia':
                out.append(mig_energy(arm))
                continue
            if t is None:
                out.append({'arm': arm, 'role': role, 'nace': nace, 'period': '', 'note': 'not in any saved download'})
                continue
            r = lambda x: '' if x is None else round(x, 2)
            out.append({'arm': arm, 'role': role, 'nace': nace, 'period': t,
                        'yoy_ca': r(yoy(ca, t)), 'yoy_sca': r(yoy(sa, t)), 'saar3_sca': r(saar3(sa, t)),
                        'level_sca': r(sa.get(t)), 'eurostat_updated_ca': up_ca[0] if up_ca else '', 'eurostat_updated_sca': up_sa[0] if up_sa else '', 'note': ''})
    path = Path(__file__).parent / 'S01-key.csv'
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['arm', 'role', 'nace', 'period', 'yoy_ca', 'yoy_sca', 'saar3_sca', 'level_sca',
                                          'eurostat_updated_ca', 'eurostat_updated_sca', 'note'])
        w.writeheader(); w.writerows(out)
    print(open(path).read())
