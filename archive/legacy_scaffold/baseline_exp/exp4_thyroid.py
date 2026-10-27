import json, re, random, argparse, collections, os
import numpy as np
from sacrebleu.metrics import BLEU, CHRF
ap=argparse.ArgumentParser()
ap.add_argument('--jsonl',default=os.path.expanduser('~/Downloads/thyroid_grounded_full_v1.jsonl'))
ap.add_argument('--records',default=None,help='json list of prebuilt records (ds,path,count,loc,ratio)')
ap.add_argument('--max',type=int,default=3000)
ap.add_argument('--bert-model',default=None,help='e.g. distilbert-base-uncased; needs bert-score + internet')
ap.add_argument('--out',default='exp4_results.json')
args=ap.parse_args()
random.seed(0); np.random.seed(0)
# ---------- 1. build records from UltraG thyroid annotations ----------
recs=[]; skipped=collections.Counter()
if args.records: recs=json.load(open(args.records))
for f in ([] if args.records else [open(args.jsonl)]):
    for line in f:
        d=json.loads(line)
        nod=[m for m in d['masks'] if m.get('target_type')=='nodule']
        if not nod: skipped['no nodule mask']+=1; continue
        paths={m.get('pathology_label') for m in nod}
        if paths not in ({'benign'},{'malignant'}): skipped['pathology unclear']+=1; continue
        nod.sort(key=lambda m:-m.get('mask_area_px',0))
        recs.append(dict(ds=d['dataset'],path=paths.pop(),count=len(nod),
            loc=nod[0].get('location_grid','middle-central'),
            ratio=sum(m.get('area_ratio',0) for m in nod)))
print('usable samples',len(recs),'skipped',dict(skipped))
print('by dataset',dict(collections.Counter(r['ds'] for r in recs)))
print('pathology',dict(collections.Counter(r['path'] for r in recs)))
if len(recs)>args.max: recs=random.sample(recs,args.max)
q1,q2=np.quantile([r['ratio'] for r in recs],[1/3,2/3])
for r in recs: r['size']='small' if r['ratio']<q1 else 'medium' if r['ratio']<q2 else 'large'
print('using',len(recs),'samples; size terciles of area ratio:',round(float(q1),3),round(float(q2),3))
# ---------- 2. templated report, errors, harmless rewording ----------
CNT={1:'a single nodule',2:'two nodules'}
def cnt(n): return CNT.get(n,'three or more nodules')
def std(r):
    return (f"The largest nodule is {r['size']} relative to the image and lies in the {r['loc']} part of the image. "
            f"The scan shows {cnt(r['count'])} in total. Pathology: {r['path']}.")
SYN=[('The largest nodule','The biggest nodule'),('lies in','is located in'),('part of the image','area of the image'),
     ('The scan shows','The scan contains'),('Pathology:','Pathology label:')]
def mild(t):
    for a,b in SYN: t=t.replace(a,b)
    return t
def err(r,k):
    e=dict(r)
    if k=='pathology': e['path']={'benign':'malignant','malignant':'benign','class 0':'class 1','class 1':'class 0'}[r['path']]
    elif k=='count': e['count']={1:2,2:1}.get(r['count'],1)
    elif k=='location':
        v,h=r['loc'].split('-'); e['loc']=v+'-'+{'left':'right','right':'left','central':'right'}[h]
    elif k=='size': e['size']={'small':'large','medium':'large','large':'small'}[r['size']]
    return e
kinds=['pathology','count','location','size']
# ---------- 3. metrics ----------
bleu=BLEU(effective_order=True); chrf=CHRF()
def tok(t): return re.findall(r"[a-z0-9]+",t.lower())
def rougeL(ref,hyp):
    a,b=tok(ref),tok(hyp); dp=[[0]*(len(b)+1) for _ in range(len(a)+1)]
    for i in range(len(a)):
        for j in range(len(b)): dp[i+1][j+1]=dp[i][j]+1 if a[i]==b[j] else max(dp[i][j+1],dp[i+1][j])
    l=dp[-1][-1]
    if not l: return 0.0
    p,r=l/len(b),l/len(a); return 2*p*r/(p+r)
def fields(t):
    out=set()
    m=re.search(r'is (\w+) relative',t); out.add(('size',m.group(1) if m else '?'))
    m=re.search(r'(?:lies|located) in the ([\w-]+)',t); out.add(('loc',m.group(1) if m else '?'))
    m=re.search(r'(a single nodule|two nodules|three or more nodules)',t); out.add(('count',m.group(1) if m else '?'))
    m=re.search(r'(benign|malignant|class [01])',t); out.add(('path',m.group(1) if m else '?'))
    return out
def fieldF1(ref,hyp):
    a,b=fields(ref),fields(hyp); return 2*len(a&b)/(len(a)+len(b))
def allscores(ref,hyp):
    return dict(bleu=bleu.sentence_score(hyp,[ref]).score/100,rougeL=rougeL(ref,hyp),chrf=chrf.sentence_score(hyp,[ref]).score/100,fieldF1=fieldF1(ref,hyp))
items=[]
for r in recs:
    ref=std(r); items.append(('mild_paraphrase',ref,mild(ref)))
    for k in kinds: items.append((k,ref,std(err(r,k))))
S=[allscores(ref,hyp) for _,ref,hyp in items]; METS=['bleu','rougeL','chrf','fieldF1']
if args.bert_model:
    from bert_score import score as bscore
    P,R,F=bscore([h for *_,h in items],[r for _,r,_ in items],model_type=args.bert_model,lang='en',batch_size=64,verbose=False)
    for s,f in zip(S,F.tolist()): s['bertscoreF1']=f
    METS.append('bertscoreF1')
def boot(v,n=1000):
    v=np.array(v); m=[np.random.choice(v,len(v)).mean() for _ in range(n)]; return v.mean(),np.percentile(m,2.5),np.percentile(m,97.5)
kk=['mild_paraphrase']+kinds; res={}
print('\nMEAN SCORE vs reference (1=identical) [95% CI]'); print(f"{'':16s}"+''.join(f'{m:>20s}' for m in METS))
for k in kk:
    res[k]={}; line=f'{k:16s}'
    for m in METS:
        mu,lo,hi=boot([s[m] for (n,*_),s in zip(items,S) if n==k]); res[k][m]=[round(float(x),3) for x in (mu,lo,hi)]; line+=f'   {mu:.2f} [{lo:.2f},{hi:.2f}]'
    print(line)
print('\nAUROC: error ranked WORSE than mild paraphrase (1=perfect, .5=chance, 0=inverted)'); print(f"{'':10s}"+''.join(f'{m:>14s}' for m in METS)); au={}
b0={m:np.array([s[m] for (n,*_),s in zip(items,S) if n=='mild_paraphrase']) for m in METS}
for k in kinds:
    au[k]={}; line=f'{k:10s}'
    for m in METS:
        a=np.array([s[m] for (n,*_),s in zip(items,S) if n==k]); b=b0[m]
        au[k][m]=round(float(np.mean(a[:,None]<b[None,:])+0.5*np.mean(a[:,None]==b[None,:])),3); line+=f'{au[k][m]:14.3f}'
    print(line)
json.dump(dict(n=len(recs),by_dataset=dict(collections.Counter(r['ds'] for r in recs)),bert=args.bert_model,means=res,auroc=au),open(args.out,'w'),indent=1)
print('\nsaved',args.out); print('\nexample:'); print(std(recs[0])); print(mild(std(recs[0])))
