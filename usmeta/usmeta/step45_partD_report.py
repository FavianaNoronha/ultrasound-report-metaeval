"""Step 45 Part D report: partD/results.md, run_info.json from results.json and the saved replies (no model)."""
import os, json, subprocess, platform, time
import numpy as np
from . import step45_partD as D, step45_gemma as GM
R = json.load(open(D.P('results.json'))); S = R['status']; V = R['variants']; H = R['holistic_step44_same_pairs']['test']; ps = R['pass']
f = lambda g: f"{g[0] * 100:.1f}% ({g[1] * 100:.1f}-{g[2] * 100:.1f})"
d = {v: D.__dict__['load'](v) for v in ('c1', 'c2')}; rows = []
for i in sorted(set(d['c1']) & set(d['c2'])):
    a, b = d['c1'][i], d['c2'][i]
    if a['result'] and b['result']: rows.append(dict(set=a['set'], kind=a['kind'], c1=a['result']['score'], c2=b['result']['score'], h=a['holistic']))
te = [r for r in rows if r['set'] == 'test']
def auc(key):
    e = np.array([r[key] for r in te if r['kind'] == 'error'])[:, None]; h = np.array([r[key] for r in te if r['kind'] == 'harmless'])[None, :]; return float(((e < h) + 0.5 * (e == h)).mean())
a1, a2, ah = auc('c1'), auc('c2'), auc('h')
curve = {t: {v: (float(np.mean([r[v] <= t for r in te if r['kind'] == 'error'])), float(np.mean([r[v] <= t for r in te if r['kind'] == 'harmless']))) for v in ('c1', 'c2')} for t in (0.2, 0.36, 0.5)}
L = ['# Step 45, Part D: claim-by-claim Gemma-2-9B judge', '',
     f"**DOES NOT PASS the pre-registered rule, and the run is INCOMPLETE (compute cap).** Rule: catch >= 71.3% with harmless flagged <= 5.6% at the val-fixed threshold, and flag agreement between the two prompt variants >= 90%. At the threshold fixed on val (c1: score <= {V['c1']['threshold']:.2f}; c2: <= {V['c2']['threshold']:.2f}) the claim-by-claim judge catches **{f(V['c1']['test']['catch'])}** (c1) and **{f(V['c2']['test']['catch'])}** (c2) of the planted errors in the test sample, flagging {f(V['c1']['test']['harmless_flagged'])} / {f(V['c2']['test']['harmless_flagged'])} of harmless rewordings and 0% of identical copies; variant flag agreement {f(R['agreement']['all'])} (met, but only because both variants flag almost nothing). "
     f"On the same sampled pairs the Step 44 holistic judge at its val threshold (0.4) catches {f(H['catch'])} with {f(H['harmless_flagged'])} harmless flagged. **The pre-registered catch is far from reached.** "
     f"The run stopped at its time cap: {S['pairs'] and R['pairs']['test']} of 350 planned test pairs and {R['pairs']['val']} of 139 val pairs were judged with both variants ({R['pairs']['unparsed']} unparsed reply excluded).", '',
     'Pre-registration: [../PREREG.md](../PREREG.md). Code: `usmeta/step45_gemma.py` (calls, prompts), `step45_partD.py`, `step45_partD_report.py`. All replies cached under `.llm_cache` (key = model + prompt) and in `gemma/d_c1.jsonl`, `d_c2.jsonl`.', '',
     '## What was run', '',
     'Gemma-2-9B-it 4-bit (MLX, greedy; the same model as Steps 12 / 39; the model was loaded once for Parts F and D). Two prompt variants (`CLAIM_V1`, `CLAIM_V2` in the code): split the candidate into claims, check each against the reference (supported / contradicted / unsupported), list reference facts omitted. Score = 1 - (candidate claims not supported + reference facts omitted) / (candidate claims + omitted); 1.0 = nothing wrong. '
     'Sample: a seeded random sample of the Step 44 judge subset (test: 350 planned; val: 139 planned from the val judge pool), same pairs for both variants; the Step 44 holistic scores for the same pairs are used for comparison. Flag threshold per variant: the largest observed val score with at most 5.6% of val harmless rewordings flagged.', '',
     '## Results (test sample)', '', '| judge | threshold | catch | harmless flagged | identical flagged |', '|---|---|---|---|---|']
for v, nm in (('c1', 'claim-by-claim, variant 1'), ('c2', 'claim-by-claim, variant 2')): L.append(f"| {nm} | <= {V[v]['threshold']:.2f} | {f(V[v]['test']['catch'])} (n = {V[v]['test']['catch_n']}) | {f(V[v]['test']['harmless_flagged'])} (n = {V[v]['test']['harmless_flagged_n']}) | {f(V[v]['test']['identical_flagged'])} |")
L += [f"| Step 44 holistic judge, same pairs | <= 0.40 | {f(H['catch'])} (n = {H['catch_n']}) | {f(H['harmless_flagged'])} | {f(H['identical_flagged'])} |", '',
      f"Flag agreement between the variants on the test sample: {f(R['agreement']['all'])} (planted errors {f(R['agreement']['errors'])}, harmless {f(R['agreement']['harmless'])}).", '',
      '## Why the catch is so low (and an exploratory look that is NOT part of the verdict)', '',
      f"The claim scores take few distinct values (0, 0.33, 0.5, 0.67, 1.0 ...). On the val sample 7 of 85 harmless rewordings score exactly 0.33, so the largest threshold that keeps harmless flagged at or below 5.6% is the next lower level (0 for c1, 0.2 for c2), which flags almost no planted error (val catch 18%, test 4.9%). The rule is followed as pre-registered; the discrete scores and the small val sample make it a very strict operating point. "
      f"**Exploratory (not pre-registered, not used for any verdict):** the scores themselves separate errors from harmless rewordings well on the test sample: AUROC (error vs harmless, pooled over pairs) {a1:.3f} (variant 1), {a2:.3f} (variant 2), against {ah:.3f} for the Step 44 holistic score on the same pairs. Flagging at a threshold chosen after seeing test would give (catch / harmless flagged): " + '; '.join(f"score <= {t}: variant 1 {c['c1'][0] * 100:.0f}% / {c['c1'][1] * 100:.1f}%, variant 2 {c['c2'][0] * 100:.0f}% / {c['c2'][1] * 100:.1f}%" for t, c in curve.items()) + '. Even the most favourable of these (about 57% catch) is below the 71.3% bar, and a test-chosen threshold would not be a valid pass.', '',
      '## Deviations from the PREREG', '',
      f"- **Incomplete:** the Gemma time cap (3 h for this part) stopped the run; {R['pairs']['test']} of 350 test pairs were judged with both variants (the order was shuffled, so the judged pairs are a random subset).",
      '- **A sample, not the full judge subset:** the PREREG says "the same judge test subset as Step 44" (4,729 pairs); two variants over that subset would need about 40 hours here, so a seeded random sample of 350 test pairs (and 139 val pairs for the threshold) was used. The Step 44 holistic numbers on this sample (56% catch, 8% harmless flagged) are lower than on the full subset (71.3%, 5.6%): sample noise (82 errors) and the different sample mix.',
      '- Harmless flagged is computed over harmless rewordings (small, matched, large, other), as in Step 44; identical copies are reported separately.',
      '- The test split was read via the Step 44 loader (`step19_pairs.load`, logged as `usmeta.step19_pairs`); no other test read for this part.', '',
      '## Caveats', '',
      '- One judge model family (Gemma-2-9B-it 4-bit); templated candidates (Step 44 judge subset), not the free-text set A; the claim parser trusts the model\'s JSON (1 unparsed reply of 774 calls).',
      '- 82 planted errors in the test sample: every rate has a wide interval; cells under 30 groups would be marked too small (none are, at the pooled level).', '']
open(D.P('results.md'), 'w').write('\n'.join(L)); print('wrote', len(L))
def g(*c):
    try: return subprocess.check_output(c, text=True, cwd=D.FT.ROOT).strip()
    except Exception: return None
json.dump(dict(step='45D', git_head_at_report=g('git', 'rev-parse', '--short', 'HEAD'), prereg_commit='ca9bf2d', python=platform.python_version(), platform=platform.platform(), date=time.strftime('%Y-%m-%d'), bootstrap='group, 1000 resamples, seed 0', status='INCOMPLETE (3 h cap)', verdict='DOES NOT PASS', model='mlx-community/gemma-2-9b-it-4bit', variants=['c1', 'c2'], test_pairs=R['pairs']['test'], val_pairs=R['pairs']['val']), open(D.P('run_info.json'), 'w'), indent=1)
