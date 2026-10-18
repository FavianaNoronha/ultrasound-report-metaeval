import csv, re, random, json, argparse, os
import numpy as np
from scipy.stats import spearmanr
from sacrebleu.metrics import BLEU, CHRF
ap=argparse.ArgumentParser()
ap.add_argument('--csv',default=os.path.expanduser('~/Downloads/archive-7/training_set_pixel_size_and_HC.csv'))
ap.add_argument('--out',default='exp6_hc18_results.json')
args=ap.parse_args()
random.seed(0); np.random.seed(0)
rows=[(r['filename'],float(r['pixel size(mm)']),float(r['head circumference (mm)'])) for r in csv.DictReader(open(args.csv))]
hc=np.array([r[2] for r in rows]); print('HC18 rows',len(rows),'head circumference mm: min %.1f median %.1f max %.1f'%(hc.min(),np.median(hc),hc.max()))
def std(h,px): return f"The fetal head circumference measures {h:.1f} mm at an image scale of {px:.3f} mm per pixel."
def mild(h,px): return f"The fetal head circumference is {h:.1f} mm with a scale of {px:.3f} mm per pixel."
def unit(h,px): return f"The fetal head circumference measures {h/10:.2f} cm at an image scale of {px:.3f} mm per pixel."
bleu=BLEU(effective_order=True); chrf=CHRF()
def tok(t): return re.findall(r"[a-z0-9]+",t.lower())
def rougeL(ref,hyp):
    a,b=tok(ref),tok(hyp); dp=[[0]*(len(b)+1) for _ in range(len(a)+1)]
    for i in range(len(a)):
        for j in range(len(b)): dp[i+1][j+1]=dp[i][j]+1 if a[i]==b[j] else max(dp[i][j+1],dp[i+1][j])
    l=dp[-1][-1]
    if not l: return 0.0
    p,r=l/len(b),l/len(a); return 2*p*r/(p+r)
def sc(ref,hyp): return dict(bleu=bleu.sentence_score(hyp,[ref]).score/100,rougeL=rougeL(ref,hyp),chrf=chrf.sentence_score(hyp,[ref]).score/100)
M=['bleu','rougeL','chrf']; SIZES=[1,2,5,10,20,40]
groups={'mild_paraphrase':[], 'unit_rewrite (4.43 cm = 44.3 mm)':[]}
for s in SIZES: groups[f'error_{s}mm']=[]
for f,px,h in rows:
    ref=std(h,px)
    groups['mild_paraphrase'].append(sc(ref,mild(h,px)))
    groups['unit_rewrite (4.43 cm = 44.3 mm)'].append(sc(ref,unit(h,px)))
    for s in SIZES:
        h2=h+s*random.choice([-1,1]); h2=max(h2,1.0)
        groups[f'error_{s}mm'].append(sc(ref,std(h2,px)))
def boot(v,n=1000):
    v=np.array(v); m=[np.random.choice(v,len(v)).mean() for _ in range(n)]; return v.mean(),np.percentile(m,2.5),np.percentile(m,97.5)
res={}
print('\nMEAN SCORE vs reference (1=identical) [95% CI]'); print(f"{'':36s}"+''.join(f'{m:>20s}' for m in M))
for k,v in groups.items():
    res[k]={}; line=f'{k:36s}'
    for m in M:
        mu,lo,hi=boot([x[m] for x in v]); res[k][m]=[round(float(a),3) for a in (mu,lo,hi)]; line+=f'   {mu:.2f} [{lo:.2f},{hi:.2f}]'
    print(line)
print('\nAUROC: error ranked WORSE than harmless version (1=perfect, .5=chance, 0=inverted)')
au={}
for ctrl in ('mild_paraphrase','unit_rewrite (4.43 cm = 44.3 mm)'):
    print('vs',ctrl); au[ctrl]={}
    for s in SIZES:
        au[ctrl][s]={}; line=f'  error {s:>2d} mm: '
        for m in M:
            a=np.array([x[m] for x in groups[f'error_{s}mm']]); b=np.array([x[m] for x in groups[ctrl]])
            au[ctrl][s][m]=round(float(np.mean(a[:,None]<b[None,:])+0.5*np.mean(a[:,None]==b[None,:])),3); line+=f'{m} {au[ctrl][s][m]:.3f}   '
        print(line)
sizes=[s for s in SIZES for _ in rows]; sp={}
print('\nSEVERITY: Spearman(score, size of error in mm); strongly negative = metric tracks severity')
for m in M:
    rho,_=spearmanr(sizes,[x[m] for s in SIZES for x in groups[f'error_{s}mm']]); sp[m]=round(float(rho),3); print(f'{m:8s}{rho:+.3f}')
json.dump(dict(n=len(rows),means=res,auroc=au,spearman=sp),open(args.out,'w'),indent=1)
print('\nexample:',std(*rows[0][1:][::-1]) if False else std(rows[0][2],rows[0][1])); print(unit(rows[0][2],rows[0][1]))
