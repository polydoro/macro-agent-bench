import sys,glob,csv,collections
sys.path.insert(0,'./answer-keys')
import x13, resid_seas as R
csv.field_size_limit(10**9)
def load(pattern):
    S=collections.defaultdict(dict)
    for p in glob.glob(pattern,recursive=True):
        try:
            with open(p,errors='ignore') as fh:
                if 'OBS_VALUE' not in fh.readline(): continue
                fh.seek(0)
                for r in csv.DictReader(fh):
                    try: S[r['KEY']][r['TIME_PERIOD']]=float(r['OBS_VALUE'])
                    except: pass
        except: pass
    return S
E='./execucoes/'
EA=load(E+'pilot-one-s06*/attempts/*/work/**/*.csv'); EA.update({k:v for k,v in load(E+'pilot-a2-s06*/attempts/*/work/**/*.csv').items() if k not in EA})
IT=load(E+'pilot-*s05*/attempts/*/work/**/*.csv')
items=['000000','XEF000','IGXE00','SERV00','NRGY00','FOOD00']
cases=[]
for it in items:
    n={p:v for p,v in EA.get(f'HICP.M.U2.N.{it}.4D0.INX',{}).items() if p<='2026-09'}
    o={p:v for p,v in EA.get(f'HICP.M.U2.Y.{it}.4F0.INX',{}).items() if p<='2026-09'}
    ps=sorted(n); _,sa=x13.adjust([n[p] for p in ps],ps[0])
    cases+= [('EA',it,'ECB_SA','good',o),('EA',it,'X13','good',dict(zip(ps,sa))),('EA',it,'NSA','bad',n)]
for it in items[1:]:
    n=IT.get(f'ICP.M.IT.N.{it}.4.INX',{}); ps=sorted(n)
    if len(ps)<60: continue
    _,sa=x13.adjust([n[p] for p in ps],ps[0])
    cases+=[('IT',it,'X13','good',dict(zip(ps,sa))),('IT',it,'NSA','bad',n)]
def saar(s):
    ps=sorted(s); return {ps[i]:100*((s[ps[i]]/s[ps[i-3]])**4-1) for i in range(3,len(ps))}
W=[None,96,60,36,24]
print('area item kind truth start | F_p (full,96,60,36,24) | KW_p full | F_p on 3mSAAR (full,60,36)')
for a,it,k,t,s in cases:
    r=[R.test(s,w) for w in W]; q=[R.test(saar(s),w,rate=True) for w in (None,60,36)]
    f=lambda x: '  -  ' if x is None else f'{x:.3f}'
    print(a,it,k,t,min(s),'|',' '.join(f(x['F_p']) for x in r),'|',f(r[0]['KW_p']),'|',' '.join(f(x['F_p']) for x in q))
