"""Step 40: per-dataset fairness on ALL test scans and calibrated U-Net confidence. NEW file; extends Step 38. Step 20 / 29 / 38 code is imported unchanged (R29.load_net, R29.predict_mask, R29.scan_scores via step38.scan_row, step38.conf_of, step38.pos_ok).
Pre-registration: results/partA/step40_fairness_calibration/PREREG.md. Saved Step 29 models, NO retraining. One new logged test read.
    python3 -m usmeta.step40_fairness_calibration run      (predictions + (a) + (b); writes rows.json and results.json)
Then: python3 -m usmeta.step40_report"""
import os, sys, json, time, collections, functools, random
import numpy as np
from PIL import Image
from . import partb, schema, location, step20, splits, step29_seg as G, step29_run as R29, step38_responsible_ai as S38

ROOT = G.ROOT; OUT = os.path.join(ROOT, 'results', 'partA', 'step40_fairness_calibration'); MIN_G = 30; NB = 1000; CAP = 300; EPS = 1e-9
DS = ['BrEaST', 'BUS-BRA', 'BUSI', 'UDIAT', 'BUS-UCLM', 'TN3K', 'DDTI', 'TN5000']; ORGAN = S38.SD; BINS = np.linspace(0, 1, 11)
def organ_of(ds): return ORGAN[ds]

def logit(c): c = np.clip(np.asarray(c, float), 0.001, 0.999); return np.log(c / (1 - c))

def ctx(dev):
    ch = json.load(open(os.path.join(ROOT, 'results', 'partA', 'step20_tolerance_image_check', 'tuning_devval.json')))['chosen']; schema.extract_rule = functools.lru_cache(maxsize=None)(schema.extract_rule)
    recs = step20.recs_all(); nets = {o: R29.load_net(o, dev) for o in ('breast', 'thyroid')}; return dict(tau=ch['tau'], pm=ch['position'], recs=recs, nets=nets)

def test_cases(sp, recs):
    """test-split cases of the eight datasets with a planted image-checkable error and an image; also the bench rows of those cases"""
    ids = collections.defaultdict(set); bench = collections.defaultdict(list)
    for l in open(os.path.join(ROOT, 'bench_v2d.jsonl')):
        r = json.loads(l)
        if r['dataset'] in DS and sp.get(r['case_id'], {}).get('split') == 'test':
            bench[r['case_id']].append(r)
            if r['kind'] == 'error' and r['field'] in step20.CHECKABLE: ids[r['dataset']].add(r['case_id'])
    out = []
    for ds in DS:
        c = sorted(x for x in ids[ds] if x in recs and os.path.exists(partb.img_path(recs[x])))
        if len(c) > CAP: c = sorted(random.Random(0).sample(c, CAP))
        out += [dict(case_id=x, dataset=ds, group_id=sp[x]['group_id'], has_true_mask=ds != 'TN5000') for x in c]
    return out, bench

def val_cases(sp, recs):
    out = []
    for ds in DS:
        c = sorted(k for k, v in sp.items() if v['split'] == 'val' and v['dataset'] == ds and k in recs and os.path.exists(partb.img_path(recs[k])))
        if len(c) > CAP: c = sorted(random.Random(0).sample(c, CAP))
        out += [dict(case_id=x, dataset=ds, group_id=sp[x]['group_id']) for x in c]
    return out

def run_scans(cx, dev, scans, bench=None, tag=''):
    rows = []; skipped = collections.Counter(); t0 = time.time()
    for i, s in enumerate(scans):
        cid = s['case_id']; ds = s['dataset']; o = organ_of(ds); rec = cx['recs'][cid]; tm = partb.true_mask(rec)
        if tm is None or not tm.any(): skipped[ds + ':no mask'] += 1; continue
        tgt = partb.largest(tm); H, W = tm.shape; model, ch = cx['nets'][o]; img = Image.open(partb.img_path(rec)).convert('L')
        if img.size != (W, H): skipped[ds + ':size mismatch'] += 1; continue
        pm = R29.predict_mask(model, dev, img, ch['threshold'], ch['keep']); c = S38.conf_of(model, dev, img, ch['threshold']); meas = partb.pred_meas(rec, pm); ref = partb.ref_meas(rec, tm)
        d = dict(case_id=cid, dataset=ds, organ=o, group=f"{ds}|{s['group_id']}", conf=c, found=bool(pm.any()), y=float(S38.pos_ok(meas, ref)), has_true_mask=bool(s.get('has_true_mask', ds != 'TN5000')))
        if bench is not None:
            sd = dict(case_id=cid, dataset=ds, group_id=s['group_id'], has_true_mask=d['has_true_mask'])
            r = S38.scan_row(dict(bench=bench, tau=cx['tau'], pm=cx['pm']), sd, rec, pm, tm, tgt); d.update({k: v for k, v in r.items() if k not in d and k != 'group'})
        rows.append(d)
        if i % 100 == 0: print(tag, i, len(scans), round(time.time() - t0), 's', flush=True)
    return rows, dict(skipped)

# ------------------------------------------------------------------ calibration
def fit_platt(rows):
    from sklearn.linear_model import LogisticRegression
    out = {}
    for o in ('breast', 'thyroid'):
        R = [r for r in rows if r['organ'] == o]; y = np.array([r['y'] for r in R]); x = logit([r['conf'] for r in R]).reshape(-1, 1)
        if len(set(y)) < 2: out[o] = dict(a=None, b=None, n=len(R), negatives=int((y == 0).sum()), note='one class in val: not fitted'); continue
        m = LogisticRegression(C=1.0).fit(x, y); out[o] = dict(a=float(m.coef_[0][0]), b=float(m.intercept_[0]), n=len(R), negatives=int((y == 0).sum()))
    return out

def apply_platt(cal, o, c):
    p = cal[o]
    if p['a'] is None: return np.asarray(c, float)
    return 1 / (1 + np.exp(-(p['a'] * logit(c) + p['b'])))

def bin_stats(p, y, w=None):
    w = np.ones(len(p)) if w is None else w; idx = np.minimum(np.digitize(p, BINS[1:-1]), 9); out = []
    for b in range(10):
        m = idx == b; out.append((float(w[m].sum()), float((w[m] * y[m]).sum()), float((w[m] * p[m]).sum())))
    return out

def ece_of(p, y): bs = bin_stats(np.asarray(p, float), np.asarray(y, float)); n = sum(b[0] for b in bs); return sum(abs(b[1] - b[2]) for b in bs) / n

def boot_ece(groups, p_before, p_after, y):
    ug, inv = np.unique(np.asarray(groups), return_inverse=True); G_ = len(ug); rng = np.random.default_rng(0); C = rng.multinomial(G_, np.full(G_, 1.0 / G_), size=NB).astype(float); out = {}
    def mats(p):
        idx = np.minimum(np.digitize(p, BINS[1:-1]), 9); gw = np.zeros((G_, 10)); gy = np.zeros((G_, 10)); gp = np.zeros((G_, 10))
        for k in range(len(p)): gw[inv[k], idx[k]] += 1; gy[inv[k], idx[k]] += y[k]; gp[inv[k], idx[k]] += p[k]
        return gw, gy, gp
    E = {}
    for tag, p in (('before', p_before), ('after', p_after)):
        gw, gy, gp = mats(np.asarray(p, float)); W = C @ gw; E[tag] = np.abs(C @ gy - C @ gp).sum(1) / W.sum(1)
    for tag in ('before', 'after'): out[tag] = dict(lo=float(np.percentile(E[tag], 2.5)), hi=float(np.percentile(E[tag], 97.5)))
    d = E['before'] - E['after']; out['fall'] = dict(lo=float(np.percentile(d, 2.5)), hi=float(np.percentile(d, 97.5))); return out

def calib_block(rows, cal):
    y = np.array([r['y'] for r in rows]); pb = np.array([r['conf'] for r in rows]); pa = np.array([apply_platt(cal, r['organ'], r['conf']) for r in rows]); g = [r['group'] for r in rows]
    eb, ea = ece_of(pb, y), ece_of(pa, y); ci = boot_ece(g, pb, pa, y)
    return dict(n=len(rows), groups=len(set(g)), position_correct=float(y.mean()), ece_before=eb, ece_after=ea, fall=eb - ea, ci=ci, reliability=dict(before=bin_stats(pb, y), after=bin_stats(pa, y)))

def risk_coverage(rows, cal):
    y = np.array([r['y'] for r in rows]); err = 1 - y; raw = np.array([r['conf'] for r in rows]); cal_p = np.array([apply_platt(cal, r['organ'], r['conf']) for r in rows]); org = np.array([r['organ'] for r in rows]); cov = np.linspace(1.0, 0.3, 15); rng = np.random.default_rng(0)
    def curve(score):
        order = np.argsort(-score, kind='stable'); return [float(err[order[:max(1, int(round(c * len(rows))))]].mean()) for c in cov]
    def within_organ():
        out = []
        for c in cov:
            kept = []
            for o in ('breast', 'thyroid'):
                ix = np.where(org == o)[0]; ix = ix[np.argsort(-raw[ix], kind='stable')]; kept += list(ix[:max(1, int(round(c * len(ix))))])
            out.append(float(err[kept].mean()))
        return out
    rand = [float(np.mean([err[rng.choice(len(rows), max(1, int(round(c * len(rows)))), replace=False)].mean() for _ in range(300)])) for c in cov]
    return dict(coverage=[float(c) for c in cov], raw_pooled=curve(raw), calibrated_pooled=curve(cal_p), raw_within_organ=within_organ(), random=rand, overall_error=float(err.mean()))

# ------------------------------------------------------------------ (a)
def gap(rows, ds):
    """mean per-scan position AUROC of ds minus that of all other datasets; group bootstrap over all scans with a defined AUROC"""
    R = [r for r in rows if r.get('auc_tol_position') is not None]; ug, inv = np.unique(np.array([r['group'] for r in R]), return_inverse=True); G_ = len(ug)
    a = np.array([r['auc_tol_position'] for r in R]); mine = np.array([r['dataset'] == ds for r in R]); sa = np.bincount(inv[mine], weights=a[mine], minlength=G_); na = np.bincount(inv[mine], minlength=G_).astype(float)
    so = np.bincount(inv[~mine], weights=a[~mine], minlength=G_); no = np.bincount(inv[~mine], minlength=G_).astype(float)
    if na.sum() == 0 or no.sum() == 0: return None
    rng = np.random.default_rng(0); C = rng.multinomial(G_, np.full(G_, 1.0 / G_), size=NB).astype(float); da = C @ na; do = C @ no; ok = (da > 0) & (do > 0); d = (C @ sa)[ok] / da[ok] - (C @ so)[ok] / do[ok]
    return dict(diff=float(sa.sum() / na.sum() - so.sum() / no.sum()), lo=float(np.percentile(d, 2.5)), hi=float(np.percentile(d, 97.5)), groups_dataset=int((na > 0).sum()))

def block(rows):
    from .step10d_analysis import gboot
    d = {}
    for k, nm in (('dice', 'dice'), ('auc_tol_position', 'position_auroc'), ('correct_tol', 'correct_report'), ('auc_tol_size', 'size_auroc'), ('auc_tol_all', 'all_auroc')):
        v = [(r[k], r['group']) for r in rows if r.get(k) is not None]; g = gboot([x for x, _ in v], [y for _, y in v]) if v else None; n = len({y for _, y in v}); d[nm] = dict(value=g, groups=n, too_small=n < MIN_G)
    v = [(float(r['found']), r['group']) for r in rows]; d['detection'] = dict(value=gboot([x for x, _ in v], [y for _, y in v]) if v else None, groups=len({y for _, y in v}), too_small=len({y for _, y in v}) < MIN_G); d['scans'] = len(rows); return d

def main():
    import torch
    t0 = time.time(); os.makedirs(OUT, exist_ok=True); dev = 'mps' if torch.backends.mps.is_available() else 'cpu'; sp = G.split_rows(); cx = ctx(dev)
    vs = val_cases(sp, cx['recs']); print('val scans', len(vs), flush=True); val_rows, val_skip = run_scans(cx, dev, vs, tag='val')
    splits.load('test', script='usmeta.step40_fairness_calibration')                 # the one new logged test read
    ts, bench = test_cases(sp, cx['recs']); print('test scans', len(ts), collections.Counter(s['dataset'] for s in ts), flush=True); rows, skip = run_scans(cx, dev, ts, bench=bench, tag='test')
    json.dump(dict(val_rows=val_rows, test_rows=rows, val_skipped=val_skip, test_skipped=skip, tau=cx['tau'], position=cx['pm'], chosen={o: cx['nets'][o][1] for o in cx['nets']}), open(os.path.join(OUT, 'rows.json'), 'w'))
    res = dict(test_scans=len(rows), val_scans=len(val_rows), val_skipped=val_skip, test_skipped=skip, per_dataset_planned=dict(collections.Counter(s['dataset'] for s in ts)))
    # (a)
    res['a'] = dict(datasets={}, organs={}, pooled=block(rows))
    for ds in DS:
        r = [x for x in rows if x['dataset'] == ds]; b = block(r); g = gap(rows, ds); b['gap'] = g; gp = b['position_auroc']['groups']
        b['verdict'] = ('too small (under 30 groups)' if gp < MIN_G else ('gap: lower than the other datasets' if g['hi'] < 0 else 'better than the other datasets' if g['lo'] > 0 else 'no gap detected (interval includes 0)')); res['a']['datasets'][ds] = b
    for o in ('breast', 'thyroid'): res['a']['organs'][o] = block([x for x in rows if x['organ'] == o])
    # consistency with the saved Step 29 rows (overlap scans)
    A29 = {r['case_id']: r for r in json.load(open(S38.A29))['rows']}; ov = [r for r in rows if r['case_id'] in A29]; dif = [abs((r.get('auc_tol_position') if r.get('auc_tol_position') is not None else -9) - (A29[r['case_id']].get('auc_tol_position') if A29[r['case_id']].get('auc_tol_position') is not None else -9)) for r in ov]
    sel38 = {s['case_id'] for s in S38.s24.selection()}; res['consistency'] = dict(step38_scans=len(sel38), step38_scans_in_new_set=len(sel38 & {r['case_id'] for r in rows}), overlap_rows=len(ov), n_position_auroc_differs=int(sum(d > 1e-9 for d in dif)), max_abs_diff=float(max(dif)) if dif else None)
    # (b)
    cal = fit_platt(val_rows); res['b'] = dict(platt=cal, val_position_correct={o: float(np.mean([r['y'] for r in val_rows if r['organ'] == o])) for o in ('breast', 'thyroid')}, pooled=calib_block(rows, cal), organs={o: calib_block([r for r in rows if r['organ'] == o], cal) for o in ('breast', 'thyroid')}, risk_coverage=risk_coverage(rows, cal))
    res['seconds'] = round(time.time() - t0); json.dump(res, open(os.path.join(OUT, 'results.json'), 'w'), indent=1); print('saved results.json', res['seconds'], 's')

if __name__ == '__main__':
    {'run': main}[sys.argv[1]]()
