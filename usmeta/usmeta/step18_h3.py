"""Step 18, H3 (Amendment 1): MedSAM measurement error vs distance to the 20 mm staging-style cutoff ('to confirm'; secondary; not a BI-RADS rule).
BrEaST MALIGNANT test cases with a true mask and a real pixel size (mm). Step 16 setup: box prompts from the TRUE mask (exact, +10%, +20%), MedSAM wanglab/medsam-vit-base.
Size = longest diameter of the whole mask in mm (layer3.measured_facts size_mm; the same definition for true and predicted mask; major axis from the mask, which can differ
from a clinician's caliper maximum dimension). No Qwen/MedGemma boxes. Test split via usmeta.splits.load('test').
    python3 -m usmeta.step18_h3 run OUT.json"""
import os, sys, json, collections
import numpy as np
from PIL import Image
from . import unified, layer3, splits, partb
from .step10d_analysis import gboot

CUT = 20.0

def run(out):
    sp = {r['case_id']: r for r in splits.load('test', script='usmeta.step18_h3')}
    recs = [c for c in unified.load('BrEaST') if c['case_id'] in sp and c['labels'].get('cls') == 'malignant' and c['region'] and c['pixel_mm']]
    P, M, dev = partb.load_model(); os.makedirs(partb.MASKS, exist_ok=True); rows = []
    for rec in recs:
        cid = rec['case_id']; tm = partb.true_mask(rec)
        if tm is None or not tm.any(): continue
        tgt = partb.largest(tm); box = partb.box_of(tgt); img = Image.open(partb.img_path(rec)).convert('RGB'); H, W = tm.shape
        if img.size != (W, H): continue
        ref = layer3.measured_facts(rec, tm)[0].get('size_mm'); r = dict(case_id=cid, group=sp[cid]['group_id'], true_mm=ref)
        for p in partb.PROMPTS:
            f = partb.mpath(cid, p)
            if not os.path.exists(f):
                b = partb.jitter_box(box, partb.FRAC[p], W, H, cid); np.savez_compressed(f, mask=np.packbits(partb.segment(P, M, dev, img, b)), shape=np.array([H, W]), box=np.array(b))
            pm, _ = partb.load_pred(cid, p); r[p] = layer3.measured_facts(rec, pm)[0].get('size_mm') if pm.any() else None
        rows.append(r)
    json.dump(rows, open(out, 'w'), indent=1); return rows

def summarise(rows):
    res = {}
    for p in partb.PROMPTS:
        R = [r for r in rows if r['true_mm'] and r[p]]; t = np.array([r['true_mm'] for r in R]); q = np.array([r[p] for r in R]); g = [r['group'] for r in R]
        err = np.abs(q - t); dist = np.abs(t - CUT); flip = (t >= CUT) != (q >= CUT)
        res[p] = dict(n=len(R), n_groups=len(set(g)), median_abs_err_mm=float(np.median(err)), median_signed_err_mm=float(np.median(q - t)), median_rel_err=float(np.median(err / t)),
                      share_cross_20=gboot([float(x) for x in flip], g), n_flip=int(flip.sum()),
                      near={f'within_{m}mm': dict(n=int((dist <= m).sum()), flips=int(flip[dist <= m].sum()), flip_share=float(flip[dist <= m].mean()) if (dist <= m).any() else None) for m in (2, 3, 5)},
                      share_within_error=float((dist < err).mean()), median_dist_to_cutoff=float(np.median(dist)), true_ge_20=int((t >= 20).sum()))
    return res

if __name__ == '__main__':
    rows = run(sys.argv[2]); print(json.dumps(summarise(rows), indent=1))
