"""Step 41: cross-dataset U-Net image check, thyroid (TN3K <-> DDTI). NEW file; mirrors step31_cross_dataset.py. step29_seg.py (training, same settings and leak filter), step29_run.py (scan_scores, predict_mask) and the Step 20 check are imported unchanged.
Fold A: train on TN3K dev -> test on the DDTI test scans; fold B: train on DDTI dev -> test on the TN3K test scans. Early stopping and post-processing chosen on the VAL images of the TRAINING dataset only; no image of the held-out dataset is used for training or tuning. One test read, logged.
Pre-registration: results/partA/step41_thyroid_cross/PREREG.md.
    python3 -m usmeta.step41_thyroid_cross train [--max-hours 1] | test"""
import os, sys, json, time, collections, functools, argparse
import numpy as np
from PIL import Image
from . import partb, schema, location, step20, splits, step24_box_reliability as s24, step29_seg as G, step29_run as R29

ROOT = G.ROOT; OUT = os.path.join(ROOT, 'results', 'partA', 'step41_thyroid_cross'); LOCAL = os.path.join(ROOT, 'local_data', 'step41'); THY = ['TN3K', 'DDTI']
def other(h): return [d for d in THY if d != h][0]                       # the training dataset of the fold whose held-out dataset is h
def name_of(h): return 'thyroid_train_' + other(h)                       # model trained on the other dataset, tested on h

def train_fold(train_ds, max_hours):
    n = 'thyroid_train_' + train_ds; G.DS[n] = [train_ds]; old = G.OUT; G.OUT = OUT; os.makedirs(OUT, exist_ok=True)       # same train() as Step 29; only the dataset list and the output folder differ
    try: G.train(n, max_hours=max_hours)
    finally: G.OUT = old
    t = json.load(open(os.path.join(OUT, f'train_{n}.json'))); t['train_dataset'] = train_ds; t['held_out'] = other(train_ds); t['max_hours'] = max_hours; json.dump(t, open(os.path.join(OUT, f'train_{n}.json'), 'w'), indent=1)

def run_train(a):
    for ds in THY:
        if os.path.exists(os.path.join(OUT, f'train_thyroid_train_{ds}.json')) and not a.force: continue
        t0 = time.time(); train_fold(ds, a.max_hours); print('fold: train on', ds, 'done', round(time.time() - t0), 's', flush=True)

def load_fold(h, dev):
    import torch
    n = name_of(h); m = G.build_model().to(dev); m.load_state_dict(torch.load(os.path.join(G.LOCAL, f'unet_{n}.pt'), map_location=dev)); return m.eval(), json.load(open(os.path.join(OUT, f'train_{n}.json')))['chosen']

def run_test():
    import torch
    dev = 'mps' if torch.backends.mps.is_available() else 'cpu'; sp = G.split_rows(); splits.load('test', script='usmeta.step41_thyroid_cross')           # one logged read of the test split
    ch = json.load(open(os.path.join(ROOT, 'results', 'partA', 'step20_tolerance_image_check', 'tuning_devval.json')))['chosen']; tau, pm_ = ch['tau'], ch['position']
    schema.extract_rule = functools.lru_cache(maxsize=None)(schema.extract_rule)
    sel = [s for s in s24.selection() if s['dataset'] in THY]; assert len(sel) == 60 and all(sp[s['case_id']]['split'] == 'test' for s in sel), 'not the 60 Step 29 thyroid test scans'
    ids = {s['case_id'] for s in sel}; recs = R29.step20.recs_all(); bench = collections.defaultdict(list)
    for l in open(os.path.join(ROOT, 'bench_v2d.jsonl')):
        r = json.loads(l)
        if r['case_id'] in ids: bench[r['case_id']].append(r)
    nets = {h: load_fold(h, dev) for h in THY}; md = os.path.join(LOCAL, 'masks'); os.makedirs(md, exist_ok=True); rows = []; t0 = time.time()
    for i, s in enumerate(sel):
        cid = s['case_id']; h = s['dataset']; rec = recs[cid]; tm = partb.true_mask(rec); tgt = partb.largest(tm); H, W = tm.shape; model, chz = nets[h]; img = Image.open(partb.img_path(rec)).convert('L')
        if img.size != (W, H): continue
        pm = R29.predict_mask(model, dev, img, chz['threshold'], chz['keep']); np.savez_compressed(os.path.join(md, cid.replace(':', '_').replace('/', '_') + '.npz'), mask=np.packbits(pm), shape=np.array([H, W]))
        meas = partb.pred_meas(rec, pm); ref = partb.ref_meas(rec, tm); d = dict(case_id=cid, dataset=h, trained_on=other(h), organ='thyroid', group=s['group_id'], found=bool(pm.any()), iou=location.mask_iou(pm, tgt), dice=location.dice(pm, tgt), pos_agree=float(meas.get('pos') == ref.get('pos')) if meas.get('pos') else 0.0)
        for k in ('size_mm', 'size_pct'):
            if ref.get(k) and isinstance(meas.get(k), (int, float)): d['size_ratio'] = meas[k] / ref[k]; break
        d.update(R29.scan_scores(bench[cid], meas, tau, pm_)); rows.append(d)
        if i % 15 == 0: print('test', i, len(sel), round(time.time() - t0), 's', flush=True)
    json.dump(dict(tau=tau, position=pm_, rows=rows, chosen={h: nets[h][1] for h in nets}), open(os.path.join(OUT, 'rows.json'), 'w')); print('saved rows.json', len(rows))

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd'); ap.add_argument('--max-hours', type=float, default=1.0); ap.add_argument('--force', action='store_true'); a = ap.parse_args()
    {'train': run_train, 'test': lambda a: run_test()}[a.cmd](a)
