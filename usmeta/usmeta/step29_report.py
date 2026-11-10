"""Step 29 report: results/partA/step29_segmentation/results.md, results.json, run_info.json from the saved json (no model calls)."""
import os, json, sys, platform, time, subprocess, collections
import numpy as np
from . import step29_seg as G
from .step10d_analysis import gboot
D = G.OUT; ROOT = G.ROOT; MIN_G = 30
A = json.load(open(os.path.join(D, 'a_rows.json'))); R = A['rows']; B = json.load(open(os.path.join(D, 'b_rows.json'))); ANN = json.load(open(os.path.join(D, 'b_annotation.json'))); C = json.load(open(os.path.join(ROOT, 'results', 'partA', 'step24_box_reliability', 'case_rows.json')))['rows']
TR = {n: json.load(open(os.path.join(D, f'train_{n}.json'))) for n in ('breast', 'thyroid', 'hc18')}
def ci(a, k=2, mark=None):
    if not a: return '—'
    s = f'{a[0]:.{k}f} ({a[1]:.{k}f}–{a[2]:.{k}f})'; return s + (' †' if mark else '')
def agg(rows, key):
    v = [(r[key], r['group']) for r in rows if r.get(key) is not None]
    if not v: return None, 0
    g = gboot([x for x, _ in v], [y for _, y in v]); return g, len({y for _, y in v})
def cell(rows, key):
    g, n = agg(rows, key); return ci(g, 2, n < MIN_G) if g else '—'
ids = {r['case_id'] for r in R}; ORG = [('breast', 'breast'), ('thyroid', 'thyroid'), (None, 'pooled')]
sub = lambda rows, o: [r for r in rows if o is None or r['organ'] == o]
res = {}
md = ['# Step 29: label-free image check by segmentation (replaces Step 23)', '',
      'Limitations: [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md). Code: `usmeta/step29_seg.py` (U-Net, training), `step29_run.py` (test pass), `step29_report.py` (new files; `partb.py`, `location.py`, `layer3.py`, `step20.py`, `step24_box_reliability.py` imported unchanged). Test split read once (logged: `usmeta.step29_run`). Training on DEV only, early stopping and post-processing chosen on VAL.', '',
      '**What it is.** A small U-Net (ResNet-18 encoder, **random init**: no pretrained weights were cached and none were downloaded; 256x256 input, flips + contrast / brightness / gamma augmentation, AdamW, BCE + Dice, at most 30 epochs, early stopping on val Dice) learns to find the lesion from the image alone, one model per organ. Its mask goes through the same measurement code as the MedSAM masks (`partb.pred_meas`) and the Step 20 tolerance-aware image check (tau 0.3, adjacent position, frozen on dev/val; the exact Step 16 rule is shown too). An **empty prediction counts as "no lesion found"**. No label, box or true mask is used at test time.', '']
# ---------------- 29a headline numbers
rows_all = {o: sub(R, o) for o, _ in ORG}; pos = {n: agg(rows_all[o], 'auc_tol_position') for o, n in ORG}; siz = {n: agg(rows_all[o], 'auc_tol_size') for o, n in ORG}; allc = {n: agg(rows_all[o], 'auc_tol_all') for o, n in ORG}
dec = lambda x: 'works label-free (>= 0.80)' if x >= 0.80 else 'partial (0.55-0.80)' if x > 0.55 else 'no (<= 0.55)'
pp = pos['pooled'][0][0]; ob = np.mean([r['auc_tol_position'] for r in C if r['cond'] == 'exact' and r['auc_tol_position'] is not None])
res['decision'] = dict(position_auroc_pooled=pos['pooled'][0], verdict=dec(pp), per_organ={n: dict(position=pos[n][0], verdict=dec(pos[n][0][0])) for n in ('breast', 'thyroid')})
bh = B['summary']; U = lambda k: np.mean([x[k] for x in B['per_case'] if x.get(k) is not None])
md += ['## Decision line', '',
       f"**29a: position AUROC {ci(pos['pooled'][0])} pooled over the 228 test scans, so by the rule of the brief (>= 0.80 works, 0.55-0.80 partial, <= 0.55 no) the check {dec(pp)}: breast {ci(pos['breast'][0])} ({dec(pos['breast'][0][0])}); thyroid {ci(pos['thyroid'][0])} ({dec(pos['thyroid'][0][0])}, on the boundary: its interval spans 0.80).** Compared with the oracle-box MedSAM check (position {ob:.2f}) it loses little on breast and about 0.15 on thyroid; the label-free boxes of Step 21a were at 0.31-0.54 and the U-Net is far above them. Size and all-checkable AUROC are lower (pooled {ci(siz['pooled'][0])} and {ci(allc['pooled'][0])}). It works because the lesion in these datasets is a single, mostly high-contrast object, and the model was trained on the same datasets (see caveats: no patient ids in several, so patient overlap with test cannot be excluded). It is not shown on other scanners, other datasets or lesions that are small or isoechoic.",
       f"**29b: head circumference from the U-Net head mask has MAE {bh['mae_mm']:.2f} mm on the 400 HC18 test images (median {bh['median_abs_mm']:.2f}, 90th percentile {bh['p90_abs_mm']:.2f}; mask Dice {bh['mean_dice']:.3f}).** With the exact Step 16 rule the planted-HC-error check reaches AUROC {U('unet|exact|bench_errors'):.2f} (bench errors) and {U('unet|exact|planted'):.2f} (planted +-1 / +-40 mm and x0.5-x2.0), but the **tolerance-aware rule (tau 0.3) cannot see HC errors at all (AUROC {U('unet|tol|bench_errors'):.2f}, the same as with the exact labelled HC): a 30% tolerance is wider than almost every planted HC error, so that rule is the wrong tool for head circumference.** The oracle-geometry numbers (HC taken from the label, or from the true annotation) are **circular** by construction (1.00 with the exact rule). FetalHead has no pixel size: **not testable**.", '',
       '## Training (DEV only; leaky dev images dropped; chosen on VAL)', '',
       '| model | dev images | dropped (8-bit cluster reaches val / test) | trained on | val images | epochs run | best val Dice (256 px) | post-processing chosen on val |', '|---|---|---|---|---|---|---|---|']
for n in ('breast', 'thyroid', 'hc18'): t = TR[n]; md.append(f"| {n} | {t['dev_total']} | {t['dev_dropped_leaky']} | {t['dev_trained']} | {t['val_n']} | {t['epochs_run']} | {t['best_val_dice_256']:.3f} | threshold {t['chosen']['threshold']}, {t['chosen']['keep']} |")
md += ['', 'Training images are the dev images with a real mask (breast: BrEaST, BUS-BRA, BUSI, UDIAT, BUS-UCLM; thyroid: TN3K, DDTI). TN5000 has boxes only, so it is **not** in training and its 30 test scans are cross-dataset; ' + f"epoch time and seeds are in `train_*.json` (seed 0, MPS).", '',
       '## 29a-1. Segmentation quality on the 228 test scans (against the true mask; TN5000: box IoU)', '', '| group | scans | found (non-empty) | Dice | IoU |', '|---|---|---|---|---|']
for o, n in ORG:
    rr = sub(R, o); mk = [r for r in rr if r['has_true_mask']]; md.append(f"| {n} | {len(rr)} | {np.mean([r['found'] for r in rr])*100:.0f}% | {cell(mk, 'dice')} (n = {len(mk)}) | {cell(mk, 'iou')} |")
md += ['', '| dataset | scans | found | Dice (mean, 95% CI) | IoU | box IoU (TN5000) |', '|---|---|---|---|---|---|']
for ds in dict.fromkeys(r['dataset'] for r in R):
    rr = [r for r in R if r['dataset'] == ds]; mk = [r for r in rr if r['has_true_mask']]
    md.append(f"| {ds} | {len(rr)} | {np.mean([r['found'] for r in rr])*100:.0f}% | " + (f"{cell(mk, 'dice')} | {cell(mk, 'iou')} | — |" if mk else f"— | — | {cell(rr, 'box_iou')} |") + ' (30 scans per dataset: † under 30 groups where marked)')
md += ['', 'Detection rate = share of scans where the model returned a non-empty mask (every test scan contains a lesion). A non-empty mask can still be in the wrong place; position agreement with the true mask (same code as the image check): ' + ', '.join(f"{n} {np.mean([r['pos_agree'] for r in sub(R, o)])*100:.0f}%" for o, n in ORG[:2]) + '.', '']
# ---------------- 29a-2 image check side by side
def crow(name, rows):
    return f"| {name} | " + ' | '.join(cell(rows, k) for k in ('auc_tol_position', 'auc_tol_size', 'auc_tol_all', 'correct_tol')) + ' | ' + ' | '.join(cell(rows, k) for k in ('auc_exact_position', 'auc_exact_all')) + ' |'
def conds(c): return [r for r in C if r['cond'] == c and r['case_id'] in ids]
def jit():
    out = []
    for r in C:
        if r['cond'] == 'jitter0.2_s0' and r['case_id'] in ids: out.append(dict(r))
    return out
md += ['## 29a-2. Image check, side by side (same 228 scans; AUROC of planted error vs harmless rewording; 95% CI by group bootstrap, 1,000, seed 0)', '',
       'Columns: Step 20 tolerance-aware rule (position / size / all-checkable AUROC and correct-report score = mean score of the identical copies), then the exact Step 16 rule (position / all-checkable). Rows below the U-Net come from saved Step 24 / 21a runs, unchanged.', '']
for o, n in ORG:
    md += [f'### {n}', '', '| source | position (tol) | size (tol) | all-checkable (tol) | correct-report score (tol) | position (exact) | all-checkable (exact) |', '|---|---|---|---|---|---|---|', crow('**U-Net, label-free (this step)**', sub(R, o))]
    for nm, cn in (('oracle-box MedSAM (Step 24 exact box)', 'exact'), ('true box x0.5 (Step 24 shrink)', 'shrink0.5'), ('true box shifted 50% of width (Step 24)', 'shift0.5'), ('true box jitter 20% (Step 24, seed 0)', 'jitter0.2_s0'), ('label-free: centre 50% box (Step 21a)', 'centre50'), ('label-free: whole image (Step 21a)', 'whole'), ('label-free: random box (Step 21a)', 'random'), ('label-free: wrong region (Step 21a)', 'wrongregion')): md.append(crow(nm, sub(conds(cn), o)))
    md.append('')
md += ['## 29a-3. U-Net vs oracle-box MedSAM, per dataset (position AUROC, tolerance rule)', '', '| dataset | scans | U-Net | oracle-box MedSAM |', '|---|---|---|---|']
for ds in dict.fromkeys(r['dataset'] for r in R): md.append(f"| {ds} | {len([r for r in R if r['dataset'] == ds])} | {cell([r for r in R if r['dataset'] == ds], 'auc_tol_position')} | {cell([r for r in conds('exact') if r['dataset'] == ds], 'auc_tol_position')} |")
md += ['', '† = under 30 groups (every dataset cell has at most 30 scans and the groups are fewer): **too small to compare**; only the organ and pooled rows have 30 or more groups.', '']
# ---------------- 29b
ann = ANN
md += ['## 29b-1. HC18: ring annotation to head circumference (no model)', '',
       'The annotation is a one-pixel ring. It was filled (`binary_fill_holes`), an ellipse was fitted, and the circumference computed with the Ramanujan formula and the pixel size from the CSV, then compared with the provided HC (mm). Three ways of fitting the ellipse; the one used for predicted masks was chosen on dev + val only.', '',
       '| ellipse fit | split | images | MAE (mm) | median abs (mm) | mean signed error (mm) | max abs (mm) |', '|---|---|---|---|---|---|---|']
for m, nm in (('moments_filled', 'second moments of the filled mask'), ('fit_filled_contour', 'cv2.fitEllipse on the outer contour of the filled mask'), ('fit_ring_points', 'cv2.fitEllipse on the ring pixels')):
    for g, gn in (('devval', 'dev + val'), ('test', 'test')): v = ann[g][m]; md.append(f"| {nm} | {gn} | {v['n']} | {v['mae_mm']:.3f} | {v['median_abs_mm']:.3f} | {v['signed_mean_mm']:+.3f} | {v['max_abs_mm']:.2f} |")
md += ['', f"Fitting the ellipse to the ring pixels reproduces the provided HC to {ann['all']['fit_ring_points']['mae_mm']:.3f} mm on average (max {ann['all']['fit_ring_points']['max_abs_mm']:.2f} mm over all 999 images): the dataset HC was derived this way. A filled-mask outline reads {ann['devval']['fit_filled_contour']['signed_mean_mm']:+.2f} mm too large (half the ring thickness), the second-moment ellipse is worse (MAE {ann['devval']['moments_filled']['mae_mm']:.2f} mm, with outliers up to {ann['all']['moments_filled']['max_abs_mm']:.0f} mm for non-elliptic rings). Predicted masks have no ring, so they use the filled-contour fit with a constant {B['summary']['correction_mm']:+.2f} mm calibrated on dev + val true masks.", '',
       '## 29b-2. U-Net head masks, HC on the 400 HC18 test images', '',
       '| quantity | value |', '|---|---|', f"| images (test split) | {bh['n_test']} (non-empty masks: {bh['found']}) |", f"| mask Dice / IoU | {bh['mean_dice']:.3f} / {bh['mean_iou']:.3f} |", f"| **HC MAE** (mm) | **{bh['mae_mm']:.2f}** |", f"| median / 90th percentile absolute error (mm) | {bh['median_abs_mm']:.2f} / {bh['p90_abs_mm']:.2f} |",
       f"| MAE without the dev-calibrated constant (mm) | {bh['mae_uncorrected_mm']:.2f} |", f"| MAE of the same geometry on the TRUE filled masks (mm) | {bh['mae_truemask_geometry_mm']:.2f} |", '',
       f"Most of the 2.7 mm comes from the segmentation, not the geometry (0.21 mm on true masks). For scale, the planted HC errors in the benchmark are 3-30 mm and x0.5-x2.0, and the +-1 mm errors are below this MAE.", '',
       '## 29b-3. Planted HC errors vs harmless rewordings (150 HC18 test cases, 1,500 harmless candidates)', '',
       'Planted errors: the 600 benchmark HC errors (3-30 mm shifts and factors) and up to 11 extra candidates per case built here by changing only the number in the reference: +-1 mm, +-40 mm, x0.5, 0.75, 0.9, 1.1, 1.25, 1.5, 2.0. AUROC = P(error scores lower than a harmless rewording of the same reference), per case, 95% CI by case bootstrap. **"Label oracle" and "true-mask geometry" are circular: the measurement is the reference HC (or a refit of the annotation that defined it).**', '',
       '| measurement source | rule | benchmark HC errors | planted +-1/40 mm and x0.5-x2.0 | planted shifts (mm) | planted factors | correct-report score |', '|---|---|---|---|---|---|---|']
G_ = lambda k: (lambda v: ci(gboot(v, list(range(len(v)))), 2) if v else '—')([x[k] for x in B['per_case'] if x.get(k) is not None])
for src, sn in (('unet', 'U-Net mask (label-free)'), ('true_mask_geometry', 'true annotation geometry (circular)'), ('label_oracle', 'labelled HC (circular)')):
    for var, vn in (('exact', 'exact (Step 16)'), ('tol', 'tolerance-aware (tau 0.3)')): md.append(f"| {sn} | {vn} | {G_(f'{src}|{var}|bench_errors')} | {G_(f'{src}|{var}|planted')} | {G_(f'{src}|{var}|planted_shift_mm')} | {G_(f'{src}|{var}|planted_factor')} | {G_(f'{src}|{var}|correct')} |")
md += ['', '**Reading.** The tolerance-aware rule gives 0.52 for every source, even the labelled HC: with tau = 0.3 an HC of 180 mm is accepted anywhere between 126 and 234 mm, so almost no planted error is seen. (tau was tuned on breast and thyroid size, not on head circumference; no other tau was tried here.) With the exact rule the U-Net check works for large errors and is blind to small ones:', '',
       '| planted error | AUROC with the U-Net mask (exact rule), mean over cases |', '|---|---|']
lv = collections.defaultdict(list)
for x in B['per_case']:
    for k, v in x.items():
        if k.startswith('unet|exact|lvl|') and v is not None: lv[k.split('|', 3)[3]].append(v)
def key(s): kd, l = s.split('|'); return (kd, float(l))
for k in sorted(lv, key=key): md.append(f"| {k.replace('|', ' ')} | {np.mean(lv[k]):.2f} (n = {len(lv[k])} cases) |")
md += ['', '(each level uses one error vs the case\'s harmless rewordings, so the cell is an average over cases, not a pooled bootstrap; levels that would make the HC non-positive were skipped. The planted-error check was first run with a text-placement bug (the new number was placed in only 59 of 150 references); it was recomputed from the saved predictions (`step29_run rescore_planted`), with no model run and no second read of the test split.)', '',
       '## 29b-4. FetalHead', '', 'FetalHead (2,833 images) has no pixel size, so head circumference in mm cannot be computed from a mask: **not testable**. Nothing was guessed or estimated for it.', '',
       '## Caveats', '',
       '- **Same-dataset test.** Train, val and test are different patients or groups only where the dataset has ids (BrEaST, BUS-BRA, BUS-UCLM, DDTI); BUSI, UDIAT, TN3K, TN5000 and HC18 have none, so near-identical images of one patient can sit on both sides despite the dHash grouping (<= 4 bits merged; dev images in <= 8-bit clusters that reach val or test were dropped, 15 breast, 148 thyroid, 26 HC18). TN5000 (no training images) is the only cross-dataset check.',
       '- **Small, random-init network, one seed, one split.** No pretrained encoder (weights not available offline; none downloaded). Val Dice is the selection signal; the test Dice and image-check numbers come from one run and have not been repeated.',
       '- **Image-check numbers are computed on the 228 scans of Step 21a / 24** (30 per dataset, at most 3 per group), not on all test images, and the reports being checked are our templated candidates. The check scores claims in the text against a measurement from the mask, so thyroid and breast positions are judged on a 3x3 grid.',
       '- **Thyroid truth for TN5000** is a box, so Dice is not defined there (box IoU instead); thyroid Dice rests on 60 scans.',
       '- **29b geometry:** the HC18 mask Dice is high (0.97) because the head is a large, clear object; the tolerance rule is shown but is not usable for HC; the planted +-1 mm errors cannot be detected at 2.7 mm MAE. The label-oracle and true-geometry rows are circular and are listed only to show the ceiling.',
       '- Step 23 (lesion detector) is not run; this step replaces it. No claim of being first; possible training exposure of none of the models here (all trained from scratch on our dev split).', '']
open(os.path.join(D, 'results.md'), 'w').write('\n'.join(md))
res.update(a_summary={n: dict(position=pos[n][0], size=siz[n][0], all=allc[n][0], groups=pos[n][1]) for n in pos}, b_summary=B['summary'], annotation={g: ann[g] for g in ('devval', 'test', 'all')}, training={n: {k: v for k, v in TR[n].items() if k != 'log'} for n in TR})
json.dump(res, open(os.path.join(D, 'results.json'), 'w'), indent=1)
def g(*c):
    try: return subprocess.check_output(c, text=True, cwd=ROOT).strip()
    except Exception: return None
json.dump(dict(step='29', model='U-Net, torchvision resnet18 encoder, random init', seed=G.SEED, git_head_at_report=g('git', 'rev-parse', '--short', 'HEAD'), python=sys.version.split()[0], platform=platform.platform(), date=time.strftime('%Y-%m-%d'), bootstrap='group (scan group), 1000 resamples, seed 0', min_groups=MIN_G, test_scans=len(R), hc18_test_images=B['summary']['n_test']), open(os.path.join(D, 'run_info.json'), 'w'), indent=1)
print('wrote results.md', len(md))
