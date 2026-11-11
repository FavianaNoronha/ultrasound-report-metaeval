"""Step 31: cross-dataset segmenter, breast only, leave-one-dataset-out. NEW file; step29_seg.py (train, same settings and leak filter), step29_run.py (scan_scores, predict_mask) and the Step 20 check are imported unchanged.
For each held-out dataset H in {BrEaST, BUS-BRA, BUSI, UDIAT, BUS-UCLM}: train the Step 29 U-Net on the DEV images of the other four (dev images in <= 8-bit clusters reaching val or test dropped), early stopping and post-processing chosen on the VAL images of the same four,
then run the Step 20 tolerance-aware image check on H's Step 29 test scans (no image of H is used for training or tuning). One test read, logged.
    python3 -m usmeta.step31_cross_dataset train [--max-hours 1] | test"""
import os, sys, json, time, collections, functools, argparse
import numpy as np
from PIL import Image
from . import partb, schema, location, step20, splits, step24_box_reliability as s24, step29_seg as G, step29_run as R29

ROOT = G.ROOT; OUT = os.path.join(ROOT, 'results', 'partA', 'step31_cross_dataset'); BREAST = ['BrEaST', 'BUS-BRA', 'BUSI', 'UDIAT', 'BUS-UCLM']

def name_of(h): return 'breast_loo_' + h.replace('-', '')

def train_fold(h, max_hours):
    n = name_of(h); G.DS[n] = [d for d in BREAST if d != h]; old = G.OUT; G.OUT = OUT; os.makedirs(OUT, exist_ok=True)       # same train() as Step 29, only the dataset list and the output folder differ
    try: G.train(n, max_hours=max_hours)
    finally: G.OUT = old
    t = json.load(open(os.path.join(OUT, f'train_{n}.json'))); t['held_out'] = h; t['train_datasets'] = G.DS[n]; json.dump(t, open(os.path.join(OUT, f'train_{n}.json'), 'w'), indent=1)

def run_train(a):
    for h in BREAST:
        if os.path.exists(os.path.join(OUT, f'train_{name_of(h)}.json')) and not a.force: continue
        t0 = time.time(); train_fold(h, a.max_hours); print('fold', h, 'done', round(time.time() - t0), 's', flush=True)

def load_fold(h, dev):
    import torch
    n = name_of(h); m = G.build_model().to(dev); m.load_state_dict(torch.load(os.path.join(G.LOCAL, f'unet_{n}.pt'), map_location=dev)); return m.eval(), json.load(open(os.path.join(OUT, f'train_{n}.json')))['chosen']

def run_test():
    import torch
    dev = 'mps' if torch.backends.mps.is_available() else 'cpu'; splits.load('test', script='usmeta.step31_cross_dataset')            # one logged read of the test split
    ch = json.load(open(os.path.join(ROOT, 'results', 'partA', 'step20_tolerance_image_check', 'tuning_devval.json')))['chosen']; tau, pm_ = ch['tau'], ch['position']
    schema.extract_rule = functools.lru_cache(maxsize=None)(schema.extract_rule)
    sel = [s for s in s24.selection() if s['dataset'] in BREAST]; ids = {s['case_id'] for s in sel}; recs = R29.step20.recs_all(); bench = collections.defaultdict(list)
    for l in open(os.path.join(ROOT, 'bench_v2d.jsonl')):
        r = json.loads(l)
        if r['case_id'] in ids: bench[r['case_id']].append(r)
    nets = {h: load_fold(h, dev) for h in BREAST}; md = os.path.join(G.LOCAL, 'masks_loo'); os.makedirs(md, exist_ok=True); rows = []; t0 = time.time()
    for i, s in enumerate(sel):
        cid = s['case_id']; h = s['dataset']; rec = recs[cid]; tm = partb.true_mask(rec); tgt = partb.largest(tm); H, W = tm.shape; model, chz = nets[h]; img = Image.open(partb.img_path(rec)).convert('L')
        if img.size != (W, H): continue
        pm = R29.predict_mask(model, dev, img, chz['threshold'], chz['keep']); np.savez_compressed(os.path.join(md, cid.replace(':', '_').replace('/', '_') + '.npz'), mask=np.packbits(pm), shape=np.array([H, W]))
        meas = partb.pred_meas(rec, pm); ref = partb.ref_meas(rec, tm); d = dict(case_id=cid, dataset=h, organ='breast', group=s['group_id'], found=bool(pm.any()), iou=location.mask_iou(pm, tgt), dice=location.dice(pm, tgt), pos_agree=float(meas.get('pos') == ref.get('pos')) if meas.get('pos') else 0.0)
        for k in ('size_mm', 'size_pct'):
            if ref.get(k) and isinstance(meas.get(k), (int, float)): d['size_ratio'] = meas[k] / ref[k]; break
        d.update(R29.scan_scores(bench[cid], meas, tau, pm_)); rows.append(d)
        if i % 30 == 0: print('test', i, len(sel), round(time.time() - t0), 's', flush=True)
    json.dump(dict(tau=tau, position=pm_, rows=rows, chosen={h: nets[h][1] for h in nets}), open(os.path.join(OUT, 'rows.json'), 'w')); print('saved rows.json', len(rows))

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd'); ap.add_argument('--max-hours', type=float, default=1.0); ap.add_argument('--force', action='store_true'); a = ap.parse_args()
    {'train': run_train, 'test': lambda a: run_test()}[a.cmd](a)
