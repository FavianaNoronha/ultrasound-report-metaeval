import pandas as pd, random, numpy as np, json, re, sys, argparse
from sacrebleu.metrics import BLEU, CHRF
random.seed(0); np.random.seed(0)
ap=argparse.ArgumentParser()
ap.add_argument('--xlsx',default='breast.xlsx')
ap.add_argument('--bert-model',default='distilbert-base-uncased',help='e.g. roberta-large (slower, better)')
ap.add_argument('--no-bert',action='store_true')
args=ap.parse_args()
df=pd.read_excel(args.xlsx)
df=df[df.Classification!='normal'].copy()
def clean(v): return str(v).strip().lower()
def rec(r):
    m=clean(r.Margin).replace('not circumscribed - ','non-circumscribed, ')
    m=m.replace('&',' and ')
    bi=str(r.BIRADS).lower()
    return dict(shape=clean(r.Shape),margin=m,echo=clean(r.Echogenicity),post=clean(r.Posterior_features),
        calc=clean(r.Calcifications),halo=clean(r.Halo),birads=bi)
POST={'no':'no posterior acoustic features','shadowing':'posterior acoustic shadowing','enhancement':'posterior acoustic enhancement','combined':'combined posterior features'}
def calc_txt(c): return 'no calcifications' if c=='no' else f'calcifications ({c})'
def halo_txt(h): return 'with an echogenic halo' if h=='yes' else 'without a halo'
def std(d):
    return (f"A {d['shape']} mass is seen with {d['margin']} margins and {d['echo']} echotexture. "
            f"There are {POST.get(d['post'],d['post'])}, {calc_txt(d['calc'])}, and the mass is {halo_txt(d['halo'])}. "
            f"Assessment: BI-RADS {d['birads']}.")
def narr(d):  # meaning-preserving rewrite: different wording & order
    return (f"Assessment is BI-RADS {d['birads']}. The lesion appears {d['shape']} in contour, its borders being {d['margin']}, "
            f"and internally {d['echo']}. Regarding secondary findings: {halo_txt(d['halo'])}; {calc_txt(d['calc'])}; "
            f"{POST.get(d['post'],d['post'])} behind the lesion.")
SWAP={'shape':{'irregular':'oval','oval':'irregular','round':'irregular'},
 'echo':{'hypoechoic':'hyperechoic','hyperechoic':'hypoechoic','anechoic':'hyperechoic','isoechoic':'hypoechoic','heterogeneous':'anechoic','complex cystic/solid':'anechoic'},
 'post':{'no':'shadowing','shadowing':'enhancement','enhancement':'shadowing','combined':'no'},
 'halo':{'yes':'no','no':'yes'}}
def err(d,kind):
    e=dict(d)
    if kind=='margin':
        e['margin']='circumscribed' if d['margin']!='circumscribed' else 'non-circumscribed, spiculated and indistinct'
    elif kind in ('shape','echo','post','halo'): e[kind]=SWAP[kind].get(d[kind],d[kind])
    elif kind=='birads':
        b=d['birads']; e['birads']={'2':'5','3':'5','4a':'2','4b':'2','4c':'2','5':'3','1':'5'}.get(b,b)
    elif kind=='calc': e['calc']='in a mass' if d['calc']=='no' else 'no'
    return e
kinds=['margin','shape','echo','post','halo','birads','calc']
bleu=BLEU(effective_order=True); chrf=CHRF()
def tok(t): return re.findall(r"[a-z0-9]+",t.lower())
def rougeL(ref,hyp):
    a,b=tok(ref),tok(hyp)
    dp=[[0]*(len(b)+1) for _ in range(len(a)+1)]
    for i in range(len(a)):
        for j in range(len(b)):
            dp[i+1][j+1]=dp[i][j]+1 if a[i]==b[j] else max(dp[i][j+1],dp[i+1][j])
    l=dp[-1][-1]
    if l==0: return 0.0
    p,r=l/len(b),l/len(a); return 2*p*r/(p+r)
def scores(ref,hyp):
    return dict(bleu=bleu.sentence_score(hyp,[ref]).score/100, rougeL=rougeL(ref,hyp), chrf=chrf.sentence_score(hyp,[ref]).score/100)

from scipy.stats import spearmanr
# --- mild paraphrase: same order, synonym swaps only
SYN=[('a ','one '),('is seen with','is identified with'),('margins','borders'),('echotexture','echogenicity'),
     ('There are','Also noted:'),('and the mass is','while the mass is'),('Assessment:','Impression:'),('without a halo','lacking a halo')]
def mild(t):
    for a,b in SYN[1:]: t=t.replace(a,b)
    return t
# --- clinical-term F1 (BUSTR-style key-term overlap) and field checker (extract fields, compare)
KEY=['circumscribed','non-circumscribed','angular','indistinct','microlobulated','spiculated','oval','round','irregular',
     'anechoic','hypoechoic','hyperechoic','isoechoic','heterogeneous','shadowing','enhancement','halo','calcifications','birads']
def terms(t):
    t=t.lower(); out=set()
    for k in KEY:
        if k=='circumscribed': 
            if re.search(r'(?<!non-)circumscribed',t): out.add(k)
        elif k=='halo':
            out.add('halo-no' if 'without a halo' in t or 'lacking a halo' in t else 'halo-yes' if 'halo' in t else 'halo-none')
        elif k=='calcifications':
            out.add('calc-no' if 'no calcifications' in t else 'calc-yes' if 'calcifications' in t else 'calc-none')
        elif k=='birads':
            m=re.search(r'bi-rads (\w+)',t); out.add('birads-'+(m.group(1) if m else '?'))
        elif k in t: out.add(k)
    return out
def termF1(ref,hyp):
    a,b=terms(ref),terms(hyp); i=len(a&b)
    if i==0: return 0.0
    p,r=i/len(b),i/len(a); return 2*p*r/(p+r)
def allscores(ref,hyp):
    s=scores(ref,hyp); s['termF1']=termF1(ref,hyp); return s
METS=['bleu','rougeL','chrf','termF1']

# ---------------- run ----------------
df2=df.copy(); items=[]   # (kind, record_idx, ref, hyp)
for idx,r in df2.iterrows():
    d=rec(r); ref=std(d)
    items.append(('mild_paraphrase',idx,ref,mild(ref)))
    items.append(('strong_rewrite',idx,ref,narr(d)))
    for k in kinds:
        e=err(d,k)
        if e!=d: items.append((k,idx,ref,std(e)))
ORD={'2':0,'3':1,'4a':2,'4b':3,'4c':4,'5':5}
sev_items=[]
for idx,r in df2.iterrows():
    d=rec(r)
    if d['birads'] not in ORD: continue
    ref=std(d)
    for b in ORD:
        if b!=d['birads']:
            e=dict(d); e['birads']=b; sev_items.append((abs(ORD[b]-ORD[d['birads']]),ref,std(e)))
print('pairs:',len(items),'severity pairs:',len(sev_items))
S=[allscores(ref,hyp) for _,_,ref,hyp in items]
SS=[allscores(ref,hyp) for _,ref,hyp in sev_items]
METS=['bleu','rougeL','chrf','termF1']
if not args.no_bert:
    from bert_score import score as bscore
    print('computing BERTScore with',args.bert_model,'(first run downloads the model)...')
    allc=[h for *_,h in items]+[h for _,_,h in sev_items]; allr=[r for _,_,r,_ in items]+[r for _,r,_ in sev_items]
    P,R,F=bscore(allc,allr,model_type=args.bert_model,lang='en',batch_size=64,verbose=False)
    F=F.tolist()
    for s,f in zip(S,F[:len(S)]): s['bertscoreF1']=f
    for s,f in zip(SS,F[len(S):]): s['bertscoreF1']=f
    METS.append('bertscoreF1')
def boot(v,n=1000):
    v=np.array(v); m=[np.random.choice(v,len(v)).mean() for _ in range(n)]
    return v.mean(),np.percentile(m,2.5),np.percentile(m,97.5)
kk=['mild_paraphrase','strong_rewrite']+kinds
print('\nMEAN SCORE vs reference (1=identical) [95% CI]')
print(f"{'':16s}"+''.join(f'{m:>20s}' for m in METS))
res={}
for k in kk:
    res[k]={}; line=f'{k:16s}'
    for m in METS:
        mu,lo,hi=boot([s[m] for (n,*_),s in zip(items,S) if n==k]); res[k][m]=[round(float(x),3) for x in (mu,lo,hi)]
        line+=f'   {mu:.2f} [{lo:.2f},{hi:.2f}]'
    print(line)
print('\nAUROC: error ranked WORSE than mild paraphrase (1=perfect, .5=chance, 0=inverted)')
print(f"{'':10s}"+''.join(f'{m:>14s}' for m in METS)); au={}
b0={m:np.array([s[m] for (n,*_),s in zip(items,S) if n=='mild_paraphrase']) for m in METS}
for k in kinds:
    au[k]={}; line=f'{k:10s}'
    for m in METS:
        a=np.array([s[m] for (n,*_),s in zip(items,S) if n==k]); b=b0[m]
        au[k][m]=round(float(np.mean(a[:,None]<b[None,:])+0.5*np.mean(a[:,None]==b[None,:])),3); line+=f'{au[k][m]:14.3f}'
    print(line)
sev=[x[0] for x in sev_items]; sp={}
print('\nSEVERITY: Spearman(score, size of BI-RADS jump). Strongly negative = metric tracks severity; ~0 = blind')
for m in METS:
    rho,_=spearmanr(sev,[s[m] for s in SS]); sp[m]=round(float(rho),3); print(f'{m:14s}{rho:+.3f}')
json.dump(dict(model=None if args.no_bert else args.bert_model,means=res,auroc=au,spearman=sp,n=len(df2)),open('exp3_results.json','w'),indent=1)
print('\nsaved exp3_results.json')
