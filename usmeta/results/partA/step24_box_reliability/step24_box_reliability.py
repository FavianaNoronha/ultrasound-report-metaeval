"""Step 24: box-reliability curve for the image check (breast + thyroid, the same 228 test scans as Steps 16 / 19b / 21a). NEW file; partb.py, step19_boxsweep.py and step20.py are reused unchanged.
Boxes come from the TRUE mask and are perturbed in four families (shrink / enlarge / shift / jitter). THIS IS A PERTURBED-PROMPT SWEEP, NOT A DETECTOR.
Reused saved masks (exact same setting): exact (Step 16), shrink x0.9/0.75/0.5 (= 19b shrink10/25/50), enlarge x1.25 (= 19b enlarge25). Everything else is new MedSAM runs.
Check: Step 20 tolerance-aware image check (tau and position mode frozen in step20_tolerance_image_check/tuning_devval.json); exact-match (Step 16 rule) is also recorded.
    python3 -m usmeta.step24_box_reliability predict | analyse"""
import os, sys, json, zlib, math, random, collections, time, functools
import numpy as np
from PIL import Image
from . import partb, unified, schema, location, step19_boxsweep as sb, step20
from .layer0 import auroc_case
from .step10d_analysis import gboot

ROOT = sb.ROOT; OUT = os.path.join(ROOT, 'results', 'partA', 'step24_box_reliability'); NEW = os.path.join(ROOT, 'local_data', 'partb_box_reliability', 'masks')
FAMILIES = {'shrink': [0.9, 0.75, 0.6, 0.5, 0.4, 0.3], 'enlarge': [1.1, 1.25, 1.5, 2.0], 'shift': [0.10, 0.25, 0.50, 0.75], 'jitter': [0.05, 0.10, 0.20]}
SEEDS = (0, 1, 2)
REUSE = {('shrink', 0.9): 'shrink10', ('shrink', 0.75): 'shrink25', ('shrink', 0.5): 'shrink50', ('enlarge', 1.25): 'enlarge25'}      # -> mask names in the 19b sweep folder
LABELFREE = ['centre50', 'whole', 'random', 'wrongregion']; LF_DIR = os.path.join(ROOT, 'local_data', 'partb_localisation', 'masks')       # Step 21a masks, reused
BINS = [(0.9, 1.01, '0.9-1.0'), (0.7, 0.9, '0.7-0.9'), (0.5, 0.7, '0.5-0.7'), (0.3, 0.5, '0.3-0.5'), (-1, 0.3, '<0.3')]
DATASETS_ORGAN = {'breast': ('BrEaST', 'BUS-BRA', 'BUSI', 'UDIAT', 'BUS-UCLM'), 'thyroid': ('TN3K', 'DDTI', 'TN5000')}

def conds():
    """list of (name, family, level, seed, reuse_name_or_None)"""
    out = [('exact', 'exact', 1.0, 0, 'exact')]
    for fam, lv in FAMILIES.items():
        for l in lv:
            for sd in (SEEDS if fam == 'jitter' else (0,)): out.append((f'{fam}{l}' + (f'_s{sd}' if fam == 'jitter' else ''), fam, l, sd, REUSE.get((fam, l))))
    return out

def selection():
    sel = json.load(open(os.path.join(partb.LOCAL, 'selected.json'))); return [s for s in sel if s['dataset'] not in ('HC18', 'FetalHead')]

def make_box(fam, l, sd, box, W, H, key):
    x0, y0, x1, y1 = map(float, box); cx, cy, w, h = (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0
    if fam in ('shrink', 'enlarge'): w, h = w * l, h * l
    elif fam == 'shift':
        th = random.Random(zlib.crc32(f'{key}|shift{l}'.encode())).uniform(0, 2 * math.pi); cx, cy = cx + l * w * math.cos(th), cy + l * w * math.sin(th)      # centre moves by l x box WIDTH
    elif fam == 'jitter':
        r = random.Random(zlib.crc32(f'{key}|jitter{l}|{sd}'.encode()))
        for _ in range(100):
            b = [x0 + r.gauss(0, l * w), y0 + r.gauss(0, l * h), x1 + r.gauss(0, l * w), y1 + r.gauss(0, l * h)]
            b = [max(0.0, b[0]), max(0.0, b[1]), min(float(W), b[2]), min(float(H), b[3])]
            if b[2] - b[0] >= 4 and b[3] - b[1] >= 4: return b
        return [x0, y0, x1, y1]
    return [max(0.0, cx - w / 2), max(0.0, cy - h / 2), min(float(W), cx + w / 2), min(float(H), cy + h / 2)]

def mask_file(cid, name, reuse):
    if name in LABELFREE: return os.path.join(LF_DIR, os.path.basename(partb.mpath(cid, name)))
    if name == 'exact': return os.path.join(sb.ORIG, os.path.basename(partb.mpath(cid, 'exact')))
    if reuse: return os.path.join(sb.SWEEP, os.path.basename(partb.mpath(cid, reuse)))
    return os.path.join(NEW, os.path.basename(partb.mpath(cid, name)))

def predict():
    sel = selection(); recs = {}
    for ds in partb.DATASETS:
        for c in unified.load(partb.LOADER.get(ds, ds)): recs[c['case_id']] = c
    os.makedirs(NEW, exist_ok=True); P, M, dev = partb.load_model(); t0 = time.time(); n = 0
    for s in sel:
        rec = recs[s['case_id']]; tm = partb.true_mask(rec); box = partb.box_of(partb.largest(tm)); img = Image.open(partb.img_path(rec)).convert('RGB'); H, W = tm.shape
        if img.size != (W, H): continue
        for name, fam, l, sd, reuse in conds():
            if mask_file(s['case_id'], name, reuse) != os.path.join(NEW, os.path.basename(partb.mpath(s['case_id'], name))): continue
            f = mask_file(s['case_id'], name, reuse)
            if os.path.exists(f): continue
            b = make_box(fam, l, sd, box, W, H, s['case_id']); np.savez_compressed(f, mask=np.packbits(partb.segment(P, M, dev, img, b)), shape=np.array([H, W]), box=np.array(b)); n += 1
        if n and n % 100 < 19: print(n, 'masks', round(time.time() - t0), 's', flush=True)
    print('done', n, 'new masks', round(time.time() - t0), 's', flush=True)

def load(fp):
    z = np.load(fp); H, W = map(int, z['shape']); return np.unpackbits(z['mask'])[:H * W].reshape(H, W).astype(bool), list(z['box'])

SIZEF = ('size_mm', 'size_pct')
def analyse():
    os.makedirs(OUT, exist_ok=True); ch = json.load(open(os.path.join(ROOT, 'results', 'partA', 'step20_tolerance_image_check', 'tuning_devval.json')))['chosen']; tau, pm = ch['tau'], ch['position']
    schema.extract_rule = functools.lru_cache(maxsize=None)(schema.extract_rule)                       # claim extraction is deterministic: cache it
    sel = selection(); ids = {s['case_id'] for s in sel}; info = {s['case_id']: s for s in sel}; recs = {}
    for ds in partb.DATASETS:
        for c in unified.load(partb.LOADER.get(ds, ds)): recs[c['case_id']] = c
    bench = collections.defaultdict(list)
    for l in open(os.path.join(ROOT, 'bench_v2d.jsonl')):
        r = json.loads(l)
        if r['case_id'] in ids: bench[r['case_id']].append(r)
    organ_of = {d: o for o, ds in DATASETS_ORGAN.items() for d in ds}; CL = conds() + [(n, 'labelfree', float(i + 1), 0, None) for i, n in enumerate(LABELFREE)]; recs_out = []
    FIELDS = {'all': step20.CHECKABLE, 'position': ('pos',), 'size': step20.SIZE}
    def auc(rs, sc, fields):
        e = [sc(r) for r in rs if r['kind'] == 'error' and r['field'] in fields]; h = [sc(r) for r in rs if r['kind'] == 'harmless']; return auroc_case(e, h) if e and h else None
    for s in sel:
        cid = s['case_id']; rec = recs[cid]; tm = partb.true_mask(rec); tgt = partb.largest(tm); tbox = partb.box_of(tgt); rs = bench[cid]; mtrue = partb.ref_meas(rec, tm); bx_area = (tbox[2] - tbox[0]) * (tbox[3] - tbox[1])
        for name, fam, l, sd, reuse in CL:
            pmask, box = load(mask_file(cid, name, reuse)); meas = partb.pred_meas(rec, pmask)
            biou = location.box_iou(list(map(float, box)), tbox); cdist = math.hypot((box[0] + box[2]) / 2 - (tbox[0] + tbox[2]) / 2, (box[1] + box[3]) / 2 - (tbox[1] + tbox[3]) / 2) / (tbox[2] - tbox[0])
            miou = location.mask_iou(pmask, tgt) if s['has_true_mask'] else location.box_iou(partb.box_of(partb.largest(pmask)) if pmask.any() else [0, 0, 0, 0], tbox)
            # box-follows proxy: the TRUE-mask facts with the linear size scaled by the box scale (no segmentation at all) -> how much of the size drop is mechanical
            sc_box = math.sqrt(max((box[2] - box[0]) * (box[3] - box[1]), 1e-9) / bx_area); mp = dict(mtrue)
            for k in SIZEF:
                if isinstance(mp.get(k), (int, float)): mp[k] = mp[k] * sc_box
            d = dict(case_id=cid, dataset=s['dataset'], organ=organ_of[s['dataset']], group=s['group_id'], cond=name, family=fam, level=l, seed=sd, box_iou=biou, centre_dist=cdist, mask_iou=miou, mask_scale=float('nan'))
            for k in SIZEF:                                                                       # size_mm (breast) or size_pct (thyroid, % of image width: linear)
                if mtrue.get(k) and isinstance(meas.get(k), (int, float)): d['mask_scale'] = meas[k] / mtrue[k]; break
            for var, (t, p) in (('tol', (tau, pm)), ('exact', (0.0, 'exact'))):
                f = lambda r, t=t, p=p: step20.tol_score(r['candidate'], r['organ'], meas, t, p)
                for k, fl in FIELDS.items(): d[f'auc_{var}_{k}'] = auc(rs, f, fl)
                I = [f(r) for r in rs if r['kind'] == 'identical']; d[f'correct_{var}'] = float(np.mean(I)) if I else None
            fb = lambda r: step20.tol_score(r['candidate'], r['organ'], mp, tau, pm); d['auc_boxproxy_size'] = auc(rs, fb, FIELDS['size'])
            recs_out.append(d)
        if len(recs_out) % (len(CL) * 20) == 0: print(len(recs_out), 'case-conditions', flush=True)
    json.dump(dict(tau=tau, position=pm, rows=recs_out), open(os.path.join(OUT, 'case_rows.json'), 'w'))
    return recs_out

if __name__ == '__main__':
    {'predict': predict, 'analyse': analyse}[sys.argv[1]]()
