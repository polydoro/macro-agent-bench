import sys,csv,glob,collections,math
sys.path.insert(0,'./answer-keys')
import extract_sa as X, resid_seas as R
E='./execucoes/'
inv=[r for r in csv.DictReader(open(E+'../harmonization-case-inventory-20261109-v1.csv',encoding='utf-8-sig')) if r['task'] in('S05','S06') and r['phase'] in('A1','A2','A3')]
# official ECB SA m/m for S06 comparison
def ecb():
    S={}
    for p in glob.glob(E+'pilot-*s06*/attempts/*/work/**/*.csv',recursive=True):
        try:
            with open(p,errors='ignore') as fh:
                if 'OBS_VALUE' not in fh.readline(): continue
                fh.seek(0)
                for r in csv.DictReader(fh):
                    k=r.get('KEY','')
                    if (k.startswith('HICP.M.U2.Y.') and k.endswith('4F0.INX')) or (k.startswith('ICP.M.U2.Y.') and k.endswith('.3.INX')):
                        S.setdefault((k.split('.')[0],k.split('.')[4]),{})[r['TIME_PERIOD']]=float(r['OBS_VALUE'])
        except Exception: pass
    return S
OFF=ecb(); CODE={'total':'000000','core':'XEF000','neig':'IGXE00','serv':'SERV00','energy':'NRGY00','food':'FOOD00'}
def mom(d):
    ps=sorted(d); return {ps[i]:100*(d[ps[i]]/d[ps[i-1]]-1) for i in range(1,len(ps)) if d[ps[i-1]]}
w=csv.writer(open(sys.argv[1],'w',newline='')); w.writerow(['phase','task','model','component','kind','first','last','n_tested','F_p','KW_p','verdict','official_ecb_mom_rmse','file','column'])
for r in inv:
    wd=glob.glob(f"{E}{r['source_campaign_id']}/attempts/{r['final_attempt_id']}/work")[0]
    got=X.extract(wd)
    for c in CODE:
        g=got.get(c)
        if not g:
            w.writerow([r['phase'],r['task'],r['model'],c,'none','','','','','','no saved series','','','']); continue
        d=g['data']; t=R.test(d,rate=g['kind']=='saar')
        n=t['n']
        if t['F_p'] is None or n<36: v='too short'
        elif t['F_p']<0.01: v='residual seasonality'
        elif t['F_p']>=0.05: v='pass'
        else: v='inconclusive'
        off=''
        if r['task']=='S06' and g['kind']=='sa':
            vals=[]
            for ds in ('HICP','ICP'):
                if (ds,CODE[c]) not in OFF: continue
                a,b=mom(d),mom(OFF[(ds,CODE[c])]); com=[p for p in a if p in b][-60:]
                if com: vals.append(math.sqrt(sum((a[p]-b[p])**2 for p in com)/len(com)))
            if vals:
                off=round(min(vals),3)
                if off<=0.02: v='official ECB SA'
        w.writerow([r['phase'],r['task'],r['model'],c,g['kind'],min(d),max(d),n,round(t['F_p'],4) if t['F_p'] is not None else '',round(t['KW_p'],4) if t['KW_p'] is not None else '',v,off,g['file'],g['col']])
