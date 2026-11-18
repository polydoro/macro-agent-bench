import json, statistics as st, math, itertools, glob
rows=[r for f in sorted(glob.glob('../../scoring/visual-rubric-v1/results/pass-A1-A2-A3-S*-visual-rubric-v1-provisional-7.json')) for r in json.load(open(f))['rows'] if r['status']=='judged']
d={(r['model'],r['task'],r['phase']):[x['L'] for x in r['repeats']] for r in rows}
top=['gpt-6-astra','claude-fable-5-1','claude-sonnet-5-5','grok-4.7','gpt-6.1-sol','claude-opus-5-5']
for a,b in itertools.combinations(top,2):
    cells=[(t,p) for (m,t,p) in d if m==a and (b,t,p) in d]
    diffs=[st.fmean(d[(a,)+c])-st.fmean(d[(b,)+c]) for c in cells]
    judge=math.sqrt(sum(st.variance(d[(a,)+c])/3+st.variance(d[(b,)+c])/3 for c in cells))/len(cells)
    print(f'{a:18s} {b:18s} n={len(cells):2d} diff={st.fmean(diffs):+.2f} se_cells={st.stdev(diffs)/math.sqrt(len(cells)):.2f} se_judge={judge:.3f}')
