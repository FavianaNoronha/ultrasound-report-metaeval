"""Step 45, Part G: better image side. NEW file; step29_seg (training, leak filter, early stopping on val), step29_run / step38 / step40 (the Step 20 image check on the same scans) and partb (MedSAM) are imported unchanged.
(1) the Step 29 U-Net with ImageNet-pretrained ResNet-18 encoder weights (torchvision resnet18 IMAGENET1K_V1, `local_data/step45/resnet18-f37072fd.pth`, git-ignored; the first conv is summed over RGB to one channel): same training settings, dev-only training, early stopping and post-processing chosen on val, one model per organ (breast, thyroid);
(2) MedSAM (wanglab/medsam-vit-base, as Step 16) prompted by the box of the pretrained U-Net's mask.
Evaluation: the SAME usable test scans as Step 40 (498), paired per scan against the random-init Step 29 model (Step 40 rows), position AUROC of the Step 20 tolerance-aware image check, group bootstrap 1,000 / seed 0.
PASS rule: pooled position AUROC >= 0.92 and the paired difference CI excludes 0 (thyroid reported separately).
    python3 -m usmeta.step45_partG train [--max-hours 1] | test"""
import os, sys, json, time, hashlib, collections, argparse, platform, subprocess
import numpy as np
from PIL import Image
from . import partb, step29_seg as G, step29_run as R29, step40_fairness_calibration as S40, splits
from .step10d_analysis import gboot

ROOT = G.ROOT; OUT = os.path.join(ROOT, 'results', 'partA', 'step45_improve_scorers', 'partG'); P = lambda f: os.path.join(OUT, f); LOCAL = os.path.join(ROOT, 'local_data', 'step45'); os.makedirs(OUT, exist_ok=True)
_ORIG_BUILD = G.build_model          # the unchanged Step 29 builder (G.build_model is replaced during pretrained training)
WEIGHTS = os.path.join(LOCAL, 'resnet18-f37072fd.pth'); SRC = 'https://download.pytorch.org/models/resnet18-f37072fd.pth'; MIN_G = 30

def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 20), b''): h.update(b)
    return h.hexdigest()

def build_pretrained():
    import torch
    m = _ORIG_BUILD(); sd = torch.load(WEIGHTS, map_location='cpu'); enc = {}
    for k, v in sd.items():
        if k.startswith('fc.'): continue
        if k == 'conv1.weight': v = v.sum(1, keepdim=True)             # RGB -> one grey channel
        enc[k] = v
    mp = {'conv1': 'l0.0', 'bn1': 'l0.1', 'layer1': 'l1', 'layer2': 'l2', 'layer3': 'l3', 'layer4': 'l4'}; new = {}
    for k, v in enc.items():
        top, rest = k.split('.', 1); new[mp[top] + '.' + rest] = v
    missing = m.load_state_dict(new, strict=False); assert not [k for k in missing.unexpected_keys], missing.unexpected_keys
    return m

def cmd_train(a):
    G.build_model = build_pretrained; old = G.OUT; G.OUT = OUT
    try:
        for organ in ('breast', 'thyroid'):
            name = organ + '_pt'; G.DS[name] = G.DS[organ]
            if os.path.exists(os.path.join(OUT, f'train_{name}.json')) and not a.force: continue
            t0 = time.time(); G.train(name, max_hours=a.max_hours); print(name, 'done', round(time.time() - t0), 's', flush=True)
    finally: G.OUT = old

def load_pt(organ, dev):
    import torch
    n = organ + '_pt'; m = _ORIG_BUILD().to(dev); m.load_state_dict(torch.load(os.path.join(G.LOCAL, f'unet_{n}.pt'), map_location=dev)); return m.eval(), json.load(open(os.path.join(OUT, f'train_{n}.json')))['chosen']

def run(cx, dev, scans, bench, medsam=None):
    """as step40.run_scans, optionally replacing the U-Net mask by a MedSAM mask prompted with the box of the U-Net mask"""
    rows = []; skipped = collections.Counter(); PS, MS, dv2 = medsam if medsam else (None, None, None)
    for s in scans:
        cid = s['case_id']; ds = s['dataset']; o = S40.organ_of(ds); rec = cx['recs'][cid]; tm = partb.true_mask(rec)
        if tm is None or not tm.any(): skipped[ds + ':no mask'] += 1; continue
        tgt = partb.largest(tm); H, W = tm.shape; model, ch = cx['nets'][o]; img = Image.open(partb.img_path(rec)).convert('L')
        if img.size != (W, H): skipped[ds + ':size mismatch'] += 1; continue
        pm = R29.predict_mask(model, dev, img, ch['threshold'], ch['keep'])
        if medsam is not None and pm.any(): pm = partb.segment(PS, MS, dv2, Image.open(partb.img_path(rec)).convert('RGB'), partb.box_of(partb.largest(pm)))
        meas = partb.pred_meas(rec, pm); ref = partb.ref_meas(rec, tm); d = dict(case_id=cid, dataset=ds, organ=o, group=f"{ds}|{s['group_id']}", found=bool(pm.any()))
        sd = dict(case_id=cid, dataset=ds, group_id=s['group_id'], has_true_mask=ds != 'TN5000'); r = S40.S38.scan_row(dict(bench=bench, tau=cx['tau'], pm=cx['pm']), sd, rec, pm, tm, tgt); d.update({k: v for k, v in r.items() if k not in d and k != 'group'}); rows.append(d)
    return rows, dict(skipped)

def pooled(rows, key='auc_tol_position'):
    v = [(r[key], r['group']) for r in rows if r.get(key) is not None]; return (gboot([x for x, _ in v], [g for _, g in v]), len({g for _, g in v})) if v else (None, 0)

def paired(new, old, key='auc_tol_position'):
    o = {r['case_id']: r for r in old}; d = [(r[key] - o[r['case_id']][key], r['group']) for r in new if r.get(key) is not None and r['case_id'] in o and o[r['case_id']].get(key) is not None]
    return (gboot([x for x, _ in d], [g for _, g in d]), len(d), len({g for _, g in d})) if d else (None, 0, 0)

def cmd_test(a):
    import torch
    dev = 'mps' if torch.backends.mps.is_available() else 'cpu'; sp = G.split_rows(); cx = S40.ctx(dev); splits.load('test', script='usmeta.step45_partG')           # the one logged test read of this part
    ts, bench = S40.test_cases(sp, cx['recs']); base = json.load(open(os.path.join(S40.OUT, 'rows.json')))['test_rows']; t0 = time.time(); res = dict(baseline_scans=len(base))
    cx['nets'] = {o: load_pt(o, dev) for o in ('breast', 'thyroid')}; rows_pt, skip = run(cx, dev, ts, bench); print('pretrained U-Net', len(rows_pt), round(time.time() - t0), 's', flush=True)
    PS, MS, dv2 = partb.load_model(); rows_ms, skip2 = run(cx, dev, ts, bench, medsam=(PS, MS, dv2)); print('MedSAM from U-Net box', len(rows_ms), round(time.time() - t0), 's', flush=True)
    json.dump(dict(pretrained=rows_pt, medsam_unet_box=rows_ms, skipped=skip), open(P('rows.json'), 'w'))
    for name, rows in (('random_init_step29_step40', base), ('pretrained_unet', rows_pt), ('medsam_from_pretrained_unet_box', rows_ms)):
        pb, n = pooled(rows); res[name] = dict(scans=len(rows), pooled=dict(position_auroc=pb, groups=n)); res[name]['by_organ'] = {o: dict(position_auroc=pooled([r for r in rows if r['organ'] == o])[0], groups=pooled([r for r in rows if r['organ'] == o])[1], scans=sum(r['organ'] == o for r in rows)) for o in ('breast', 'thyroid')}
        res[name]['dice'] = float(np.mean([r['dice'] for r in rows if r.get('dice') is not None])) if any(r.get('dice') is not None for r in rows) else None
    for name, rows in (('pretrained_unet', rows_pt), ('medsam_from_pretrained_unet_box', rows_ms)):
        d, n, ng = paired(rows, base); res[name]['paired_vs_random_init'] = dict(diff=d, scans=n, groups=ng); res[name]['paired_by_organ'] = {o: paired([r for r in rows if r['organ'] == o], [r for r in base if r['organ'] == o])[0] for o in ('breast', 'thyroid')}
        res[name]['pass'] = dict(pooled_ge_0_92=bool(res[name]['pooled']['position_auroc'][0] >= 0.92), ci_excludes_0=bool(d is not None and d[1] > 0)); res[name]['pass']['passed'] = all(res[name]['pass'].values())
    res['train'] = {o: {k: v for k, v in json.load(open(os.path.join(OUT, f'train_{o}_pt.json'))).items() if k not in ('log', 'val_grid')} for o in ('breast', 'thyroid')}
    res['seconds'] = round(time.time() - t0); json.dump(res, open(P('results.json'), 'w'), indent=1)
    print({k: (round(res[k]['pooled']['position_auroc'][0], 3), res[k].get('pass')) for k in ('random_init_step29_step40', 'pretrained_unet', 'medsam_from_pretrained_unet_box')})

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd'); ap.add_argument('--max-hours', type=float, default=1.0); ap.add_argument('--force', action='store_true'); a = ap.parse_args(); {'train': cmd_train, 'test': cmd_test}[a.cmd](a)
