"""Per task: how each delivery went through the hybrid check. Usage: python paths.py S01 S02 ..."""
import collections
import json
import sys

for t in sys.argv[1:]:
    try:
        man = {(o['phase'], o['model'], o['question']) for o in json.load(open(f'results/manual-overrides-{t}.json'))}
    except FileNotFoundError:
        man = set()
    q, d = collections.Counter(), collections.Counter()
    for c in json.load(open(f'results/code-check-{t}.json')):
        if not c['checks']:
            d['verified absence'] += 1
            continue
        st = ['manual' if (c['phase'], c['model'], k) in man else v['status'] for k, v in c['checks'].items()]
        q.update(st)
        d['all auto' if all(s == 'auto' for s in st) else 'reviewed by hand' if any(s in ('fail', 'none', 'manual') for s in st) else 'ambiguous accepted'] += 1
    print(t, 'deliveries', dict(d), '| questions', dict(q), '| overrides', len(man))
