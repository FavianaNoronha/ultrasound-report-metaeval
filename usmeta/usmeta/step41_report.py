"""Step 41 report: results/partA/step41_thyroid_cross/results.md, results.json, run_info.json (no model calls). Decision rule from PREREG.md: a fold transfers iff position AUROC >= in-dataset - 0.05 AND 95% lower bound >= 0.70; a cell with < 30 groups is 'too small': indicative, not decided."""
import os, json, sys, platform, time, subprocess
import numpy as np
from . import step29_seg as G, step41_thyroid_cross as S
from .step10d_analysis import gboot
D = S.OUT; MIN_G = 30; TOL = 0.05; LB = 0.70
A = json.load(open(os.path.join(D, 'rows.json'))); R = A['rows']; IN = {r['case_id']: r for r in json.load(open(os.path.join(G.OUT, 'a_rows.json')))['rows']}
TR = {ds: json.load(open(os.path.join(D, f'train_thyroid_train_{ds}.json'))) for ds in S.THY}; T29 = json.load(open(os.path.join(G.OUT, 'train_thyroid.json')))
def agg(rows, key):
    v = [(r[key], r['group']) for r in rows if r.get(key) is not None]
    if not v: return None, 0
    return gboot([x for x, _ in v], [y for _, y in v]), len({y for _, y in v})
def cell(rows, key):
    g, n = agg(rows, key); return '—' if not g else f"{g[0]:.2f} ({g[1]:.2f}–{g[2]:.2f})" + (' †' if n < MIN_G else '')
insame = lambda rows: [IN[r['case_id']] for r in rows if r['case_id'] in IN]
folds = {}
for h in S.THY:
    rr = [r for r in R if r['dataset'] == h]; ir = insame(rr); p, n = agg(rr, 'auc_tol_position'); ip, ni = agg(ir, 'auc_tol_position')
    within = p[0] >= ip[0] - TOL; lower = p[1] >= LB; small = n < MIN_G
    folds[h] = dict(trained_on=S.other(h), scans=len(rr), groups_defined=n, position=p, in_dataset_position=ip, groups_in_dataset=ni, within_0_05=bool(within), lower_bound_ge_0_70=bool(lower), rule_would_pass=bool(within and lower), too_small=small,
                    decision=('too small (fewer than 30 groups): not decided; indicative rule outcome: ' + ('would transfer' if within and lower else 'would not transfer')) if small else ('transfers' if within and lower else 'does not transfer'),
                    dice=agg(rr, 'dice')[0], in_dataset_dice=agg(ir, 'dice')[0], found=float(np.mean([r['found'] for r in rr])), in_dataset_found=float(np.mean([r['found'] for r in ir])), correct=agg(rr, 'correct_tol')[0], in_dataset_correct=agg(ir, 'correct_tol')[0])
pooled, npool = agg(R, 'auc_tol_position'); ipool, _ = agg(insame(R), 'auc_tol_position')
f = lambda x: f"{x[0]:.2f} ({x[1]:.2f}-{x[2]:.2f})"
dl = []
for h in S.THY:
    o = folds[h]; dl.append(f"- **Train on {o['trained_on']} dev -> test on {h} ({o['scans']} scans, {o['groups_defined']} groups with a defined position AUROC): position AUROC {f(o['position'])} against {f(o['in_dataset_position'])} in-dataset (Step 29 model, same scans). Within 0.05 of in-dataset: {'yes' if o['within_0_05'] else 'no'}; lower bound >= 0.70: {'yes' if o['lower_bound_ge_0_70'] else 'no'}. Decision: {o['decision']}.**")
res = dict(folds=folds, pooled_position=pooled, pooled_groups=npool, in_dataset_pooled_position=ipool, rule=dict(tolerance=TOL, lower_bound=LB, min_groups=MIN_G))
md = ['# Step 41: does the label-free U-Net image check transfer between thyroid datasets?', '',
      'Pre-registration: [PREREG.md](PREREG.md) (committed before any training or test number). Limitations: [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md). Code: `usmeta/step41_thyroid_cross.py`, `step41_report.py` (new files; `step29_seg.py` training, `step29_run.py` scoring and the Step 20 check imported unchanged). Test split read once (logged: `usmeta.step41_thyroid_cross`).', '',
      '## Decision lines', ''] + dl + ['',
      f"Pooled over both folds (60 scans, descriptive only, no decision): position AUROC {f(pooled)} ({npool} groups" + (', under 30: too small' if npool < MIN_G else '') + f") against {f(ipool)} for the in-dataset Step 29 model on the same scans. Rule (fixed in the PREREG): a fold transfers iff position AUROC is within 0.05 of the in-dataset value on the same scans AND its 95% lower bound is >= 0.70; a cell under 30 groups is reported, not decided.", '',
      '**DDTI is small:** the DDTI-trained fold has about ' + f"{TR['DDTI']['dev_trained']} dev images against {TR['TN3K']['dev_trained']} for TN3K, so a weak DDTI-trained fold may reflect training-set size and not domain shift; this design cannot tell the two apart.", '',
      '## Training per fold (DEV of the training dataset; VAL of the same dataset)', '', '| trained on | tested on | dev images (after leak filter and mask check) | val images | epochs | best val Dice (256 px) | post-processing chosen on val | minutes |', '|---|---|---|---|---|---|---|---|']
for ds in S.THY: t = TR[ds]; md.append(f"| {ds} | {t['held_out']} | {t['dev_trained']} (dev {t['dev_total']}, dropped {t['dev_dropped_leaky']}) | {t['val_n']} | {t['epochs_run']} | {t['best_val_dice_256']:.3f} | threshold {t['chosen']['threshold']}, {t['chosen']['keep']} | {t['seconds'] / 60:.0f} |")
md += ['', f"For reference the Step 29 thyroid model (TN3K + DDTI): {T29['dev_trained']} dev images, {T29['val_n']} val images, {T29['epochs_run']} epochs, best val Dice {T29['best_val_dice_256']:.3f}. Fold time cap 1 h: " + ('no fold reached it.' if all(TR[d]['seconds'] < 3600 for d in S.THY) else 'a fold reached the cap (see minutes).'), '',
       '## Cross-dataset vs in-dataset on the same test scans', '', '| held-out dataset (trained on) | scans | Dice cross | Dice in-dataset (Step 29) | detection cross / in-dataset | position AUROC cross | position AUROC in-dataset | size AUROC cross | size in-dataset | all-checkable cross | all-checkable in-dataset | correct-report score cross | in-dataset |', '|---|---|---|---|---|---|---|---|---|---|---|---|---|']
for h in S.THY + [None]:
    rr = [r for r in R if h is None or r['dataset'] == h]; ir = insame(rr); nm = 'pooled (both folds)' if h is None else f"{h} (trained on {S.other(h)})"
    md.append(f"| {nm} | {len(rr)} | {cell(rr, 'dice')} | {cell(ir, 'dice')} | {np.mean([r['found'] for r in rr]) * 100:.0f}% / {np.mean([r['found'] for r in ir]) * 100:.0f}% | {cell(rr, 'auc_tol_position')} | {cell(ir, 'auc_tol_position')} | {cell(rr, 'auc_tol_size')} | {cell(ir, 'auc_tol_size')} | {cell(rr, 'auc_tol_all')} | {cell(ir, 'auc_tol_all')} | {cell(rr, 'correct_tol')} | {cell(ir, 'correct_tol')} |")
md += ['', '† = under 30 groups (groups with a defined per-scan value): too small to compare. Dice uses the true mask; detection = share of non-empty predictions. TN3K has 30 groups and DDTI 26 among the 60 scans, so the DDTI cells can never reach 30.', '',
       '## Exact-rule variant (Step 16 exact match, for reference)', '', '| held-out dataset | position AUROC cross | in-dataset | all-checkable cross | in-dataset |', '|---|---|---|---|---|']
for h in S.THY + [None]:
    rr = [r for r in R if h is None or r['dataset'] == h]; ir = insame(rr); md.append(f"| {'pooled' if h is None else h} | {cell(rr, 'auc_exact_position')} | {cell(ir, 'auc_exact_position')} | {cell(rr, 'auc_exact_all')} | {cell(ir, 'auc_exact_all')} |")
md += ['', '## Deviations from the PREREG', '', '- None known at the time of writing (this line is edited by hand if a deviation occurs).', '', '## Caveats', '',
       '- 30 scans per held-out dataset (26 groups in DDTI); one seed, one split, no repeat; random-init encoder; templated candidates; thyroid only.',
       '- The in-dataset comparison model (Step 29 thyroid) was trained on both TN3K and DDTI dev images, so it had more and more varied training data than either fold: part of any gap is training-set size, not domain shift.',
       '- Neither dataset records the scanner or centre, so "dataset" stands in for domain; images shared between the datasets, if any, are not caught by the within-dataset leak filter.', '']
open(os.path.join(D, 'results.md'), 'w').write('\n'.join(md)); json.dump(res, open(os.path.join(D, 'results.json'), 'w'), indent=1)
def g(*c):
    try: return subprocess.check_output(c, text=True, cwd=G.ROOT).strip()
    except Exception: return None
json.dump(dict(step='41', seed=G.SEED, folds=S.THY, train_seconds={ds: TR[ds]['seconds'] for ds in S.THY}, git_head_at_report=g('git', 'rev-parse', '--short', 'HEAD'), prereg_commit=g('git', 'log', '--format=%h', '-1', '--', 'usmeta/results/partA/step41_thyroid_cross/PREREG.md'), python=sys.version.split()[0], platform=platform.platform(), date=time.strftime('%Y-%m-%d'), bootstrap='group, 1000 resamples, seed 0', min_groups=MIN_G, test_scans=len(R), device=TR['TN3K'].get('device')), open(os.path.join(D, 'run_info.json'), 'w'), indent=1)
print('wrote results.md', len(md)); print('\n'.join(dl))
