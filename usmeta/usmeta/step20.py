"""Step 20 (optional): tolerance-aware image check. NEW file; layer3.py and partb.py are not changed. See results/partA/step20_tolerance_image_check/PLAN.md.
    python3 -m usmeta.step20 select | predict | tune | test"""
import os, sys, json, random, collections
import numpy as np
from PIL import Image
from . import unified, layer3, schema, splits, partb
from .layer0 import auroc_case
from .step10d_analysis import gboot

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..'); LOCAL = os.path.join(ROOT, 'local_data', 'partb_devval'); MASKS = os.path.join(LOCAL, 'masks')
TAUS = (0.0, 0.1, 0.2, 0.3, 0.4, 0.5); POS = ('exact', 'adjacent'); N_PER = 30; PER_GROUP = 3; SEED = 1
VERT = {'upper': 0, 'middle': 1, 'lower': 2}; HORIZ = {'left': 0, 'central': 1, 'right': 2}
SIZE = ('size_mm', 'size_pct', 'hc_mm'); CHECKABLE = ('lesion', 'count', 'pos', 'orient') + SIZE

def pos_adjacent(a, b):
    try:
        (va, ha), (vb, hb) = a.split('-'), b.split('-'); dv, dh = abs(VERT[va] - VERT[vb]), abs(HORIZ[ha] - HORIZ[hb])
    except Exception: return False
    return dv + dh == 1

def tol_score(text, organ, meas, tau, posmode):
    """mean credit over the checkable claims; tau = 0 and posmode 'exact' reproduces layer3.mask_verified"""
    claims = {k: v for k, v in schema.extract_rule(text, organ).items() if k in layer3.CHECK}; cred = []
    for k, v in claims.items():
        m = meas.get(k)
        if m is None: continue
        if k == 'count' and organ == 'thyroid': m = min(m, 3)
        if k in SIZE:
            if v is None: c = 0.0
            elif k == 'hc_mm' and tau == 0: c = schema.attr_credit(k, m, v)
            else: d = abs(m - v) / m if m else float(m != v); c = max(0.0, 1 - max(0.0, d - tau) / 0.5)
        elif k == 'pos' and posmode == 'adjacent' and str(m) != str(v): c = 1.0 if pos_adjacent(str(m), str(v)) else 0.0
        else: c = float(str(m) == str(v))
        cred.append(c)
    return float(np.mean(cred)) if cred else 1.0

def recs_all():
    r = {}
    for ds in partb.DATASETS:
        for c in unified.load(partb.LOADER.get(ds, ds)): r[c['case_id']] = c
    return r

def select():
    sp = {r['case_id']: r for s in ('dev', 'val') for r in splits.load(s)}; bench = collections.defaultdict(set)
    for l in open(os.path.join(ROOT, 'bench_v2d.jsonl')):
        r = json.loads(l); bench[r['dataset']].add(r['case_id'])
    out = []; rng = random.Random(SEED)
    for ds in partb.DATASETS:
        recs = {c['case_id']: c for c in unified.load(partb.LOADER.get(ds, ds))}; ids = sorted(c for c in bench[ds] if c in sp and recs.get(c) and recs[c]['region']); rng.shuffle(ids)
        seen = collections.Counter(); pick = []
        for c in ids:
            g = sp[c]['group_id']
            if seen[g] >= PER_GROUP: continue
            m = partb.true_mask(recs[c])
            if m is None or not m.any() or m.shape != (recs[c]['region']['H'], recs[c]['region']['W']): continue
            seen[g] += 1; pick.append(c)
            if len(pick) == N_PER: break
        out += [dict(case_id=c, dataset=ds, group_id=sp[c]['group_id'], has_true_mask=recs[c]['region']['kind'] != 'box') for c in pick]; print(ds, len(pick), 'of', len(ids))
    os.makedirs(LOCAL, exist_ok=True); json.dump(out, open(os.path.join(LOCAL, 'selected.json'), 'w'), indent=1)

def predict():
    partb.MASKS = MASKS; os.makedirs(MASKS, exist_ok=True); sel = json.load(open(os.path.join(LOCAL, 'selected.json'))); P, M, dev = partb.load_model(); recs = recs_all(); n = 0
    for s in sel:
        rec = recs[s['case_id']]; tm = partb.true_mask(rec); box = partb.box_of(partb.largest(tm)); img = Image.open(partb.img_path(rec)).convert('RGB'); f = partb.mpath(s['case_id'], 'exact')
        if os.path.exists(f): continue
        H, W = tm.shape
        if img.size != (W, H): continue
        np.savez_compressed(f, mask=np.packbits(partb.segment(P, M, dev, img, box)), shape=np.array([H, W]), box=np.array(box)); n += 1
    print('new masks', n)

def rows_for(sel, masks_dir):
    """one row per bench_v2d candidate of the selected cases, with the facts measured from the predicted (exact) mask"""
    partb.MASKS = masks_dir; recs = recs_all(); ids = {s['case_id']: s for s in sel}; M = {}
    for s in sel:
        rec = recs[s['case_id']]
        try: pm, _ = partb.load_pred(s['case_id'], 'exact')
        except FileNotFoundError: continue
        M[s['case_id']] = partb.pred_meas(rec, pm)
    rows = [json.loads(l) for l in open(os.path.join(ROOT, 'bench_v2d.jsonl'))]; return [(r, M[r['case_id']], ids[r['case_id']]) for r in rows if r['case_id'] in M]

def table(R, ds_filter=None):
    """per (tau, posmode): identical mean, share exactly 1.0, AUROC (all checkable) pooled over `ds_filter` datasets, with group bootstrap"""
    out = {}
    R = [x for x in R if ds_filter is None or ds_filter(x[2]['dataset'])]
    by = collections.defaultdict(list)
    for r, m, s in R: by[r['case_id']].append((r, m, s))
    for tau in TAUS:
        for pm in POS:
            ident, auc, grp = [], [], []
            for cid, rs in by.items():
                sc = lambda r, m: tol_score(r['candidate'], r['organ'], m, tau, pm)
                ident += [sc(r, m) for r, m, s in rs if r['kind'] == 'identical']
                e = [sc(r, m) for r, m, s in rs if r['kind'] == 'error' and r['field'] in CHECKABLE]; h = [sc(r, m) for r, m, s in rs if r['kind'] == 'harmless']
                if e and h: auc.append(auroc_case(e, h)); grp.append(rs[0][2]['group_id'])
            out[(tau, pm)] = dict(identical_mean=float(np.mean(ident)), share_full=float(np.mean([x > 0.999 for x in ident])), n_identical=len(ident), auroc=gboot(auc, grp), n_cases=len(auc))
    return out

LES = lambda ds: ds not in ('HC18', 'FetalHead')

def tune():
    sel = json.load(open(os.path.join(LOCAL, 'selected.json'))); R = rows_for(sel, MASKS); T = table(R, LES); best = None
    lines = ['| tau | position | identical mean | share 1.0 | AUROC (all checkable) | J |', '|---|---|---|---|---|---|']
    for (tau, pm), v in T.items():
        J = 0.5 * (v['auroc'][0] + v['identical_mean']); lines.append(f"| {tau} | {pm} | {v['identical_mean']:.3f} | {v['share_full']:.2f} | {v['auroc'][0]:.3f} ({v['auroc'][1]:.3f}–{v['auroc'][2]:.3f}) | {J:.3f} |")
        if best is None or J > best[0] + 1e-9: best = (J, tau, pm)
    print('\n'.join(lines)); print('chosen', best); json.dump(dict(chosen=dict(J=best[0], tau=best[1], position=best[2]), table={f'{k[0]}|{k[1]}': v for k, v in T.items()}, n_cases=T[(0.0, 'exact')]['n_cases']),
                              open(os.path.join(ROOT, 'results', 'partA', 'step20_tolerance_image_check', 'tuning_devval.json'), 'w'), indent=1); open(os.path.join(ROOT, 'results', 'partA', 'step20_tolerance_image_check', 'tuning_devval.md'), 'w').write('\n'.join(lines) + f'\n\nChosen on dev/val: tau={best[1]}, position={best[2]}, J={best[0]:.3f}\n')
    return best

if __name__ == '__main__':
    {'select': select, 'predict': predict, 'tune': tune}.get(sys.argv[1], lambda: None)()

# ---------------------------------------------------------------- evaluation ONCE on the test split (frozen tau / position from tuning_devval.json)
SUBS = {'all checkable': CHECKABLE, 'position errors': ('pos',), 'size errors': SIZE}

def evaluate(out):
    ch = json.load(open(os.path.join(ROOT, 'results', 'partA', 'step20_tolerance_image_check', 'tuning_devval.json')))['chosen']; tau, pm = ch['tau'], ch['position']
    sel = json.load(open(os.path.join(partb.LOCAL, 'selected.json'))); R = rows_for(sel, partb.MASKS); res = dict(frozen=dict(tau=tau, position=pm)); by = collections.defaultdict(lambda: collections.defaultdict(list))
    for r, m, s in R: by[s['dataset']][r['case_id']].append((r, m, s))
    groups = {'LESIONS': [d for d in by if LES(d)], 'HC18': ['HC18'], 'FetalHead': ['FetalHead']} ; groups.update({d: [d] for d in by if LES(d)})
    for gname, dss in groups.items():
        cases = {c: rs for d in dss for c, rs in by[d].items()}; row = {}
        for variant, (t, p) in (('exact-match (Step 16 rule)', (0.0, 'exact')), (f'tolerance-aware (tau={tau}, {pm})', (tau, pm))):
            sc = lambda r, m, t=t, p=p: tol_score(r['candidate'], r['organ'], m, t, p)
            ident = [sc(r, m) for rs in cases.values() for r, m, s in rs if r['kind'] == 'identical']; harm = [sc(r, m) for rs in cases.values() for r, m, s in rs if r['kind'] == 'harmless']; v = dict(n_identical=len(ident), identical_mean=float(np.mean(ident)), share_full=float(np.mean([x > 0.999 for x in ident])), harmless_mean=float(np.mean(harm)))
            for sname, fields in SUBS.items():
                a, g = [], []
                for c, rs in cases.items():
                    e = [sc(r, m) for r, m, s in rs if r['kind'] == 'error' and r['field'] in fields]; h = [sc(r, m) for r, m, s in rs if r['kind'] == 'harmless']
                    if e and h: a.append(auroc_case(e, h)); g.append(rs[0][2]['group_id'])
                v[sname] = dict(n=len(a), auroc=gboot(a, g) if a else None)
            row[variant] = v
        res[gname] = row
    json.dump(res, open(out, 'w'), indent=1); return res

if __name__ == '__main__' and sys.argv[1] == 'test': evaluate(sys.argv[2])
