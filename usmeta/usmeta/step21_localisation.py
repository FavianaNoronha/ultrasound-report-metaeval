"""Step 21a: LABEL-FREE prompts for the image check (breast + thyroid, the same 228 test scans as Steps 16 / 19b). NEW file; partb.py and step19_boxsweep.py are reused unchanged.
Prompts that need no label: centre50 (centred box covering 50% of the image area), whole (whole-image box), random (box of the SAME SIZE as the true box at a random position),
wrongregion (box of the same size as the true box, placed at random with NO overlap with the true box). Seed 0 -> crc32(case|condition). 'exact' = cached Step 16 masks, as the oracle reference.
THIS IS LABEL-FREE PROMPTING, NOT A DETECTOR: nothing here finds the lesion; random/wrong-region boxes use the true box SIZE only to keep box size comparable.
    python3 -m usmeta.step21_localisation predict | analyse"""
import os, sys, json, zlib, math, random, collections, time
import numpy as np
from PIL import Image
from . import partb, unified, step19_boxsweep as sb

OUT = os.path.join(sb.ROOT, 'results', 'partA', 'step21a_localisation'); MASKS = os.path.join(sb.ROOT, 'local_data', 'partb_localisation', 'masks'); TMP = os.path.join(sb.ROOT, 'local_data', 'partb_localisation')
CONDS = ['exact', 'centre50', 'whole', 'random', 'wrongregion']
LABEL = {'exact': 'exact box (oracle, Step 16)', 'centre50': 'centre box, 50% of image', 'whole': 'whole-image box', 'random': 'random box, true-box size', 'wrongregion': 'wrong-region box (no overlap with lesion box)'}

def rng_for(key, cond): return random.Random(zlib.crc32(f'{key}|{cond}'.encode()))

def box_for(cond, true_box, W, H, key):
    x0, y0, x1, y1 = map(float, true_box); w, h = x1 - x0, y1 - y0
    if cond == 'whole': return [0.0, 0.0, float(W), float(H)], True
    if cond == 'centre50':
        f = math.sqrt(0.5); bw, bh = W * f, H * f; return [(W - bw) / 2, (H - bh) / 2, (W + bw) / 2, (H + bh) / 2], True
    r = rng_for(key, cond)
    for _ in range(500):
        if w >= W or h >= H: break
        nx, ny = r.uniform(0, W - w), r.uniform(0, H - h); b = [nx, ny, nx + w, ny + h]
        ov = not (b[2] <= x0 or b[0] >= x1 or b[3] <= y0 or b[1] >= y1)
        if cond == 'random' or not ov: return b, True
    # fallback (box too large to avoid the lesion box): same aspect, scaled down until a non-overlapping position exists
    for s in (0.75, 0.5, 0.35, 0.25, 0.15):
        bw, bh = w * s, h * s
        for _ in range(500):
            nx, ny = r.uniform(0, max(1e-6, W - bw)), r.uniform(0, max(1e-6, H - bh)); b = [nx, ny, nx + bw, ny + bh]
            if not (b[2] <= x0 or b[0] >= x1 or b[3] <= y0 or b[1] >= y1): continue
            return b, False
    return [0.0, 0.0, 1.0, 1.0], False

def selection():
    sel = json.load(open(os.path.join(partb.LOCAL, 'selected.json'))); return [s for s in sel if s['dataset'] not in ('HC18', 'FetalHead')]

def predict():
    sel = selection(); recs = {}
    for ds in partb.DATASETS:
        for c in unified.load(partb.LOADER.get(ds, ds)): recs[c['case_id']] = c
    partb.MASKS = MASKS; os.makedirs(MASKS, exist_ok=True); P, M, dev = partb.load_model(); t0 = time.time(); n = 0; fb = []
    for s in sel:
        rec = recs[s['case_id']]; tm = partb.true_mask(rec); box = partb.box_of(partb.largest(tm)); img = Image.open(partb.img_path(rec)).convert('RGB'); H, W = tm.shape
        if img.size != (W, H): continue
        for cond in CONDS[1:]:
            f = partb.mpath(s['case_id'], cond)
            if os.path.exists(f): continue
            b, ok = box_for(cond, box, W, H, s['case_id'])
            if not ok: fb.append((s['case_id'], cond))
            np.savez_compressed(f, mask=np.packbits(partb.segment(P, M, dev, img, b)), shape=np.array([H, W]), box=np.array(b)); n += 1
        if n and n % 60 == 0: print(n, 'masks', round(time.time() - t0), 's', flush=True)
    json.dump(fb, open(os.path.join(OUT, 'wrongregion_fallbacks.json'), 'w')); print('done', n, 'new masks', round(time.time() - t0), 's; fallbacks', len(fb), flush=True)

def analyse():
    os.makedirs(TMP, exist_ok=True); json.dump(selection(), open(os.path.join(TMP, 'selected.json'), 'w'))
    real_local = partb.LOCAL; partb.LOCAL = TMP; sb.COND = CONDS; sb.SWEEP = MASKS; sb.LABEL = LABEL
    try: res = sb.analyse(OUT)
    finally: partb.LOCAL = real_local
    rows = [json.loads(l) for l in open(os.path.join(OUT, 'sweep_rows.jsonl'))]; extra = {}
    for c in CONDS:
        I = [o['mvf_' + c] for o in rows if o['kind'] == 'identical']; extra[c] = dict(n_correct_reports=len(I), share_below_0_5=float(np.mean([x < 0.5 for x in I])), share_below_0_8=float(np.mean([x < 0.8 for x in I])))
    json.dump(extra, open(os.path.join(OUT, 'correct_report_flags.json'), 'w'), indent=1); return res, extra

if __name__ == '__main__':
    {'predict': predict, 'analyse': analyse}[sys.argv[1]]()
