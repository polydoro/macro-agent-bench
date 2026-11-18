"""Numeric 40 points: a separate request per delivery with only the numeric questions.

The 60-point requests and their stored responses are untouched (their bodies do not change).
References come from references.py; S05/S06 3m SAAR answers fixed by the SA criterion are
recorded without a call.

Usage:
  python run_numeric.py --phases A1 A2 A3 --tasks S01 --repeats 3 [--dry-run]
  python run_numeric.py ... --shift 4 --cells A1:S01:claude-fable-5-1   # false-pass test:
      every admitted value moved by +4 tolerances, so a correct judge never answers ATENDE.
"""
import argparse
import json
import statistics
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import aggregate
import judge
import references as R
import rubric
from a4_cells import a4_cells, seed_cells
from run_pass import REPO, cells

HERE = Path(__file__).parent


def numeric_questions(task):
    qs = {q: s for q, s in rubric.questions(task).items() if s['kind'] == 'numeric'}
    gs = {g: k for g, k in rubric.groups(task).items() if g.startswith('N_')}
    return qs, gs


def shifted(refs, k):
    """False-pass test: the admitted values move by k tolerances; the delivery's true value is now a decoy."""
    return {q: {**r, 'variants': [(l, round(v + k * t, 2), t) for l, v, t in r['variants']]} for q, r in refs.items()}


def score_cell(task, images, refs, fixed, repeats, store):
    qs, gs = numeric_questions(task)
    out = []
    for repeat in range(repeats):
        record = judge.judge(task, images, store, repeat, refs, long_context=True, kinds={'numeric'})
        raw = judge.answers(record)
        answers = {q: R.to_options(p, R.blind(refs[q])[1]) for q, p in raw.items()}
        answers.update({q: {'NAO_ATENDE': 1.0} for q in fixed})
        result = aggregate.score(qs, gs, answers)
        # the judge's own single choice per question (raw option, then mapped); fixed answers kept
        top = {q: R.to_options({max(p, key=p.get): 1.0}, R.blind(refs[q])[1]) for q, p in raw.items()}
        top.update({q: {'NAO_ATENDE': 1.0} for q in fixed})
        result_choice = aggregate.score(qs, gs, top)
        out.append({'repeat': repeat, 'request_sha256': record['request_sha256'], 'usage': record['response'].get('usage'),
                    'N': result['L'], 'N_upper': result['U'], 'N_choice': result_choice['L'], 'pending': result['pending_points'], 'questions': result['questions'],
                    'choices': {q: max(p, key=p.get) for q, p in raw.items()},
                    'admitted': {q: R.blind(refs[q])[1] for q in raw}})
    lows = [s['N'] for s in out]
    return {'N_choice_mean': statistics.fmean(s['N_choice'] for s in out), 'N_mean': statistics.fmean(lows), 'N_sd': statistics.stdev(lows) if len(lows) > 1 else None,
            'N_upper_mean': statistics.fmean(s['N_upper'] for s in out), 'repeats': out}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--phases', nargs='+', required=True)
    p.add_argument('--tasks', nargs='+', required=True, choices=sorted(rubric.TASKS))
    p.add_argument('--cells', nargs='*', help='phase:task:model filters')
    p.add_argument('--repeats', type=int, default=3)
    p.add_argument('--shift', type=float, default=0, help='false-pass test: move every reference by this many tolerances')
    p.add_argument('--workers', type=int, default=6)
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--store', type=Path, default=HERE / 'responses')
    p.add_argument('--out', type=Path, default=HERE / 'results')
    args = p.parse_args()

    source = (a4_cells(set(args.tasks)) if args.phases == ['A4'] else seed_cells(set(args.tasks)) if args.phases == ['A4seed']
              else cells(set(args.phases), set(args.tasks)))
    todo = [(row, images) for row, images in source
            if not args.cells or f"{row['phase']}:{row['task']}:{row['model']}" in args.cells]

    def prepare(row):
        refs, fixed = R.references(row['task'], row['phase'], row['model'])
        refs = {q: r for q, r in refs.items() if q not in fixed and q.startswith('N_')}
        return (shifted(refs, args.shift) if args.shift else refs), fixed

    if args.dry_run:
        for row, images in todo:
            if images:
                refs, fixed = prepare(row)
                body, _ = judge.build_request(row['task'], images, refs, {'numeric'})
                print(row['phase'], row['task'], row['model'], len(body['questions']), 'asked,', len(fixed), 'fixed,',
                      round(len(json.dumps(body)) / 1e6, 2), 'MB')
        print(len(todo), 'cells')
        return

    def one(item):
        row, images = item
        cell = {k: row[k] for k in ('phase', 'task', 'model', 'source_campaign_id', 'final_attempt_id', 'disposition')}
        if not images:
            return {**cell, 'status': 'verified_absence', 'N_mean': 0.0}
        refs, fixed = prepare(row)
        res = score_cell(row['task'], images, refs, fixed, args.repeats, args.store)
        print(f"{row['phase']} {row['task']} {row['model']:22s} N_choice={res['N_choice_mean']:.2f} N_prob={res['N_mean']:.2f}", flush=True)
        return {**cell, 'status': 'judged', 'references': refs, 'fixed': fixed,
                'images': [str(i.relative_to(REPO)) for i in images], **res}

    with ThreadPoolExecutor(args.workers) as pool:
        rows = list(pool.map(one, todo))
    args.out.mkdir(parents=True, exist_ok=True)
    tag = f'-shift{args.shift:g}' if args.shift else ''
    target = args.out / f"numeric-{'-'.join(sorted(args.phases))}-{'-'.join(sorted(args.tasks))}{tag}-{rubric.VERSION}.json"
    if args.cells:
        target = target.with_name(target.stem + f'-{len(todo)}cells.json')
    target.write_text(json.dumps({'rubric_version': rubric.VERSION, 'model_requested': judge.MODEL, 'shift_tolerances': args.shift,
                                  'status': 'provisional, not a published score', 'rows': rows}, ensure_ascii=False, indent=1))
    print('wrote', target)


if __name__ == '__main__':
    main()
