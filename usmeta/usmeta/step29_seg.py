"""Step 29: small U-Net (ResNet-18 encoder, random init: no pretrained weights are cached and none were downloaded) for label-free lesion segmentation (29a: breast, thyroid) and head masks (29b: HC18).
NEW file; partb.py, location.py, layer3.py, step20.py, step24_box_reliability.py are imported unchanged.
Rules: training on DEV only (minus dev images whose <= 8-bit near-duplicate cluster has members in val or test), early stopping and post-processing chosen on VAL, TEST read once at the end (usmeta.splits.load, logged).
    python3 -m usmeta.step29_seg train breast|thyroid|hc18   [--max-hours 3]
Model files go to local_data/step29 (git-ignored); logs and tuning json go to results/partA/step29_segmentation."""
import os, sys, json, time, argparse, collections
import numpy as np
from PIL import Image
from . import unified, location, partb, splits

ROOT = partb.ROOT; LOCAL = os.path.join(ROOT, 'local_data', 'step29'); OUT = os.path.join(ROOT, 'results', 'partA', 'step29_segmentation'); S = 256
DS = {'breast': ['BrEaST', 'BUS-BRA', 'BUSI', 'UDIAT', 'BUS-UCLM'], 'thyroid': ['TN3K', 'DDTI'], 'hc18': ['HC18']}      # TN5000 has boxes only: not used for training
SEED = 0

def split_rows():
    sp = {}
    for l in open(os.path.join(ROOT, 'splits.jsonl')): r = json.loads(l); sp[r['case_id']] = r
    return sp

def leaky_dev(sp):
    """dev case ids whose <= 8-bit near-duplicate cluster (inside one dataset; Step 21f) has a member in val or test"""
    par = {}
    def find(x):
        par.setdefault(x, x)
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    for l in open(os.path.join(ROOT, 'duplicates.jsonl')):
        r = json.loads(l)
        if r['dist'] <= 8 and r['ds_a'] == r['ds_b'] and not r['ds_a'].startswith('Diverse') and r['a'] in sp and r['b'] in sp: par[find(r['a'])] = find(r['b'])
    cl = collections.defaultdict(set)
    for x in list(par): cl[find(x)].add(x)
    out = set()
    for c in cl.values():
        s = {sp[x]['split'] for x in c}
        if s & {'val', 'test'}:
            out |= {x for x in c if sp[x]['split'] == 'dev'}
    return out

def organ_records(name):
    recs = {}
    for ds in DS[name]:
        for c in unified.load(partb.LOADER.get(ds, ds)): recs[c['case_id']] = c
    return recs

def mask_of(rec):
    m = location.gt_mask(rec)
    return m

def preload(cases, recs):
    """arrays at SxS: images uint8 (N,S,S), masks uint8 (N,S,S); skips cases without image / mask / size match"""
    X, M, ids = [], [], []
    for cid in cases:
        rec = recs[cid]; m = mask_of(rec)
        if m is None or not m.any(): continue
        p = partb.img_path(rec)
        if not os.path.exists(p): continue
        im = Image.open(p).convert('L')
        if im.size != (m.shape[1], m.shape[0]): continue
        X.append(np.asarray(im.resize((S, S), Image.BILINEAR))); M.append((np.asarray(Image.fromarray(m.astype(np.uint8) * 255).resize((S, S), Image.NEAREST)) > 127).astype(np.uint8)); ids.append(cid)
    return np.stack(X), np.stack(M), ids

# ---------------------------------------------------------------- model
def build_model():
    import torch, torch.nn as nn, torch.nn.functional as F, torchvision
    class Block(nn.Module):
        def __init__(s, i, o): super().__init__(); s.f = nn.Sequential(nn.Conv2d(i, o, 3, padding=1, bias=False), nn.BatchNorm2d(o), nn.ReLU(True), nn.Conv2d(o, o, 3, padding=1, bias=False), nn.BatchNorm2d(o), nn.ReLU(True))
        def forward(s, x): return s.f(x)
    class UNet(nn.Module):
        def __init__(s):
            super().__init__(); r = torchvision.models.resnet18(weights=None); r.conv1 = nn.Conv2d(1, 64, 7, 2, 3, bias=False)
            s.l0 = nn.Sequential(r.conv1, r.bn1, r.relu); s.pool = r.maxpool; s.l1, s.l2, s.l3, s.l4 = r.layer1, r.layer2, r.layer3, r.layer4
            s.d4 = Block(512 + 256, 256); s.d3 = Block(256 + 128, 128); s.d2 = Block(128 + 64, 64); s.d1 = Block(64 + 64, 64); s.d0 = Block(64, 32); s.out = nn.Conv2d(32, 1, 1)
        def forward(s, x):
            x0 = s.l0(x); x1 = s.l1(s.pool(x0)); x2 = s.l2(x1); x3 = s.l3(x2); x4 = s.l4(x3); up = lambda a, b: torch.cat([F.interpolate(a, size=b.shape[-2:], mode='bilinear', align_corners=False), b], 1)
            y = s.d4(up(x4, x3)); y = s.d3(up(y, x2)); y = s.d2(up(y, x1)); y = s.d1(up(y, x0)); y = s.d0(F.interpolate(y, scale_factor=2, mode='bilinear', align_corners=False)); return s.out(y)
    return UNet()

def dice_np(p, t):
    i = (p & t).sum(); s = p.sum() + t.sum(); return float(2 * i / s) if s else 1.0

def predict_batch(model, X, dev, bs=32):
    import torch
    model.eval(); out = []
    with torch.no_grad():
        for i in range(0, len(X), bs):
            x = (torch.from_numpy(X[i:i + bs]).float().div(255).sub(0.5).div(0.25)).unsqueeze(1).to(dev); out.append(torch.sigmoid(model(x)).squeeze(1).cpu().numpy())
    return np.concatenate(out)

def train(name, max_hours=3.0, max_epochs=30, patience=6, bs=16):
    import torch, torch.nn.functional as F
    os.makedirs(LOCAL, exist_ok=True); os.makedirs(OUT, exist_ok=True); torch.manual_seed(SEED); np.random.seed(SEED); dev = 'mps' if torch.backends.mps.is_available() else 'cpu'
    sp = split_rows(); recs = organ_records(name); leak = leaky_dev(sp)
    dev_all = [c for c in recs if sp.get(c, {}).get('split') == 'dev']; dev_keep = [c for c in dev_all if c not in leak]; val = [c for c in recs if sp.get(c, {}).get('split') == 'val']
    t0 = time.time(); Xt, Mt, it = preload(dev_keep, recs); Xv, Mv, iv = preload(val, recs); print(name, 'dev', len(dev_all), '-> kept', len(dev_keep), '(dropped', len(dev_all) - len(dev_keep), 'leaky) -> with mask', len(it), '| val', len(iv), '| load', round(time.time() - t0), 's', flush=True)
    model = build_model().to(dev); opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4); sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=max_epochs)
    Xt_t = torch.from_numpy(Xt).float().div(255).unsqueeze(1).to(dev); Mt_t = torch.from_numpy(Mt).float().unsqueeze(1).to(dev); log = []; best = -1; bad = 0; start = time.time(); g = torch.Generator().manual_seed(SEED)
    for ep in range(max_epochs):
        if time.time() - start > max_hours * 3600: print('time limit'); break
        model.train(); perm = torch.randperm(len(Xt_t), generator=g); tl = 0; n = 0
        for i in range(0, len(perm) - bs + 1, bs):
            idx = perm[i:i + bs].to(dev); x = Xt_t[idx].clone(); m = Mt_t[idx].clone()
            fl = torch.rand(len(idx), device=dev) < 0.5; x[fl] = x[fl].flip(-1); m[fl] = m[fl].flip(-1)                                 # horizontal flip
            fv = torch.rand(len(idx), device=dev) < 0.5; x[fv] = x[fv].flip(-2); m[fv] = m[fv].flip(-2)                                 # vertical flip
            c = 0.75 + 0.5 * torch.rand(len(idx), 1, 1, 1, device=dev); b = 0.1 * (torch.rand(len(idx), 1, 1, 1, device=dev) - 0.5); gam = torch.exp(0.4 * (torch.rand(len(idx), 1, 1, 1, device=dev) - 0.5))
            x = ((x.clamp(0, 1) ** gam) * c + b).clamp(0, 1); x = (x - 0.5) / 0.25                                                      # intensity: contrast, brightness, gamma
            lo = model(x); p = torch.sigmoid(lo); inter = (p * m).sum((1, 2, 3)); dsc = 1 - (2 * inter + 1) / (p.sum((1, 2, 3)) + m.sum((1, 2, 3)) + 1)
            loss = F.binary_cross_entropy_with_logits(lo, m) + dsc.mean(); opt.zero_grad(); loss.backward(); opt.step(); tl += float(loss) * len(idx); n += len(idx)
        sched.step(); P = predict_batch(model, Xv, dev); vd = float(np.mean([dice_np(P[k] > 0.5, Mv[k] > 0) for k in range(len(Xv))]))
        log.append(dict(epoch=ep + 1, train_loss=tl / n, val_dice_256=vd, seconds=round(time.time() - start))); print(log[-1], flush=True)
        if vd > best: best = vd; bad = 0; torch.save(model.state_dict(), os.path.join(LOCAL, f'unet_{name}.pt'))
        else:
            bad += 1
            if bad >= patience: print('early stop'); break
    # post-processing chosen on VAL (threshold, keep largest component or not), best checkpoint
    model.load_state_dict(torch.load(os.path.join(LOCAL, f'unet_{name}.pt'))); P = predict_batch(model, Xv, dev); grid = {}
    from scipy import ndimage
    def largest(m):
        lab, k = ndimage.label(m)
        return m if k <= 1 else lab == (int(np.argmax(ndimage.sum(m, lab, range(1, k + 1)))) + 1)
    for th in (0.3, 0.4, 0.5, 0.6, 0.7):
        for lg in (False, True): grid[f'{th}|{"largest" if lg else "raw"}'] = float(np.mean([dice_np(largest(P[k] > th) if lg else P[k] > th, Mv[k] > 0) for k in range(len(Xv))]))
    ch = max(grid, key=grid.get); th, lg = ch.split('|')
    json.dump(dict(organ=name, dev_total=len(dev_all), dev_dropped_leaky=len(dev_all) - len(dev_keep), dev_trained=len(it), val_n=len(iv), epochs_run=len(log), best_val_dice_256=best, log=log, val_grid=grid, chosen=dict(threshold=float(th), keep=lg), encoder='resnet18 (random init, no pretrained weights)',
                   seconds=round(time.time() - start), device=dev, seed=SEED), open(os.path.join(OUT, f'train_{name}.json'), 'w'), indent=1); print('chosen on val', ch, grid[ch])

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd'); ap.add_argument('name'); ap.add_argument('--max-hours', type=float, default=3.0); a = ap.parse_args()
    train(a.name, a.max_hours)
