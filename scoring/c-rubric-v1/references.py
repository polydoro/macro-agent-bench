"""Reference sheets for the numeric block, from keys/*-key.csv. The reference is never shown to Jev.

references(task, attempt) -> {question id: {'period', 'unit', 'variants': [(label, value, tolerance)]}}

blind(), blind_text() and to_options() follow visual-rubric-v1/references.py (PR #1): options are
the tolerance bands of the admitted values plus same-width decoys, a catch-all, NAO_MOSTRADO and
NAO_VERIFICAVEL; a choice inside an admitted band maps to ATENDE.

C04: admitted values are the key's mean revision for every admitted sample and every horizon
definition of that horizon group, separately for q/q and YoY growth, in pp (tolerance 0.03, the author
2026-11-17); q/q also annualised (x4, tolerance 0.12). The key uses only vintages published before the cell's run.
"""
import csv
from pathlib import Path

KEYS = Path(__file__).parent / 'keys'
C04_TOL = 0.03


def _rows(name):
    with (KEYS / name).open(encoding='utf-8') as handle:
        return list(csv.DictReader(handle))


def _c04(attempt, last=None):
    cells = {r['attempt']: r for r in _rows('C04-cells.csv')}
    last = last or cells[attempt]['last_vintage']
    out = {}
    for measure in ('qoq', 'yoy'):
        for group in ('short', 'one_year', 'two_years', 'three_years', 'latest'):
            rows = [r for r in _rows('C04-key.csv') if r['last_vintage'] == last and r['measure'] == measure and r['horizon_group'] == group]
            variants, seen = [], set()
            for r in rows:
                options = [(f"amostra {r['sample']}, horizonte {r['horizon']}, p.p. {measure}", float(r['mean']), C04_TOL)]
                if measure == 'qoq':  # q/q revisions may be shown annualised
                    options.append((f"amostra {r['sample']}, horizonte {r['horizon']}, p.p. q/q anualizado", 4 * float(r['mean']), 4 * C04_TOL))
                for label, value, tol in options:
                    if (round(value, 3), tol) not in seen:
                        seen.add((round(value, 3), tol))
                        variants.append((label, round(value, 3), tol))
            out[f'N_{measure}_{group}'] = {'period': f'vintages até {last}', 'unit': 'pontos percentuais', 'variants': variants}
    return out


RATE, SAAR = 0.15, 0.3  # PR #1 tolerances: published one-decimal rates 0.15 pp; 3m SAAR 0.3 pp
PCT = '% (taxa de variação)'
ARMS = {'one': 'A1', 'a2': 'A2', 'a3': 'A3'}


def _variants(pairs):
    out, seen = [], set()
    for label, value, tol in pairs:
        if value not in ('', None) and round(float(value), 2) not in seen:
            seen.add(round(float(value), 2))
            out.append((label, round(float(value), 2), tol))
    return out


def _c01(attempt, arm=None):
    """Production: keys/C01-production.csv (4 admitted totals). Orders: S02 key (A1, A2, 2026-08) or C01-orders-A3.csv (2026-09)."""
    arm = arm or ARMS[attempt.split('-')[0]]
    prod = [r for r in _rows('C01-production.csv') if r['arm'] == arm]
    if arm == 'A3' or arm.startswith('A4'):  # orders: Destatis September release of 5 Nov is the latest for every A4 run
        o = _rows('C01-orders-A3.csv')[0]
        nsa = o['yoy_nsa']
    else:
        o = next(r for r in _rows('S02-key.csv') if r['arm'] == arm and r['role'] == 'total')
        nsa = next(r for r in _rows('S02-extra-yoy.csv') if r['arm'] == arm and r['role'] == 'total')['yoy_nsa']
    ref = lambda period, pairs: {'period': period, 'unit': PCT, 'variants': _variants(pairs), 'show_period': True}
    p = max(r['period'] for r in prod)
    prod = [r for r in prod if r['period'] == p]  # A4-late: B-D_F has no September stamp; keep the latest month only
    return {
        'N_prod_yoy': ref(p, [(f"{r['nace']}, YoY {adj}", r[col], RATE) for r in prod
                              for adj, col in (('ajustado por calendário', 'yoy_ca'), ('ajustado sazonal e por calendário', 'yoy_sca'))]),
        'N_prod_3m': ref(p, [(f"{r['nace']}, 3m/3m SAAR", r['saar3_sca'], SAAR) for r in prod]),
        'N_ord_yoy': ref(o['period'], [('YoY ajustado por calendário', o['yoy_ca'], RATE), ('YoY ajustado sazonal e por calendário', o['yoy_sa'], RATE),
                                       ('YoY série original', nsa, RATE)]),
        'N_ord_3m': ref(o['period'], [('3m/3m SAAR', o['saar3_sa'], SAAR)]),
    }


UNITS = {'N_conf': 'saldo (pontos)', 'N_sav': '% da renda disponível bruta'}


def _long(name, attempt):
    """Per-cell rows from a long key file (attempt, question, period, label, value, tol)."""
    out = {}
    for r in _rows(name):
        if r['attempt'] == attempt:
            ref = out.setdefault(r['question'], {'period': r['period'], 'unit': UNITS.get(r['question'], PCT), 'variants': [], 'show_period': True})
            ref['variants'].append((r['label'], float(r['value']), float(r['tol'])))
    for ref in out.values():
        ref['variants'] = _variants(ref['variants'])
    return out


def _quarter(p):
    y, q = p.split('-Q')
    return f'{q}º trimestre de {y} ({y}T{q})'


def _c03(attempt):
    """Last observed GDP from keys/C03-key.csv; target-quarter question from keys/C03-cells.csv (fixed criteria, no value)."""
    out = {}
    for r in _rows('C03-key.csv'):
        if r['attempt'] == attempt:
            ref = out.setdefault(r['question'], {'period': r['period'], 'unit': PCT, 'variants': [], 'show_period': True})
            ref['variants'].append((r['label'], float(r['value']), float(r['tol'])))
    for ref in out.values():
        ref['variants'] = _variants(ref['variants'])
    cell = next(c for c in _rows('C03-cells.csv') if c['attempt'] == attempt)
    obs, target = _quarter(cell['observed']), _quarter(cell['target'])
    pending = cell['observed'] < '2026-Q3'  # A1: Q3 not yet released when the cell ran
    criteria = {
        'ALVO_CORRETO': (f'A entrega apresenta um nowcast do PIB para o {target}, identificado como estimativa e separado dos dados observados'
                         + ('. Uma estimativa adicional para o trimestre seguinte é permitida.' if pending else
                            f', tratando o {obs} como já divulgado.')),
        'SO_OUTRO': (f'A entrega apresenta nowcast apenas para outro trimestre, sem estimativa para o {target}'
                     + ('.' if pending else f' (por exemplo, só para o {obs}, que já tinha sido divulgado).')),
        'ROTULO_ERRADO': (f'A entrega apresenta estimativa para o {target}, mas a mostra como dado observado, a confunde com outro trimestre '
                          'ou não a separa dos dados observados' + ('.' if pending else f', ou trata o {obs} como ainda não divulgado.')),
        'NAO_MOSTRADO': 'A entrega não apresenta estimativa numérica do PIB para nenhum trimestre.',
        'NAO_VERIFICAVEL': 'Não é possível identificar o trimestre da estimativa.',
    }
    out['T_target'] = {'period': cell['target'], 'unit': '', 'variants': [], 'criteria': criteria, 'admitted': ['ALVO_CORRETO'],
                       'text': (f" Data de execução da entrega: {cell['start'][:10]}. Último trimestre do PIB divulgado nessa data: {obs}"
                                f" (o {target} {'ainda não tinha sido divulgado' if pending else 'é o trimestre corrente'}).")}
    return out


def _c05(attempt, out=None):
    """S06 key per cell plus the author's SA rule for the core 3m SAAR (keys/C05-sa-gate.csv, build_c05_sa.py):
    pass admits the delivery's own 3m SAAR at the reference month; fail fixes the answer to NAO_ATENDE.
    out: an already merged key (A4: seed's month and October); the gate is always the delivery's own."""
    out = out or _long('C05-key.csv', attempt)
    gate = next((g for g in _rows('C05-sa-gate.csv') if g['attempt'] == attempt), None)
    ref = out['N_core_3m']
    if gate and gate['sa_pass'] == 'True':
        for col in ('own_3msaar_at_period', 'own_3msaar_seed_period'):
            if gate.get(col):
                ref['variants'] = _variants(ref['variants'] + [('núcleo, 3m SAAR do ajuste sazonal da própria entrega',
                                                                 float(gate[col]), SAAR)])
    else:
        ref['fixed'] = 'NAO_ATENDE'
        ref['fixed_reason'] = gate['verdict'] if gate else 'no gate row'
    return out


def _a4_cell(attempt):
    return next(r for r in _rows('A4-cells.csv') if r['attempt'] == attempt)


def _a4_newer(task, cell):
    """Key at the A4 run's own date, where a newer release came out after the A1 seed; {} if none."""
    if task == 'C01':
        return _c01(cell['seed_attempt'], 'A4-late' if cell['start_utc'] >= '2026-11-07T10:00' else 'A4-early')
    if task == 'C02':  # build_c02.py keys each A4 revision at its own start, reading its saved files too
        return _long('C02-key.csv', cell['attempt'])
    if task == 'C03':
        return _c03(cell['attempt'])
    if task == 'C05':  # October flash (4 Nov) out before every A4 revision
        return _long('C05-key.csv', cell['attempt'])
    if task == 'C04':  # every A4 revision ran 6-8 Nov: last BBKRT vintage 2026-10-30 (Q3 flash), as for A2/A3
        return _c04(cell['seed_attempt'], '2026-10-30')
    return {}


def _c03_a4(attempt, seed):
    """Target question for an A4 revision: the seed's target (A1: nowcast Q3 as not yet released) or the target
    at the revision's own date (Q3 flash out: nowcast Q4 with Q3 observed) both count."""
    old = next(c for c in _rows('C03-cells.csv') if c['attempt'] == seed)
    new = next(c for c in _rows('C03-cells.csv') if c['attempt'] == attempt)
    if old['target'] == new['target']:
        return _c03(attempt)['T_target']
    o_obs, o_t, n_obs, n_t = (_quarter(old['observed']), _quarter(old['target']), _quarter(new['observed']), _quarter(new['target']))
    criteria = {
        'ALVO_CORRETO': (f'A entrega apresenta um nowcast do PIB identificado como estimativa e separado dos dados observados, para o {n_t} '
                         f'(tratando o {n_obs} como já divulgado) ou para o {o_t} (tratando o {o_obs} como último dado divulgado). '
                         'Uma estimativa adicional para outro trimestre é permitida.'),
        'SO_OUTRO': f'A entrega apresenta nowcast apenas para outro trimestre, sem estimativa para o {o_t} nem para o {n_t}.',
        'ROTULO_ERRADO': (f'A entrega apresenta estimativa para o {o_t} ou o {n_t}, mas a mostra como dado observado, a confunde com outro '
                          'trimestre ou não a separa dos dados observados.'),
        'NAO_MOSTRADO': 'A entrega não apresenta estimativa numérica do PIB para nenhum trimestre.',
        'NAO_VERIFICAVEL': 'Não é possível identificar o trimestre da estimativa.',
    }
    return {'period': new['target'], 'unit': '', 'variants': [], 'criteria': criteria, 'admitted': ['ALVO_CORRETO'],
            'text': (f" Entrega revisada em {new['start'][:10]}, a partir de uma entrega original de {old['start'][:10]}."
                     f" Na data original, o último PIB divulgado era o {o_obs}; na data da revisão, o {n_obs} (estimativa flash)."
                     " Vale tanto manter o trimestre-alvo da entrega original quanto atualizá-lo.")}


def _a4(task, attempt):
    """A4 revision: the seed's (A1) key, plus the key of any newer release out when the revision ran
    ("seed's release or newer", confirmed by the author 2026-11-17)."""
    cell = _a4_cell(attempt)
    out = _long('C05-key.csv', cell['seed_attempt']) if task == 'C05' else BUILDERS[task](cell['seed_attempt'])
    for q, new in _a4_newer(task, cell).items():
        old = out.get(q)
        if old is None or 'criteria' in old or old.get('fixed'):
            continue
        if new['period'] != old['period']:
            old['periods'] = sorted({old['period'], new['period']})
        old['variants'] = _variants(old['variants'] + [(f"{new['period']} {l}", v, t) for l, v, t in new['variants']])
    if task == 'C03':
        out['T_target'] = _c03_a4(attempt, cell['seed_attempt'])
    if task == 'C05':  # SA gate on the revised delivery's own series
        out = _c05(attempt, out)
    return out


BUILDERS = {'C01': _c01, 'C02': lambda a: _long('C02-key.csv', a), 'C03': _c03, 'C04': _c04, 'C05': _c05}


def references(task, attempt):
    if attempt.startswith('a4-result-'):
        return _a4(task, attempt)
    return BUILDERS[task](attempt)


def blind(ref):
    """(criteria, admitted option names): admitted bands merged, two decoys of the same width each side."""
    if 'criteria' in ref:  # a closed question with fixed options (C03 target quarter)
        return ref['criteria'], ref['admitted']
    bands = sorted((v - t, v + t) for _, v, t in ref['variants'])
    merged = []
    for a, b in bands:
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    segments = [(a, b, True) for a, b in merged]
    for a, b in merged:
        w = b - a
        for lo, hi in ((a - 2 * w, a - w), (a - w, a), (b, b + w), (b + w, b + 2 * w)):
            for x, y in merged:
                if lo < y and hi > x:
                    lo, hi = (lo, x) if lo < x else (y, hi)
            if hi - lo > 1e-9 and not any(lo < y - 1e-9 and hi > x + 1e-9 for x, y, _ in segments):
                segments.append((lo, hi, False))
    segments.sort()
    criteria, admitted = {}, []
    for i, (lo, hi, ok) in enumerate(segments, 1):
        name = f'FAIXA_{i:02d}'
        criteria[name] = f'O valor mostrado está entre {lo:.3f} e {hi:.3f}.'
        if ok:
            admitted.append(name)
    criteria['OUTRO_VALOR'] = f"Há um valor mostrado para esse {'mês' if ref.get('show_period') else 'horizonte'}, fora de todas as faixas acima."
    criteria['NAO_MOSTRADO'] = 'A entrega não mostra esse valor (nem no texto, nem em tabela ou rótulo).'
    criteria['NAO_VERIFICAVEL'] = 'Há um valor, mas não é possível situá-lo em uma faixa.'
    return criteria, admitted


def blind_text(ref):
    if 'criteria' in ref:
        return ref['text']
    if ref.get('show_period'):
        y, m = ref['period'].split('-')
        if m.startswith('Q') and ref.get('periods'):  # A4: the seed's quarter or a newer one
            word = 'trimestre'
            spell = lambda p: f"{p} ({p[-1]}º trimestre de {p[:4]}, {p[:4]}T{p[-1]}, Q{p[-1]} {p[:4]})"
            when = "Trimestre de referência: o mais recente que a entrega mostra entre " + ' e '.join(spell(p) for p in ref['periods'])
        elif m.startswith('Q'):
            word = 'trimestre'
            when = f"Trimestre de referência: {ref['period']} ({m[1]}º trimestre de {y}, também escrito {y}T{m[1]}, {m[1]}T{y[2:]} ou Q{m[1]} {y})"
        elif ref.get('periods'):  # A4: the seed's month or a newer one
            word = 'mês'
            names = 'janeiro fevereiro março abril maio junho julho agosto setembro outubro novembro dezembro'.split()
            spell = lambda p: f"{p} ({names[int(p[5:]) - 1]} de {p[:4]}, {names[int(p[5:]) - 1][:3]}/{p[2:4]})"
            when = "Mês de referência: o mais recente que a entrega mostra entre " + ' e '.join(spell(p) for p in ref['periods'])
        else:
            word = 'mês'
            month = 'janeiro fevereiro março abril maio junho julho agosto setembro outubro novembro dezembro'.split()[int(m) - 1]
            when = f"Mês de referência: {ref['period']} ({month} de {y}, também escrito {month[:3]}/{y[2:]})"
        return (f" {when}. Unidade: {ref['unit']}."
                " Valores com vírgula decimal (por exemplo, -0,4) são lidos como -0.4."
                f" Se a entrega mostra vários totais ou ajustes para esse {word}, use o que ela apresenta como principal."
                f" Escolha a faixa que contém o valor mostrado. Um valor de outro {word} não conta: se a entrega não mostra "
                + (f"nenhum desses {'meses' if word == 'mês' else 'trimestres'}" if ref.get('periods') else f'esse {word}') + ", o valor não está mostrado.")
    return (f" Unidade: {ref['unit']}."
            " Se a entrega reporta vários valores para esse horizonte, use o da amostra que ela apresenta como principal."
            " Escolha a faixa que contém o valor mostrado. Se a entrega não reporta esse horizonte, o valor não está mostrado.")


def to_options(probabilities, admitted):
    out = {'ATENDE': 0.0, 'NAO_ATENDE': 0.0, 'NAO_MOSTRADO': 0.0, 'NAO_VERIFICAVEL': 0.0}
    for option, p in probabilities.items():
        if option in admitted:
            out['ATENDE'] += p
        elif option not in out:  # decoy bands, OUTRO_VALOR and fixed wrong options (C03 target)
            out['NAO_ATENDE'] += p
        else:
            out[option] += p
    return out
