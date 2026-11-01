"""Step 19b: box-degradation sweep for the Step 16 image check (oracle dependence). NEW file; partb.py is reused unchanged.
Same scans (Step 16 selection, test split), same MedSAM (wanglab/medsam-vit-base, MPS), same mask_verified_facts check, same reports (bench_v2d rows of those scans).
Conditions (box from the TRUE mask, then degraded; seed 0 -> crc32(case|condition)): exact (cached Step 16 masks), shrink 10/25/50% about the centre, shift 10/25% of the box size in a random direction, enlarge 25%.
THIS IS A DEGRADED-PROMPT SWEEP, NOT A DETECTOR: every box is still derived from the true mask and does not replace an end-to-end test.
    python3 -m usmeta.step19_boxsweep predict | analyse OUT_DIR"""
import os, sys, json, zlib, math, random, collections, time
import numpy as np
from PIL import Image
from . import partb, unified, location, layer3
from .layer0 import auroc_case
from .step10d_analysis import gboot

ROOT = partb.ROOT; SWEEP = os.path.join(ROOT, 'local_data', 'partb_sweep', 'masks'); ORIG = partb.MASKS
COND = ['exact', 'shrink10', 'shrink25', 'shrink50', 'shift10', 'shift25', 'enlarge25']
LABEL = {'exact': 'exact', 'shrink10': 'shrink 10%', 'shrink25': 'shrink 25%', 'shrink50': 'shrink 50%', 'shift10': 'shift 10%', 'shift25': 'shift 25%', 'enlarge25': 'enlarge 25%'}

def degrade(box, W, H, cond, key):
    x0, y0, x1, y1 = map(float, box); cx, cy, w, h = (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0
    if cond.startswith('shrink'): f = int(cond[6:]) / 100; w, h = w * (1 - f), h * (1 - f)
    elif cond.startswith('enlarge'): f = int(cond[7:]) / 100; w, h = w * (1 + f), h * (1 + f)
    elif cond.startswith('shift'):
        f = int(cond[5:]) / 100; th = random.Random(zlib.crc32(f'{key}|{cond}'.encode())).uniform(0, 2 * math.pi); cx, cy = cx + f * w * math.cos(th), cy + f * h * math.sin(th)
    return [max(0.0, cx - w / 2), max(0.0, cy - h / 2), min(float(W), cx + w / 2), min(float(H), cy + h / 2)]

def mpath_for(cid, cond): return partb.mpath(cid, cond) if cond != 'exact' else None

def predict():
    sel = json.load(open(os.path.join(partb.LOCAL, 'selected.json'))); recs = {}
    for ds in partb.DATASETS:
        for c in unified.load(partb.LOADER.get(ds, ds)): recs[c['case_id']] = c
    partb.MASKS = SWEEP; os.makedirs(SWEEP, exist_ok=True); P, M, dev = partb.load_model(); t0 = time.time(); n = 0
    for s in sel:
        rec = recs[s['case_id']]; tm = partb.true_mask(rec); box = partb.box_of(partb.largest(tm)); img = Image.open(partb.img_path(rec)).convert('RGB'); H, W = tm.shape
        if img.size != (W, H): continue
        for cond in COND[1:]:
            f = partb.mpath(s['case_id'], cond)
            if os.path.exists(f): continue
            b = degrade(box, W, H, cond, s['case_id']); np.savez_compressed(f, mask=np.packbits(partb.segment(P, M, dev, img, b)), shape=np.array([H, W]), box=np.array(b)); n += 1
        if n and n % 60 == 0: print(n, 'masks', round(time.time() - t0), 's', flush=True)
    print('done', n, 'new masks', round(time.time() - t0), 's', flush=True)

def load_cond(cid, cond):
    partb.MASKS = ORIG if cond == 'exact' else SWEEP; return partb.load_pred(cid, cond)

SIZE = partb.SIZE
def analyse(out):
    sel = json.load(open(os.path.join(partb.LOCAL, 'selected.json'))); recs = {}
    for ds in partb.DATASETS:
        for c in unified.load(partb.LOADER.get(ds, ds)): recs[c['case_id']] = c
    ids = {s['case_id'] for s in sel}; grp = {s['case_id']: s['group_id'] for s in sel}; dsof = {s['case_id']: s['dataset'] for s in sel}; hasmask = {s['case_id']: s['has_true_mask'] for s in sel}
    bench = [json.loads(l) for l in open(os.path.join(ROOT, 'bench_v2d.jsonl'))]; bench = [r for r in bench if r['case_id'] in ids]
    L0 = json.load(open(os.path.join(ROOT, 'scores_v2d_layer0.json'))); idx = {tuple(p): i for i, p in enumerate(L0['pairs'])}; rt = L0['scores']['ratescore']
    iou = collections.defaultdict(dict); M = {}
    for s in sel:
        rec = recs[s['case_id']]; tm = partb.true_mask(rec); tgt = partb.largest(tm); M[(s['case_id'], 'true')] = partb.ref_meas(rec, tm)
        for cond in COND:
            pm, box = load_cond(s['case_id'], cond); M[(s['case_id'], cond)] = partb.pred_meas(rec, pm)
            if s['has_true_mask']: iou[cond][s['case_id']] = location.mask_iou(pm, tgt)
            else: iou[cond][s['case_id']] = location.box_iou(partb.box_of(partb.largest(pm)) if pm.any() else [0, 0, 0, 0], partb.box_of(tgt))     # TN5000: box IoU
    rows = []
    for r in bench:
        o = dict(case_id=r['case_id'], dataset=r['dataset'], group=grp[r['case_id']], kind=r['kind'], field=r['field'], hgroup=r['group'])
        for src in ('true',) + tuple(COND): o['mvf_' + src] = (lambda v: 1.0 if v[0] is None else v[0])(layer3.mask_verified(r['candidate'], r['organ'], M[(r['case_id'], src)]))
        i = idx.get((r['reference'], r['candidate'])); o['ratescore'] = float(rt[i]) if i is not None else float('nan'); rows.append(o)
    subs = {'all checkable': ('lesion', 'count', 'pos', 'orient') + SIZE, 'position': ('pos',), 'size': SIZE}
    groups = {'breast+thyroid (pooled)': lambda d: d not in ('HC18', 'FetalHead'), 'fetal head (pooled)': lambda d: d in ('HC18', 'FetalHead')}
    for d in partb.DATASETS: groups[d] = (lambda d: lambda x: x == d)(d)
    res = {}; lines = []
    def aucs(rs, name, fields):
        by = collections.defaultdict(list)
        for o in rs: by[o['case_id']].append(o)
        v, g = [], []
        for c, rr in by.items():
            e = [o[name] for o in rr if o['kind'] == 'error' and o['field'] in fields]; h = [o[name] for o in rr if o['kind'] == 'harmless']
            if e and h: v.append(auroc_case(e, h)); g.append(rr[0]['group'])
        return (gboot(v, g) if v else None), len(v), len(set(g))
    for gname, f in groups.items():
        rs = [o for o in rows if f(o['dataset'])]; cs = [c for c in ids if f(dsof[c])]
        for cond in COND:
            d = dict(n_scans=len(cs)); cm = [c for c in cs if hasmask[c]]; vals = [iou[cond][c] for c in cm]; d['n_mask_iou'] = len(cm); d['iou'] = gboot(vals, [grp[c] for c in cm]) if vals else None       # mask IoU only where a true mask exists
            cb = [c for c in cs if not hasmask[c]]
            if cb: d['box_iou_tn5000'] = gboot([iou[cond][c] for c in cb], [grp[c] for c in cb])
            for sname, fields in subs.items():
                a, n, ng = aucs(rs, 'mvf_' + cond, fields); d['auroc_' + sname] = a; d['n_' + sname] = n; d['groups_' + sname] = ng
                ra, _, _ = aucs(rs, 'ratescore', fields); d['ratescore_' + sname] = ra
            I = [o['mvf_' + cond] for o in rs if o['kind'] == 'identical']; d['identical_mean'] = float(np.mean(I)) if I else None; d['identical_full'] = float(np.mean([x > 0.999 for x in I])) if I else None
            res[f'{gname}|{cond}'] = d
    # ratescore reference per group/subset (independent of condition)
    json.dump(res, open(os.path.join(out, 'sweep_results.json'), 'w'), indent=1)
    open(os.path.join(out, 'sweep_rows.jsonl'), 'w').write(''.join(json.dumps(o) + '\n' for o in rows))
    json.dump({f'{k[0]}|{k[1]}': v for k, v in iou_summary(iou, sel).items()}, open(os.path.join(out, 'iou_by_case_summary.json'), 'w'), indent=1)
    return res

def iou_summary(iou, sel):
    return {(s['dataset'], c): float(np.mean([iou[c][s['case_id']] for s in sel if s['dataset'] == s['dataset']])) for s in sel[:0] for c in COND}

if __name__ == '__main__':
    if sys.argv[1] == 'predict': predict()
    if sys.argv[1] == 'analyse': os.makedirs(sys.argv[2], exist_ok=True); analyse(sys.argv[2])
