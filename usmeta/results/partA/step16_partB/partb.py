"""Part B (Step 16): the NON-CIRCULAR image check. Layer 3 in Step 8 read sizes and positions from the TRUE masks, the same masks the reference facts came from.
Here a segmenter (MedSAM, wanglab/medsam-vit-base, Apache-2.0) predicts the mask from a box prompt and Layer 3 reads size / position / count / orientation / head circumference
from the PREDICTED mask. Prompts are boxes derived from the TRUE masks (exact, and shifted + enlarged by ~10% and ~20%). Qwen / MedGemma boxes are NOT used as prompts (their IoU is too low).
Test split only (locked, logged), dataset by dataset, at most 3 scans per group.
    python3 -m usmeta.partb select | predict | analyse"""
import os, sys, json, zlib, random, collections, time
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.stats import spearmanr
from . import unified, location, layer3, splits
from .layer0 import auroc_case
from .step10d_analysis import gboot

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..')
LOCAL = os.path.join(ROOT, 'local_data', 'partb'); MASKS = os.path.join(LOCAL, 'masks')       # predicted masks: git-ignored
MODEL = 'wanglab/medsam-vit-base'
DATASETS = ['BrEaST', 'BUS-BRA', 'BUSI', 'UDIAT', 'BUS-UCLM', 'TN3K', 'DDTI', 'HC18', 'FetalHead', 'TN5000']
LOADER = {'BUS-BRA': 'BUSBRA', 'BUS-UCLM': 'BUSUCLM'}
PROMPTS = ('exact', 'j10', 'j20'); FRAC = {'exact': 0.0, 'j10': 0.10, 'j20': 0.20}
PER_GROUP = 3       # at most 3 scans of one patient / exam group (group-level bootstrap handles the clustering)
N_PER = 30          # the plan said ~20; 30 so that the whole-dataset rows reach the n >= 30 rule (cheap: ~1 s per scan)
SEED = 0

def largest(mask):
    lab, n = ndimage.label(mask)
    if n == 0: return mask
    areas = ndimage.sum(mask, lab, range(1, n + 1)); return lab == (int(np.argmax(areas)) + 1)

def box_of(mask):
    ys, xs = np.where(mask); return [float(xs.min()), float(ys.min()), float(xs.max() + 1), float(ys.max() + 1)]

def jitter_box(box, frac, W, H, key):
    """enlarge the box by (1+frac) about its centre, then shift the centre by +-frac/2 of the box size (random signs, seeded by the case id)"""
    if frac == 0: return list(box)
    rng = random.Random(zlib.crc32(f'{key}|{frac}'.encode())); x0, y0, x1, y1 = box; w, h = x1 - x0, y1 - y0; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    cx += rng.choice([-1, 1]) * frac / 2 * w; cy += rng.choice([-1, 1]) * frac / 2 * h; w *= 1 + frac; h *= 1 + frac
    return [max(0.0, cx - w / 2), max(0.0, cy - h / 2), min(float(W), cx + w / 2), min(float(H), cy + h / 2)]

def img_path(rec): return rec['image'].replace(rec['image'].split('/mnt/Downloads')[0] + '/mnt/Downloads', os.path.expanduser('~/Downloads')) if '/mnt/Downloads' in rec['image'] else rec['image']

def true_mask(rec):
    m = location.gt_mask(rec)
    if m is None and rec['region'] and rec['region'].get('kind') == 'box':          # TN5000: boxes only
        m = np.zeros((rec['region']['H'], rec['region']['W']), bool)
        for b in rec['region']['boxes']: m[int(b[1]):int(b[3]), int(b[0]):int(b[2])] = True
    return m

# ---------------------------------------------------------------- select
def select():
    sp = {r['case_id']: r for r in splits.load('test', script='partb.py')}; bench = collections.defaultdict(set)
    for l in open(os.path.join(ROOT, 'bench_v2d.jsonl')):
        r = json.loads(l); bench[r['dataset']].add(r['case_id'])
    out = []; rng = random.Random(SEED)
    for ds in DATASETS:
        recs = {c['case_id']: c for c in unified.load(LOADER.get(ds, ds))}; ids = sorted(c for c in bench[ds] if c in sp and recs.get(c) and recs[c]['region'])
        rng.shuffle(ids); seen = collections.Counter(); pick = []
        for c in ids:
            g = sp[c]['group_id']
            if seen[g] >= PER_GROUP: continue
            m = true_mask(recs[c])
            if m is None or not m.any() or m.shape != (recs[c]['region']['H'], recs[c]['region']['W']): continue
            seen[g] += 1; pick.append(c)
            if len(pick) == N_PER: break
        out += [dict(case_id=c, dataset=ds, group_id=sp[c]['group_id'], has_true_mask=recs[c]['region']['kind'] != 'box') for c in pick]
        print(ds, len(pick), 'of', len(ids), 'candidates (test split, in bench_v2d, lesion + mask)')
    os.makedirs(LOCAL, exist_ok=True); json.dump(out, open(os.path.join(LOCAL, 'selected.json'), 'w'), indent=1); return out

# ---------------------------------------------------------------- predict
def load_model():
    import torch
    from transformers import SamModel, SamProcessor
    dev = 'mps' if torch.backends.mps.is_available() else 'cpu'
    return SamProcessor.from_pretrained(MODEL), SamModel.from_pretrained(MODEL).to(dev).eval(), dev

def segment(P, M, dev, img, box):
    import torch
    inp = P(img, input_boxes=[[list(map(float, box))]], return_tensors='pt'); inp = {k: (v.to(dev, torch.float32) if v.is_floating_point() else v.to(dev)) for k, v in inp.items()}
    with torch.no_grad(): out = M(pixel_values=inp['pixel_values'], input_boxes=inp['input_boxes'], multimask_output=False)
    m = P.image_processor.post_process_masks(out.pred_masks.cpu(), inp['original_sizes'].cpu(), inp['reshaped_input_sizes'].cpu())[0]
    return np.asarray(m[0, 0]).astype(bool)

def mpath(cid, p): return os.path.join(MASKS, cid.replace(':', '_').replace('/', '_') + f'.{p}.npz')

def predict():
    sel = json.load(open(os.path.join(LOCAL, 'selected.json'))); os.makedirs(MASKS, exist_ok=True); P, M, dev = load_model(); print('device', dev); t0 = time.time(); n = 0
    recs = {}
    for ds in DATASETS:
        for c in unified.load(LOADER.get(ds, ds)): recs[c['case_id']] = c
    for s in sel:
        rec = recs[s['case_id']]; tm = true_mask(rec); tgt = largest(tm); box = box_of(tgt); img = Image.open(img_path(rec)).convert('RGB'); H, W = tm.shape
        if img.size != (W, H): raise SystemExit(f'image/mask size mismatch {s["case_id"]}: {img.size} vs {(W, H)}')
        for p in PROMPTS:
            f = mpath(s['case_id'], p)
            if os.path.exists(f): continue
            b = jitter_box(box, FRAC[p], W, H, s['case_id']); np.savez_compressed(f, mask=np.packbits(segment(P, M, dev, img, b)), shape=np.array([H, W]), box=np.array(b)); n += 1
        if n and n % 30 == 0: print(n, 'masks', round(time.time() - t0), 's', flush=True)
    print('done', n, 'new masks', round(time.time() - t0), 's')

def load_pred(cid, p):
    z = np.load(mpath(cid, p)); H, W = map(int, z['shape']); return np.unpackbits(z['mask'])[:H * W].reshape(H, W).astype(bool), list(z['box'])

# ---------------------------------------------------------------- segmenter alone
def hausdorff(a, b):
    if not a.any() or not b.any(): return float('nan'), float('nan')
    ea, eb = a & ~ndimage.binary_erosion(a), b & ~ndimage.binary_erosion(b)
    da, db = ndimage.distance_transform_edt(~eb)[ea], ndimage.distance_transform_edt(~ea)[eb]
    return float(max(da.max(), db.max())), float(max(np.percentile(da, 95), np.percentile(db, 95)))

def contrast(img_gray, mask):
    """|mean inside - mean of a 15 px ring outside| / 255: low = low contrast lesion"""
    ring = ndimage.binary_dilation(mask, iterations=15) & ~ndimage.binary_dilation(mask, iterations=2)
    return float(abs(img_gray[mask].mean() - img_gray[ring].mean()) / 255) if ring.any() else float('nan')

def seg_rows(sel, recs):
    rows = []
    for s in sel:
        rec = recs[s['case_id']]; tm = true_mask(rec); tgt = largest(tm); H, W = tm.shape
        g = np.asarray(Image.open(img_path(rec)).convert('L')).astype(float) if s['has_true_mask'] else None
        for p in PROMPTS:
            pm, box = load_pred(s['case_id'], p); r = dict(case_id=s['case_id'], dataset=s['dataset'], group=s['group_id'], prompt=p, has_true_mask=s['has_true_mask'], area_frac=float(tgt.mean()),
                                                     empty=not pm.any(), contrast=contrast(g, tgt) if g is not None else None)
            r['box_iou_prompt_vs_true_box'] = location.box_iou(box, box_of(tgt))
            if s['has_true_mask']:
                r['iou'] = location.mask_iou(pm, tgt); r['dice'] = location.dice(pm, tgt); hd, hd95 = hausdorff(pm, tgt); diag = float(np.hypot(H, W)); r['hd_pct_diag'] = 100 * hd / diag; r['hd95_pct_diag'] = 100 * hd95 / diag
            else:                                                         # TN5000: boxes only, so the only comparison is the box of the predicted mask vs the true box
                r['box_iou_pred_vs_true_box'] = location.box_iou(box_of(largest(pm)) if pm.any() else [0, 0, 0, 0], box_of(tgt))
            rows.append(r)
        r0 = dict(case_id=s['case_id'], dataset=s['dataset'], group=s['group_id'], prompt='true_vs_true', has_true_mask=s['has_true_mask'])
        if s['has_true_mask']: r0.update(iou=location.mask_iou(tgt, tgt), dice=location.dice(tgt, tgt), hd_pct_diag=0.0, hd95_pct_diag=0.0)
        rows.append(r0)
    return rows

# ---------------------------------------------------------------- Layer 3 with predicted masks
def ref_meas(rec, tm):
    meas, _ = layer3.measured_facts(rec, tm)
    return meas                                    # HC18: hc_mm = the dataset's labelled value (not derived from the mask)

def pred_meas(rec, pm):
    if pm is None or not pm.any(): return {'lesion': 'absent'}
    meas, _ = layer3.measured_facts(rec, pm)
    if rec['dataset'] == 'HC18': meas['hc_mm'] = round(location.hc_error_mm(pm, rec['pixel_mm'], rec['labels']['hc_mm'])[1], 1)
    return meas

SIZE = ('size_mm', 'size_pct', 'hc_mm')
def meas_rows(sel, recs):
    rows = []; M = {}
    for s in sel:
        rec = recs[s['case_id']]; tm = true_mask(rec); ref = ref_meas(rec, tm); M[(s['case_id'], 'true')] = ref
        for p in PROMPTS:
            pm, _ = load_pred(s['case_id'], p); pr = pred_meas(rec, pm); M[(s['case_id'], p)] = pr
            r = dict(case_id=s['case_id'], dataset=s['dataset'], group=s['group_id'], prompt=p, lesion_found=bool(pm.any()))
            for k in SIZE:
                if k in ref and k in pr: r['size_key'] = k; r['size_ref'] = float(ref[k]); r['size_pred'] = float(pr[k]); r['size_abs_err'] = abs(pr[k] - ref[k]); r['size_signed_err'] = pr[k] - ref[k]; r['size_rel_err'] = abs(pr[k] - ref[k]) / ref[k] if ref[k] else None
            for k in ('pos', 'orient', 'count'):
                if k in ref: r[k + '_agree'] = float(pr.get(k) == ref[k])
            rows.append(r)
    return rows, M

def verification(sel, M, recs):
    """mask_verified_facts on the bench_v2d rows of the selected cases: TRUE-mask measurements vs PREDICTED-mask measurements (3 prompts), next to the text scorers"""
    ids = {s['case_id'] for s in sel}; grp = {s['case_id']: s['group_id'] for s in sel}; rows = [json.loads(l) for l in open(os.path.join(ROOT, 'bench_v2d.jsonl'))]; rows = [r for r in rows if r['case_id'] in ids]
    L0 = json.load(open(os.path.join(ROOT, 'scores_v2d_layer0.json'))); idx = {tuple(p): i for i, p in enumerate(L0['pairs'])}; out = []
    for r in rows:
        o = dict(case_id=r['case_id'], dataset=r['dataset'], group=grp[r['case_id']], kind=r['kind'], field=r['field'], hgroup=r['group'], severity=r['severity'], magnitude=r['magnitude'])
        for src in ('true',) + PROMPTS: o['mvf_' + src] = (lambda v: 1.0 if v[0] is None else v[0])(layer3.mask_verified(r['candidate'], r['organ'], M[(r['case_id'], src)]))
        i = idx.get((r['reference'], r['candidate']))
        for n, arr in L0['scores'].items(): o[n] = float(arr[i]) if i is not None else float('nan')
        out.append(o)
    return out

SCORERS = ['mvf_true', 'mvf_exact', 'mvf_j10', 'mvf_j20', 'bleu', 'rougeL', 'chrf', 'bertscore[roberta-large]', 'ratescore']
SUBSETS = {'position errors': lambda f: f == 'pos', 'size errors': lambda f: f in SIZE, 'all mask-checkable errors': lambda f: f in ('lesion', 'count', 'pos', 'orient') + SIZE}

def case_aurocs(V, name, subset, ds=None):
    by = collections.defaultdict(list)
    for o in V:
        if ds == 'LESIONS':
            if o['dataset'] in ('HC18', 'FetalHead'): continue
        elif ds and o['dataset'] != ds: continue
        by[o['case_id']].append(o)
    vals, grs = [], []
    for c, rs in by.items():
        e = [o[name] for o in rs if o['kind'] == 'error' and SUBSETS[subset](o['field'])]; h = [o[name] for o in rs if o['kind'] == 'harmless']
        if e and h: vals.append(auroc_case(e, h)); grs.append(rs[0]['group'])
    return vals, grs

# ---------------------------------------------------------------- analyse + write-up
def fm(x, d=2):
    if x is None: return '—'
    return f'{x[0]:.{d}f} ({x[1]:.{d}f}–{x[2]:.{d}f})' if isinstance(x, tuple) else f'{x:.{d}f}'

def gb(vals_groups):
    v = [a for a, _ in vals_groups if a is not None and a == a]; g = [b for a, b in vals_groups if a is not None and a == a]
    return gboot(v, g) if v else None

def small(n): return ' †' if n < 30 else ''

def analyse():
    sel = json.load(open(os.path.join(LOCAL, 'selected.json'))); recs = {}
    for ds in DATASETS:
        for c in unified.load(LOADER.get(ds, ds)): recs[c['case_id']] = c
    S = seg_rows(sel, recs); MR, M = meas_rows(sel, recs); V = verification(sel, M, recs); res = dict(n_cases={ds: sum(s['dataset'] == ds for s in sel) for ds in DATASETS}); out = []
    ncase = res['n_cases']
    # 1 segmenter alone
    out += ['## 1. The segmenter alone (predicted mask vs TRUE mask, test split)', '', 'Target = the largest connected region of the true mask (the object the box prompt points at). 95% CIs resample patient/exam groups (1,000 resamples, seed 0). † = n < 30: too small to compare.', '',
            '| dataset | n scans | prompt | IoU | Dice | HD95 (% of image diagonal) | empty masks |', '|---|---|---|---|---|---|---|']; res['seg'] = {}
    for ds in DATASETS:
        for p in ('true_vs_true',) + PROMPTS:
            R = [r for r in S if r['dataset'] == ds and r['prompt'] == p]
            if not R: continue
            if not R[0]['has_true_mask']:
                if p == 'true_vs_true': continue
                b = gb([(r['box_iou_pred_vs_true_box'], r['group']) for r in R]); res['seg'][f'{ds}|{p}'] = dict(box_iou=b, n=len(R))
                out.append(f'| {ds}{small(len(R))} | {len(R)} | {p} | box IoU {fm(b)} (no true mask) | — | — | {sum(r["empty"] for r in R)} |'); continue
            iou, dc, hd = gb([(r['iou'], r['group']) for r in R]), gb([(r['dice'], r['group']) for r in R]), gb([(r['hd95_pct_diag'], r['group']) for r in R])
            res['seg'][f'{ds}|{p}'] = dict(iou=iou, dice=dc, hd95=hd, n=len(R)); out.append(f'| {ds}{small(len(R))} | {len(R)} | {p} | {fm(iou)} | {fm(dc)} | {fm(hd, 1)} | {sum(r.get("empty", False) for r in R)} |')
    out += ['', '**All datasets with true masks pooled** (n scans, group bootstrap):', '', '| prompt | n | IoU | Dice | HD95 (% diag) |', '|---|---|---|---|---|']
    for p in ('true_vs_true',) + PROMPTS:
        R = [r for r in S if r['prompt'] == p and r['has_true_mask']]; iou, dc, hd = gb([(r['iou'], r['dataset'] + str(r['group'])) for r in R]), gb([(r['dice'], r['dataset'] + str(r['group'])) for r in R]), gb([(r['hd95_pct_diag'], r['dataset'] + str(r['group'])) for r in R])
        res['seg'][f'ALL|{p}'] = dict(iou=iou, dice=dc, hd95=hd, n=len(R)); out.append(f'| {p} | {len(R)} | {fm(iou)} | {fm(dc)} | {fm(hd, 1)} |')
    # 2 failure analysis (exact prompt, pooled, true masks only)
    E = [r for r in S if r['prompt'] == 'exact' and r['has_true_mask']]; out += ['', '## 2. Where the segmenter fails (exact box prompt, datasets with true masks pooled)', '', '| group | n | mean IoU | share with IoU < 0.5 |', '|---|---|---|---|']; res['fail'] = {}
    for lab, f in (('lesion < 2% of the image', lambda r: r['area_frac'] < 0.02), ('lesion 2–10%', lambda r: 0.02 <= r['area_frac'] < 0.10), ('lesion ≥ 10%', lambda r: r['area_frac'] >= 0.10)):
        R = [r for r in E if f(r)]
        if R: res['fail'][lab] = dict(n=len(R), iou=float(np.mean([r['iou'] for r in R])), low=float(np.mean([r['iou'] < 0.5 for r in R]))); out.append(f"| {lab} | {len(R)} | {np.mean([r['iou'] for r in R]):.2f} | {np.mean([r['iou'] < 0.5 for r in R]):.2f} |")
    C = [r for r in E if r['contrast'] is not None and r['contrast'] == r['contrast']]
    if C:
        q = np.quantile([r['contrast'] for r in C], [1 / 3, 2 / 3])
        for lab, f in (('low contrast (lowest third)', lambda r: r['contrast'] <= q[0]), ('mid contrast', lambda r: q[0] < r['contrast'] <= q[1]), ('high contrast (top third)', lambda r: r['contrast'] > q[1])):
            R = [r for r in C if f(r)]; res['fail'][lab] = dict(n=len(R), iou=float(np.mean([r['iou'] for r in R])), low=float(np.mean([r['iou'] < 0.5 for r in R]))); out.append(f"| {lab} | {len(R)} | {np.mean([r['iou'] for r in R]):.2f} | {np.mean([r['iou'] < 0.5 for r in R]):.2f} |")
        rho1, rho2 = spearmanr([r['area_frac'] for r in E], [r['iou'] for r in E])[0], spearmanr([r['contrast'] for r in C], [r['iou'] for r in C])[0]; res['fail']['spearman'] = dict(area=float(rho1), contrast=float(rho2))
        L = [r for r in E if r['dataset'] not in ('HC18', 'FetalHead')]; LC = [r for r in L if r['contrast'] is not None and r['contrast'] == r['contrast']]
        out += ['', '**Breast and thyroid lesions only** (fetal-head sets removed, because their target is a whole skull outline):', '', '| group | n | mean IoU | share with IoU < 0.5 |', '|---|---|---|---|']
        for lab, f in (('lesion < 2% of the image', lambda r: r['area_frac'] < 0.02), ('lesion 2–10%', lambda r: 0.02 <= r['area_frac'] < 0.10), ('lesion ≥ 10%', lambda r: r['area_frac'] >= 0.10)):
            R = [r for r in L if f(r)]
            if R: out.append(f"| {lab} | {len(R)} | {np.mean([r['iou'] for r in R]):.2f} | {np.mean([r['iou'] < 0.5 for r in R]):.2f} |"); res['fail']['lesions: ' + lab] = dict(n=len(R), iou=float(np.mean([r['iou'] for r in R])))
        q2 = np.quantile([r['contrast'] for r in LC], [1 / 3, 2 / 3])
        for lab, f in (('low contrast (lowest third)', lambda r: r['contrast'] <= q2[0]), ('mid contrast', lambda r: q2[0] < r['contrast'] <= q2[1]), ('high contrast (top third)', lambda r: r['contrast'] > q2[1])):
            R = [r for r in LC if f(r)]; out.append(f"| {lab} | {len(R)} | {np.mean([r['iou'] for r in R]):.2f} | {np.mean([r['iou'] < 0.5 for r in R]):.2f} |"); res['fail']['lesions: ' + lab] = dict(n=len(R), iou=float(np.mean([r['iou'] for r in R])))
        res['fail']['lesions: spearman'] = dict(area=float(spearmanr([r['area_frac'] for r in L], [r['iou'] for r in L])[0]), contrast=float(spearmanr([r['contrast'] for r in LC], [r['iou'] for r in LC])[0]))
        out += ['', f"Breast and thyroid only: Spearman of IoU with lesion size {res['fail']['lesions: spearman']['area']:.2f}, with contrast {res['fail']['lesions: spearman']['contrast']:.2f}."]
        out += ['', f'Spearman of IoU with lesion size {rho1:.2f}, with contrast {rho2:.2f}. Contrast = |mean grey inside − mean grey of a ring outside| / 255.']
    out += ['', 'Per dataset, share of scans with IoU < 0.5 (exact prompt): ' + ', '.join(f"{ds} {np.mean([r['iou'] < 0.5 for r in E if r['dataset'] == ds]):.2f} (n={sum(r['dataset'] == ds for r in E)})" for ds in DATASETS if any(r['dataset'] == ds for r in E)),
            '', 'Ten lowest-IoU scans (exact prompt): ' + '; '.join(f"{r['case_id']} IoU {r['iou']:.2f}, lesion {100 * r['area_frac']:.1f}% of image" for r in sorted(E, key=lambda r: r['iou'])[:10])]
    # 3 measurement error
    out += ['', '## 3. Layer 3 read from the PREDICTED mask: measurement error vs the reference facts', '',
            'Reference facts come from the TRUE masks (HC18: the dataset\'s labelled head circumference). Size unit: mm (BrEaST; fetal head circumference), percent of image width (all others, no pixel size). Agreement = same third-of-image position / orientation word / lesion count. † n < 30.', '',
            '| dataset | prompt | size unit | median abs. size error | median signed error (pred − ref) | median rel. size error | position agrees | orientation agrees | count agrees | lesion found |', '|---|---|---|---|---|---|---|---|---|---|']; res['meas'] = {}
    for ds in DATASETS:
        for p in PROMPTS:
            R = [r for r in MR if r['dataset'] == ds and r['prompt'] == p]
            if not R: continue
            sz = [r for r in R if 'size_abs_err' in r]; unit = {'size_mm': 'mm', 'size_pct': '% width', 'hc_mm': 'mm'}[sz[0]['size_key']] if sz else '—'
            ag = lambda k: gb([(r[k], r['group']) for r in R if k in r]); res['meas'][f'{ds}|{p}'] = dict(n=len(R), size_signed=float(np.median([r['size_signed_err'] for r in sz])) if sz else None, size_abs=float(np.median([r['size_abs_err'] for r in sz])) if sz else None, size_rel=float(np.median([r['size_rel_err'] for r in sz if r['size_rel_err'] is not None])) if sz else None,
                                                                           pos=ag('pos_agree'), orient=ag('orient_agree'), count=ag('count_agree'), found=float(np.mean([r['lesion_found'] for r in R])))
            m = res['meas'][f'{ds}|{p}']; out.append(f"| {ds}{small(len(R))} | {p} | {unit} | {fm(m['size_abs'], 1) if sz else '—'} | {fm(m['size_signed'], 1) if sz else '—'} | {fm(m['size_rel']) if sz else '—'} | {fm(m['pos'])} | {fm(m['orient'])} | {fm(m['count'])} | {m['found']:.2f} |")
    # 4 mask_verified_facts on planted errors
    out += ['', '## 4. mask_verified_facts on planted position / size errors: true masks (circular) vs predicted masks (non-circular) vs text scorers', '',
            'AUROC = chance that the check scores a planted error below a harmless rewording of the same report (per case, group bootstrap). 0.5 = chance. `mvf_true` is the Step 8 check (upper bound, templated, circular); `mvf_exact / j10 / j20` read the PREDICTED mask from the exact / 10%-jittered / 20%-jittered box. † n < 30 cases with such errors: too small to compare.', '']; res['auroc'] = {}
    for sub in SUBSETS:
        out += [f'### {sub}', '', '| dataset | n cases | ' + ' | '.join(SCORERS) + ' |', '|---|---|' + '---|' * len(SCORERS)]
        for ds in DATASETS + ['LESIONS', None]:
            cells = []; n = None
            for nm in SCORERS:
                v, g = case_aurocs(V, nm, sub, ds); n = len(v); a = gboot(v, g) if v else None
                res['auroc'][f'{sub}|{ds or "ALL"}|{nm}'] = dict(n=n, auroc=a); cells.append(fm(a))
            if n: out.append(f"| {'**breast + thyroid pooled (no fetal head)**' if ds == 'LESIONS' else (ds or '**all 10 datasets pooled**')}{small(n)} | {n} | " + ' | '.join(cells) + ' |')
        out.append('')
    out += ['### Identical copies and harmless rewordings (mean score)', '', '| scorer | identical mean | harmless mean |', '|---|---|---|']
    for nm in SCORERS:
        I = [o[nm] for o in V if o['kind'] == 'identical']; H = [o[nm] for o in V if o['kind'] == 'harmless']; res['auroc'][f'means|{nm}'] = dict(identical=float(np.mean(I)), harmless=float(np.mean(H))); out.append(f'| {nm} | {np.mean(I):.3f} | {np.mean(H):.3f} |')
    out += ['', '### Size errors by how big the planted error is (lesion datasets pooled: BrEaST in mm, others in % of image width; ×1.5 = 50% too large, ×0.5 = half, ×2 = double)', '', '| planted size error | n cases | ' + ' | '.join(SCORERS) + ' |', '|---|---|' + '---|' * len(SCORERS)]
    LES = [o for o in V if o['dataset'] not in ('HC18', 'FetalHead')]; res['by_mag'] = {}
    for mag in (1.5, 0.5, 2.0):
        cells = []
        for nm in SCORERS:
            by = collections.defaultdict(list)
            for o in LES: by[o['case_id']].append(o)
            v, g = [], []
            for c, rs in by.items():
                e = [o[nm] for o in rs if o['kind'] == 'error' and o['field'] in SIZE and o['magnitude'] == mag]; h = [o[nm] for o in rs if o['kind'] == 'harmless']
                if e and h: v.append(auroc_case(e, h)); g.append(rs[0]['group'])
            a = gboot(v, g) if v else None; n = len(v); res['by_mag'][f'{mag}|{nm}'] = dict(n=n, auroc=a); cells.append(fm(a))
        out.append(f'| ×{mag} | {n} | ' + ' | '.join(cells) + ' |')
    out += ['', '### What a correct (identical) report scores with the predicted-mask check, per dataset', '', 'A correct report should score 1.0. Any shortfall is a false alarm caused by the segmenter, not by the report.', '', '| dataset | n reports | mean mvf_exact | share scoring 1.0 (exact) | mean mvf_j10 | mean mvf_j20 |', '|---|---|---|---|---|---|']; res['identical'] = {}
    for ds in DATASETS:
        I = [o for o in V if o['kind'] == 'identical' and o['dataset'] == ds]
        if I: res['identical'][ds] = dict(n=len(I), exact=float(np.mean([o['mvf_exact'] for o in I])), full=float(np.mean([o['mvf_exact'] > 0.999 for o in I]))); out.append(f"| {ds}{small(len(I))} | {len(I)} | {np.mean([o['mvf_exact'] for o in I]):.2f} | {np.mean([o['mvf_exact'] > 0.999 for o in I]):.2f} | {np.mean([o['mvf_j10'] for o in I]):.2f} | {np.mean([o['mvf_j20'] for o in I]):.2f} |")
    json.dump(res, open(os.path.join(LOCAL, 'results_aggregates.json'), 'w'), indent=1)
    with open(os.path.join(LOCAL, 'per_case.json'), 'w') as f: json.dump(dict(seg=S, meas=MR), f)
    open(os.path.join(LOCAL, 'tables.md'), 'w').write('\n'.join(out)); print('\n'.join(out)); return res

if __name__ == '__main__':
    {'select': select, 'predict': predict, 'analyse': analyse}.get(sys.argv[1], lambda: None)()
