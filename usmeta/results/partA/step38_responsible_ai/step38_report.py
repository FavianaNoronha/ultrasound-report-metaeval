"""Step 38 report: results/partA/step38_responsible_ai/results.md, results.json, robustness.png (no model calls)."""
import os, json, sys, platform, time, subprocess
import numpy as np
from . import step38_responsible_ai as S
D = S.OUT; A = json.load(open(os.path.join(D, 'a_results.json'))); B = json.load(open(os.path.join(D, 'b_results.json'))); C = json.load(open(os.path.join(D, 'c_rows.json')))
def ci(g, k=2, mark=False):
    if not g: return '—'
    return f'{g[0]:.{k}f} ({g[1]:.{k}f}–{g[2]:.{k}f})' + (' †' if mark else '')
def cell(d, key=None, k=2):
    d = d[key] if key else d
    return '—' if not d['value'] else ci(d['value'], k, d['too_small'])
# (c) aggregates
def agg_rows(rows, organ=None):
    rr = [r for r in rows if organ is None or r['organ'] == organ]; out = {}
    for k, nm in (('dice', 'dice'), ('auc_tol_position', 'position'), ('auc_tol_size', 'size'), ('auc_tol_all', 'all'), ('correct_tol', 'correct')):
        g, n = S.agg(rr, k); out[nm] = (g, n)
    g, n = S.agg([dict(r, f=float(r['found'])) for r in rr], 'f'); out['detect'] = (g, n); out['scans'] = len(rr); return out
CR = {k: {'pooled': agg_rows(v), 'breast': agg_rows(v, 'breast'), 'thyroid': agg_rows(v, 'thyroid')} for k, v in C.items()}
clean = CR['clean|clean']['pooled']
md = ['# Step 38: responsible-AI checks on the Step 29 image check', '',
      'Limitations: [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md). Code: `usmeta/step38_responsible_ai.py`, `step38_report.py` (new files). **Nothing was retrained and no new `splits.load(\'test\')` call was made:** the saved Step 29 U-Net models, saved test masks and saved per-scan results are reused for the 228 test scans (Steps 21a / 24 / 29, whose test reads were logged); part (b) and (c) run the saved models on those scans\' images. Same Step 20 tolerance-aware rule (tau 0.3, adjacent position), same group bootstrap (1,000, seed 0), cells under 30 groups marked † (too small to compare).', '']
p = A['pooled']; ex = B['exact_coverage']; op = B['operating_points']; worst = lambda key: min(((k, v[key][0][0] if isinstance(v[key], tuple) else v[key]) for k, v in CR.items() if k != 'clean|clean'), key=lambda x: x[1])
pos = lambda k: CR[k]['pooled']['position'][0][0]; dic = lambda k: CR[k]['pooled']['dice'][0][0]
wk = min((k for k in CR if k != 'clean|clean'), key=pos)
md += ['## Headline', '',
       f"- **(a) The image check is not equally good on every source dataset.** Position AUROC per dataset (30 scans each, every cell under 30 groups: too small to compare, shown for orientation): " + ', '.join(f"{ds} {A['datasets'][ds]['position_auroc']['value'][0]:.2f}" for ds in A['datasets']) + f"; the weakest are TN5000 (the only dataset with no training images: {A['datasets']['TN5000']['position_auroc']['value'][0]:.2f}), DDTI ({A['datasets']['DDTI']['position_auroc']['value'][0]:.2f}) and BUSI ({A['datasets']['BUSI']['position_auroc']['value'][0]:.2f}); Dice is lowest on BrEaST ({A['datasets']['BrEaST']['dice']['value'][0]:.2f}), DDTI ({A['datasets']['DDTI']['dice']['value'][0]:.2f}) and BUSI ({A['datasets']['BUSI']['dice']['value'][0]:.2f}). **Scanner / device identity exists in the files of one dataset only (BUS-BRA, 4 device codes); no other dataset has a scanner or acquisition-protocol field, so scanner effects cannot be examined elsewhere** (nothing was inferred or guessed).",
       f"- **(b) Abstaining on low U-Net confidence helps: modestly for the position check, strongly for mask failure.** Keeping the 80% most confident scans (per organ) lowers the position-check error from {ex['100%']['error_rate'][0]*100:.1f}% to {ex['80%']['error_rate'][0]*100:.1f}% and raises position AUROC from {ex['100%']['position_auroc'][0]:.2f} to {ex['80%']['position_auroc'][0]:.2f}; at 60% coverage the error is {ex['60%']['error_rate'][0]*100:.1f}% and AUROC {ex['60%']['position_auroc'][0]:.2f}; random abstention leaves both unchanged ({ex['100%']['random_abstention_error']*100:.1f}% and {ex['60%']['random_abstention_position_auroc']:.2f}). The val-chosen thresholds give 80% and 58% test coverage. The gain on position error is small in absolute terms because only {int(round(B['curves']['position_error']['overall_error'] * 228))} of 228 scans have a wrong position at all; abstention works much better against mask failure (Dice < 0.5): {B['curves']['dice_below_0.5']['overall_error']*100:.1f}% of the scans with a true mask fail, {[p for p in B['curves']['dice_below_0.5']['points'] if abs(p[0] - 0.8) < 0.03][0][1]*100:.1f}% at 80% coverage and {[p for p in B['curves']['dice_below_0.5']['points'] if abs(p[0] - 0.6) < 0.03][0][1]*100:.1f}% at 60%, against a flat random-abstention baseline.",
       f"- **(c) The check is robust to these corruptions: no setting lowers pooled position AUROC by more than 0.05.** Clean position AUROC {pos('clean|clean'):.2f} and Dice {dic('clean|clean'):.2f}; the largest drops are the strongest brightness / gamma shift ({pos('brightness_gamma|gamma 0.55, +45'):.2f}, Dice {dic('brightness_gamma|gamma 0.55, +45'):.2f}) and the strongest noise ({pos('noise|sigma 50'):.2f}, Dice {dic('noise|sigma 50'):.2f}); blur (radius 4 px: AUROC {pos('blur|radius 4 px'):.2f}, Dice {dic('blur|radius 4 px'):.2f}) and JPEG quality 5 ({pos('jpeg|quality 5'):.2f}) change the AUROC by 0.02 or less, although blur lowers Dice. All differences are inside the group-bootstrap intervals (which are wide because the same 228 scans are used in every row). Thyroid is the more sensitive organ (clean 0.80, strongest gamma 0.72).", '',
       '## (a) Per-dataset gap table (Step 29 U-Net, 228 test scans; saved results)', '',
       'Position AUROC and correct-report score: Step 20 tolerance-aware check (AUROC of planted errors vs harmless rewordings; correct-report score = mean score of the identical copies). Dice only for scans with a true mask (TN5000 has boxes only: no Dice). Detection = share of non-empty masks. 95% group bootstrap; † = under 30 groups.', '',
       '| source | scans | detection rate | Dice | position AUROC | correct-report score | groups (position) |', '|---|---|---|---|---|---|---|']
for ds in A['datasets']:
    v = A['datasets'][ds]; md.append(f"| {ds} ({S.SD[ds]}) | {v['scans']} | {cell(v, 'detection')} | {cell(v, 'dice')} | {cell(v, 'position_auroc')} | {cell(v, 'correct_report')} | {v['position_auroc']['groups']} |")
for o in ('breast', 'thyroid'):
    v = A['organs'][o]; md.append(f"| **{o} (all)** | {v['scans']} | {cell(v, 'detection')} | {cell(v, 'dice')} | {cell(v, 'position_auroc')} | {cell(v, 'correct_report')} | {v['position_auroc']['groups']} |")
v = A['pooled']; md.append(f"| **pooled** | {v['scans']} | {cell(v, 'detection')} | {cell(v, 'dice')} | {cell(v, 'position_auroc')} | {cell(v, 'correct_report')} | {v['position_auroc']['groups']} |")
md += ['', 'The Step 29 model was trained on the dev images of all the datasets above except TN5000 (boxes only): TN5000 is the one cross-dataset row, and it is the lowest on position AUROC and correct-report score. Dataset gaps are not separable from lesion mix, image size and the number of training images per dataset.', '',
       '### Scanner / acquisition metadata that exists in the dataset files (column names and counts only; no licensed text copied)', '']
for k in ('BUS-BRA', 'BrEaST', 'UDIAT', 'BUS-UCLM', 'BUSI', 'TN3K', 'TN5000', 'DDTI', 'HC18'): md.append(f"- **{k}:** {A['metadata'][k]}")
md += ['', f"**{A['metadata']['conclusion']}**", '',
       f"BUS-BRA by anonymised scanner code (codes D1-D4 by image count in the whole dataset: {', '.join(f'{k} {v:,}' for k, v in A['bus_bra_device_counts_all_images'].items())}; the codes are not device names and cannot be mapped back from this file). Test scans in this sample:", '', '| scanner code | scans | Dice | position AUROC | correct-report score |', '|---|---|---|---|---|']
for k, v in A['bus_bra_by_scanner_code'].items(): md.append(f"| {k} | {v['scans']} | {cell(v, 'dice')} | {cell(v, 'position_auroc')} | {cell(v, 'correct_report')} |")
md += ['', 'Each scanner cell has 2-17 scans (under 30 groups): **too small to compare**; D3 has no scan in this sample. No scanner difference can be claimed from this table.', '',
       '## (b) Risk-coverage: abstain when the mask is empty or its mean foreground probability is low', '',
       '**Confidence** = mean probability of the pixels the model calls foreground (probability above the model\'s own threshold, at its 256 x 256 resolution); an empty mask has confidence 0 and always abstains. **Threshold chosen on VAL only:** the 20th and 40th percentile of the confidence of all val images with a mask, per organ model (breast 0.936 / 0.961, thyroid 0.875 / 0.910), i.e. the thresholds that would keep 80% and 60% of val scans; they are applied unchanged to the test scans. **Error** = the position check fails: the predicted position (3 x 3 grid) of the lesion is neither the true cell nor an adjacent one (tolerance rule), or the mask is empty.', '',
       '| operating point | scans kept (coverage) | position error rate (95% CI) | position AUROC (95% CI) | mean Dice of kept scans |', '|---|---|---|---|---|']
for k, v in op.items(): md.append(f"| {k} | {v['scans']} ({v['coverage']*100:.0f}%) | {v['error_rate'][0]*100:.1f}% ({v['error_rate'][1]*100:.1f}–{v['error_rate'][2]*100:.1f}) | {ci(v['position_auroc'], 2, v['too_small'])} | {v['dice_mean']:.2f} |")
md += ['', '**Exact coverage by rank** (per organ the most confident 100%, 80%, 60% of the test scans are kept; no threshold, to give the three requested coverage points), with random abstention of the same size as the baseline (mean of 300 draws):', '', '| coverage | scans | position error | random-abstention error | position AUROC (95% CI) | random-abstention AUROC |', '|---|---|---|---|---|---|']
for k, v in ex.items(): md.append(f"| {k} | {v['scans']} | {v['error_rate'][0]*100:.1f}% ({v['error_rate'][1]*100:.1f}–{v['error_rate'][2]*100:.1f}) | {v['random_abstention_error']*100:.1f}% | {ci(v['position_auroc'], 2, v['too_small'])} | {v['random_abstention_position_auroc']:.2f} |")
c2 = B['curves']['dice_below_0.5']; c1 = B['curves']['position_error']
md += ['', f"Second error definition, mask failure (Dice < 0.5, {c2['n']} scans with a true mask): overall error {c2['overall_error']*100:.1f}%; at 80% coverage {[p for p in c2['points'] if abs(p[0] - 0.8) < 0.03][0][1]*100:.1f}%, at 60% {[p for p in c2['points'] if abs(p[0] - 0.6) < 0.03][0][1]*100:.1f}% (random abstention stays at {c2['overall_error']*100:.1f}%). Full curves in `b_results.json`; plot: `risk_coverage.png` (both error definitions, with the random-abstention baseline).", '',
       '![risk-coverage](risk_coverage.png)', '',
       '## (c) Robustness to image corruptions (228 test scans; position check re-run on the model\'s mask of the corrupted image)', '',
       'Corruptions on the grayscale image the model sees: Gaussian noise (sigma 10 / 25 / 50 grey levels), Gaussian blur (radius 1 / 2 / 4 px), JPEG re-compression (quality 50 / 20 / 5), brightness and gamma shift (gamma 0.85 with +10, gamma 0.70 with +25, gamma 0.55 with +45 grey levels: darker tones lifted, brighter overall). Deterministic (noise seeded per scan). Position AUROC and correct-report score as in Step 29; the clean row is recomputed in this run with the same code (it reproduces the saved Step 29 numbers).', '',
       '| corruption | strength | detection | Dice (pooled) | position AUROC pooled (95% CI) | breast | thyroid | correct-report score | change in position AUROC vs clean |', '|---|---|---|---|---|---|---|---|---|']
for k, v in CR.items():
    kind, st = k.split('|'); pl = v['pooled']; md.append(f"| {kind} | {st} | {ci(pl['detect'][0], 2)} | {ci(pl['dice'][0], 2)} | {ci(pl['position'][0], 2)} | {ci(v['breast']['position'][0], 2)} | {ci(v['thyroid']['position'][0], 2)} | {ci(pl['correct'][0], 2)} | {pl['position'][0][0] - clean['position'][0][0]:+.2f} |")
md += ['', 'Pooled rows have 207 groups (all intervals shown are over groups; the 228 scans are the same in every row, so the rows are strongly dependent); per-organ cells have 120 and 87 groups. Size and all-checkable AUROC for every setting are in `c_results.json`.', '',
       '## Caveats', '',
       '- **Same 228 scans, one model, one seed** (the Step 29 U-Net, trained on dev only, random-init encoder): the per-dataset cells have 30 scans (BUS-UCLM 18) and are too small to compare; the gaps are indications of where to look, not estimates of dataset effects. Dataset, lesion mix, image size and training-set size are confounded.',
       '- **Scanner effect cannot be tested** except inside BUS-BRA (4 device codes, 2-17 test scans each). No scanner or acquisition information was inferred for any other dataset.',
       '- **(b) The position check has few errors** (about 11 of 228 scans under the tolerance rule), so the risk-coverage curve is coarse and its intervals are wide; the confidence is the model\'s own foreground probability, which is not calibrated. The val thresholds are quantiles of val confidence (no label was used to pick them); the test coverage they give differs from 80% / 60% (see the table).',
       '- **(c) Corruptions are synthetic and mild-to-strong by our choice of strengths**; they are applied to the already-compressed public images, so JPEG quality 50 is a second compression. The model was not trained with these corruptions (it saw flips and brightness / contrast / gamma jitter only). Real acquisition shifts (different scanner, gain, depth) are not covered.',
       '- Templated candidates, as in Step 29: the position check scores claims of templated text against a measurement from the mask.', '']
open(os.path.join(D, 'results.md'), 'w').write('\n'.join(md))
json.dump({k: {o: {kk: (vv if not isinstance(vv, tuple) else dict(value=vv[0], groups=vv[1])) for kk, vv in agg.items()} for o, agg in v.items()} for k, v in CR.items()}, open(os.path.join(D, 'c_results.json'), 'w'), indent=1)
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
fig, axs = plt.subplots(1, 2, figsize=(11, 4.2)); strengths = [0, 1, 2, 3]
for ax, key, nm in ((axs[0], 'auc_tol_position', 'position AUROC (pooled)'), (axs[1], 'dice', 'Dice (pooled)')):
    for kind in S.CORR:
        ys = [clean['position' if key != 'dice' else 'dice'][0][0]] + [CR[f'{kind}|{n}']['pooled']['position' if key != 'dice' else 'dice'][0][0] for n, _ in S.CORR[kind]]; ax.plot(strengths, ys, 'o-', label=kind)
    ax.set_xticks(strengths); ax.set_xticklabels(['clean', 'mild', 'medium', 'strong']); ax.set_ylabel(nm); ax.grid(alpha=0.3); ax.legend(fontsize=8)
fig.tight_layout(); fig.savefig(os.path.join(D, 'robustness.png'), dpi=130); plt.close(fig)
def g(*c):
    try: return subprocess.check_output(c, text=True, cwd=S.ROOT).strip()
    except Exception: return None
json.dump(dict(step='38', retrained='no', new_test_split_read='no', git_head_at_report=g('git', 'rev-parse', '--short', 'HEAD'), python=sys.version.split()[0], platform=platform.platform(), date=time.strftime('%Y-%m-%d'), bootstrap='group, 1000 resamples, seed 0', min_groups=30), open(os.path.join(D, 'run_info.json'), 'w'), indent=1); print('wrote', len(md))
