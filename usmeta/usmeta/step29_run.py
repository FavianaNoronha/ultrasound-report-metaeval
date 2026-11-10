"""Step 29 test run (single pass; the test split is read once, logged): 29a label-free image check by U-Net segmentation (breast, thyroid; the same 228 scans as Steps 21a / 24),
29b fetal head geometry on HC18 (ellipse head circumference, U-Net head masks, planted HC errors).
    python3 -m usmeta.step29_run annotation   (29b-1: annotation ellipse vs the provided HC; dev + val only chosen method; no test numbers for the model)
    python3 -m usmeta.step29_run test         (needs the three trained models)
Image check = Step 20 tolerance-aware check (tau, position rule frozen on dev/val in step20_tolerance_image_check/tuning_devval.json) and the Step 16 exact rule; same scoring code as Step 24."""
import os, sys, json, math, random, collections, functools, time
import numpy as np
import cv2
from PIL import Image
from scipy import ndimage
from . import partb, unified, schema, location, step20, splits, step24_box_reliability as s24, step29_seg as G
from .layer0 import auroc_case
from .step10d_analysis import gboot

OUT = G.OUT; ROOT = G.ROOT
def largest(m):
    lab, k = ndimage.label(m)
    return m if k <= 1 else lab == (int(np.argmax(ndimage.sum(m, lab, range(1, k + 1)))) + 1)

def load_net(name, dev):
    import torch
    m = G.build_model().to(dev); m.load_state_dict(torch.load(os.path.join(G.LOCAL, f'unet_{name}.pt'), map_location=dev)); return m.eval(), json.load(open(os.path.join(OUT, f'train_{name}.json')))['chosen']

def predict_mask(model, dev, img_gray, th, keep):
    """full-resolution boolean mask from one grayscale PIL image"""
    import torch, torch.nn.functional as F
    W, H = img_gray.size; x = np.asarray(img_gray.resize((G.S, G.S), Image.BILINEAR))[None]; p = G.predict_batch(model, x, dev)[0]
    p = F.interpolate(torch.from_numpy(p)[None, None], size=(H, W), mode='bilinear', align_corners=False)[0, 0].numpy(); m = p > th
    return largest(m) if (keep == 'largest' and m.any()) else m

# ---------------------------------------------------------------- 29a
FIELDS = {'all': step20.CHECKABLE, 'position': ('pos',), 'size': step20.SIZE}
def scan_scores(rs, meas, tau, pm):
    def auc(sc, fields):
        e = [sc(r) for r in rs if r['kind'] == 'error' and r['field'] in fields]; h = [sc(r) for r in rs if r['kind'] == 'harmless']; return auroc_case(e, h) if e and h else None
    d = {}
    for var, (t, p) in (('tol', (tau, pm)), ('exact', (0.0, 'exact'))):
        f = lambda r, t=t, p=p: step20.tol_score(r['candidate'], r['organ'], meas, t, p)
        for k, fl in FIELDS.items(): d[f'auc_{var}_{k}'] = auc(f, fl)
        I = [f(r) for r in rs if r['kind'] == 'identical']; d[f'correct_{var}'] = float(np.mean(I)) if I else None
    return d

def run_29a(dev):
    ch = json.load(open(os.path.join(ROOT, 'results', 'partA', 'step20_tolerance_image_check', 'tuning_devval.json')))['chosen']; tau, pm_ = ch['tau'], ch['position']
    schema.extract_rule = functools.lru_cache(maxsize=None)(schema.extract_rule)
    sel = s24.selection(); ids = {s['case_id'] for s in sel}; recs = step20.recs_all(); bench = collections.defaultdict(list)
    for l in open(os.path.join(ROOT, 'bench_v2d.jsonl')):
        r = json.loads(l)
        if r['case_id'] in ids: bench[r['case_id']].append(r)
    organ_of = {d: o for o, ds in s24.DATASETS_ORGAN.items() for d in ds}; nets = {o: load_net(o, dev) for o in ('breast', 'thyroid')}; md = os.path.join(G.LOCAL, 'masks'); os.makedirs(md, exist_ok=True); rows = []; t0 = time.time()
    for i, s in enumerate(sel):
        cid = s['case_id']; rec = recs[cid]; o = organ_of[s['dataset']]; tm = partb.true_mask(rec); tgt = partb.largest(tm); H, W = tm.shape; model, chz = nets[o]
        img = Image.open(partb.img_path(rec)).convert('L')
        if img.size != (W, H): continue
        pm = predict_mask(model, dev, img, chz['threshold'], chz['keep']); np.savez_compressed(os.path.join(md, cid.replace(':', '_').replace('/', '_') + '.npz'), mask=np.packbits(pm), shape=np.array([H, W]))
        meas = partb.pred_meas(rec, pm); d = dict(case_id=cid, dataset=s['dataset'], organ=o, group=s['group_id'], has_true_mask=bool(s['has_true_mask']), found=bool(pm.any()), area_frac_true=float(tgt.mean()))
        if s['has_true_mask']: d['iou'] = location.mask_iou(pm, tgt); d['dice'] = location.dice(pm, tgt)
        else: d['box_iou'] = location.box_iou(partb.box_of(largest(pm)) if pm.any() else [0, 0, 0, 0], partb.box_of(tgt))
        for k in ('size_mm', 'size_pct'):
            ref = partb.ref_meas(rec, tm)
            if ref.get(k) and isinstance(meas.get(k), (int, float)): d['size_ratio'] = meas[k] / ref[k]; break
        d['pos_agree'] = float(meas.get('pos') == partb.ref_meas(rec, tm).get('pos')) if meas.get('pos') else 0.0
        d.update(scan_scores(bench[cid], meas, tau, pm_)); rows.append(d)
        if i % 30 == 0: print('29a', i, len(sel), round(time.time() - t0), 's', flush=True)
    json.dump(dict(tau=tau, position=pm_, rows=rows, chosen={o: nets[o][1] for o in nets}), open(os.path.join(OUT, 'a_rows.json'), 'w')); return rows

# ---------------------------------------------------------------- 29b
def ramanujan(a, b): return math.pi * (3 * (a + b) - math.sqrt((3 * a + b) * (a + 3 * b)))

def hc_from_mask(mask, pixel_mm, method):
    """head circumference (mm) from a filled head mask. 'moments': ellipse with the same second moments; 'fit': cv2.fitEllipse on the outer contour"""
    if not mask.any(): return None
    if method == 'moments':
        ys, xs = np.where(mask); ev = np.sort(np.linalg.eigvalsh(np.cov(np.vstack([xs, ys])))); a, b = 2 * math.sqrt(ev[1]), 2 * math.sqrt(ev[0])          # semi-axes of the equivalent ellipse
    else:
        cs, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); c = max(cs, key=len)
        if len(c) < 5: return None
        (_, _), (w, h), _ = cv2.fitEllipse(c); a, b = w / 2, h / 2
    return ramanujan(max(a, b), min(a, b)) * pixel_mm

def hc_from_ring(ring, pixel_mm):
    pts = np.argwhere(ring)[:, ::-1].astype(np.float32)
    if len(pts) < 5: return None
    (_, _), (w, h), _ = cv2.fitEllipse(pts); return ramanujan(max(w, h) / 2, min(w, h) / 2) * pixel_mm

def hc18_annotation(sp):
    """29b-1: ring annotation -> filled -> ellipse -> HC, against the provided HC (mm). Method chosen on DEV + VAL only."""
    root = unified.find('archive-7'); recs = {c['case_id']: c for c in unified.load('HC18')}; out = []
    for cid, rec in recs.items():
        p = os.path.join(root, 'training_set', cid.split(':', 1)[1] + '_Annotation.png')
        if not os.path.exists(p): continue
        ring = unified.load_mask(p); filled = ndimage.binary_fill_holes(ring); px = rec['pixel_mm']; lab = rec['labels']['hc_mm']
        e = dict(case_id=cid, split=sp.get(cid, {}).get('split'), label=lab, pixel_mm=px)
        for m, v in (('moments_filled', hc_from_mask(filled, px, 'moments')), ('fit_filled_contour', hc_from_mask(filled, px, 'fit')), ('fit_ring_points', hc_from_ring(ring, px))): e[m] = v
        out.append(e)
    return out

def run_annotation():
    sp = G.split_rows(); rows = hc18_annotation(sp); meth = ['moments_filled', 'fit_filled_contour', 'fit_ring_points']; res = {'n': len(rows)}
    for grp, sel in (('devval', ('dev', 'val')), ('test', ('test',)), ('all', ('dev', 'val', 'test'))):
        R = [r for r in rows if r['split'] in sel]; res[grp] = {m: dict(n=len(R), mae_mm=float(np.mean([abs(r[m] - r['label']) for r in R if r[m] is not None])), median_abs_mm=float(np.median([abs(r[m] - r['label']) for r in R if r[m] is not None])), signed_mean_mm=float(np.mean([r[m] - r['label'] for r in R if r[m] is not None])), max_abs_mm=float(max(abs(r[m] - r['label']) for r in R if r[m] is not None))) for m in meth}
    best = min(meth, key=lambda m: res['devval'][m]['mae_mm']); res['chosen_on_devval'] = best; json.dump(dict(res, rows=rows), open(os.path.join(OUT, 'b_annotation.json'), 'w')); print(json.dumps({k: v for k, v in res.items() if k != 'rows'}, indent=1)); return res

PLANT_SHIFT = (-40.0, -1.0, 1.0, 40.0); PLANT_FACTOR = (0.5, 0.75, 0.9, 1.1, 1.25, 1.5, 2.0)
def plant_texts(ref_text, hc):
    """planted HC errors on top of the reference text: +-1 mm, +-40 mm, and x0.5 ... x2.0 of the labelled HC (same wording, only the number changes)"""
    out = []
    for kind, lv in [('shift_mm', s) for s in PLANT_SHIFT] + [('factor', f) for f in PLANT_FACTOR]:
        new = hc + lv if kind == 'shift_mm' else hc * lv
        if new <= 0: continue
        out.append(dict(kind=kind, level=lv, text=ref_text.replace(f'{hc:g} mm', f'{new:.1f} mm') if f'{hc:g} mm' in ref_text else None))
    return [o for o in out if o['text']]

def run_29b(dev, chosen_method):
    ann = json.load(open(os.path.join(OUT, 'b_annotation.json'))); corr = -ann['devval']['fit_filled_contour']['signed_mean_mm']       # dev+val calibration of the filled-contour ellipse (ring thickness bias), applied to predicted masks
    sp = G.split_rows(); recs = {c['case_id']: c for c in unified.load('HC18')}; test_ids = [c for c in recs if sp.get(c, {}).get('split') == 'test']; model, chz = load_net('hc18', dev); root = unified.find('archive-7'); rows = []; t0 = time.time()
    for i, cid in enumerate(test_ids):
        rec = recs[cid]; img = Image.open(partb.img_path(rec)).convert('L'); pm = predict_mask(model, dev, img, chz['threshold'], 'largest'); pm = ndimage.binary_fill_holes(pm)
        px = rec['pixel_mm']; lab = rec['labels']['hc_mm']; tm = location.gt_mask(rec); hc0 = hc_from_mask(pm, px, 'fit'); hc = None if hc0 is None else hc0 + corr; hct0 = hc_from_mask(tm, px, 'fit') if tm is not None else None; hct = None if hct0 is None else hct0 + corr
        rows.append(dict(case_id=cid, label=lab, pred_hc=hc, pred_hc_uncorrected=hc0, truemask_hc=hct, found=bool(pm.any()), dice=location.dice(pm, tm) if tm is not None else None, iou=location.mask_iou(pm, tm) if tm is not None else None))
        if i % 100 == 0: print('29b', i, len(test_ids), round(time.time() - t0), 's', flush=True)
    err = [abs(r['pred_hc'] - r['label']) for r in rows if r['pred_hc'] is not None]; res = dict(n_test=len(rows), method='cv2.fitEllipse on the outer contour of the filled mask, plus a constant calibrated on dev+val true masks', correction_mm=corr, annotation_method_chosen=chosen_method, mae_uncorrected_mm=float(np.mean([abs(r['pred_hc_uncorrected'] - r['label']) for r in rows if r['pred_hc_uncorrected'] is not None])), found=sum(r['found'] for r in rows), mae_mm=float(np.mean(err)), median_abs_mm=float(np.median(err)), p90_abs_mm=float(np.percentile(err, 90)),
        mae_truemask_geometry_mm=float(np.mean([abs(r['truemask_hc'] - r['label']) for r in rows if r['truemask_hc'] is not None])), mean_dice=float(np.mean([r['dice'] for r in rows if r['dice'] is not None])), mean_iou=float(np.mean([r['iou'] for r in rows if r['iou'] is not None])))
    # planted HC errors on the bench test cases of HC18 (150), harmless = the case's template rewordings
    ch = json.load(open(os.path.join(ROOT, 'results', 'partA', 'step20_tolerance_image_check', 'tuning_devval.json')))['chosen']; tau, pm_ = ch['tau'], ch['position']; by = {r['case_id']: r for r in rows}; bench = collections.defaultdict(list)
    for l in open(os.path.join(ROOT, 'bench_test_v2d.jsonl')):
        r = json.loads(l)
        if r['dataset'] == 'HC18': bench[r['case_id']].append(r)
    per = []
    for cid, bs in bench.items():
        if cid not in by: continue
        ref = bs[0]['reference']; lab = by[cid]['label']; H = [b['candidate'] for b in bs if b['kind'] == 'harmless']; I = [b['candidate'] for b in bs if b['kind'] == 'identical']; P = plant_texts(ref, lab); E_bench = [b['candidate'] for b in bs if b['kind'] == 'error' and b['field'] == 'hc_mm']
        d = dict(case_id=cid, group=cid, organ='fetal')
        for src, hcv in (('unet', by[cid]['pred_hc']), ('true_mask_geometry', by[cid]['truemask_hc']), ('label_oracle', lab)):
            if hcv is None: meas = {'lesion': 'absent'}
            else: meas = {'hc_mm': round(hcv, 1)}
            for var, (t, p) in (('tol', (tau, pm_)), ('exact', (0.0, 'exact'))):
                f = lambda tx, t=t, p=p: step20.tol_score(tx, 'fetal', meas, t, p); h = [f(x) for x in H]
                d[f'{src}|{var}|bench_errors'] = auroc_case([f(x) for x in E_bench], h) if E_bench and h else None
                d[f'{src}|{var}|planted'] = auroc_case([f(p_['text']) for p_ in P], h) if P and h else None
                for kind in ('shift_mm', 'factor'):
                    sub = [f(p_['text']) for p_ in P if p_['kind'] == kind]; d[f'{src}|{var}|planted_{kind}'] = auroc_case(sub, h) if sub and h else None
                for p_ in P: d[f'{src}|{var}|lvl|{p_["kind"]}|{p_["level"]:g}'] = auroc_case([f(p_['text'])], h) if h else None
                d[f'{src}|{var}|correct'] = float(np.mean([f(x) for x in I])) if I else None
        per.append(d)
    json.dump(dict(summary=res, rows=rows, per_case=per, tau=tau, position=pm_, chosen=chz), open(os.path.join(OUT, 'b_rows.json'), 'w')); print(json.dumps(res, indent=1)); return res

def main():
    import torch
    dev = 'mps' if torch.backends.mps.is_available() else 'cpu'
    if sys.argv[1] == 'annotation': run_annotation(); return
    ann = json.load(open(os.path.join(OUT, 'b_annotation.json')))['chosen_on_devval']
    splits.load('test', script='usmeta.step29_run')                       # one logged read of the test split for the whole run
    run_29a(dev); run_29b(dev, ann)

if __name__ == '__main__': main()
