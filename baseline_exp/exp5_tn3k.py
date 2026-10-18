import libarchive, os, io, json, collections, argparse
import numpy as np
from PIL import Image
from scipy import ndimage
ap=argparse.ArgumentParser()
ap.add_argument('--rar',default=os.path.expanduser('~/Downloads/TN3K.rar'))
ap.add_argument('--out',default='tn3k_records.json')
args=ap.parse_args()
masks={}; labels={}
with libarchive.file_reader(args.rar) as a:
    for e in a:
        if e.isdir: continue
        name=e.pathname; base=os.path.basename(name)
        if name.endswith('label4trainval.csv') or name.endswith('label4test.csv'):
            sp='test' if name.endswith('label4test.csv') else 'trainval'
            for ln in b''.join(e.get_blocks()).decode().strip().splitlines():
                f,l=ln.split(','); labels[(sp,f)]=int(l)
        elif '-mask/' in name:
            split='test' if 'test-mask' in name else 'trainval'
            m=np.array(Image.open(io.BytesIO(b''.join(e.get_blocks()))).convert('L'))>127
            masks[(split,base)]=m
rows=[]
for (split,f),m in masks.items():
    h,w=m.shape; area=m.sum()
    if (split,f) not in labels or area==0: continue
    lab,ncomp=ndimage.label(m)
    sizes=ndimage.sum(m,lab,range(1,ncomp+1)); keep=int((sizes>=0.002*h*w).sum())  # ignore specks <0.2% of image
    ys,xs=np.nonzero(m); cy,cx=ys.mean()/h,xs.mean()/w
    v='upper' if cy<1/3 else 'middle' if cy<2/3 else 'lower'; hz='left' if cx<1/3 else 'central' if cx<2/3 else 'right'
    rows.append(dict(ds='TN3K',split=split,file=f,path=f'class {labels[(split,f)]}',count=max(keep,1),loc=f'{v}-{hz}',ratio=float(area/(h*w)),w=w,h=h))
print('TN3K samples analysed:',len(rows),'(masks',len(masks),', labels',len(labels),')')
print('\nclass counts:',dict(collections.Counter(r['path'] for r in rows)))
print('split counts:',dict(collections.Counter(r['split'] for r in rows)))
for c in ('class 0','class 1'):
    rr=[r for r in rows if r['path']==c]; ra=np.array([r['ratio'] for r in rr])
    print(f'\n{c}: n={len(rr)}  nodule area / image area: median {np.median(ra):.3f}, 25-75% {np.percentile(ra,25):.3f}-{np.percentile(ra,75):.3f}')
    print('  nodules per image:',dict(sorted(collections.Counter(min(r['count'],3) for r in rr).items())),'(3 = three or more)')
    print('  location:',dict(collections.Counter(r['loc'] for r in rr).most_common(5)))
ws=[r['w'] for r in rows]; hs=[r['h'] for r in rows]
print(f'\nimage width {min(ws)}-{max(ws)} (median {int(np.median(ws))}), height {min(hs)}-{max(hs)} (median {int(np.median(hs))})')
json.dump(rows,open(args.out,'w'))
print('saved',args.out)
