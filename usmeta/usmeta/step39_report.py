"""Step 39 report: results/partA/step39_judge_ensemble/results.md, run_info.json (no model calls)."""
import os, json, sys, platform, time, subprocess
import numpy as np
from . import step39_judge_ensemble as M
D = M.OUT; R = json.load(open(os.path.join(D, 'results.json'))); G = json.load(open(os.path.join(D, 'devval_gate.json'))); CL = json.load(open(os.path.join(D, 'compute_clock.json')))
cfg = R['config']; h1 = R['H1']; h2 = R['H2']
def ci(v, k=3, pct=False):
    if not v: return '—'
    f = (lambda x: f'{x*100:.1f}%') if pct else (lambda x: f'{x:.{k}f}')
    return f'{f(v[0])} ({f(v[1])}–{f(v[2])})'
pp = h1['pooled']; d_m = h2['pooled'].get('matched'); d_s = h2['pooled'].get('small')
md = ['# Step 39: stabilising the Gemma-2-9B judge by averaging over prompt wordings', '',
      f"**H1 (stability): {'SUPPORTED' if h1['supported'] else 'NOT SUPPORTED'}.** Share of pairs with |ensemble A - ensemble B| > 0.1: **{ci(pp['ensemble_share'], pct=True)}** ({pp['pairs']} pairs, {pp['groups']} groups) against the single-prompt share (P0 vs P3, same pairs) **{ci(pp['single_share'], pct=True)}**. Pre-registered rule: ensemble share < 10% AND its CI upper bound below the single-prompt point estimate ({pp['single_share'][0]*100:.1f}%).",
      f"**H2 (no loss of accuracy): {'SUPPORTED' if h2['supported'] else 'NOT SUPPORTED'}.** ensemble A minus P0 alone, per-case AUROC difference (pooled, {h2['cases_total_by_organ']['breast'] + h2['cases_total_by_organ']['thyroid'] + h2['cases_total_by_organ']['fetal head']} cases): vs matched synonym {ci(d_m['difference']) if d_m else '—'}; vs harmless_small {ci(d_s['difference']) if d_s else '—'}. Pre-registered rule: lower bound of the difference > -0.02 for both.", '',
      'Pre-registration: [PREREG.md](PREREG.md) (committed before any new test-split judge call). Limitations: [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md). Code: `usmeta/step39_judge_ensemble.py`, `step39_report.py` (new files; frozen `judge2.PROMPT_V2`, Step 21c paraphrases and saved replies reused). Same model (Gemma-2-9B-it 4-bit, MLX, greedy), same parser. Group bootstrap (1,000, seed 0); cells under 30 groups are marked † (too small to compare).', '',
      '## Prompts', '', '| id | what | reused from |', '|---|---|---|', '| P0 | the frozen judge prompt (prompt_v2) | saved Step 10d / 12 replies |', '| P1 | Step 21c paraphraseA | saved Step 21c replies |', '| P2 | Step 21c paraphraseB **plus a verbatim-copy rule** (amended after the dev/val gate) | new replies (the Step 21c replies belong to the old text) |',
      '| P3 | P0 text with the candidate in the REFERENCE slot and vice versa (Step 21c swap) | saved Step 21c replies |', '| P4 | new paraphrase C | new replies |', '| P5 | new paraphrase D **plus the verbatim-copy rule** | new replies |', '',
      'Set A = {P0, P1, P2}, set B = {P3, P4, P5}; ensemble score = mean `judge_score` over a set. Full texts and SHA-256 hashes: PREREG.md.', '',
      '## H1: stability on the 89 Step 21c cases (432 pairs)', '', '| group | pairs | groups | ensemble share (A vs B > 0.1) | single-prompt share (P0 vs P3 > 0.1) |', '|---|---|---|---|---|']
for k in ('pooled', 'breast', 'thyroid', 'fetal head'):
    v = h1[k]; miss = (" (" + str(v['missing_pairs']) + " excluded: a reply missing)") if v['missing_pairs'] else ""; dag = " †" if v['too_small'] else ""
    md.append("| " + k + " | " + str(v['pairs']) + miss + " | " + str(v['groups']) + dag + " | " + ci(v['ensemble_share'], pct=True) + " | " + ci(v['single_share'], pct=True) + " |")
md += ['', f"Context: Step 21c measured |judge_score change| > 0.1 in 21% (swap) and 18% / 26% (paraphrases) of pairs against the original prompt; here the single-prompt comparison is P0 vs P3 on the same pairs. Per-organ rows are shown for orientation; fetal head has 20 cases (under 30 groups: too small to compare).", '',
       '## H2: accuracy, ensemble A vs P0 alone (AUROC of planted errors vs harmless, per case, ties 0.5)', '',
       f"Cases: the 89 Step 21c cases (P0, P1, P2 replies for all of their pairs) plus {sum(h2['cases_total_by_organ'].values()) - sum(h2['cases_h1_only'].values())} extra cases from the Step 12 sample ({cfg['h2_extra_cases_per_dataset']} per dataset), {sum(h2['cases_total_by_organ'].values())} cases in all. Each case has 1 small + 1 matched + 1 large harmless rewording and its planted errors.", '',
       '| group | harmless | cases / groups | AUROC P0 | AUROC ensemble A | difference (95% CI) |', '|---|---|---|---|---|---|']
for k in ('pooled', 'breast', 'thyroid', 'fetal head'):
    for ht, nm in (('matched', 'matched synonym'), ('small', 'harmless_small')):
        v = h2[k].get(ht)
        if v: md.append(f"| {k} | {nm} | {v['cases']} / {v['groups']}{' †' if v['too_small'] else ''} | {ci(v['auroc_P0'], 2)} | {ci(v['auroc_ensembleA'], 2)} | {ci(v['difference'], 3)} |")
gate_txt = "**passed** for all six prompts" if G['gate_passed'] else "**NOT passed**"
md += ['', '## Dev / val gate (before any new test call)', '',
       "Identical-copy gate on " + str(G['n_identical']) + " identical copies from the dev / val judge sample (one per distinct reference): " + gate_txt + ". The first draft of P2 (= Step 21c paraphraseB) and of P5 scored one of eight identical copies 0.4 (a dev report ending in the abbreviation \"Histology: fa.\"); both were amended with a verbatim-copy rule on dev / val, re-frozen, and the gate re-run (file `devval_gate_v1.json` keeps the first result). Seconds per judge call: " + format(G['seconds_per_call'], '.1f') + ".", '',
       '| prompt | identical copies, mean judge_score | unparsed identical | unparsed other pairs |', '|---|---|---|---|']
for n, v in G['prompts'].items(): md.append("| " + n + " | " + format(v['identical_mean'], '.3f') + " | " + str(v['unparsed_identical']) + " | " + (str(v['unparsed_other']) if v['unparsed_other'] is not None else '—') + " |")
md += ['', '## Compute and deviations', '', f"Compute clock started {CL['start_iso']} (first dev / val judge call); cap {cfg['compute_cap_hours']:.0f} h. See `run_info.json` for the compute used and the n reached.", '',
       '- The Step 21c replies of paraphraseB cannot be reused for P2 (amended text), so P2 was re-run on all H1 pairs.', '- **The compute cap (3 h) stopped the test run after 66 of 91 cases** (about 311 of 432 H1 pairs have all six replies; 121 pairs are excluded for a missing reply, no extension). The excluded pairs are the last cases of a seeded dataset round-robin order, so the kept pairs are balanced across datasets but fewer than planned.', '- The first test schedule (all P4 calls first) would have run past the cap with P5 incomplete; after 54 P4 replies it was replaced by a prompt-interleaved order (P2, P4, P5 per pair, case by case). No reply was discarded. This changed order only, not any prompt text or rule.', '- Prompt texts were amended during the dev/val gate (P2 and P5 several versions, superseded files kept) until all six prompts gave 1.0 on identical copies, before any test call; H2 used no extra cases beyond the 89.', '- The optional second-family judge (Llama-3.1-8B-Instruct) was **not run** (compute cap; it would need a new 4-bit download).', '',
       '## Caveats', '',
       '- One model family (Gemma-2-9B), one machine, greedy decoding; the ensemble averages **prompt wordings**, not models, so any model-specific bias is untouched (the optional second-family check was not run).',
       '- Set B contains the order swap (P3), so H1 compares three reworded prompts with the swap plus two paraphrases; the single-prompt reference is P0 vs P3.',
       '- Templated candidates; 89 Step 21c cases for H1 (breast 40, thyroid 29, fetal head 20): per-organ cells are small, only the pooled row has 30 or more groups; H2 adds a few extra cases per dataset.',
       '- The judge penalty score is floored by its error-count rule; an ensemble mean of floored scores is still a mean of the same scale.', '']
open(os.path.join(D, 'results.md'), 'w').write('\n'.join(md))
def g(*c):
    try: return subprocess.check_output(c, text=True, cwd=M.ROOT).strip()
    except Exception: return None
json.dump(dict(step='39', prereg='PREREG.md', H1_supported=h1['supported'], H2_supported=h2['supported'], compute_start=CL['start_iso'], compute_cap_hours=cfg['compute_cap_hours'], git_head_at_report=g('git', 'rev-parse', '--short', 'HEAD'), python=sys.version.split()[0], platform=platform.platform(), date=time.strftime('%Y-%m-%d'), bootstrap='group, 1000 resamples, seed 0', min_groups=30), open(os.path.join(D, 'run_info.json'), 'w'), indent=1); print('wrote', len(md))
