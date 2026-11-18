"""A4 C-task cells: each revised delivery (evaluation snapshot) with its A1 seed and run window.

A4 seeds are the A1 final deliveries (all 45 C seeds byte-identical to the A1 work/entrega tree, checked
2026-11-17). Each seed was revised twice: A4_self_review (the same model reviews and fixes its delivery)
and A4_external_review (a reviewer writes a review, the same model fixes). 'Before' is the A1 score;
'after' is the snapshot score. Writes A4-cells.csv.
"""
import csv
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
REPO = HERE.parent.parent


def show(path):
    return json.loads(subprocess.run(['git', '-C', str(REPO), 'show', f'origin/main:{path}'], capture_output=True, text=True, check=True).stdout)


def main():
    out = []
    with (REPO / 'harmonization-case-inventory-20261109-v1.csv').open(encoding='utf-8-sig') as handle:
        rows = [r for r in csv.DictReader(handle) if r['phase'].startswith('A4') and r['task'].startswith('C')]
    for r in rows:
        base = f"execucoes/{r['source_campaign_id']}/evaluation-snapshots/{r['final_attempt_id']}"
        src = show(f'{base}/evaluation-source.json')
        pair = src['pair_directory'].split('/srv/benchmark/')[1]
        state = show(f"execucoes/{pair}/arms/{r['phase']}/primary/branch-state.json")
        out.append({'attempt': r['final_attempt_id'], 'phase': r['phase'], 'task': r['task'], 'model': r['model'],
                    'seed_attempt': src['source_A1_primary_attempt_id'], 'branch_state': src['branch_state'],
                    'no_op_snapshot': src.get('no_op_scientific_snapshot'), 'start_utc': state['created_at_utc'],
                    'end_utc': state['updated_at_utc'], 'active_seconds': round(state.get('active_seconds') or 0, 1),
                    'pngs': len(src.get('png_paths', []))})
    out.sort(key=lambda x: (x['task'], x['model'], x['phase']))
    with (HERE / 'A4-cells.csv').open('w', newline='') as handle:
        w = csv.DictWriter(handle, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    print(len(out), 'cells')


if __name__ == '__main__':
    main()
