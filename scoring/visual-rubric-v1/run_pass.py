"""Score the final delivery of every cell in the harmonization inventory. Does not touch any existing score.

Usage:
  python run_pass.py --phases A1 A2 A3 --tasks S01 S02 ... --repeats 3 [--dry-run]

The final attempt of each cell comes from harmonization-case-inventory-20261109-v1.csv.
The delivery is every PNG under that attempt's work/entrega/. Cells the inventory marks
verified_absence score 0 without a call. Numeric questions stay evaluator-pending.
"""
import argparse
import csv
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import judge
import rubric
from a4_cells import a4_cells, seed_cells
from run_pilot import judge_delivery

HERE = Path(__file__).parent
REPO = HERE.parent
INVENTORY = REPO / 'harmonization-case-inventory-20261109-v1.csv'


def cells(phases, tasks):
    with INVENTORY.open(encoding='utf-8-sig') as handle:
        for row in csv.DictReader(handle):
            if row['phase'] in phases and row['task'] in tasks:
                entrega = REPO / 'execucoes' / row['source_campaign_id'] / 'attempts' / row['final_attempt_id'] / 'work' / 'entrega'
                yield row, sorted(entrega.rglob('*.png'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--phases', nargs='+', required=True)
    parser.add_argument('--tasks', nargs='+', required=True, choices=sorted(rubric.TASKS))
    parser.add_argument('--repeats', type=int, default=3)
    parser.add_argument('--workers', type=int, default=6)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--store', type=Path, default=HERE / 'responses')
    parser.add_argument('--out', type=Path, default=HERE / 'results')
    args = parser.parse_args()

    todo = (list(a4_cells(set(args.tasks))) if args.phases == ['A4'] else list(seed_cells(set(args.tasks))) if args.phases == ['A4seed']
            else list(cells(set(args.phases), set(args.tasks))))
    for row, images in todo:
        if row['disposition'] == 'verified_absence' and images:
            raise SystemExit(f"{row['final_attempt_id']}: inventory says absent but PNGs exist")
        if row['disposition'] != 'verified_absence' and not images:
            raise SystemExit(f"{row['final_attempt_id']}: no PNG found; check MANIFESTO-EXCLUIDOS.tsv and the sparse checkout")
    if args.dry_run:
        for row, images in todo:
            if images:
                body, manifest = judge.build_request(row['task'], images)
                print(row['phase'], row['task'], row['model'], len(images), 'images',
                      round(len(json.dumps(body)) / 1e6, 2), 'MB', sum(i['resized'] for i in manifest['images']), 'resized')
        print(len(todo), 'cells,', sum(1 for _, i in todo if i), 'to judge')
        return

    def one(item):
        row, images = item
        cell = {k: row[k] for k in ('phase', 'task', 'model', 'source_campaign_id', 'final_attempt_id', 'disposition')}
        if not images:
            return {**cell, 'status': 'verified_absence', 'L_mean': 0.0, 'U_mean': 0.0}
        result = judge_delivery(row['task'], images, args.repeats, args.store, long_context=True)
        result['images'] = [str(p.relative_to(REPO)) for p in images]
        print(f"{row['phase']} {row['task']} {row['model']:22s} L={result['L_mean']:.2f} sd={result['L_sd']}", flush=True)
        return {**cell, 'status': 'judged', **result}

    with ThreadPoolExecutor(args.workers) as pool:
        rows = list(pool.map(one, todo))
    args.out.mkdir(parents=True, exist_ok=True)
    target = args.out / f"pass-{'-'.join(sorted(args.phases))}-{'-'.join(sorted(args.tasks))}-{rubric.VERSION}.json"
    target.write_text(json.dumps({'rubric_version': rubric.VERSION,
                                  'rubric_sha256': {t: rubric.rubric_hash(t) for t in sorted(args.tasks)},
                                  'model_requested': judge.MODEL, 'status': 'provisional, not a published score',
                                  'rows': rows}, ensure_ascii=False, indent=1))
    print('wrote', target)


if __name__ == '__main__':
    main()
