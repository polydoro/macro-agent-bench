import csv,os,sys,glob,math,collections
sys.path.insert(0,'./answer-keys')
import x13
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
area=sys.argv[1]; pat=sys.argv[2]; end=sys.argv[3]
S=load(pat)
items={'total':'000000','core':'XEF000','neig':'IGXE00','serv':'SERV00','energy':'NRGY00','food':'FOOD00'}
def saar(sa,ps):
    return {ps[i]:100*((sa[i]/sa[i-3])**4-1) for i in range(3,len(ps))}
def rmse(a,b,ps): return math.sqrt(sum((a[p]-b[p])**2 for p in ps)/len(ps))
for name,it in items.items():
    nk=[k for k in S if k.startswith(f'HICP.M.{area}.N.{it}.') and k.endswith('.INX') and '.4D0.' in k] or [k for k in S if k.startswith(f'ICP.M.{area}.N.{it}.') and k.endswith('INX')]
    if not nk: print(name,'no NSA'); continue
    nk=sorted(nk,key=lambda k:-len(S[k])); n=S[nk[0]]; ps=sorted(p for p in n if p<=end)
    last24=ps[-24:]
    fits={}
    for start in ['1997-01','2005-01','2010-01','2015-01']:
        q=[p for p in ps if p>=start]
        if len(q)<60: continue
        cfg,sa=x13.adjust([n[p] for p in q],q[0])
        fits[start]=saar(sa,q)
    # spec variant: no outliers, forced log, on 2010 start
    q=[p for p in ps if p>="2010-01"]
    if not fits: print(name,nk[0],len(ps),ps[:2]); continue
    for lab,spec in [('log',('l',True,None,True)),('noout',('n',None,None,False))]:
        sa=x13._run(x13.spec([n[p] for p in q],q[0],spec[1],spec[2],spec[3]))
        if sa: fits['2010'+lab]=saar(sa,q)
    base=fits[min(fits)]
    out={k:round(rmse(v,base,last24),2) for k,v in fits.items()}
    sk=f'HICP.M.{area}.Y.{it}.4F0.INX'
    if sk in S:
        o=S[sk]; op=sorted(p for p in o if p<=end)
        off=saar([o[p] for p in op],op)
        out['ECB_vs_X13_1997']=round(rmse(off,base,last24),2)
        out['ECB_vs_X13_2010']=round(rmse(off,fits['2010-01'],last24),2)
        out['latest_ECB']=round(off[last24[-1]],2); out['latest_X13']=round(base[last24[-1]],2)
        # residual seasonality of official vs NSA: RMSE of m/m SA vs nothing
    nsa=saar([n[p] for p in ps],ps)
    out['NSA_vs_X13']=round(rmse(nsa,base,last24),2)
    print(name,nk[0],out)
