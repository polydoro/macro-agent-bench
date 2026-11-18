"""Judge repeat variance for Jev: identical requests, 3 repeats. Reads stored results/responses only."""
import json, glob, statistics as st, random, sys, collections, csv, math
from pathlib import Path
V = Path('../../scoring/visual-rubric-v1'); C = Path('../../scoring/c-rubric-v1')
sys.path.insert(0, str(V)); import rubric, aggregate
VAL = aggregate.VALUE
def block(q):
    return {'I': 'identity', 'C': 'coverage', 'P': 'presentation', 'N': 'numeric', 'E': 'text(E)'}[q[0]]

# ---------- load visual 60-pt rows (provisional-7)
vis = []
for f in sorted(glob.glob(str(V/'results/pass-A1-A2-A3-S*-visual-rubric-v1-provisional-7.json'))):
    for r in json.load(open(f))['rows']:
        if r['status'] == 'judged': vis.append(r)
num = []
for f in sorted(glob.glob(str(V/'results/numeric-A1-A2-A3-S*-visual-rubric-v1-provisional-7.json'))):
    for r in json.load(open(f))['rows']:
        if r['status'] == 'judged' and r.get('repeats'): num.append(r)
c04 = [r for r in json.load(open(C/'results/pass-A1-A2-A3-C04-c-rubric-v1-pilot-3.json'))['rows'] if r.get('repeats')]

def load_resp(store, h, k):
    p = store/'responses'/h/f'r{k}.json'
    return json.load(open(p))['response'] if p.exists() else None

out = {}
# ---------- question-level: every (request, question) with 3 repeats
qrows = []  # source, task, model, phase, qid, choices, probs list
def add_q(source, row, hashes, store):
    resps = [load_resp(store, h, k) for k, h in enumerate(hashes)]
    if any(x is None for x in resps): return
    if len(set(hashes)) != 1: return  # must be identical request
    for qid in resps[0]['answers']:
        a = [x['answers'][qid] for x in resps]
        qrows.append(dict(source=source, task=row['task'], phase=row['phase'], model=row['model'], qid=qid,
                          choices=[x['choice'] for x in a], probs=[x['probabilities'] for x in a]))
for r in vis: add_q('visual60', r, [x['request_sha256'] for x in r['repeats']], V)
for r in num: add_q('numeric', r, [x['request_sha256'] for x in r['repeats']], V)
for kind in ('images', 'text', 'numeric'):
    for r in c04:
        hs = [x['requests'].get(kind) for x in r['repeats']]
        if all(hs): add_q('C04-'+kind, r, hs, C)

def summarise(rows):
    n = len(rows); flips = sum(len(set(q['choices'])) > 1 for q in rows)
    # prob of the modal (repeat-0) option: SD across repeats
    sds, rng = [], []
    for q in rows:
        opts = set().union(*q['probs'])
        for o in opts:
            v = [p.get(o, 0) for p in q['probs']]
            sds.append(st.pstdev(v)); rng.append(max(v) - min(v))
    # value-weighted (expected credit) range per question
    vr = []
    for q in rows:
        ev = [sum(VAL.get(o, 0) * p for o, p in pr.items()) for pr in q['probs']]
        vr.append(max(ev) - min(ev))
    return dict(n_questions=n, flip_rate=round(flips / n, 4), flips=flips,
                prob_abs_range_median=round(st.median(rng), 3), prob_abs_range_p95=round(sorted(rng)[int(.95*len(rng))], 3),
                prob_abs_range_max=round(max(rng), 3),
                credit_range_mean=round(st.fmean(vr), 4), credit_range_p95=round(sorted(vr)[int(.95*len(vr))], 3))
qs = {}
for key in ['ALL'] + sorted({q['source'] for q in qrows}):
    rows = qrows if key == 'ALL' else [q for q in qrows if q['source'] == key]
    qs[key] = summarise(rows)
for b in ['identity', 'coverage', 'presentation', 'numeric', 'text(E)']:
    rows = [q for q in qrows if block(q['qid']) == b]
    if rows: qs['block:' + b] = summarise(rows)
for t in sorted({q['task'] for q in qrows}):
    rows = [q for q in qrows if q['task'] == t and q['source'] == 'visual60']
    if rows: qs['visual60 task:' + t] = summarise(rows)
out['question_level'] = qs

# flips vs margin: a flip should happen only when top-2 probabilities are close
def margin(p):
    s = sorted(p.values(), reverse=True); return s[0] - (s[1] if len(s) > 1 else 0)
bins = [(0, .1), (.1, .2), (.2, .4), (.4, .6), (.6, 1.01)]
mb = {}
for lo, hi in bins:
    rows = [q for q in qrows if lo <= st.fmean(margin(p) for p in q['probs']) < hi]
    if rows: mb[f'{lo}-{hi}'] = dict(n=len(rows), flip_rate=round(sum(len(set(q['choices'])) > 1 for q in rows) / len(rows), 3))
out['flip_rate_by_mean_top2_margin'] = mb
# does the chosen option always equal argmax of probabilities?
mism = sum(1 for q in qrows for c, p in zip(q['choices'], q['probs']) if p.get(c, 0) < max(p.values()) - 1e-9)
out['choice_not_argmax'] = dict(count=mism, of=3 * len(qrows))

# ---------- score-level: visual 60
def sd(v): return st.stdev(v)
def choice_L(task, rep_hash, k):
    resp = load_resp(V, rep_hash, k)
    ans = {q: {a['choice']: 1.0} for q, a in resp['answers'].items()}
    ans = {q: ({'NAO_VERIFICAVEL': 1.0} if list(v)[0] == 'NAO_VERIFICAVEL' else v) for q, v in ans.items()}
    return aggregate.score(rubric.questions(task), rubric.groups(task), ans)['L']
vrows = []
for r in vis:
    Ls = [x['L'] for x in r['repeats']]
    blk = collections.defaultdict(lambda: [0, 0, 0])
    for k, x in enumerate(r['repeats']):
        # block points incl. best-K groups: recompute from detail
        g = collections.defaultdict(list)
        for q, d in x['questions'].items():
            if d['state'] != 'answered': continue
            if d['group']: g[d['group']].append((q, d['supported']))
            else: blk[block(q)][k] += d['supported']
        for grp, mem in g.items():
            K = rubric.groups(r['task'])[grp]
            for q, s in sorted(mem, key=lambda t: -t[1])[:K]: blk[block(q)][k] += s
    for k, x in enumerate(r['repeats']):
        assert abs(sum(blk[b][k] for b in blk) - x['L']) < 1e-6, (r['model'], k)
    Lc = [choice_L(r['task'], x['request_sha256'], k) for k, x in enumerate(r['repeats'])]
    vrows.append(dict(task=r['task'], phase=r['phase'], model=r['model'], n_img=len(r.get('images', [])),
                      L=Ls, Lc=Lc, blocks={b: v for b, v in blk.items()}))
def dist(v):
    v = sorted(v); n = len(v)
    return dict(n=n, mean=round(st.fmean(v), 3), median=round(v[n//2], 3), p90=round(v[int(.9*n)], 3), max=round(v[-1], 3))
pooled = lambda sds: round(math.sqrt(st.fmean([s*s for s in sds])), 3)
sl = {}
sl['visual60_L_prob'] = {**dist([sd(r['L']) for r in vrows]), 'pooled_sd': pooled([sd(r['L']) for r in vrows]),
                         'range_dist': dist([max(r['L']) - min(r['L']) for r in vrows])}
sl['visual60_L_choice'] = {**dist([sd(r['Lc']) for r in vrows]), 'pooled_sd': pooled([sd(r['Lc']) for r in vrows]),
                           'range_dist': dist([max(r['Lc']) - min(r['Lc']) for r in vrows])}
for b in ['identity', 'coverage', 'presentation']:
    s = [sd(r['blocks'].get(b, [0, 0, 0])) for r in vrows]
    sl[f'visual60_block_{b}_of20'] = {**dist(s), 'pooled_sd': pooled(s)}
# by task, by number of images
sl['visual60_by_task_pooled_sd'] = {t: pooled([sd(r['L']) for r in vrows if r['task'] == t]) for t in sorted({r['task'] for r in vrows})}
ib = collections.defaultdict(list)
for r in vrows: ib['1' if r['n_img'] <= 1 else '2-3' if r['n_img'] <= 3 else '4-6' if r['n_img'] <= 6 else '7+'].append(sd(r['L']))
sl['visual60_by_image_count_pooled_sd'] = {k: dict(n=len(v), pooled_sd=pooled(v)) for k, v in sorted(ib.items())}
top = sorted(vrows, key=lambda r: -sd(r['L']))[:8]
sl['visual60_top_sd_deliveries'] = [dict(task=r['task'], phase=r['phase'], model=r['model'], L=[round(x, 2) for x in r['L']], Lchoice=[round(x, 2) for x in r['Lc']]) for r in top]
# numeric
ns = [st.stdev([x['N_choice'] for x in r['repeats']]) for r in num]
npr = [st.stdev([x['N'] for x in r['repeats']]) for r in num]
sl['numeric40_jev_choice'] = {**dist(ns), 'pooled_sd': pooled(ns), 'tasks': sorted({r['task'] for r in num})}
sl['numeric40_jev_prob'] = {**dist(npr), 'pooled_sd': pooled(npr)}
sl['numeric_top'] = [dict(task=r['task'], phase=r['phase'], model=r['model'], N_choice=[x['N_choice'] for x in r['repeats']]) for r in sorted(num, key=lambda r: -st.stdev([x['N_choice'] for x in r['repeats']]))[:6]]
cs = [st.stdev([x['L'] for x in r['repeats']]) for r in c04]
sl['C04_L_of100'] = {**dist(cs), 'pooled_sd': pooled(cs)}
for b in 'ABCDE':
    s = [st.stdev([x['blocks'][b] for x in r['repeats']]) for r in c04]
    sl[f'C04_block_{b}'] = {**dist(s), 'pooled_sd': pooled(s)}
sl['C04_top'] = [dict(phase=r['phase'], model=r['model'], L=[round(x['L'], 2) for x in r['repeats']], D=[x['blocks']['D'] for x in r['repeats']]) for r in sorted(c04, key=lambda r: -st.stdev([x['L'] for x in r['repeats']]))[:3]]
out['score_level'] = sl

# ---------- noise vs signal (visual 60)
# share of delivery-score variance due to judge repeats
allL = [x for r in vrows for x in r['L']]
within = st.fmean([st.variance(r['L']) for r in vrows]); total = st.variance(allL)
out['visual60_variance_share_judge'] = dict(within_var=round(within, 3), total_var=round(total, 2), share=round(within / total, 5),
                                            reliability_single_call=round(1 - within / total, 4))
# model means (over all arms/tasks, mean of 3 repeats) and their SE from judge noise
bym = collections.defaultdict(list)
for r in vrows: bym[r['model']].append(r)
mm = {}
for m, rs in bym.items():
    mean = st.fmean(st.fmean(r['L']) for r in rs)
    se_judge = math.sqrt(sum(st.variance(r['L']) / 3 for r in rs)) / len(rs)
    sd_deliv = st.stdev([st.fmean(r['L']) for r in rs])
    mm[m] = dict(n=len(rs), mean=round(mean, 2), se_from_judge_noise=round(se_judge, 3), se_from_delivery_spread=round(sd_deliv / math.sqrt(len(rs)), 2))
out['model_means_visual60'] = dict(sorted(mm.items(), key=lambda kv: -kv[1]['mean']))
# rank stability: draw one repeat per delivery (as if judged once), recompute model ranks
random.seed(1)
order = [m for m, _ in sorted(mm.items(), key=lambda kv: -kv[1]['mean'])]
same_top3 = same_order = 0; max_shift = collections.Counter(); N = 2000
gapdist = collections.defaultdict(list)
for _ in range(N):
    means = {m: st.fmean(random.choice(r['L']) for r in rs) for m, rs in bym.items()}
    o = sorted(means, key=lambda m: -means[m])
    same_order += o == order; same_top3 += o[:3] == order[:3]
    for i, m in enumerate(o): max_shift[abs(i - order.index(m))] += 1
    for a, b in zip(order, order[1:]): gapdist[(a, b)].append(means[a] - means[b])
out['rank_stability_single_call'] = dict(draws=N, same_full_order=round(same_order / N, 3), same_top3=round(same_top3 / N, 3),
    adjacent_gaps={f'{a} - {b}': dict(gap=round(mm[a]['mean'] - mm[b]['mean'], 2), p_reversed=round(sum(g < 0 for g in gapdist[(a, b)]) / N, 3)) for a, b in zip(order, order[1:])})
# per task x arm cell: within-cell model gaps vs per-delivery judge SD
gaps = []
cells = collections.defaultdict(list)
for r in vrows: cells[(r['task'], r['phase'])].append(r)
close = 0; tot = 0
for c, rs in cells.items():
    ms = sorted(rs, key=lambda r: -st.fmean(r['L']))
    for a, b in zip(ms, ms[1:]):
        g = st.fmean(a['L']) - st.fmean(b['L']); se = math.sqrt(st.variance(a['L'])/3 + st.variance(b['L'])/3)
        tot += 1; close += g < 2 * se
out['within_cell_adjacent_pairs'] = dict(pairs=tot, gap_below_2se_of_judge_noise=close)
json.dump(out, open('./summary.json', 'w'), indent=1)
json.dump([dict(q, probs=q['probs']) for q in qrows if len(set(q['choices'])) > 1], open('./flips.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
