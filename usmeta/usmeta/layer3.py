"""Step 8 Layer 3: image / location check against the TRUE masks (Test 1, core). Scorers on bench_loc rows (text + boxes):
  location_check      best-match box IoU (Hungarian) between candidate boxes and true boxes
  grounded_check      finding_f1(text vs reference) x location_check   (a report is only as good as its worst part: both must be right)
  mask_verified_facts share of the text's mask-checkable claims (lesion presence, count, image position, orientation, size) that the TRUE mask backs (credit >= 0.5)
  semacc              UltraG-Bench-style yes/no checks (presence, category, location, size): mean over the checks that apply   [idea: UltraG-Bench; cite, not new]
  box_support         spatial support: 1 if >= 50% of the candidate box area lies inside the true region (mean over boxes), plus pixel precision / recall
  oracle_label_check  finding_f1: text vs the reference built from dataset labels (the old 'evidence_check' idea; upper bound)
and the Layer 0 text scorers looked up from the Step 4/5 score files.
HONESTY: pos/size/orientation in the reference were measured from these same masks with the same code, so mask_verified_facts on text cannot fail
on true text: Test 1 shows what the check catches when a mask is available. The real test is with PREDICTED masks (Part B)."""
import json, sys, os, collections, argparse
import numpy as np
from scipy.stats import spearmanr
from . import location, schema, templates_v2 as T, unified, layer0
from .layer0 import auroc_case, boot

def measured_facts(rec, mask):
    """facts re-measured from the mask file (falls back to the record's region when no mask file: TN5000 boxes, DDTI outlines)"""
    r = rec['region']
    if mask is not None and mask.any(): r = unified.region_feats(mask, kind=r['kind'])
    rec2 = dict(rec, region=r); f = T.facts(rec2); return {k: v[0] for k, v in f.items()}, r

CHECK = ('lesion', 'count', 'pos', 'orient', 'size_mm', 'size_pct', 'hc_mm')
def mask_verified(text, organ, meas):
    """(share of checkable claims backed, n claims, n backed)"""
    claims = {k: v for k, v in schema.extract_rule(text, organ).items() if k in CHECK}; n = b = 0; cred = []
    for k, v in claims.items():
        m = meas.get(k)
        if m is None: continue
        if k == 'count' and organ == 'thyroid': m = min(m, 3)    # the thyroid wording stops at 'three or more nodules'
        c = schema.attr_credit(k, m, v) if k in ('size_mm', 'size_pct', 'hc_mm') else float(str(m) == str(v)); n += 1; b += c >= 0.5; cred.append(c)
    return (float(np.mean(cred)) if cred else None), n, b

def semacc(text, rec, meas):
    c = schema.extract_rule(text, rec['organ']); out = []
    out.append(float((c.get('lesion') == 'present') == (meas.get('lesion') == 'present')))                                  # presence
    lab = rec['labels'].get('cls')
    if lab in ('benign', 'malignant') and 'path' in c or (lab in ('benign', 'malignant') and meas.get('lesion') == 'present'): out.append(float(c.get('path') == lab))   # category
    if meas.get('pos'): out.append(float(c.get('pos') == meas['pos']))                                                    # location
    for k in ('size_mm', 'size_pct', 'hc_mm'):                                                                              # size (within the 50% credit band)
        if k in meas: out.append(float(schema.attr_credit(k, meas[k], c.get(k)) >= 0.5)); break
    return float(np.mean(out))

def box_support(boxes, mask, gt_boxes):
    """(share of boxes with >= 50% of their area inside the true region, pixel precision, pixel recall)"""
    if not boxes: return 0.0, 0.0, 0.0
    inside = [location.inside_fraction(b, mask) >= 0.5 for b in boxes]; union = np.zeros_like(mask, bool)
    for b in boxes:
        x0, y0, x1, y1 = [int(round(v)) for v in b]; union[max(y0, 0):max(y1, 0), max(x0, 0):max(x1, 0)] = True
    inter = (union & mask).sum(); return float(np.mean(inside)), float(inter / union.sum()) if union.sum() else 0.0, float(inter / mask.sum()) if mask.sum() else 0.0

def score_rows(rows, text_scores=None):
    recs = {}
    for ds in sorted({r['dataset'] for r in rows}):
        for c in unified.load({'BUS-BRA': 'BUSBRA', 'BUS-UCLM': 'BUSUCLM'}.get(ds, ds)): recs[c['case_id']] = c
    ctx = {}; out = []
    for r in rows:
        cid = r['case_id']
        if cid not in ctx:
            rec = recs[cid]; m = location.gt_mask(rec)
            if m is None:   # boxes only (TN5000) or outline datasets: rasterise the true boxes as the true region
                m = np.zeros((rec['region']['H'], rec['region']['W']), bool)
                for b in rec['region']['boxes']: m[int(b[1]):int(b[3]), int(b[0]):int(b[2])] = True
            meas, reg = measured_facts(rec, m); ctx[cid] = (rec, m, meas)
        rec, m, meas = ctx[cid]; s = {}
        s['location_check'] = location.best_match_iou(r['gt_boxes'], r['boxes'])
        f1 = schema.finding_scores(schema.to_findings(schema.extract_rule(r['reference'], r['organ']), r['organ']), schema.to_findings(schema.extract_rule(r['candidate'], r['organ']), r['organ']))[2]
        s['oracle_label_check'] = f1; s['grounded_check'] = f1 * s['location_check']
        mv, nclaims, nback = mask_verified(r['candidate'], r['organ'], meas); s['mask_verified_facts'] = mv if mv is not None else 1.0; s['_claims'] = nclaims; s['_backed'] = nback
        s['semacc'] = semacc(r['candidate'], rec, meas)
        s['box_support'], s['pixel_precision'], s['pixel_recall'] = box_support(r['boxes'], m, r['gt_boxes'])
        gtm = np.zeros_like(m, bool)
        for b in r['gt_boxes']: gtm[int(b[1]):int(b[3]), int(b[0]):int(b[2])] = True
        s['box_support_gtbox'] = box_support(r['boxes'], gtm, r['gt_boxes'])[0]   # same 50% rule against the TRUE BOX region (a tight box of an irregular mask fills < 50% of itself)
        s['mask_iou_true_vs_true'] = location.mask_iou(m, m); s['dice_true_vs_true'] = location.dice(m, m)
        out.append(s)
    return out

SCORERS = ['bleu', 'rougeL', 'chrf', 'bertscore[roberta-large]', 'ratescore', 'oracle_label_check', 'mask_verified_facts', 'semacc', 'location_check', 'grounded_check', 'box_support', 'box_support_gtbox']

def analyse(rows, S):
    res = {}; by = collections.defaultdict(lambda: collections.defaultdict(list))
    for r, s in zip(rows, S): by[r['dataset']][r['case_id']].append((r, s))
    for ds, cases in by.items():
        for name in SCORERS:
            A, H, I, SEV = [], [], [], []; byg = collections.defaultdict(list); gh = collections.defaultdict(list)
            for cid, rs in cases.items():
                e = [s[name] for r, s in rs if r['kind'] == 'error']; h = [s[name] for r, s in rs if r['kind'] == 'harmless']
                I += [s[name] for r, s in rs if r['kind'] == 'identical']; H += h
                if e and h: A.append(auroc_case(e, h))
                if h:
                    for g in {r['group'] for r, s in rs if r['kind'] == 'error'}: byg[g].append(auroc_case([s[name] for r, s in rs if r['group'] == g and r['kind'] == 'error'], h))
                SEV += [(r['severity'], s[name]) for r, s in rs if r['kind'] == 'error']
            sv = [a for a, _ in SEV]; sc = [b for _, b in SEV]
            rho = float(spearmanr(sv, sc)[0]) if len(set(sv)) > 1 and len(set(sc)) > 1 else None
            res.setdefault(ds, {})[name] = dict(n_cases=len(cases), auroc=boot(A) if A else None, harmless_mean=float(np.mean(H)) if H else None,
                identical_mean=float(np.mean(I)), identical_min=float(np.min(I)), severity_rho=rho, auroc_by_group={g: float(np.mean(v)) for g, v in byg.items()})
    return res

def run(bench='bench_loc.jsonl', layer0_scores='scores_v2d_layer0.json'):
    rows = [json.loads(l) for l in open(bench)]; S = score_rows(rows); L0 = json.load(open(layer0_scores)); idx = {tuple(p): i for i, p in enumerate(L0['pairs'])}; miss = 0
    for r, s in zip(rows, S):
        i = idx.get((r['reference'], r['candidate']))
        if i is None: miss += 1
        for n, arr in L0['scores'].items(): s[n] = float(arr[i]) if i is not None else float('nan')
    return rows, S, miss

def tables(res):
    out = []
    for ds, d in res.items():
        out += [f'### {ds} ({next(iter(d.values()))["n_cases"]} cases)', '', '| scorer | AUROC (95% CI) | box-only | text position (box right) | text position + box moved | size | harmless mean | identical mean | severity ρ |', '|---|---|---|---|---|---|---|---|---|']
        fm = lambda x: '—' if x is None else (f'{x[0]:.2f} ({x[1]:.2f}–{x[2]:.2f})' if isinstance(x, tuple) else f'{x:.2f}')
        for n, v in d.items():
            g = v['auroc_by_group']
            out.append(f"| {n} | {fm(v['auroc'])} | {fm(g.get('box_only'))} | {fm(g.get('text_pos'))} | {fm(g.get('text_pos_box'))} | {fm(g.get('size'))} | {fm(v['harmless_mean'])} | {v['identical_mean']:.4f} | {fm(v['severity_rho'])} |")
        out.append('')
    return out

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); a = ap.parse_args()
    rows, S, miss = run(); res = analyse(rows, S); os.makedirs(a.out, exist_ok=True)
    json.dump(res, open(os.path.join(a.out, 'results_partA_layer3.json'), 'w'), indent=1)
    open(os.path.join(a.out, 'tables.md'), 'w').write('\n'.join(tables(res)))
    claims = collections.defaultdict(lambda: [0, 0])
    for r, s in zip(rows, S):
        if r['kind'] == 'identical': claims[r['dataset']][0] += s['_claims']; claims[r['dataset']][1] += s['_backed']
    sanity = {k: (min(s[k] for s in S), max(s[k] for s in S)) for k in ('mask_iou_true_vs_true', 'dice_true_vs_true')}
    json.dump(dict(rows=len(rows), text_pairs_missing=miss, claims_backed_on_true_text={k: v for k, v in claims.items()}, sanity=sanity), open(os.path.join(a.out, 'meta.json'), 'w'), indent=1)
    print('rows', len(rows), 'missing text pairs', miss, '| true-vs-true IoU/Dice', sanity, '| identical gate min', min(v['identical_min'] for d in res.values() for v in d.values()))
