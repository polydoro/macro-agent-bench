"""S05 (Italy) and S06 (euro area) answer keys: HICP YoY and 3m SAAR at the latest month, per arm.

YoY: Eurostat RCH_A (published, 1 dp) and the same rate recomputed from the I25 index.
3m SAAR end to end, 100*((SA_t/SA_t-3)^4-1):
  S06: ECB official SA index HICP.M.U2.Y.<item>.4F0.INX saved by the agents (same arm).
  S05: no official SA exists; X13 (ABS-X13-reference-v3, x13.py) on Eurostat I25 NSA from 2010-01.
Energy 3m SAAR: SA or unadjusted admitted (the author 2026-11-17); for S06 the ECB SA energy equals NSA.
Vintages: Eurostat stamp 2026-10-16 for A1/A2 (latest 2026-09), 2026-11-04 for A3 (October flash).
"""
import csv, glob, sys
sys.path.insert(0, 'answer-keys')
import jsonstat as J, x13

STAMP = {'A1': '2026-10-16T23:00:00+0200', 'A2': '2026-10-16T23:00:00+0200', 'A3': '2026-11-04T11:00:00+0100'}
ARMDIR = {'A1': 'pilot-one', 'A2': 'pilot-a2', 'A3': 'pilot-a3'}
ROLES = {'total': ('TOTAL', '000000'), 'nucleo': ('TOT_X_NRG_FOOD', 'XEF000'), 'bens_nao_energeticos': ('IGD_NNRG', 'IGXE00'),
         'servicos': ('SERV', 'SERV00'), 'energia': ('NRG', 'NRGY00'), 'alimentos': ('FOOD', 'FOOD00')}
GEO = {'S05': 'IT', 'S06': 'EA'}


def eurostat(task, arm):
    """{(unit, coicop18): {time: value}} for the arm's stamp; every saved copy must agree cell by cell."""
    out = {}
    for p in glob.glob(f'execucoes/pilot-*{task.lower()}*/attempts/*/work/**/*.json', recursive=True):
        if not J.is_jsonstat(p, 'coicop18'):
            continue
        up, rs = J.rows(p)
        if up != STAMP[arm]:
            continue
        for d, v in rs:
            if d.get('geo') != GEO[task] or d.get('unit') not in ('I25', 'RCH_A') or 'release' in d:  # flash-vs-final table skipped
                continue
            cell = out.setdefault((d['unit'], d['coicop18']), {})
            if d['time'] in cell and abs(cell[d['time']] - v) > 1e-9:
                raise ValueError(f'disagreement {task} {arm} {d} {cell[d["time"]]} vs {v}')
            cell[d['time']] = v
    return out


def ecb_sa(arm, item):
    out = {}
    for p in glob.glob(f'execucoes/{ARMDIR[arm]}-s06*/attempts/*/work/**/*.csv', recursive=True):
        with open(p, errors='ignore') as fh:
            if 'OBS_VALUE' not in fh.readline():
                continue
            fh.seek(0)
            for r in csv.DictReader(fh):
                if r.get('KEY') == f'HICP.M.U2.Y.{item}.4F0.INX' and r.get('OBS_VALUE'):
                    v = float(r['OBS_VALUE'])
                    if r['TIME_PERIOD'] in out and abs(out[r['TIME_PERIOD']] - v) > 1e-9:
                        raise ValueError(f'ECB disagreement {arm} {item} {r["TIME_PERIOD"]}')
                    out[r['TIME_PERIOD']] = v
    return out


def shift(p, k):
    y, m = int(p[:4]), int(p[5:7]) - 1 + k
    return f'{y + m // 12}-{m % 12 + 1:02d}'


def saar3(s, t):
    return 100 * ((s[t] / s[shift(t, -3)]) ** 4 - 1)


if __name__ == '__main__':
    w = csv.writer(open('answer-keys/S05-S06-key.csv', 'w', newline=''))
    w.writerow(['task', 'arm', 'role', 'period', 'yoy_rch_a', 'yoy_calc_i25', 'saar3_sa', 'saar3_source', 'saar3_nsa'])
    for task in ('S05', 'S06'):
        for arm in ('A1', 'A2', 'A3'):
            es = eurostat(task, arm)
            for role, (code, item) in ROLES.items():
                idx, rch = es[('I25', code)], es[('RCH_A', code)]
                t = max(idx)
                yc = 100 * (idx[t] / idx[shift(t, -12)] - 1)
                if task == 'S06':
                    sa = ecb_sa(arm, item); src = f'ECB HICP.M.U2.Y.{item}.4F0.INX'
                else:
                    ps = sorted(p for p in idx if p >= '2010-01')
                    cfg, adj = x13.adjust([idx[p] for p in ps], ps[0]); sa = dict(zip(ps, adj)); src = f'X13 {cfg} on Eurostat I25 2010-01..{ps[-1]}'
                s3 = round(saar3(sa, t), 2) if t in sa else ''
                if t not in sa:
                    src += f' (no SA for {t})'
                w.writerow([task, arm, role, t, rch.get(t, ''), round(yc, 2), s3, src, round(saar3(idx, t), 2)])
    print(open('answer-keys/S05-S06-key.csv').read())


# --- S05 NIC (ISTAT national index), admitted as the headline ---------------------------------
# YoY: ISTAT published rates. A1/A2: serie09_2026.xlsx Tabella_6 (September final; one identical
# file across all saved copies). A3: ISTAT preliminary release of 30 Oct 2026 (October), saved as
# text; it also gives September's rates. Components below are ISTAT's own aggregates from the
# release text (Italian core = ex energy and fresh food), quoted, not recomputed.
MONTHS = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto',
          'settembre', 'ottobre', 'novembre', 'dicembre']
NIC_RELEASE = {  # arm -> period, {role: yoy} from ISTAT release text
    'A1': ('2026-09', {'total': 4.2, 'nucleo_istat': 1.6, 'servicos': 2.6, 'ex_energia': 2.0}),
    'A2': ('2026-09', {'total': 4.2, 'nucleo_istat': 1.6, 'servicos': 2.6, 'ex_energia': 2.0}),
    'A3': ('2026-10', {'total': 5.4, 'nucleo_istat': 2.0, 'servicos': 2.9, 'ex_energia': 2.5}),
}


def nic_index():
    """Monthly NIC, base 2025=100: ISTAT series M.IT.39.4.00 (base 2015, 2016-01..2025-12) divided by
    ISTAT's linking coefficient 1.226, then M.IT.85.4.00 (base 2025, 2026). Both via DBnomics, saved
    by an A3 agent. Checked against Tabella_6 of serie09_2026.xlsx for every month it shows."""
    import json, openpyxl
    d = glob.glob('execucoes/pilot-a3-s05*/attempts/*kimi*/work/dados')[0]
    def obs(f):
        s = json.load(open(f'{d}/{f}'))['series']['docs'][0]
        return {p: float(v) for p, v in zip(s['period'], s['value']) if v not in (None, 'NA')}
    old, new = obs('istat167745_total_39.json'), obs('istat167745_total_85.json')
    series = {p: v / 1.226 for p, v in old.items()}
    series.update(new)
    # cross-check with ISTAT's own table (A1/A2 copy)
    f = sorted(glob.glob('execucoes/pilot-*s05*/attempts/*/work/**/serie09_2026.xlsx', recursive=True))[0]
    year, base = None, None
    for r in openpyxl.load_workbook(f, read_only=True, data_only=True)['Tabella_6'].iter_rows(values_only=True):
        if isinstance(r[2], str) and 'Base' in r[2]:
            base = r[2].strip()
        if isinstance(r[0], int):
            year = r[0]
        if r[1] in MONTHS and isinstance(r[2], (int, float)):
            p = f'{year}-{MONTHS.index(r[1]) + 1:02d}'
            ref = old.get(p) if base == 'Base 2015=100' else new.get(p)
            assert ref is not None and abs(ref - r[2]) < 1e-9, (p, base, ref, r[2])
    return series


if __name__ == '__main__':
    nic = nic_index()
    w = csv.writer(open('answer-keys/S05-NIC-key.csv', 'w', newline=''))
    w.writerow(['arm', 'role', 'period', 'yoy_istat', 'yoy_calc_index', 'saar3_sa', 'saar3_source'])
    for arm, (t, rates) in NIC_RELEASE.items():
        s = {p: v for p, v in nic.items() if p <= t}
        ps = sorted(s)
        cfg, adj = x13.adjust([s[p] for p in ps], ps[0])
        sa = dict(zip(ps, adj))
        for role, y in rates.items():
            calc = round(100 * (s[t] / s[shift(t, -12)] - 1), 2) if role == 'total' else ''
            s3 = round(saar3(sa, t), 2) if role == 'total' else ''
            w.writerow([arm, role, t, y, calc, s3, f'X13 {cfg} on NIC (ISTAT) {ps[0]}..{t}' if role == 'total' else 'ISTAT release text'])
    print(open('answer-keys/S05-NIC-key.csv').read())
