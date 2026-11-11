"""Step 31 report: results/partA/step31_cross_dataset/results.md, results.json, run_info.json (no model calls)."""
import os, json, sys, platform, time, subprocess
import numpy as np
from . import step29_seg as G, step31_cross_dataset as S
from .step10d_analysis import gboot
D = S.OUT; MIN_G = 30
A = json.load(open(os.path.join(D, 'rows.json'))); R = A['rows']; IN = {r['case_id']: r for r in json.load(open(os.path.join(G.OUT, 'a_rows.json')))['rows']}
TR = {h: json.load(open(os.path.join(D, f'train_{S.name_of(h)}.json'))) for h in S.BREAST}; T29 = json.load(open(os.path.join(G.OUT, 'train_breast.json')))
def agg(rows, key):
    v = [(r[key], r['group']) for r in rows if r.get(key) is not None]
    if not v: return None, 0
    return gboot([x for x, _ in v], [y for _, y in v]), len({y for _, y in v})
def cell(rows, key):
    g, n = agg(rows, key); return '—' if not g else f"{g[0]:.2f} ({g[1]:.2f}–{g[2]:.2f})" + (' †' if n < MIN_G else '')
dec = lambda x: 'works label-free (>= 0.80)' if x >= 0.80 else 'partial (0.55-0.80)' if x > 0.55 else 'no (<= 0.55)'
insame = lambda rows: [IN[r['case_id']] for r in rows if r['case_id'] in IN]
res = {}; pooled_pos, ng = agg(R, 'auc_tol_position'); inpool_pos, _ = agg(insame(R), 'auc_tol_position')
per = {}
for h in S.BREAST:
    rr = [r for r in R if r['dataset'] == h]; ir = insame(rr); p, n = agg(rr, 'auc_tol_position'); ip, _ = agg(ir, 'auc_tol_position')
    per[h] = dict(scans=len(rr), groups=n, position=p, in_dataset_position=ip, dice=agg(rr, 'dice')[0], in_dataset_dice=agg(ir, 'dice')[0], found=float(np.mean([r['found'] for r in rr])), in_dataset_found=float(np.mean([r['found'] for r in ir])))
res.update(pooled_position=pooled_pos, pooled_groups=ng, in_dataset_pooled_position=inpool_pos, verdict=dec(pooled_pos[0]), per_dataset=per)
cols = [('dice', 'Dice'), ('iou', 'IoU')]
md = ['# Step 31: cross-dataset segmenter (breast, leave-one-dataset-out)', '',
      'Limitations: [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md). Code: `usmeta/step31_cross_dataset.py`, `step31_report.py` (new files; `step29_seg.py` training code, `step29_run.py` scoring, the Step 20 check imported unchanged). Test split read once (logged: `usmeta.step31_cross_dataset`). Dev-only training, val tuning.', '',
      '**What it is.** For each held-out breast dataset the Step 29 U-Net (same architecture, settings, augmentation, early stopping, leak filter) is trained on the **dev** images of the other four breast datasets only, early stopping and the threshold / largest-component choice are made on the **val** images of the same four, and the Step 20 tolerance-aware image check (tau 0.3, adjacent position; same code as Steps 24 / 29) is run on the held-out dataset\'s test scans, the same 138 scans as in Step 29 (30 per dataset, BUS-UCLM 18). No image of the held-out dataset was used for training, early stopping or tuning. An empty prediction counts as "no lesion found".', '',
      '## Decision line', '',
      f"**Pooled over the five held-out datasets (138 scans, each scored by the model that never saw its dataset), position AUROC is {pooled_pos[0]:.2f} ({pooled_pos[1]:.2f}-{pooled_pos[2]:.2f}), against {inpool_pos[0]:.2f} ({inpool_pos[1]:.2f}-{inpool_pos[2]:.2f}) for the in-dataset Step 29 model on the same scans: by the rule of the brief (>= 0.80 works, 0.55-0.80 partial, <= 0.55 no) the check {dec(pooled_pos[0])} across datasets.** Per held-out dataset (30 scans each, so every per-dataset cell is under 30 groups: **too small to compare**, shown for orientation): " + '; '.join(f"{h} {per[h]['position'][0]:.2f} (in-dataset {per[h]['in_dataset_position'][0]:.2f})" for h in S.BREAST if per[h]['position']) + '.', '',
      '## Training per fold (DEV of the other four datasets; VAL of the same four)', '', '| held out | trained on | dev images (after leak filter and mask check) | val images | epochs | best val Dice (256 px) | post-processing chosen on val | minutes |', '|---|---|---|---|---|---|---|---|']
for h in S.BREAST: t = TR[h]; md.append(f"| {h} | {', '.join(t['train_datasets'])} | {t['dev_trained']} (dev {t['dev_total']}, dropped {t['dev_dropped_leaky']}) | {t['val_n']} | {t['epochs_run']} | {t['best_val_dice_256']:.3f} | threshold {t['chosen']['threshold']}, {t['chosen']['keep']} | {t['seconds']/60:.0f} |")
md += ['', f"For reference the Step 29 breast model (all five datasets): {T29['dev_trained']} dev images, {T29['val_n']} val images, {T29['epochs_run']} epochs, best val Dice {T29['best_val_dice_256']:.3f}. Fold time cap 1 h: " + ('no fold reached it' if all(TR[h]['seconds'] < 3600 for h in S.BREAST) else 'a fold reached the cap (see minutes)') + '.', '',
       '## Cross-dataset vs in-dataset, per held-out dataset (same test scans)', '', '| held-out dataset | scans | Dice cross (95% CI) | Dice in-dataset (Step 29) | detection cross / in-dataset | position AUROC cross | position AUROC in-dataset | size AUROC cross | size in-dataset | all-checkable cross | all-checkable in-dataset | correct-report score cross | in-dataset |', '|---|---|---|---|---|---|---|---|---|---|---|---|---|']
for h in S.BREAST + [None]:
    rr = [r for r in R if h is None or r['dataset'] == h]; ir = insame(rr); nm = 'pooled (5 datasets)' if h is None else h
    md.append(f"| {nm} | {len(rr)} | {cell(rr, 'dice')} | {cell(ir, 'dice')} | {np.mean([r['found'] for r in rr])*100:.0f}% / {np.mean([r['found'] for r in ir])*100:.0f}% | {cell(rr, 'auc_tol_position')} | {cell(ir, 'auc_tol_position')} | {cell(rr, 'auc_tol_size')} | {cell(ir, 'auc_tol_size')} | {cell(rr, 'auc_tol_all')} | {cell(ir, 'auc_tol_all')} | {cell(rr, 'correct_tol')} | {cell(ir, 'correct_tol')} |")
md += ['', '† = under 30 groups: too small to compare (each dataset has 30 scans or fewer, 18 for BUS-UCLM; only the pooled row reaches 30 groups). Dice and position agreement use the true mask of the scan; detection = share of non-empty predictions (every test scan contains a lesion).', '',
       '## Exact-rule variant (Step 16 exact match, for reference)', '', '| held-out dataset | position AUROC cross | in-dataset | all-checkable cross | in-dataset | correct-report score (exact) cross | in-dataset |', '|---|---|---|---|---|---|---|']
for h in S.BREAST + [None]:
    rr = [r for r in R if h is None or r['dataset'] == h]; ir = insame(rr); md.append(f"| {'pooled' if h is None else h} | {cell(rr, 'auc_exact_position')} | {cell(ir, 'auc_exact_position')} | {cell(rr, 'auc_exact_all')} | {cell(ir, 'auc_exact_all')} | {cell(rr, 'correct_exact')} | {cell(ir, 'correct_exact')} |")
drop = {h: per[h]['in_dataset_position'][0] - per[h]['position'][0] for h in S.BREAST if per[h]['position'] and per[h]['in_dataset_position']}
md += ['', '## Reading', '',
       f"- **Generalisation gap (position AUROC, in-dataset minus held-out):** pooled {inpool_pos[0] - pooled_pos[0]:+.2f}; by dataset " + ', '.join(f"{h} {v:+.2f}" for h, v in drop.items()) + '. Dice: ' + ', '.join(f"{h} {per[h]['dice'][0]:.2f} vs {per[h]['in_dataset_dice'][0]:.2f}" for h in S.BREAST if per[h]['dice']) + '.',
       '- The held-out datasets differ in scanner, patient population and image format (BrEaST, BUS-BRA, BUSI, UDIAT and BUS-UCLM come from different centres), so this is a different and harder test than Step 29, where the same datasets appear in training and test (different groups only where patient ids exist).',
       '', '## Caveats', '',
       '- **30 scans per held-out dataset (BUS-UCLM 18) at most 3 per group:** per-dataset cells are too small to compare; only the pooled row has 30 or more groups. One seed, one split, no repeat; random-init encoder (no pretrained weights), as in Step 29.',
       '- **Leave-one-dataset-out removes a dataset, not its patients\' look-alikes elsewhere**: other datasets can contain similar scanners or public re-uses of the same images (Step 10a found no cross-dataset duplicates at <= 4 bits; the leak filter only drops dev images whose <= 8-bit clusters reach val or test inside one dataset).',
       '- Breast only; thyroid and fetal head were not run. The image-check numbers are scored on our templated candidates and on the 228-scan selection of Steps 21a / 24 (breast part).',
       '- Fold epochs may differ from Step 29 because of early stopping on the other four datasets\' val images; the 30-epoch maximum and 1 h cap were the same or tighter.', '']
open(os.path.join(D, 'results.md'), 'w').write('\n'.join(md))
json.dump(res, open(os.path.join(D, 'results.json'), 'w'), indent=1)
def g(*c):
    try: return subprocess.check_output(c, text=True, cwd=G.ROOT).strip()
    except Exception: return None
json.dump(dict(step='31', seed=G.SEED, folds=S.BREAST, git_head_at_report=g('git', 'rev-parse', '--short', 'HEAD'), python=sys.version.split()[0], platform=platform.platform(), date=time.strftime('%Y-%m-%d'), bootstrap='group, 1000 resamples, seed 0', min_groups=MIN_G, test_scans=len(R)), open(os.path.join(D, 'run_info.json'), 'w'), indent=1)
print('wrote results.md', len(md))
