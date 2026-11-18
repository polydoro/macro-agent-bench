"""Reference sheets for the numeric questions, built from ../answer-keys/*-key.csv.

references(task, arm, model) -> ({question id: reference}, {question id: fixed answer}).

A reference is {'period', 'unit', 'variants': [(label, value, tolerance)]}; the delivery's
value matches if it equals ANY admitted variant within that variant's tolerance, for the
same series and period. The period is the latest one available on the arm's run date
(the author 2026-11-17): a delivery that stops earlier does not show the value and scores zero.

Fixed answers are decided in code, without a model call: the S05/S06 3m SAAR of a
non-energy series whose seasonal adjustment failed the SA criterion (sa_gate.py) scores
NAO_ATENDE. When it passed, the delivery's own latest 3m SAAR is admitted as a variant.

Tolerances (pp unless noted): published one-decimal rates and pp changes 0.15; 3m/3m and
3m SAAR, and annualised q/q, 0.3; survey balances and indices published as integers 0.6.
"""
import csv
from pathlib import Path

KEYS = Path(__file__).parent.parent / 'answer-keys'
RATE, SAAR, BALANCE = 0.15, 0.3, 0.6
PCT = '% (taxa de variação)'


def _rows(name):
    with (KEYS / name).open(encoding='utf-8') as handle:
        return list(csv.DictReader(handle))


def _ref(period, unit, variants):
    seen, out = set(), []
    for label, value, tol in variants:
        if value in ('', None):
            continue
        value = round(float(value), 2)
        if (label, value) not in seen:
            seen.add((label, value))
            out.append((label, value, tol))
    return {'period': period, 'unit': unit, 'variants': out} if out else None


def _s01(arm):
    rows = {r['role']: r for r in _rows('S01-key.csv') if r['arm'] == arm and r['period']}
    totals = [('total_BD', 'B-D (indústria sem construção)'), ('total_BDF', 'B-D_F (com construção, manchete Destatis)'),
              ('industria_BC_destatis', 'B_C "Industrie" do Destatis (sem energia e construção)')]
    period = rows['total_BD']['period']
    out = {
        'N_total_yoy': _ref(period, PCT, [v for k, name in totals for v in (
            (f'{name}, YoY ajustado por calendário', rows[k]['yoy_ca'], RATE),
            (f'{name}, YoY ajustado sazonal e por calendário', rows[k]['yoy_sca'], RATE))]),
        'N_total_3m': _ref(period, PCT, [(f'{name}, 3m/3m SAAR', rows[k]['saar3_sca'], SAAR) for k, name in totals]),
    }
    names = {'MIG_NRG': 'energia (agrupamento MIG do Destatis)', 'D': 'energia NACE D'}
    for split in ('consumo_duraveis', 'consumo_nao_duraveis'):  # used by code_check only: consumer goods shown as two series
        r = rows.get(split)
        if r:
            out[f'X_{split}_yoy'] = _ref(period, PCT, [(f'{r["nace"]}, YoY ajustado por calendário', r['yoy_ca'], RATE),
                                                       (f'{r["nace"]}, YoY ajustado sazonal e por calendário', r['yoy_sca'], RATE)])
    for role, keys in (('intermediarios', ['intermediarios']), ('capital', ['capital']), ('consumo', ['consumo']),
                       ('energia', ['energia', 'energia_D']), ('construcao', ['construcao'])):
        variants = []
        for r in (rows[k] for k in keys if k in rows):
            n = names.get(r['nace'], r['nace'])
            variants += [(f'{n}, YoY ajustado por calendário', r['yoy_ca'], RATE), (f'{n}, YoY ajustado sazonal e por calendário', r['yoy_sca'], RATE)]
        out[f'N_{role}_yoy'] = _ref(period, PCT, variants)
    return out


def _s02(arm):
    rows = {r['role']: r for r in _rows('S02-key.csv') if r['arm'] == arm}
    extra = {r['role']: r for r in _rows('S02-extra-yoy.csv') if r['arm'] == arm}  # GENESIS 42151-0004: CA components, NSA all
    ca = {k: r['yoy_ca'] for k, r in extra.items()}
    t = rows['total']
    out = {'N_total_yoy': _ref(t['period'], PCT, [('YoY ajustado por calendário', t['yoy_ca'], RATE),
                                                  ('YoY ajustado sazonal e por calendário', t['yoy_sa'], RATE),
                                                  ('YoY série original', extra['total']['yoy_nsa'], RATE)]),
           'N_total_3m': _ref(t['period'], PCT, [('3m/3m SAAR', t['saar3_sa'], SAAR)])}
    for role in ('domestico', 'externo'):
        r = rows[role]
        out[f'N_{role}_yoy'] = _ref(r['period'], PCT, [('YoY ajustado por calendário', r['yoy_ca'] or ca.get(role, ''), RATE),
                                                       ('YoY ajustado sazonal e por calendário', r['yoy_sa'], RATE),
                                                       ('YoY série original', extra[role]['yoy_nsa'], RATE)])
    return out


def _yoy3(r, label=''):
    pre = f'{label}, ' if label else ''
    return [(f'{pre}YoY ajustado sazonal e por calendário', r['yoy_sa'], RATE),
            (f'{pre}YoY ajustado por calendário', r['yoy_ca'], RATE), (f'{pre}YoY série original', r['yoy_orig'], RATE)]


def _s03(arm):
    rows = {r['role']: r for r in _rows('S03-key.csv') if r['arm'] == arm}
    g, s = rows['total_general'], rows['total_sin_eess']
    out = {'N_total_yoy': _ref(g['period'], PCT, _yoy3(g, 'índice geral') + _yoy3(s, 'geral sem estações de serviço')),
           'N_total_3m': _ref(g['period'], PCT, [('índice geral, 3m/3m SAAR', g['saar3_sa'], SAAR),
                                                 ('geral sem estações de serviço, 3m/3m SAAR', s['saar3_sa'], SAAR)])}
    for role in ('alimentacion', 'resto', 'equipo_personal', 'equipo_hogar', 'grandes_superficies', 'grandes_cadenas',
                 'pequenas_cadenas', 'unilocalizadas'):
        out[f'N_{role}_yoy'] = _ref(rows[role]['period'], PCT, _yoy3(rows[role]))
    return out


def _s04(arm):
    out = {}
    for r in _rows('S04-key.csv'):
        if r['arm'] == arm:
            names, values = r['series'].split(' | '), r['value'].split(' | ')
            out[f"N_{r['role']}_native"] = _ref(r['period'], 'nível do índice ou saldo de opinião (pontos)',
                                                [(n, v, BALANCE) for n, v in zip(names, values)])
    return out


S56_ROLES = ('total', 'nucleo', 'bens_nao_energeticos', 'servicos', 'energia', 'alimentos')


def _s05_s06(task, arm, model, gate_phase=None):
    rows = {r['role']: r for r in _rows('S05-S06-key.csv') if r['task'] == task and r['arm'] == arm}
    nic = {r['role']: r for r in _rows('S05-NIC-key.csv') if r['arm'] == arm} if task == 'S05' else {}
    gate_file = 'S05-S06-sa-gate-A4.csv' if gate_phase else 'S05-S06-sa-gate.csv'
    gate = {r['role']: r for r in _rows(gate_file) if r['task'] == task and r['phase'] == (gate_phase or arm) and r['model'] == model}
    index = 'HICP' if task == 'S06' else 'HICP/IPCA'
    nic_role = {'total': 'total', 'nucleo': 'nucleo_istat', 'servicos': 'servicos'}
    refs, fixed = {}, {}
    for role in S56_ROLES:
        r = rows[role]
        yoy = [(f'{index}, YoY publicado', r['yoy_rch_a'], RATE), (f'{index}, YoY calculado do índice', r['yoy_calc_i25'], RATE)]
        if role in nic_role and nic_role[role] in nic:
            yoy.append(('NIC (ISTAT), YoY publicado' + (' — núcleo ISTAT: sem energia e alimentos frescos' if role == 'nucleo' else ''),
                        nic[nic_role[role]]['yoy_istat'], RATE))
        refs[f'N_{role}_yoy'] = _ref(r['period'], PCT, yoy)
        qid = f'N_{role}_3me'
        g = gate.get(role)
        if g is None:
            raise KeyError(f'no SA gate row for {task} {arm} {model} {role}')
        if g['sa_pass'] != 'True':
            fixed[qid] = {'NAO_ATENDE': 1.0, 'reason': f"SA criterion: {g['reason']}"}
            continue
        saar = [(f'{index}, 3m SAAR de referência ({r["saar3_source"].split(" on ")[0].replace("ECB ", "BCE ")})', r['saar3_sa'], SAAR)]
        if role == 'total' and 'total' in nic:
            saar.append(('NIC (ISTAT), 3m SAAR de referência (X13)', nic['total']['saar3_sa'], SAAR))
        if g['own_last'] == r['period'] and g['own_latest_3msaar']:
            saar.append(('valor da própria série dessazonalizada da entrega', g['own_latest_3msaar'], SAAR))
        refs[qid] = _ref(r['period'], PCT, saar)
    if 'energia' in rows:  # energy: SA or unadjusted admitted
        nsa = rows['energia'].get('saar3_nsa')
        if nsa and f'N_energia_3me' in refs:
            refs['N_energia_3me']['variants'].append(('energia sem ajuste sazonal, 3m SAAR', round(float(nsa), 2), SAAR))
    return refs, fixed


def _s07(arm):
    out = {}
    for r in _rows('S07-key.csv'):
        if r['arm'] != arm or r['role'] == 'manufatura':
            continue
        out[f"N_{r['role']}_yoy"] = _ref(r['period'], PCT, [('YoY do mês', r['yoy'], RATE), ('YoY publicado pelo ONS', r['ons_yoy'], RATE)])
        if r['role'] == 'total':
            out['N_total_3m'] = _ref(r['period'], PCT, [('3m/3m SAAR (anualizado)', r['saar3m3m'], SAAR),
                                                        ('3m/3m do ONS, anualizado', r['ons_3m3m_annualised'], SAAR)])
    return out


def _s08(arm):
    rows = [r for r in _rows('S08-key.csv') if r['arm'] == arm]
    adj = {'csa': 'sem ajuste por eventos esportivos', 'cssa': 'com ajuste por eventos esportivos'}  # SECO: cssa = sport-adjusted
    period = rows[0]['period']
    out = {}
    tot = [r for r in rows if r['role'] == 'total']
    out['N_total_yoy'] = _ref(period, PCT, [(f'PIB {adj[r["adjustment"]]}, YoY', r['yoy'], RATE) for r in tot])
    out['N_total_qoq'] = _ref(period, PCT, [v for r in tot for v in (
        (f'PIB {adj[r["adjustment"]]}, q/q', r['qoq'], RATE), (f'PIB {adj[r["adjustment"]]}, q/q anualizado', r['qoq_annualised'], SAAR))])
    for role in ('consumo_familias', 'consumo_governo', 'investimento', 'exportacoes', 'importacoes', 'industria', 'servicos'):
        variants = []
        for r in rows:
            if r['role'] == role:
                name = f"{r['code']} ({adj[r['adjustment']]})" if 'release' not in r['code'] else r['code'].replace('(release text)', '(texto da divulgação SECO)')
                variants += [(f'{name}, YoY', r['yoy'], RATE), (f'{name}, q/q', r['qoq'], RATE), (f'{name}, q/q anualizado', r['qoq_annualised'], SAAR)]
        out[f'N_{role}_growth'] = _ref(period, PCT, variants)
    return out


def _s09(arm):
    rows = [r for r in _rows('S09-key.csv') if r['arm'] == arm]
    period = rows[0]['period']
    yoy = lambda r: [(f"NACE {r['nace']}, YoY {k}", r[f'yoy_{c}'], RATE) for c, k in
                     (('sa', 'ajustado sazonal'), ('ca', 'ajustado por calendário'), ('nsa', 'série original'))]
    out = {'N_total_yoy': _ref(period, PCT, [v for r in rows if r['role'] == 'total' for v in yoy(r)]),
           'N_total_3m': _ref(period, PCT, [(f"NACE {r['nace']}, 3m/3m SAAR", r['saar3m3m_sa'], SAAR) for r in rows if r['role'] == 'total'])}
    for role in ('alimentos', 'combustivel', 'equipamentos_domesticos', 'cultura_lazer', 'outros_bens', 'internet'):
        out[f'N_{role}_yoy'] = _ref(period, PCT, [v for r in rows if r['role'] == role for v in yoy(r)])
    return out


def _s10(arm):
    names = {'nsa': 'série original', 'sa': 'dessazonalizada', 'sa_suavizada': 'dessazonalizada e suavizada (SCB)'}
    rows = [r for r in _rows('S10-key.csv') if r['arm'] == arm]
    return {'N_total_native': _ref(rows[0]['period'], '% da força de trabalho, 15–74 anos',
                                   [(f"taxa {names[r['version']]}", r['rate'], RATE) for r in rows])}


def _s11(arm):
    out = {}
    for r in _rows('S11-key.csv'):
        if r['arm'] == arm and r['horizon'] == 'realised':
            out[f"N_{r['role']}_native"] = _ref(
                f"{r['time_period_ecb']} no portal de dados do BCE, que o relatório do BCE chama de pesquisa do 3º trimestre de 2026 (outubro de 2026); os dois rótulos são o mesmo período",
                'percentual líquido, variação realizada (não a expectativa)', [('percentual líquido realizado', r['net_pct'], BALANCE)])
    return out


BUILDERS = {'S01': _s01, 'S02': _s02, 'S03': _s03, 'S04': _s04, 'S07': _s07, 'S08': _s08, 'S09': _s09, 'S10': _s10, 'S11': _s11}


A4_SOURCES = ('A1', 'A3')  # the author 2026-11-17: the seed's release or newer (A1 key, A3 vintage, plus A4_NEWER)
A4_NEWER = {'S02'}  # tasks with a release after A3 and before the A4 runs (Destatis orders, 2026-11-05): key arm 'A4'


def references(task, arm, model=None):
    if arm in ('A4s', 'A4e'):
        return _a4(task, arm, model)
    if task in ('S05', 'S06'):
        refs, fixed = _s05_s06(task, arm, model)
    else:
        refs, fixed = BUILDERS[task](arm), {}
    return {q: r for q, r in refs.items() if r}, fixed


def blind(ref):
    """Closed reading question that does not reveal the reference.

    Options are value ranges: each admitted value's tolerance band (merged where they overlap)
    plus two decoy ranges of the same width on each side, all looking alike, then a catch-all
    for other values. Returns (criteria, admitted option names).
    """
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
            for x, y in merged:  # trim decoys at admitted bands
                if lo < y and hi > x:
                    lo, hi = (lo, x) if lo < x else (y, hi)
            if hi - lo > 1e-9 and not any(lo < y - 1e-9 and hi > x + 1e-9 for x, y, _ in segments):
                segments.append((lo, hi, False))
    segments.sort()
    criteria, admitted = {}, []
    for i, (lo, hi, ok) in enumerate(segments, 1):
        name = f'FAIXA_{i:02d}'
        criteria[name] = f'O valor mostrado para essa série e período está entre {lo:.2f} e {hi:.2f}.'
        if ok:
            admitted.append(name)
    criteria['OUTRO_VALOR'] = 'Há um valor legível para essa série e período, fora de todas as faixas acima.'
    criteria['NAO_MOSTRADO'] = 'A entrega não mostra esse valor de forma legível (nem impresso, nem em tabela ou rótulo).'
    criteria['NAO_VERIFICAVEL'] = 'Há um valor, mas a imagem não permite situá-lo em uma faixa.'
    return criteria, admitted


def blind_text(ref):
    names = '; '.join(dict.fromkeys(label for label, _, _ in ref['variants']))
    return (f" Período: {ref['period']}. Unidade: {ref['unit']}. Séries admitidas: {names}."
            " Leia o valor que a entrega mostra para essa série nesse período e escolha a faixa que o contém."
            " Se a entrega termina em período anterior ou mostra só outra série, o valor não está mostrado.")


def to_options(probabilities, admitted):
    """Map a blind answer onto the rubric's numeric options."""
    out = {'ATENDE': 0.0, 'NAO_ATENDE': 0.0, 'NAO_MOSTRADO': 0.0, 'NAO_VERIFICAVEL': 0.0}
    for option, p in probabilities.items():
        if option in admitted:
            out['ATENDE'] += p
        elif option.startswith('FAIXA_') or option == 'OUTRO_VALOR':
            out['NAO_ATENDE'] += p
        else:
            out[option] += p
    return out


def render(ref):
    """Text appended to a numeric question."""
    variants = '; '.join(f'{label} = {value} (±{tol})' for label, value, tol in ref['variants'])
    return (f" Período de referência: {ref['period']}. Unidade: {ref['unit']}. Variantes admitidas (série: valor e tolerância): {variants}."
            " ATENDE se a entrega mostra, para essa mesma série e esse mesmo período, um valor dentro da tolerância de alguma variante admitida."
            " Se a entrega termina em período anterior ou mostra só outra série, o valor não está mostrado.")


def _a4(task, arm, model):
    """A4 revisions: admitted values of every release in A4_SOURCES; S05/S06 SA criterion from the A4 gate.
    Each variant label carries its period; the question's period lists both when they differ."""
    out, fixed = {}, {}
    for src in A4_SOURCES + (('A4',) if task in A4_NEWER else ()):
        if task in ('S05', 'S06'):
            refs, fx = _s05_s06(task, src, model, gate_phase=arm)
        else:
            refs, fx = BUILDERS[task](src), {}
        for q, r in refs.items():
            if not r:
                continue
            per = r['period'].split(' ')[0]
            vs = [(f'{l} [{per}]' , v, t) for l, v, t in r['variants']]
            if q in out:
                if per not in out[q]['period']:
                    out[q]['period'] = f"{out[q]['period']} ou {r['period']}"
                out[q]['variants'] += [x for x in vs if x[1:] not in [y[1:] for y in out[q]['variants']]]
            else:
                out[q] = {**r, 'variants': vs, 'periods': []}
            out[q]['periods'].append((per, [x[1:] for x in r['variants']]))
        for q, f in fx.items():
            fixed.setdefault(q, f)
    for q in list(fixed):
        if q in out:  # admitted under one release: the question is asked
            del fixed[q]
    return out, fixed
