import json, glob, os, hashlib, collections
rows=[]
for g in glob.glob('avaliacao/juiz-opus/**/grade.json', recursive=True):
    d=os.path.dirname(g); pid=os.path.basename(d)
    root=d.split('/attempts/')[0]
    pk=glob.glob(f'{root}/packets/{pid}/packet.private.json')
    try: gr=json.load(open(g))
    except Exception: continue
    cr=json.load(open(f'{d}/calibrated-receipt.json')) if os.path.exists(f'{d}/calibrated-receipt.json') else {}
    req=json.load(open(f'{d}/request.json')) if os.path.exists(f'{d}/request.json') else {}
    if not pk: continue
    p=json.load(open(pk[0]))
    mat=hashlib.sha256(json.dumps(sorted(m['sha256'] for m in (p.get('materials') or p.get('images') or []) if m.get('kind')!='view_manifest')).encode()).hexdigest()[:12]
    rows.append(dict(scope=root.split('/')[-1], campaign=root.split('/')[2], pid=pid, attempt=p['attempt_id'], arm=p.get('arm'), task=p['task'], mat=mat,
        total=gr.get('total_out_of_20'), scores=gr.get('scores'), prompt=hashlib.sha256(req.get('prompt','').encode()).hexdigest()[:8],
        rubric=cr.get('rubric_sha256','')[:8], model=cr.get('model_requested'), effort=cr.get('effort')))
print(len(rows), collections.Counter(r['scope'] for r in rows).most_common(10))
grp=collections.defaultdict(list)
for r in rows: grp[(r['mat'],)].append(r)
rep=[v for v in grp.values() if len(v)>1]
print('deliveries (same materials) graded >1 time:', len(rep), 'of', len(grp))
same=[v for v in rep if len({(x['prompt'],x['rubric'],x['model'],x['effort']) for x in v})==1]
print('... with identical prompt/rubric/model/effort:', len(same))
for v in rep[:15]:
    print([ (x['campaign'][:45], x['scope'], x['attempt'][:30], x['total'], x['prompt'], x['rubric']) for x in v])
json.dump(rows, open('./opus_rows.json','w'))
