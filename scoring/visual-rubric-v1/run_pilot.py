"""Pilot: judge image packets with Jev and write one results file. Does not touch any existing score.

Usage:
  python run_pilot.py --packets ../qa-preview/A2-S01 --task S01 --repeats 3
  python run_pilot.py --packets ../qa-preview/A2-S01 --task S01 --dry-run   # build requests only, no call

Each sub-folder of --packets is one delivery (its PNG files). Without a reference
sheet the numeric questions are not asked and stay evaluator-pending.
"""
import argparse
import json
import statistics
from pathlib import Path

import aggregate
import judge
import rubric

HERE = Path(__file__).parent


def judge_delivery(task, images, repeats, store, references=None, long_context=False):
    """Judge one delivery `repeats` times and summarise. Stored responses are reused, never re-fetched."""
    questions, groups = rubric.questions(task), rubric.groups(task)
    scores = []
    for repeat in range(repeats):
        record = judge.judge(task, images, store, repeat, references, long_context)
        result = aggregate.score(questions, groups, judge.answers(record))
        scores.append({'repeat': repeat, 'request_sha256': record['request_sha256'],
                       'model': record['response'].get('model'), 'usage': record['response'].get('usage'),
                       **{k: result[k] for k in ('L', 'U', 'asked_points', 'pending_points')},
                       'questions': result['questions']})
    lows = [s['L'] for s in scores]
    return {'task': task, 'repeats': scores, 'L_mean': statistics.fmean(lows),
            'L_sd': statistics.stdev(lows) if len(lows) > 1 else None, 'L_min': min(lows), 'L_max': max(lows),
            'U_mean': statistics.fmean(s['U'] for s in scores)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--packets', required=True, type=Path)
    parser.add_argument('--task', required=True, choices=sorted(rubric.TASKS))
    parser.add_argument('--repeats', type=int, default=1)
    parser.add_argument('--references', type=Path, help='JSON {delivery: {question id: {value, unit, period, tolerance}}}')
    parser.add_argument('--long-context', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--store', type=Path, default=HERE / 'responses')
    parser.add_argument('--out', type=Path, default=HERE / 'results')
    args = parser.parse_args()

    references = json.loads(args.references.read_text()) if args.references else {}
    rows = []
    for folder in sorted(p for p in args.packets.iterdir() if p.is_dir()):
        images = sorted(folder.glob('*.png'))
        if not images:
            continue
        if args.dry_run:
            body, manifest = judge.build_request(args.task, images, references.get(folder.name))
            print(folder.name, len(images), 'images,', len(body['questions']), 'questions,',
                  round(len(json.dumps(body)) / 1e6, 2), 'MB,', sum(i['resized'] for i in manifest['images']), 'resized')
            continue
        rows.append({'delivery': folder.name, **judge_delivery(args.task, images, args.repeats, args.store,
                                                                  references.get(folder.name), args.long_context)})
        print(f"{folder.name:32s} L={rows[-1]['L_mean']:.2f} sd={rows[-1]['L_sd']} U={rows[-1]['U_mean']:.2f}")
    if rows:
        args.out.mkdir(parents=True, exist_ok=True)
        target = args.out / f'pilot-{args.packets.name}-{rubric.VERSION}.json'
        target.write_text(json.dumps({'rubric_version': rubric.VERSION, 'rubric_sha256': rubric.rubric_hash(args.task),
                                      'model_requested': judge.MODEL, 'status': 'provisional pilot, not a published score',
                                      'rows': rows}, ensure_ascii=False, indent=1))
        print('wrote', target)


if __name__ == '__main__':
    main()
