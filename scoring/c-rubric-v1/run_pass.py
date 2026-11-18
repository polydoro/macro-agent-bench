"""Score the final delivery of every cell of a C task. Does not touch any existing score.

Usage:
  python run_pass.py --phases A1 A2 A3 --task C04 --repeats 3 [--cells A1:C04:claude-opus-5-5 ...] [--dry-run]
  python run_pass.py ... --shift 4    # false-pass test: every admitted numeric value moved by +4 tolerances

Per cell: three requests ('images' A-C, 'text' E, 'numeric' D), each repeated. Blocks A, B, C, E
score the probability-weighted value (S 60-point convention); block D scores the judge's own
choice per question (S numeric convention, PR #1). A cell with no report text gets NAO_ATENDE on
E without a call; a cell with no product at all scores 0; verified absences are reported absent.
"""
import argparse
import csv
import json
import statistics
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import aggregate
import judge
import references as R
import rubric

HERE = Path(__file__).parent
REPO = HERE.parent
INVENTORY = REPO / 'harmonization-case-inventory-20261109-v1.csv'


def cells(phases, task):
    seen = set()
    with INVENTORY.open(encoding='utf-8-sig') as handle:
        for row in csv.DictReader(handle):
            key = (row['phase'], row['task'], row['model'])
            if row['phase'] in phases and row['task'] == task and key not in seen:
                seen.add(key)
                entrega = REPO / 'execucoes' / row['source_campaign_id'] / 'attempts' / row['final_attempt_id'] / 'work' / 'entrega'
                if row['phase'].startswith('A4'):  # revised delivery: evaluation snapshot (keys/A4-cells.csv)
                    entrega = REPO / 'execucoes' / row['source_campaign_id'] / 'evaluation-snapshots' / row['final_attempt_id'] / 'work' / 'entrega'
                yield row, entrega


def shifted(refs, k):
    return {q: ({**r, 'variants': [(l, round(v + k * t, 3), t) for l, v, t in r['variants']]} if 'criteria' not in r else r)
            for q, r in refs.items()}


def score_cell(task, row, entrega, repeats, store, shift=0, workers_call=judge.post):
    questions, groups = rubric.questions(task), rubric.groups(task)
    images = sorted(entrega.rglob('*.png')) if entrega.exists() else []
    report = judge.report_text(entrega) if entrega.exists() else ''
    refs = R.references(task, row['final_attempt_id'])
    if shift:
        refs = shifted(refs, shift)
    out = []
    for repeat in range(repeats):
        raw, prob, choice, shas = {}, {}, {}, {}
        for request in ('images', 'text', 'numeric'):
            if request == 'images' and not images:
                fixed = {q: {'NAO_ATENDE': 1.0} for q, s in questions.items() if s['request'] == 'images'}
                prob.update(fixed); choice.update(fixed)
                continue
            if request == 'text' and not report.strip():
                fixed = {q: {'NAO_ATENDE': 1.0} for q, s in questions.items() if s['request'] == 'text'}
                prob.update(fixed); choice.update(fixed)
                continue
            body, manifest = judge.build_request(task, request, images, report, refs)
            record = judge.judge(body, manifest, store, repeat, call=workers_call)
            shas[request] = record['request_sha256']
            for qid, p in judge.answers(record).items():
                raw[qid] = p
                top = {max(p, key=p.get): 1.0}
                if questions[qid]['needs_reference'] and refs[qid].get('fixed'):  # decided in code (C05 SA rule)
                    prob[qid] = choice[qid] = {refs[qid]['fixed']: 1.0}
                elif questions[qid]['needs_reference']:
                    admitted = R.blind(refs[qid])[1]
                    prob[qid], choice[qid] = R.to_options(p, admitted), R.to_options(top, admitted)
                else:
                    prob[qid], choice[qid] = p, top
        # blocks A, B, C, E probability-weighted; block D by the judge's choice
        mixed = {q: (choice[q] if questions[q]['kind'] in ('numeric', 'target') else prob[q]) for q in prob}
        result = aggregate.score(questions, groups, mixed)
        blocks = {}
        for qid, d in result['questions'].items():
            block = {'identity': 'A', 'conventions': 'A', 'coverage': 'B', 'legibility': 'C', 'identification': 'C',
                     'numeric': 'D', 'target': 'D'}.get(questions[qid]['kind'], 'E')
            blocks.setdefault(block, 0.0)
            if block != 'D':
                blocks[block] += d.get('supported', 0.0)
        n_scores = sorted((d.get('supported', 0.0) for q, d in result['questions'].items() if questions[q]['kind'] == 'numeric'), reverse=True)
        blocks['D'] = sum(n_scores[:groups['N']]) + sum(d.get('supported', 0.0) for q, d in result['questions'].items()
                                                         if questions[q]['kind'] == 'target')
        out.append({'repeat': repeat, 'requests': shas, 'L': result['L'], 'U': result['U'], 'blocks': blocks,
                    'choices': {q: max(p, key=p.get) for q, p in raw.items()}, 'probabilities': raw})
    mean = lambda key: statistics.fmean(s[key] for s in out)
    return {'images': [str(p.relative_to(REPO)) for p in images], 'report_chars': len(report),
            'L_mean': mean('L'), 'L_sd': statistics.stdev(s['L'] for s in out) if len(out) > 1 else None,
            'U_mean': mean('U'), 'blocks_mean': {b: statistics.fmean(s['blocks'][b] for s in out) for b in 'ABCDE'},
            'references': refs, 'repeats': out}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--phases', nargs='+', required=True)
    p.add_argument('--task', required=True, choices=sorted(rubric.TASKS))
    p.add_argument('--cells', nargs='*', help='phase:task:model filters')
    p.add_argument('--repeats', type=int, default=3)
    p.add_argument('--shift', type=float, default=0)
    p.add_argument('--workers', type=int, default=6)
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--store', type=Path, default=HERE / 'responses')
    p.add_argument('--out', type=Path, default=HERE / 'results')
    args = p.parse_args()

    todo = [(r, e) for r, e in cells(set(args.phases), args.task)
            if not args.cells or f"{r['phase']}:{r['task']}:{r['model']}" in args.cells]
    if args.dry_run:
        for row, entrega in todo:
            images = sorted(entrega.rglob('*.png')) if entrega.exists() else []
            report = judge.report_text(entrega) if entrega.exists() else ''
            refs = R.references(args.task, row['final_attempt_id'])
            sizes = [len(json.dumps(judge.build_request(args.task, r, images, report, refs)[0])) / 1e6 for r in ('images', 'text', 'numeric')]
            print(row['phase'], row['model'], row['disposition'], len(images), 'png', len(report), 'chars', [round(s, 2) for s in sizes], 'MB')
        print(len(todo), 'cells')
        return

    def one(item):
        row, entrega = item
        cell = {k: row[k] for k in ('phase', 'task', 'model', 'source_campaign_id', 'final_attempt_id', 'disposition')}
        if row['disposition'] == 'verified_absence':
            return {**cell, 'status': 'verified_absence'}
        if not entrega.exists() or not any(entrega.rglob('*')):
            return {**cell, 'status': 'no_product', 'L_mean': 0.0}
        res = score_cell(args.task, row, entrega, args.repeats, args.store, args.shift)
        print(f"{row['phase']} {row['model']:22s} L={res['L_mean']:.1f} sd={res['L_sd']} "
              + ' '.join(f'{b}={v:.1f}' for b, v in res['blocks_mean'].items()), flush=True)
        return {**cell, 'status': 'judged', **res}

    with ThreadPoolExecutor(args.workers) as pool:
        rows = list(pool.map(one, todo))
    args.out.mkdir(parents=True, exist_ok=True)
    tag = (f'-shift{args.shift:g}' if args.shift else '') + (f'-{len(todo)}cells' if args.cells else '')
    target = args.out / f"pass-{'-'.join(sorted(args.phases))}-{args.task}{tag}-{rubric.VERSION}.json"
    target.write_text(json.dumps({'rubric_version': rubric.VERSION, 'rubric_sha256': rubric.rubric_hash(args.task),
                                  'model_requested': judge.MODEL, 'shift_tolerances': args.shift,
                                  'status': 'provisional pilot, not a published score', 'rows': rows}, ensure_ascii=False, indent=1))
    print('wrote', target)


if __name__ == '__main__':
    main()
