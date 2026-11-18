"""S03 answer key: Spanish retail trade (INE ICM) at constant prices, latest month, per arm.

A2 and A3 saved INE tempus3 series (September release, published 2026-10-29 before A2 ran).
A1 ran on 2026-10-27, when August was the latest month; its key comes from the INE August
release annex (ICM0826.xlsx, 2026-09-29) that A1 agents saved, which gives official YoY rates
and the SA level but not monthly history, so A1's 3m SAAR comes from a separate source (see README).
"""
import collections, csv, glob, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import ine
from build_s01 import yoy, saar3

ARMS = {'pilot-one': 'A1', 'pilot-a2': 'A2', 'pilot-a3': 'A3'}
P = 'Total Nacional. Cifra de negocio a precios constantes. '
SIN = 'Comercio al por menor sin Estaciones de Servicio (47 sin 473). '
STEMS = {
    'total_general': P + 'General. Comercio al por menor, excepto de vehículos de motor y motocicletas. Índice.',
    'total_sin_eess': P + SIN + 'General. Índice.',
    'alimentacion': P + 'Alimentación (4711+472). General. Índice.',
    'resto': P + 'Resto (4719+474+475+476+477+478+479). General. Índice.',
    'equipo_personal': P + 'Equipo personal (4751+4771+4772). General. Índice.',
    'equipo_hogar': P + 'Equipo del hogar (4743+4752+4754+4759+4763). General. Índice.',
    'grandes_superficies': P + SIN + 'Grandes Superficies. Índice.',
    'grandes_cadenas': P + SIN + 'Grandes cadenas. Índice.',
    'pequenas_cadenas': P + SIN + 'Pequeñas cadenas. Índice.',
    'unilocalizadas': P + SIN + 'Empresas unilocalizadas. Índice.',
}
ADJ = {'orig': '', 'ca': ' Datos ajustados de calendario.', 'sa': ' Datos ajustados de estacionalidad y calendario.'}


def load():
    obs = collections.defaultdict(dict)
    for f in glob.glob('execucoes/pilot-*-s03-*/attempts/*/work/**/*.json', recursive=True):
        arm = ARMS[f.split('/')[1].rsplit('-s03', 1)[0]]
        for _, name, pts in ine.series(f):
            if not any(name == stem + a for stem in STEMS.values() for a in ADJ.values()):
                continue  # rate series come with different decimals; only index series are used
            for t, v in pts.items():
                old = obs[(arm, name)].setdefault(t, v)
                if abs(old - v) > 1e-9:
                    raise SystemExit(f'disagreement {arm} {name} {t}: {old} vs {v}')
    return obs


ANNEX_LABELS = {'ÍNDICE GENERAL': 'total_general', 'General sin estaciones de servicio': 'total_sin_eess',
                '- Alimentación': 'alimentacion', '- Resto': 'resto', '- Equipo personal': 'equipo_personal',
                '- Equipo del hogar': 'equipo_hogar', '- Empresas unilocalizadas': 'unilocalizadas',
                '- Pequeñas cadenas': 'pequenas_cadenas', '- Grandes cadenas': 'grandes_cadenas',
                '- Grandes superficies': 'grandes_superficies'}


def annex_rates():
    """{role: {'sa': yoy, 'ca': yoy, 'orig': yoy}} at constant prices ('deflactado') from ICM0826.xlsx."""
    import openpyxl
    found = {}
    for f in sorted(glob.glob('execucoes/pilot-one-s03-*/attempts/*/work/**/ICM0826*.xlsx', recursive=True)):
        wb = openpyxl.load_workbook(f, data_only=True)
        rates = collections.defaultdict(dict)
        for sheet, table_adj in (('Tabla1_2', ('sa', 'ca')), ('Tabla3_4', ('orig', None))):
            ws = wb[sheet] if sheet in wb.sheetnames else None
            if ws is None:
                continue
            block = -1
            for row in ws.iter_rows(values_only=True):
                cells = [c for c in row if c is not None]
                if cells and isinstance(cells[0], str) and cells[0][:2] in ('1.', '2.', '3.', '4.'):
                    block += 1
                if len(cells) < 4 or not isinstance(cells[0], str):
                    continue
                role = ANNEX_LABELS.get(cells[0].strip()) or ANNEX_LABELS.get('- ' + cells[0].strip().lstrip('- ').strip())
                adj = table_adj[block] if 0 <= block < 2 else None
                if role and adj and role not in rates or (role and adj and adj not in rates[role]):
                    # SA block: index, m/m, y/y, ytd | deflated index, m/m, y/y, ytd -> y/y deflated is cells[7]
                    # CA/orig blocks: index, y/y, ytd | deflated index, y/y, ytd -> y/y deflated is cells[5]
                    rates[role][adj] = float(cells[7] if adj == 'sa' else cells[5])
        if not rates:
            continue  # English copy: labels differ, nothing matched
        if found and found != rates:
            raise SystemExit(f'annex copies differ: {f}')
        found = dict(rates)
    return found


def a1_rows():
    """A1: August 2026 from the INE annex; total 3m SAAR from Eurostat sts_trtu_m (stamp 2026-10-27,
    SA level equals the annex's 111.6)."""
    import jsonstat
    rates = annex_rates()
    euro = {}
    for f in glob.glob('execucoes/pilot-one-s03-*/attempts/*/work/**/*.json', recursive=True):
        if jsonstat.is_jsonstat(f, 'nace_r2'):
            _, rs = jsonstat.rows(f)
            for d, v in rs:
                if d.get('geo') == 'ES' and d['nace_r2'] == 'G47' and d['s_adj'] == 'SCA' and d.get('unit') == 'I21' \
                        and d.get('indic_bt') in ('VOL_SLS', None):
                    euro[d['time']] = v
    rows = []
    for role in STEMS:
        x = rates.get(role, {})
        rows.append({'arm': 'A1', 'role': role, 'period': '2026-08', 'yoy_sa': x.get('sa', ''), 'yoy_ca': x.get('ca', ''),
                     'yoy_orig': x.get('orig', ''), 'saar3_sa': round(saar3(euro, '2026-08'), 2) if role == 'total_general' else '',
                     'source': 'INE ICM0826 annex' + ('; 3m SAAR Eurostat 2026-10-27' if role == 'total_general' else '')})
    return rows


if __name__ == '__main__':
    obs = load()
    # the same release seen by two arms must agree
    for (arm, name), s in obs.items():
        if arm == 'A2' and ('A3', name) in obs:
            o = obs[('A3', name)]
            diff = [t for t in s if t in o and abs(s[t] - o[t]) > 1e-9]
            if diff:
                print('A2/A3 differ', name, diff[:3])
    r = lambda x: '' if x is None else round(x, 2)
    rows = []
    for arm in ('A2', 'A3'):
        for role, stem in STEMS.items():
            s = {k: obs.get((arm, stem + a), {}) for k, a in ADJ.items()}
            t = max(s['sa']) if s['sa'] else ''
            rows.append({'arm': arm, 'role': role, 'period': t, 'yoy_sa': r(yoy(s['sa'], t)) if t else '',
                         'yoy_ca': r(yoy(s['ca'], t)) if t else '', 'yoy_orig': r(yoy(s['orig'], t)) if t else '',
                         'saar3_sa': r(saar3(s['sa'], t)) if t else '', 'source': 'INE tempus3 series'})
    rows = a1_rows() + rows
    path = Path(__file__).parent / 'S03-key.csv'
    with open(path, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    print(open(path).read())
