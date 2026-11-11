"""Step 33 report: results.md + edit_size_law.png from results.json (no model calls)."""
import os, json, sys, platform, time, subprocess
import numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from . import step33_edit_size_law as S
D = S.OUT; R = json.load(open(os.path.join(D, 'results.json')))
ci = lambda v, k=3: '—' if not v else f'{v[0]:.{k}f} to {v[1]:.{k}f}'
rows = []
for n, v in R.items():
    p = v['primary']; s = v['sensitivity_ge30']; rows.append((n, v, p, s))
big = [v['label'] for n, v, p, s in rows if p and p['r2'] >= 0.6]; small = [v['label'] for n, v, p, s in rows if p and p['r2'] < 0.6]
# plot
fig, axs = plt.subplots(2, 4, figsize=(17, 7.5), sharey=True); col = {'small': '#1f77b4', 'matched': '#2ca02c', 'large': '#d62728', 'other': '#9467bd', 'human': '#ff7f0e'}; mk = {'breast': 'o', 'thyroid': 's', 'fetal head': '^'}
for ax, (n, v, p, s) in zip(axs.ravel(), rows):
    for c in v['cells']: ax.scatter(np.log(c['median_ratio']), c['auroc'], c=col[c['group']], marker=mk[c['organ']], s=60 if not c['too_small'] else 38, alpha=1 if not c['too_small'] else 0.55, edgecolor='k', linewidth=0.5)
    xs = np.linspace(min(np.log(c['median_ratio']) for c in v['cells']), max(np.log(c['median_ratio']) for c in v['cells']), 20); ax.plot(xs, p['intercept'] + p['slope'] * xs, 'k--', lw=1)
    ax.set_title(f"{v['label']}  R²={p['r2']:.2f}  slope={p['slope']:.2f}", fontsize=10); ax.set_xlabel('ln(median harmless edit / error edit)'); ax.grid(alpha=0.3); ax.set_ylim(-0.03, 1.03)
for ax in axs[:, 0]: ax.set_ylabel('AUROC (error vs harmless)')
h = [plt.Line2D([], [], marker='o', ls='', color=c, label=g) for g, c in col.items()] + [plt.Line2D([], [], marker=m, ls='', color='gray', label=o) for o, m in mk.items()]
fig.legend(handles=h, loc='lower center', ncol=8, frameon=False); fig.tight_layout(rect=(0, 0.05, 1, 1)); fig.savefig(os.path.join(D, 'edit_size_law.png'), dpi=130); plt.close(fig)
md = ['# Step 33: edit-size law (saved scores only)', '',
      'Limitations: [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md). Code: `usmeta/step33_edit_size_law.py`, `step33_report.py` (new files, no model call; test access logged under `usmeta.step33_edit_size_law`). Data: `bench_test_v2d`, saved test scores (Layer 0, judge replies of Steps 10d + 12, Step 27 pair scores for `llm_finding_f1`), and the 29 human rewordings of Step 21d (saved word-scorer scores; `llm_finding_f1` from the Step 27 extraction cache; no per-pair judge scores were saved for them, so judge rows have no human cell). Plot: `edit_size_law.png`; every cell: `cells.csv`.', '',
      '**Method.** One point per (organ, harmless group) cell: **AUROC** of planted error vs harmless (per case, ties 0.5, mean over cases) and the **median edit-size ratio** (harmless edit size / error edit size over all error x harmless pairs; edit size = normalised character Levenshtein distance to the reference). Groups: small, matched one-word synonym, large style swap, other secondary variants, and the human rewordings of Step 21d. **Model per scorer: AUROC = a + b * ln(ratio)** by ordinary least squares over that scorer\'s cells (15 cells for the word scorers: 3 organs x 5 groups; 9 for the judge: small / matched / large only; 12 for `llm_finding_f1`: its judged subset plus the human cell). 95% intervals: group bootstrap (resample patient / exam groups, recompute all cells, refit; 1,000 resamples, seed 0). The primary fit uses all cells; the sensitivity fit drops cells with fewer than 30 groups (the three human cells and the fetal-head cells of the judge). **Decision rule: R² >= 0.6 means "scorer behaviour is largely predicted by edit size".**', '',
      '## Decision line', '',
      f"**Edit size largely predicts BLEU and ROUGE-L (R² >= 0.6) and does not predict the others.** " + ', '.join(f"{v['label']} R² {p['r2']:.2f} ({ci(p['r2_ci'], 2)})" for n, v, p, s in rows) + f". Meeting the rule: {', '.join(big) if big else 'none'}. Below the rule: {', '.join(small)}. For BLEU and ROUGE-L, a doubling of the harmless-to-error edit ratio lowers the AUROC by {-np.log(2)*R['bleu']['primary']['slope']:.2f} and {-np.log(2)*R['rougeL']['primary']['slope']:.2f}. chrF, BERTScore, RaTEScore and the judge are less tied to the edit ratio, but that is not evidence that they track facts (see Steps 21e, 28): their cells are low or high for other reasons (e.g. a one-word synonym is scored as a change by chrF), and with 9-15 cells per scorer the fit is coarse. `llm_finding_f1` is flat (R² {R['llm_finding_f1']['primary']['r2']:.2f}) because it is near 1.0 in every template cell (its one low cell is the 9-item human breast cell, 0.73).", '',
      '## Fit per scorer (AUROC = a + b * ln(ratio))', '', '| scorer | cells (>= 30 groups) | slope b (95% CI) | per doubling of the ratio | R² (95% CI) | R² >= 0.6 | sensitivity: slope / R² on cells with >= 30 groups |', '|---|---|---|---|---|---|---|']
for n, v, p, s in rows: md.append(f"| {v['label']} | {v['n_cells']} ({v['n_cells_ge30']}) | {p['slope']:.3f} ({ci(p['slope_ci'])}) | {p['slope']*np.log(2):+.3f} | {p['r2']:.2f} ({ci(p['r2_ci'], 2)}) | {'yes' if p['r2'] >= 0.6 else 'no'} | " + (f"{s['slope']:.3f} / {s['r2']:.2f}" if s else '—') + ' |')
md += ['', 'Slope is per unit of ln(ratio); a negative slope means the AUROC falls when the harmless rewording changes more text than the error does. Intervals are percentile intervals of the 1,000 group-bootstrap refits.', '', '## The cells (organ x harmless group; † = under 30 groups: too small to compare)', '']
for n, v, p, s in rows:
    md += [f"### {v['label']}", '', '| organ | group | cases / groups | median harmless / error edit ratio | AUROC |', '|---|---|---|---|---|']
    for c in sorted(v['cells'], key=lambda c: (c['organ'], S.GROUPS.index(c['group']))): md.append(f"| {c['organ']} | {c['group']} | {c['cases']} / {c['groups']}{' †' if c['too_small'] else ''} | {c['median_ratio']:.2f} | {c['auroc']:.2f} |")
    md.append('')
md += ['## Caveats', '',
       '- **Cells are not independent samples:** the same references and error candidates appear in every harmless group of an organ, the harmless groups differ mainly in how much text they change (that is the point), and organ is not modelled. 9-15 cells per scorer is a small regression; the bootstrap resamples groups, not cells, and does not capture the choice of groups.',
       '- **Edit-size ratio is a median over pairs; fetal-head cells have very short texts** (a changed number is a large relative edit), so their ratios and AUROCs are extreme; the fit is shown with and without cells under 30 groups.',
       '- **Judge and `llm_finding_f1` rows use the judged subset only** (59 cases per dataset); `llm_finding_f1` has no "other" group (not in the judged subset); no human cell for the judge (aggregates only were saved). R² compares scorers on different cell sets.',
       '- **A high R² means edit size predicts the AUROC, not that the scorer is right or wrong**; a low R² for `llm_finding_f1` and the judge means they are not driven by edit size on these data, not that they are validated on free text.',
       '- Human cells have 9-10 items each; the human rewordings are mostly large edits (Step 21e).', '']
open(os.path.join(D, 'results.md'), 'w').write('\n'.join(md))
def g(*c):
    try: return subprocess.check_output(c, text=True, cwd=S.ROOT).strip()
    except Exception: return None
json.dump(dict(step='33', saved_scores_only=True, git_head_at_report=g('git', 'rev-parse', '--short', 'HEAD'), python=sys.version.split()[0], platform=platform.platform(), date=time.strftime('%Y-%m-%d'), bootstrap='group, 1000 resamples, seed 0', min_groups=S.MIN_G, model='AUROC = a + b ln(median edit ratio), OLS per scorer'), open(os.path.join(D, 'run_info.json'), 'w'), indent=1); print('wrote', len(md), 'big:', big)
