"""Step 38: responsible-AI checks on the Step 29 label-free U-Net image check (no retraining; the saved Step 29 models, masks and per-scan results are reused; the 228 test scans are the ones of Steps 21a / 24 / 29,
read through their logged test reads: this step makes no new `splits.load('test')` call and trains nothing).
 (a) per-dataset gap table (+ the metadata that exists in the dataset files, names of columns only and, for BUS-BRA, counts per anonymised scanner code);
 (b) risk-coverage: abstain when the U-Net mask is empty or its mean foreground probability (mean probability of the pixels above the model's own threshold, at the 256 x 256 model resolution) is below a threshold chosen on VAL only;
 (c) robustness: Gaussian noise, blur, JPEG, brightness / gamma shift at three strengths each on the 228 scans.
    python3 -m usmeta.step38_responsible_ai a | b | c"""
import os, sys, json, math, io, zlib, collections, functools, time, argparse
import numpy as np
from PIL import Image, ImageFilter
from . import partb, schema, location, step20, step24_box_reliability as s24, step29_seg as G, step29_run as R29
from .layer0 import auroc_case
from .step10d_analysis import gboot

ROOT = G.ROOT; OUT = os.path.join(ROOT, 'results', 'partA', 'step38_responsible_ai'); A29 = os.path.join(G.OUT, 'a_rows.json'); MIN_G = 30; HOME = os.path.expanduser('~/Downloads')
SD = {'BrEaST': 'breast', 'BUS-BRA': 'breast', 'BUSI': 'breast', 'UDIAT': 'breast', 'BUS-UCLM': 'breast', 'TN3K': 'thyroid', 'TN5000': 'thyroid', 'DDTI': 'thyroid'}
CORR = {'noise': [('sigma 10', 10), ('sigma 25', 25), ('sigma 50', 50)], 'blur': [('radius 1 px', 1), ('radius 2 px', 2), ('radius 4 px', 4)], 'jpeg': [('quality 50', 50), ('quality 20', 20), ('quality 5', 5)],
        'brightness_gamma': [('gamma 0.85, +10', (0.85, 10)), ('gamma 0.70, +25', (0.70, 25)), ('gamma 0.55, +45', (0.55, 45))]}

def ctx(dev):
    ch = json.load(open(os.path.join(ROOT, 'results', 'partA', 'step20_tolerance_image_check', 'tuning_devval.json')))['chosen']; schema.extract_rule = functools.lru_cache(maxsize=None)(schema.extract_rule)
    sel = s24.selection(); ids = {s['case_id'] for s in sel}; recs = R29.step20.recs_all(); bench = collections.defaultdict(list)
    for l in open(os.path.join(ROOT, 'bench_v2d.jsonl')):
        r = json.loads(l)
        if r['case_id'] in ids: bench[r['case_id']].append(r)
    nets = {o: R29.load_net(o, dev) for o in ('breast', 'thyroid')}; return dict(tau=ch['tau'], pm=ch['position'], sel=sel, recs=recs, bench=bench, nets=nets)

def corrupt(img, kind, par, key):
    """img: grayscale PIL; deterministic corruption"""
    if kind == 'noise':
        rng = np.random.default_rng(zlib.crc32(f'{key}|noise|{par}'.encode())); a = np.asarray(img, float) + rng.normal(0, par, (img.size[1], img.size[0])); return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    if kind == 'blur': return img.filter(ImageFilter.GaussianBlur(par))
    if kind == 'jpeg':
        b = io.BytesIO(); img.save(b, 'JPEG', quality=par); b.seek(0); return Image.open(b).convert('L')
    g, off = par; a = 255 * (np.asarray(img, float) / 255) ** g + off; return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def conf_of(model, dev, img, th):
    """256 x 256 probability map: confidence = mean probability of the pixels above the model's own threshold (0 if none)"""
    x = np.asarray(img.resize((G.S, G.S), Image.BILINEAR))[None]; p = G.predict_batch(model, x, dev)[0]; m = p > th; return float(p[m].mean()) if m.any() else 0.0

def pos_ok(meas, ref):
    a, b = meas.get('pos'), ref.get('pos')
    if a is None or b is None: return False
    return str(a) == str(b) or step20.pos_adjacent(str(a), str(b))

def scan_row(cx, s, rec, pm, tm, tgt):
    meas = partb.pred_meas(rec, pm); ref = partb.ref_meas(rec, tm); d = dict(case_id=s['case_id'], dataset=s['dataset'], organ=SD[s['dataset']], group=s['group_id'], found=bool(pm.any()), pos_ok=bool(pos_ok(meas, ref)), has_true_mask=bool(s['has_true_mask']))
    if s['has_true_mask']: d['dice'] = location.dice(pm, tgt); d['iou'] = location.mask_iou(pm, tgt)
    d.update(R29.scan_scores(cx['bench'][s['case_id']], meas, cx['tau'], cx['pm'])); return d

def agg(rows, key):
    v = [(r[key], r['group']) for r in rows if r.get(key) is not None]
    if not v: return None, 0
    return gboot([x for x, _ in v], [y for _, y in v]), len({y for _, y in v})

# ---------------------------------------------------------------- (a)
def cmd_a(a):
    os.makedirs(OUT, exist_ok=True); A = json.load(open(A29)); R = A['rows']; res = {'datasets': {}, 'organs': {}}
    def block(rows):
        d = {}
        for k, nm in (('dice', 'dice'), ('iou', 'iou'), ('auc_tol_position', 'position_auroc'), ('auc_tol_size', 'size_auroc'), ('auc_tol_all', 'all_auroc'), ('correct_tol', 'correct_report')):
            g, n = agg(rows, k); d[nm] = dict(value=g, groups=n, too_small=n < MIN_G)
        g, n = agg([dict(r, f=float(r['found'])) for r in rows], 'f'); d['detection'] = dict(value=g, groups=n, too_small=n < MIN_G); d['scans'] = len(rows); return d
    for ds in SD: res['datasets'][ds] = block([r for r in R if r['dataset'] == ds])
    for o in ('breast', 'thyroid'): res['organs'][o] = block([r for r in R if r['organ'] == o])
    res['pooled'] = block(R)
    # metadata that exists in the dataset files (column names only; no licensed text is copied)
    import pandas as pd
    bb = pd.read_csv(os.path.join(HOME, 'archive-5/BUSBRA/BUSBRA/bus_data.csv')); codes = {v: f'D{i + 1}' for i, v in enumerate(bb['Device'].value_counts().index)}
    dev_of = {f"BUS-BRA:{i}": codes[d] for i, d in zip(bb['ID'], bb['Device'])}
    res['metadata'] = {'BUS-BRA': 'bus_data.csv has a `Device` column with %d distinct values over %d images (counts %s); used below as anonymised codes D1-D%d (names not copied)' % (bb['Device'].nunique(), len(bb), sorted(bb['Device'].value_counts().tolist(), reverse=True), bb['Device'].nunique()),
                       'BrEaST': 'clinical spreadsheet has `Pixel_size` (acquisition resolution) but no device / scanner column', 'UDIAT': 'DatasetB.xlsx: Image, Type, Diagnosis, legend columns only; no scanner field', 'BUS-UCLM': 'INFO.csv: Image;Resolution;Label (image resolution only); no scanner field',
                       'BUSI': 'no table of metadata in the folder', 'TN3K': 'no metadata table', 'TN5000': 'Pascal-VOC XML (filename, size, bounding box; generic folder / database / owner fields); no scanner field', 'DDTI': 'XML with age, sex, TI-RADS, composition, echogenicity, margins, calcifications; no scanner field',
                       'HC18': 'CSV with pixel size (mm) and head circumference only', 'conclusion': 'Scanner / device identity exists in the files of ONE dataset (BUS-BRA); all other datasets have no scanner or acquisition-protocol field (BrEaST, BUS-UCLM, HC18 give pixel size / resolution only). No scanner was inferred for any other dataset.'}
    per = collections.defaultdict(list)
    for r in R:
        if r['dataset'] == 'BUS-BRA': per[dev_of.get(r['case_id'])].append(r)
    res['bus_bra_by_scanner_code'] = {k: block(v) for k, v in sorted(per.items(), key=lambda x: str(x[0]))}; res['bus_bra_device_counts_all_images'] = {codes[k]: int(v) for k, v in bb['Device'].value_counts().items()}
    json.dump(res, open(os.path.join(OUT, 'a_results.json'), 'w'), indent=1); print('saved a_results.json')

# ---------------------------------------------------------------- (b)
def cmd_b(a):
    import torch
    dev = 'mps' if torch.backends.mps.is_available() else 'cpu'; cx = ctx(dev); sp = G.split_rows(); out = {'val_conf': {}, 'thresholds': {}}; t0 = time.time()
    for o in ('breast', 'thyroid'):          # VAL: confidence of every val image with a mask (no label is used for the threshold)
        recs = G.organ_records(o); val = [c for c in recs if sp.get(c, {}).get('split') == 'val']; X, M, ids = G.preload(val, recs); model, ch = cx['nets'][o]; P = G.predict_batch(model, X, dev); conf = [float(p[p > ch['threshold']].mean()) if (p > ch['threshold']).any() else 0.0 for p in P]
        out['val_conf'][o] = dict(n=len(conf), quantiles={str(q): float(np.percentile(conf, q)) for q in (5, 10, 20, 40, 50, 80)}, empty_share=float(np.mean([c == 0 for c in conf])))
        out['thresholds'][o] = {'cov80': float(np.percentile(conf, 20)), 'cov60': float(np.percentile(conf, 40))}; print(o, 'val', len(conf), out['thresholds'][o], round(time.time() - t0), 's', flush=True)
    md = os.path.join(G.LOCAL, 'masks'); rows = []
    for s in cx['sel']:
        cid = s['case_id']; o = SD[s['dataset']]; rec = cx['recs'][cid]; tm = partb.true_mask(rec); tgt = partb.largest(tm); model, ch = cx['nets'][o]; img = Image.open(partb.img_path(rec)).convert('L')
        z = np.load(os.path.join(md, cid.replace(':', '_').replace('/', '_') + '.npz')); H, W = map(int, z['shape']); pm = np.unpackbits(z['mask'])[:H * W].reshape(H, W).astype(bool)         # the SAVED Step 29 mask
        meas = partb.pred_meas(rec, pm); ref = partb.ref_meas(rec, tm); c = conf_of(model, dev, img, ch['threshold'])
        rows.append(dict(case_id=cid, dataset=s['dataset'], organ=o, group=s['group_id'], conf=c, found=bool(pm.any()), pos_error=float(not pos_ok(meas, ref)), dice_error=(float(location.dice(pm, tgt) < 0.5) if s['has_true_mask'] else None)))
    A = {r['case_id']: r for r in json.load(open(A29))['rows']}
    for r in rows: r['auc_tol_position'] = A[r['case_id']]['auc_tol_position']; r['auc_tol_all'] = A[r['case_id']]['auc_tol_all']
    out['rows'] = rows; json.dump(out, open(os.path.join(OUT, 'b_rows.json'), 'w')); print('saved b_rows.json', len(rows))

def curves(rows, rng):
    """risk-coverage: rank scans by confidence within each organ (conf scales differ), pooled coverage c = share kept from the top of each organ's ranking; error rate of the kept scans; random-abstention baseline"""
    res = {}; n = len(rows)
    for tag, key in (('position_error', 'pos_error'), ('dice_below_0.5', 'dice_error')):
        R = [r for r in rows if r.get(key) is not None]; cov = np.linspace(1.0, 0.3, 15); pts = []
        for c in cov:
            kept = []
            for o in ('breast', 'thyroid'):
                ro = sorted([r for r in R if r['organ'] == o], key=lambda r: -r['conf']); kept += ro[:max(1, int(round(c * len(ro))))]
            pts.append((float(c), float(np.mean([r[key] for r in kept])), len(kept)))
        base = float(np.mean([r[key] for r in R])); rand = []
        for c in cov:
            m = max(1, int(round(c * len(R)))); rand.append(float(np.mean([np.mean([R[i][key] for i in rng.choice(len(R), m, replace=False)]) for _ in range(200)])))
        res[tag] = dict(points=pts, random_baseline=rand, overall_error=base, n=len(R))
    return res

def cmd_b_report(a):
    D = json.load(open(os.path.join(OUT, 'b_rows.json'))); rows = D['rows']; rng = np.random.default_rng(0); res = dict(curves=curves(rows, rng), val=D['val_conf'], thresholds=D['thresholds'])
    def stats(sub):
        e = [(r['pos_error'], r['group']) for r in sub]; auc = [(r['auc_tol_position'], r['group']) for r in sub if r['auc_tol_position'] is not None]
        return dict(scans=len(sub), groups=len({r['group'] for r in sub}), coverage=len(sub) / len(rows), error_rate=gboot([x for x, _ in e], [y for _, y in e]) if e else None, position_auroc=(gboot([x for x, _ in auc], [y for _, y in auc]) if auc else None), too_small=len({r['group'] for r in sub}) < MIN_G,
                    dice_mean=(float(np.mean([r.get('dice') for r in sub if r.get('dice') is not None])) if any(r.get('dice') is not None for r in sub) else None))
    A = {r['case_id']: r for r in json.load(open(A29))['rows']}
    for r in rows: r['dice'] = A[r['case_id']].get('dice')
    ops = {'100% (no abstention)': rows}
    for nm, tk in (('val-chosen threshold for 80% val coverage', 'cov80'), ('val-chosen threshold for 60% val coverage', 'cov60')): ops[nm] = [r for r in rows if r['found'] and r['conf'] >= D['thresholds'][r['organ']][tk]]
    res['operating_points'] = {k: stats(v) for k, v in ops.items()}
    exact = {}                                          # exact rank-based coverage (per organ ranking), for the AUROC at 100 / 80 / 60%
    rng2 = np.random.default_rng(0)
    for c in (1.0, 0.8, 0.6):
        kept = []
        for o in ('breast', 'thyroid'):
            ro = sorted([r for r in rows if r['organ'] == o], key=lambda r: -r['conf']); kept += ro[:int(round(c * len(ro)))]
        st = stats(kept); rands = []
        for _ in range(300):
            idx = rng2.choice(len(rows), len(kept), replace=False); v = [rows[i]['auc_tol_position'] for i in idx if rows[i]['auc_tol_position'] is not None]; rands.append(float(np.mean(v)))
        st['random_abstention_position_auroc'] = float(np.mean(rands)); st['random_abstention_error'] = float(np.mean([np.mean([rows[i]['pos_error'] for i in rng2.choice(len(rows), len(kept), replace=False)]) for _ in range(300)])); exact[f'{int(c * 100)}%'] = st
    res['exact_coverage'] = exact; json.dump(res, open(os.path.join(OUT, 'b_results.json'), 'w'), indent=1); print({k: (round(v['error_rate'][0], 3), round(v['position_auroc'][0], 3)) for k, v in exact.items()})
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.2))
    for ax, (tag, nm) in zip(axs, (('position_error', 'position check wrong (tolerance rule) or empty mask'), ('dice_below_0.5', 'Dice < 0.5 (scans with a true mask)'))):
        c = res['curves'][tag]; cov = [p[0] for p in c['points']]; ax.plot(cov, [p[1] for p in c['points']], 'o-', label='abstain on low confidence'); ax.plot(cov, c['random_baseline'], 's--', color='gray', label='random abstention (mean of 200)'); ax.set_xlim(1.02, 0.28); ax.set_xlabel('coverage (share of the 228 scans kept)'); ax.set_ylabel('error rate of the kept scans'); ax.set_title(nm, fontsize=9); ax.grid(alpha=0.3); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, 'risk_coverage.png'), dpi=130); plt.close(fig)

# ---------------------------------------------------------------- (c)
def cmd_c(a):
    import torch
    dev = 'mps' if torch.backends.mps.is_available() else 'cpu'; cx = ctx(dev); out = {}; t0 = time.time(); settings = [('clean', 'clean', None)] + [(k, nm, p) for k, lst in CORR.items() for nm, p in lst]
    for ki, (kind, nm, par) in enumerate(settings):
        rows = []
        for s in cx['sel']:
            cid = s['case_id']; rec = cx['recs'][cid]; tm = partb.true_mask(rec); tgt = partb.largest(tm); H, W = tm.shape; model, ch = cx['nets'][SD[s['dataset']]]; img = Image.open(partb.img_path(rec)).convert('L')
            if img.size != (W, H): continue
            im = img if kind == 'clean' else corrupt(img, kind, par, cid); pm = R29.predict_mask(model, dev, im, ch['threshold'], ch['keep']); rows.append(scan_row(cx, s, rec, pm, tm, tgt))
        out[f'{kind}|{nm}'] = rows; print(kind, nm, len(rows), round(time.time() - t0), 's', flush=True)
    json.dump(out, open(os.path.join(OUT, 'c_rows.json'), 'w')); print('saved c_rows.json')

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd'); a = ap.parse_args()
    {'a': cmd_a, 'b': cmd_b, 'breport': cmd_b_report, 'c': cmd_c}[a.cmd](a)
