"""Step 10a: duplicate / leakage check with 64-bit difference hashes (dHash). No new dependencies (PIL + numpy).
    python3 -m usmeta.dedupe hash   -> dedupe_hashes.npz   (one hash per image of the 10 benchmark datasets + 'DiverseFetal' reference set)
    python3 -m usmeta.dedupe pairs  -> duplicates.jsonl, dedupe_report.md numbers
Near-duplicate = Hamming distance <= 4 of 64 bits; 'possible' = 5..8. Constant (almost uniform) images are excluded from matching (hash is meaningless)."""
import os, sys, json, glob, time, collections
import numpy as np
from PIL import Image
from . import unified

DL = os.path.expanduser('~/Downloads')
LUT = np.array([bin(i).count('1') for i in range(256)], dtype=np.uint8)

def local_path(p): return p.replace(os.path.dirname(os.path.dirname(os.path.dirname(p.split('/mnt/Downloads')[0] + '/mnt/Downloads'))), '') if False else (DL + p.split('/mnt/Downloads', 1)[1] if '/mnt/Downloads' in p else p)

def dhash(path):
    try:
        im = Image.open(path); im.draft('L', (64, 64)); a = np.asarray(im.convert('L').resize((9, 8), Image.LANCZOS), dtype=np.float32)
    except Exception: return None, None
    bits = (a[:, 1:] > a[:, :-1]).flatten(); h = 0
    for b in bits: h = (h << 1) | int(b)
    return np.uint64(h), float(a.std())

def collect():
    items = []
    for ds in ['BrEaST', 'BUSBRA', 'BUSI', 'UDIAT', 'BUSUCLM', 'TN3K', 'TN5000', 'DDTI', 'HC18', 'FetalHead']:
        for c in unified.load(ds): items.append((c['dataset'], c['case_id'], local_path(c['image']), c['group_id']))
    for f in sorted(glob.glob(os.path.join(DL, 'Diverse Fetal Head Images', 'Orginal_train_images_to_959_661', '*.png'))):
        items.append(('DiverseFetal(ref)', 'DiverseFetal:' + os.path.basename(f), f, None))
    return items

def cmd_hash(out='dedupe_hashes.npz'):
    items = collect(); H = np.zeros(len(items), np.uint64); S = np.zeros(len(items), np.float32); ok = np.zeros(len(items), bool); t = time.time()
    for i, (ds, cid, p, g) in enumerate(items):
        h, s = dhash(p)
        if h is not None: H[i], S[i], ok[i] = h, s, True
        if i % 3000 == 0: print(i, len(items), round(time.time() - t), 's', flush=True)
    np.savez(out, H=H, S=S, ok=ok, ds=np.array([x[0] for x in items]), cid=np.array([x[1] for x in items]), path=np.array([x[2] for x in items]), grp=np.array([x[3] or '' for x in items]))
    print('hashed', int(ok.sum()), 'of', len(items), 'unreadable', int((~ok).sum()))

def hamming_block(a, B):
    x = np.bitwise_xor(a[:, None], B[None, :]); return LUT[x.view(np.uint8).reshape(x.shape + (8,))].sum(-1)

def cmd_pairs(inp='dedupe_hashes.npz', out='duplicates.jsonl', thr_dup=4, thr_poss=8, min_std=2.0):
    Z = np.load(inp, allow_pickle=True); H, S, ok = Z['H'], Z['S'], Z['ok']; ds, cid, path, grp = Z['ds'], Z['cid'], Z['path'], Z['grp']
    use = np.where(ok & (S >= min_std))[0]; skipped = int((~(ok & (S >= min_std))).sum()); Hu = H[use]; n = len(use); rows = []
    for s in range(0, n, 600):
        d = hamming_block(Hu[s:s + 600], Hu)
        for i, j in zip(*np.where(d <= thr_poss)):
            gi, gj = s + i, j
            if gj <= gi: continue
            a, b = use[gi], use[gj]; rows.append(dict(a=str(cid[a]), b=str(cid[b]), ds_a=str(ds[a]), ds_b=str(ds[b]), dist=int(d[i, j]), same_group=bool(grp[a] and grp[a] == grp[b]), path_a=os.path.basename(str(path[a])), path_b=os.path.basename(str(path[b]))))
    open(out, 'w').write(''.join(json.dumps(r) + '\n' for r in rows)); print(len(rows), 'pairs (<= 8 bits) among', n, 'images; skipped (unreadable or near-uniform):', skipped)

if __name__ == '__main__':
    {'hash': cmd_hash, 'pairs': cmd_pairs}[sys.argv[1]]()
