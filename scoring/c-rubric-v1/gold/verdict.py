"""Gold answer (result) for the C tasks: Jev classifies the delivery's own conclusion; code compares it with
the gold category (the author 2026-11-17: verdict about 10 of 100 points, Jev for homogeneity).

One text-only request per delivery and repeat ('verdict'), separate from the c-rubric-v1 requests so their
stored answers stay valid. Jev never sees the gold category. C03 has no verdict request: its result is the
nowcast error, computed in code (gold/c03_nowcast.py).

Usage:
  python gold/verdict.py --task C01 --dry-run            # cells, request sizes, calls (no call made)
  python gold/verdict.py --task C01 --cells A1:claude-opus-5-5 ... --repeats 3   # needs the author's go
"""
import argparse
import csv
import json
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import judge  # noqa: E402
import rubric  # noqa: E402
import run_pass  # noqa: E402

VERSION = 'c-gold-verdict-v1'
PHASES = {'A1', 'A2', 'A3', 'A4_self_review', 'A4_external_review'}
INTRO = """Material: o texto do relatório da entrega (Markdown, HTML convertido em texto ou TXT).
Classifique a conclusão que a própria entrega apresenta, como ela a apresenta. Não avalie se a conclusão está certa
e não use conhecimento próprio sobre os dados. Se a entrega apresenta várias leituras, use a que ela dá como principal.
Se não há conclusão sobre o ponto perguntado, escolha NAO_CONCLUI."""
NC = {'NAO_CONCLUI': 'A entrega não apresenta conclusão sobre esse ponto.',
      'NAO_VERIFICAVEL': 'Há conclusão, mas não é possível classificá-la nas alternativas acima.'}

QUESTIONS = {
    'C01': {'V_veredito': ('Qual é o diagnóstico principal da entrega sobre a recuperação da indústria alemã?', {
        'RECUPERACAO_CLARA': 'A indústria já está se recuperando: a produção (atividade corrente) mostra recuperação.',
        'SINAIS_MISTOS': 'A produção ainda não se recupera (ou segue fraca/caindo), mas encomendas ou outros indicadores antecedentes mostram melhora; '
                         'recuperação incipiente, estabilização ou sinais mistos.',
        'SEM_RECUPERACAO': 'Não há recuperação, nem na produção nem em indicadores antecedentes como encomendas.', **NC}, 10)},
    'C02': {'V_ritmo': ('Como a entrega caracteriza o ritmo atual do consumo das famílias na zona do euro?', {
        'FORTE': 'Crescimento forte ou acelerando de forma clara.',
        'MODERADO': 'Crescimento moderado, modesto ou próximo da tendência; recuperação gradual.',
        'FRACO_OU_PERDENDO_FORCA': 'Crescimento fraco, estagnado ou perdendo força.',
        'CONTRACAO': 'Consumo em queda.', **NC}, 10)},
    'C04': {'V_direcao': ('Qual é a resposta principal da entrega: as primeiras estimativas do PIB alemão costumam ser revisadas para cima?', {
        'SIM': 'Sim: em média, as revisões são para cima (mesmo que pequenas).',
        'NAO': 'Não: em média, as revisões são para baixo.',
        'SEM_VIES_CLARO': 'Não há viés claro: as revisões médias são próximas de zero, não significativas ou sem direção predominante.', **NC}, 6),
            'V_tamanho': ('Como a entrega dimensiona a revisão média da variação trimestral (q/q) do PIB?', {
        'PEQUENA': 'Pequena: até cerca de 0,1 ponto percentual na variação trimestral (ou descrita como pequena/modesta).',
        'GRANDE': 'Grande: bem acima de 0,1 ponto percentual na variação trimestral (ou descrita como grande/relevante).',
        'NAO_QUANTIFICA': 'A entrega não dimensiona a revisão média.', 'NAO_VERIFICAVEL': NC['NAO_VERIFICAVEL']}, 4)},
    'C05': {'V_efeito': ('Qual é a conclusão principal da entrega sobre o efeito da energia no núcleo da inflação?', {
        'EFEITO_PEQUENO_OU_LIMITADO': 'A energia tem efeito indireto positivo, mas pequeno, moderado ou limitado até agora sobre o núcleo '
                                      '(por exemplo, alguns décimos de ponto percentual, ou repasse ainda contido).',
        'SEM_EFEITO': 'A energia não tem afetado o núcleo de forma perceptível; o núcleo é explicado por outros fatores.',
        'EFEITO_GRANDE': 'A energia é o principal motor do núcleo, com repasse amplo já visível.', **NC}, 10)},
}


def gold(task, attempt, phase):
    """Admitted categories per question (gold/README.md has the evidence)."""
    if task == 'C01':
        return {'V_veredito': {'SINAIS_MISTOS'}}
    if task == 'C02':
        import references as R
        ret = R.references('C02', attempt)['N_ret_yoy']
        saw_sept = '2026-09' in (ret.get('periods') or [ret['period']])
        return {'V_ritmo': {'MODERADO', 'FRACO_OU_PERDENDO_FORCA'} if saw_sept else {'MODERADO'}}
    if task == 'C04':  # gold/C04-significance.csv: positive and significant at horizons of a year or more
        return {'V_direcao': {'SIM'}, 'V_tamanho': {'PEQUENA'}}
    if task == 'C05':  # gold/C05-passthrough.csv: LR 0.08 [0.03, 0.13], about +0.4 pp on core YoY so far
        return {'V_efeito': {'EFEITO_PEQUENO_OU_LIMITADO'}}
    raise KeyError(task)


def build(task, report):
    t = rubric.TASKS[task]
    state = (f"{rubric.COMMON}\n\nTarefa: {task}. Pedido: {t['request']}\n\n{INTRO}\n\nRelatório da entrega:\n<<<\n{report}\n>>>")
    qs = {q: {'type': 'choice', 'instructions': text, 'criteria': crit} for q, (text, crit, _) in QUESTIONS[task].items()}
    body = {'model': judge.MODEL, 'state': state, 'questions': qs}
    manifest = {'task': task, 'request': 'verdict', 'model_requested': judge.MODEL, 'rubric_version': VERSION,
                'report_sha256': judge.sha256(report.encode()), 'report_chars': len(report), 'questions_asked': sorted(qs)}
    return body, manifest


def todo(task, cells=None):
    for row, entrega in run_pass.cells(PHASES, task):
        if row['disposition'] == 'verified_absence' or not entrega.exists():
            continue
        if cells and f"{row['phase']}:{row['model']}" not in cells:
            continue
        yield row, entrega, judge.report_text(entrega)


def score(task, row, report, repeats, store, call=judge.post):
    g = gold(task, row['final_attempt_id'], row['phase'])
    weights = {q: w for q, (_, _, w) in QUESTIONS[task].items()}
    if not report.strip():  # nothing to classify: no call
        return {'points': 0.0, 'choices': {q: 'NAO_CONCLUI' for q in weights}, 'gold': {q: sorted(v) for q, v in g.items()}, 'calls': 0}
    body, manifest = build(task, report)
    reps = []
    for r in range(repeats):
        rec = judge.judge(body, manifest, store, r, call=call)
        ch = {q: max(p, key=p.get) for q, p in judge.answers(rec).items()}
        reps.append({'choices': ch, 'points': sum(weights[q] for q in weights if ch.get(q) in g[q])})
    return {'points': statistics.fmean(x['points'] for x in reps), 'repeats': reps, 'gold': {q: sorted(v) for q, v in g.items()}}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--task', required=True, choices=sorted(QUESTIONS))
    p.add_argument('--cells', nargs='*')
    p.add_argument('--repeats', type=int, default=3)
    p.add_argument('--workers', type=int, default=6)
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--store', type=Path, default=HERE.parent / 'responses')
    a = p.parse_args()
    items = list(todo(a.task, a.cells))
    if a.dry_run:
        n = sum(1 for *_, rep in items if rep.strip())
        chars = [len(json.dumps(build(a.task, rep)[0], ensure_ascii=False)) for *_, rep in items if rep.strip()]
        print(a.task, len(items), 'deliveries,', n, 'with report text;', n * a.repeats, 'calls at', a.repeats, 'repeats;',
              'request chars mean', round(statistics.fmean(chars)), 'max', max(chars), 'total', sum(chars) * a.repeats)
        return
    with ThreadPoolExecutor(a.workers) as pool:
        res = list(pool.map(lambda it: {**{k: it[0][k] for k in ('phase', 'task', 'model', 'final_attempt_id')},
                                        **score(a.task, it[0], it[2], a.repeats, a.store)}, items))
    tag = f'-{len(items)}cells' if a.cells else ''
    out = HERE.parent / f'results/verdict-{a.task}{tag}-{VERSION}.json'
    out.write_text(json.dumps(res, indent=1, ensure_ascii=False))
    for r in res:
        print(r['phase'][:7], r['model'][:12].ljust(12), r['points'], [x['choices'] for x in r.get('repeats', [])][:1])


if __name__ == '__main__':
    main()
