"""A4 cells for S01-S11: one final result per (task, model, arm). A completed timeout-retry replaces a
timed-out primary; a cell with no completed result is a verified absence. 'before' is the A1 primary
the revision started from."""
import csv, glob, json
from pathlib import Path

REPO = Path(__file__).parent.parent
ARMS = {'A4_self_review': 'A4s', 'A4_external_review': 'A4e'}


def a4_cells(tasks=None):
    best = {}
    for p in sorted(glob.glob(str(REPO / 'execucoes/pilot-a4-*/evaluation-snapshots/*/evaluation-source.json'))):
        d = json.load(open(p))
        if not d['task'].startswith('S') or (tasks and d['task'] not in tasks):
            continue
        key = (d['task'], d['requested_executor_profile']['model'], ARMS[d['experimental_arm']])
        rank = (d['branch_state'] == 'completed', d['branch_attempt'] != 'primary')
        if key not in best or rank > best[key][0]:
            best[key] = (rank, d, Path(p).parent)
    for (task, model, arm), (rank, d, snap) in sorted(best.items()):
        work = snap / 'work'
        images = sorted(work / p for p in d['png_paths']) if d['branch_state'] == 'completed' else []
        yield {'phase': arm, 'task': task, 'model': model, 'source_campaign_id': d['campaign_id'], 'final_attempt_id': d['attempt_id'],
               'disposition': 'scored' if images else 'verified_absence', 'created_at_utc': d['created_at_utc'],
               'branch_state': d['branch_state'], 'before_campaign': d['source_A1_campaign_id'], 'before_attempt': d['source_A1_primary_attempt_id'],
               'workdir': str(work)}, images


def seed_cells(tasks=None):
    """Before-revision deliveries that differ from the scored A1 delivery (A1 scored a retry, or was absent).
    Scored as A1 deliveries (A1 key); every other seed is the A1 delivery itself and keeps its A1 score.
    A seed with no charts (the A1 primary failed before delivering) is a verified absence."""
    from run_pass import cells
    a1 = {(r['task'], r['model']): r['final_attempt_id'] for r, _ in cells({'A1'}, tasks or {f'S{i:02d}' for i in range(1, 12)})}
    seen = set()
    for row, _ in a4_cells(tasks):
        key = (row['task'], row['model'])
        if key in seen or a1.get(key) == row['before_attempt']:
            continue
        seen.add(key)
        work = REPO / 'execucoes' / row['before_campaign'] / 'attempts' / row['before_attempt'] / 'work'
        images = sorted((work / 'entrega').rglob('*.png'))
        yield {'phase': 'A1', 'task': row['task'], 'model': row['model'], 'source_campaign_id': row['before_campaign'],
               'final_attempt_id': row['before_attempt'], 'disposition': 'scored' if images else 'verified_absence',
               'workdir': str(work)}, images
