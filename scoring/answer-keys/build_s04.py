"""S04 answer key: INSEE household confidence (CAMME), SA, latest month, per arm.

Source: the INSEE release annex 260_IR_Camme.xlsx (first sheet, SA history) that agents in all
three arms saved; A1 also saved the BDM SDMX file. All arms saw the October 2026 survey.
Values are native (index or balance); the key is the published value itself.
"""
import csv, glob, sys
from pathlib import Path
import openpyxl

ARMS = {'pilot-one': 'A1', 'pilot-a2': 'A2', 'pilot-a3': 'A3'}
ROLES = {  # role -> French column label(s) in the annex; several labels = any is admissible
    'total': ['Indicateur synthétique de confiance des ménages'],
    'situacao_financeira_passada': ['Situation financière personnelle - évolution passée'],
    'situacao_financeira_futura': ["Situation financière personnelle - perspectives d'évolution"],
    'nivel_vida_futuro': ["Niveau de vie en France - perspectives d'évolution"],
    'compras_importantes': ['Opportunité de faire des achats importants'],
    'capacidade_poupanca': ["Capacité d'épargne actuelle", "Capacité d'épargne future"],
    'desemprego_esperado': ["Chômage - perspectives d'évolution"],
    'precos': ['Prix - évolution passée', "Prix - perspectives d'évolution"],
}


def read(f):
    ws = openpyxl.load_workbook(f, data_only=True, read_only=True).worksheets[0]
    header, data = None, []
    for r in ws.iter_rows(values_only=True):
        if r and r[0] == 'DATE':
            header = [str(c).strip() if c else '' for c in r]
        elif header and r and hasattr(r[0], 'year'):
            data.append(r)
    return header, data


if __name__ == '__main__':
    found = {}
    for f in sorted(glob.glob('execucoes/pilot-*-s04-*/attempts/*/work/**/*.xlsx', recursive=True)):
        if f.endswith('_EN.xlsx'):
            continue  # English edition: its first sheet is a different table
        header, data = read(f)
        if not header or 'Indicateur synthétique de confiance des ménages' not in header:
            continue  # English or other workbook
        arm = ARMS[f.split('/')[1].rsplit('-s04', 1)[0]]
        last = data[-1]
        vals = {label: last[header.index(label)] for labels in ROLES.values() for label in labels if label in header}
        key = (arm, last[0].strftime('%Y-%m'))
        if key in found and found[key] != vals:
            raise SystemExit(f'disagreement {key} {f}')
        found[key] = vals
    latest = {arm: max(t for a, t in found if a == arm) for arm, _ in found}
    rows = []
    for (arm, period), vals in sorted(found.items()):
        if period != latest[arm]:
            continue  # an older edition of the annex (e.g. a 2022 file one agent also saved)
        for role, labels in ROLES.items():
            v = [f'{vals[l]:.2f}' for l in labels if isinstance(vals.get(l), (int, float))]
            rows.append({'arm': arm, 'role': role, 'period': period, 'value': ' | '.join(v),
                         'series': ' | '.join(l for l in labels if isinstance(vals.get(l), (int, float)))})
    path = Path(__file__).parent / 'S04-key.csv'
    with open(path, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    print(open(path).read())
