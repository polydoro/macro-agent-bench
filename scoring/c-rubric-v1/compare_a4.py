"""Before (A1) vs after (A4 self, external) for one C task; numeric picks checked against admitted bands.
Usage: python compare_a4.py C02"""
import json
import statistics as st
import sys

import references as R
import rubric

task = sys.argv[1]
a1 = {r['model']: r for r in json.load(open(f'results/pass-A1-A2-A3-{task}-{rubric.VERSION}.json'))['rows'] if r['phase'] == 'A1'}
by = {}
for r in json.load(open(f'results/pass-A4_external_review-A4_self_review-{task}-{rubric.VERSION}.json'))['rows']:
    by.setdefault(r['model'], {})[r['phase']] = r
B = lambda r: ' '.join(f"{k}{v:4.1f}" for k, v in (r.get('blocks_mean') or {}).items())
decoys = 0
for m in sorted(by):
    b, s, e = a1[m], by[m]['A4_self_review'], by[m]['A4_external_review']
    print(f"{m[:12]:12s} before {b.get('L_mean', 0):5.1f} self {s.get('L_mean', 0):5.1f} ({s.get('L_mean', 0) - b.get('L_mean', 0):+5.1f}) "
          f"ext {e.get('L_mean', 0):5.1f} ({e.get('L_mean', 0) - b.get('L_mean', 0):+5.1f})")
    for tag, r in (('before', b), ('self', s), ('ext', e)):
        print(f'   {tag:6s}', B(r))
    for r in (s, e):
        for q, ref in (r.get('references') or {}).items():
            if 'criteria' in ref or ref.get('fixed'):
                continue
            adm = R.blind(ref)[1]
            for x in r['repeats']:
                c = x['choices'][q]
                if c not in adm and c not in ('NAO_MOSTRADO', 'NAO_VERIFICAVEL'):
                    decoys += 1
                    print('   wrong band', r['phase'], q, c)
for ph in ('A4_self_review', 'A4_external_review'):
    d = [by[m][ph].get('L_mean', 0) - a1[m].get('L_mean', 0) for m in by]
    print(ph, 'mean', round(st.fmean(by[m][ph].get('L_mean', 0) for m in by), 1), 'delta', round(st.fmean(d), 1),
          'up', sum(x > 1 for x in d), 'down', sum(x < -1 for x in d))
print('before mean', round(st.fmean(a1[m].get('L_mean', 0) for m in by), 1), '| wrong-band picks', decoys)
