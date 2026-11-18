"""S11 answer key: ECB euro area bank lending survey (BLS), net percentages, latest round, per arm.

Source: ECB data portal CSVs (BLS.Q.U2.ALL.*.WFNET) saved in all three arms; copies agree.
Every arm has the October 2026 round, published as "the third quarter of 2026" in the ECB report
but stored by the ECB under TIME_PERIOD 2026-Q4. Deliveries may label it either way; both labels
are correct. Realised changes (B3) are the keyed values; expectations for the next quarter (F3)
are listed separately and are a different horizon. Cross-check with the ECB report text:
firms standards 9, demand -6; housing standards 0, demand -27; consumer standards 14, demand -2.
"""
import csv, glob

csv.field_size_limit(10 ** 9)
ROLES = {'total': 'O.E.Z.{h}.ST.S', 'demanda_empresas': 'O.E.Z.{h}.ZZ.D', 'padroes_habitacao': 'Z.H.H.{h}.ST.S',
         'demanda_habitacao': 'Z.H.H.{h}.ZZ.D', 'padroes_consumo': 'Z.H.C.{h}.ST.S', 'demanda_consumo': 'Z.H.C.{h}.ZZ.D'}
ARMDIR = {'A1': 'pilot-one', 'A2': 'pilot-a2', 'A3': 'pilot-a3'}


def load(arm):
    cells = {}
    for p in glob.glob(f'execucoes/{ARMDIR[arm]}-s11-*/attempts/*/work/**/*.csv', recursive=True):
        if '/entrega/' in p:
            continue
        with open(p, errors='ignore') as fh:
            head = fh.readline()
            if 'OBS_VALUE' not in head or 'TIME_PERIOD' not in head:
                continue
            fh.seek(0)
            for r in csv.DictReader(fh):
                if not r.get('KEY') or not r.get('OBS_VALUE'):
                    continue
                k, v = (r['KEY'], r['TIME_PERIOD']), float(r['OBS_VALUE'])
                if k in cells and abs(cells[k] - v) > 1e-9:
                    raise ValueError(f'disagreement {arm} {k}')
                cells[k] = v
    return cells


if __name__ == '__main__':
    with open('answer-keys/S11-key.csv', 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['arm', 'role', 'horizon', 'key', 'time_period_ecb', 'report_label', 'net_pct', 'net_pct_previous'])
        for arm in ARMDIR:
            cells = load(arm)
            for role, pat in ROLES.items():
                for h, name in (('B3', 'realised'), ('F3', 'expected_next_quarter')):
                    key = f'BLS.Q.U2.ALL.{pat.format(h=h)}.WFNET'
                    ts = sorted(t for k, t in cells if k == key)
                    if not ts:
                        continue
                    t = ts[-1]
                    label = '2026 Q3 (October 2026 survey)' if t == '2026-Q4' else ''
                    w.writerow([arm, role, name, key, t, label, round(cells[(key, t)], 2), round(cells[(key, ts[-2])], 2)])
