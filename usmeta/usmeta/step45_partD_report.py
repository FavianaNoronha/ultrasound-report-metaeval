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
inc = bool(S.get('stopped_by_cap'))
unparsed = R['pairs']['unparsed']
unparsed_text = f"{unparsed} unparsed response{'s' if unparsed != 1 else ''}"
if inc:
    run_coverage = f"The run stopped at its 3 h cap: {R['pairs']['test']}/350 test and {R['pairs']['val']}/139 val pairs parsed with both variants ({unparsed_text} excluded)."
else:
    run_coverage = f"The initial 3 h cap stopped after 247/350 planned test pairs; after resuming saved replies, {R['pairs']['test']}/350 test and {R['pairs']['val']}/139 val pairs parsed with both variants ({unparsed_text} excluded)."
best_exploratory_catch = max(x[v][0] for x in curve.values() for v in ('c1', 'c2'))
L = ['# Step 45, Part D: claim-by-claim Gemma-2-9B judge', '',
     f"**DOES NOT PASS the pre-registered rule; {'INCOMPLETE (compute cap)' if inc else 'the sampled run completed after resuming saved replies from the initial 3 h cap'}.** Rule: catch >= 71.3% with harmless flagged <= 5.6% at the val-fixed threshold, and flag agreement between the two prompt variants >= 90%. At the threshold fixed on val (c1: score <= {V['c1']['threshold']:.2f}; c2: <= {V['c2']['threshold']:.2f}) the claim-by-claim judge catches **{f(V['c1']['test']['catch'])}** (c1) and **{f(V['c2']['test']['catch'])}** (c2) of the planted errors in the test sample, flagging {f(V['c1']['test']['harmless_flagged'])} / {f(V['c2']['test']['harmless_flagged'])} of harmless rewordings and {f(V['c1']['test']['identical_flagged'])} / {f(V['c2']['test']['identical_flagged'])} of identical copies; variant flag agreement {f(R['agreement']['all'])}. "
     f"On the same sampled pairs the Step 44 holistic judge at its val threshold (0.4) catches {f(H['catch'])} with {f(H['harmless_flagged'])} harmless flagged. **The pre-registered catch is far from reached.** "
     f"{run_coverage}", '',
     'Pre-registration: [../PREREG.md](../PREREG.md). Code: `usmeta/step45_gemma.py` (calls, prompts), `step45_partD.py`, `step45_partD_report.py`. All replies cached under `.llm_cache` (key = model + prompt) and in `gemma/d_c1.jsonl`, `d_c2.jsonl`.', '',
     '## What was run', '',
     'Gemma-2-9B-it 4-bit (MLX, greedy; the same model as Steps 12 / 39; the model was loaded once for Parts F and D). Two prompt variants (`CLAIM_V1`, `CLAIM_V2` in the code): split the candidate into claims, check each against the reference (supported / contradicted / unsupported), list reference facts omitted. Score = 1 - (candidate claims not supported + reference facts omitted) / (candidate claims + omitted); 1.0 = nothing wrong. '
     'Sample: a seeded random sample of the Step 44 judge subset (test: 350 planned; val: 139 planned from the val judge pool), same pairs for both variants; the Step 44 holistic scores for the same pairs are used for comparison. Flag threshold per variant: the largest observed val score with at most 5.6% of val harmless rewordings flagged.', '',
     '## Results (test sample)', '', '| judge | threshold | catch | harmless flagged | identical flagged |', '|---|---|---|---|---|']
for v, nm in (('c1', 'claim-by-claim, variant 1'), ('c2', 'claim-by-claim, variant 2')): L.append(f"| {nm} | <= {V[v]['threshold']:.2f} | {f(V[v]['test']['catch'])} (n = {V[v]['test']['catch_n']}) | {f(V[v]['test']['harmless_flagged'])} (n = {V[v]['test']['harmless_flagged_n']}) | {f(V[v]['test']['identical_flagged'])} |")
L += [f"| Step 44 holistic judge, same pairs | <= 0.40 | {f(H['catch'])} (n = {H['catch_n']}) | {f(H['harmless_flagged'])} | {f(H['identical_flagged'])} |", '',
      f"Flag agreement between the variants on the test sample: {f(R['agreement']['all'])} (planted errors {f(R['agreement']['errors'])}, harmless {f(R['agreement']['harmless'])}).", '',
      '## Why the catch is so low (and an exploratory look that is NOT part of the verdict)', '',
      f"The claim scores take few distinct values (0, 0.33, 0.5, 0.67, 1.0 ...). On the val sample, 7 of 85 harmless rewordings score exactly 0.33, so the largest threshold that holds harmless flags at or below 5.6% is the next lower level (0 for c1, 0.2 for c2). The rule is followed as pre-registered; discrete scores and the small val sample make it a strict operating point. "
      f"**Exploratory (not pre-registered, not used for any verdict):** AUROC (error vs harmless, pooled over pairs) is {a1:.3f} (variant 1), {a2:.3f} (variant 2), against {ah:.3f} for the Step 44 holistic score on the same pairs. Thresholds chosen after seeing test would give (catch / harmless flagged): " + '; '.join(f"score <= {t}: variant 1 {c['c1'][0] * 100:.1f}% / {c['c1'][1] * 100:.1f}%, variant 2 {c['c2'][0] * 100:.1f}% / {c['c2'][1] * 100:.1f}%" for t, c in curve.items()) + f". The best catch among these displayed thresholds is {best_exploratory_catch * 100:.1f}%; test-chosen thresholds are invalid for the pre-registered pass rule.", '',
      '## Deviations from the PREREG', '',
      f"- The initial 3 h run stopped after 774 variant calls (247 test pairs and all 139 val pairs). Saved replies were resumed to finish the 489-pair sample; {R['pairs']['test']} test and {R['pairs']['val']} val pairs parsed with both variants. One c1 response remained unparsed after a retry. This extends compute beyond the initial cap.",
      '- **A sample, not the full judge subset:** the PREREG says "the same judge test subset as Step 44" (4,729 pairs); two variants over that subset would need about 40 hours here, so a seeded random sample of 350 test pairs (and 139 val pairs for the threshold) was used. The Step 44 holistic numbers shown above are computed on the same parsed sample.',
      '- Harmless flagged is computed over harmless rewordings (small, matched, large, other), as in Step 44; identical copies are reported separately.',
      '- The test split was read via the Step 44 loader (`step19_pairs.load`, logged as `usmeta.step19_pairs`); no other test read for this part.', '',
      '## Caveats', '',
      f"- One judge model family (Gemma-2-9B-it 4-bit); templated candidates (Step 44 judge subset), not the free-text set A; {unparsed_text} among {2 * R['pairs']['planned']} planned variant outputs, excluded from paired-variant scoring.",
      f"- {V['c1']['test']['catch_n']} planted errors in the parsed test sample: every rate has an interval; cells under 30 groups would be marked too small (none are, at the pooled level).", '']
open(D.P('results.md'), 'w').write('\n'.join(L)); print('wrote', len(L))
def g(*c):
    try: return subprocess.check_output(c, text=True, cwd=D.FT.ROOT).strip()
    except Exception: return None
json.dump(dict(step='45D', git_head_at_report=g('git', 'rev-parse', '--short', 'HEAD'), prereg_commit='ca9bf2d', python=platform.python_version(), platform=platform.platform(), date=time.strftime('%Y-%m-%d'), bootstrap='group, 1000 resamples, seed 0', status='INCOMPLETE (compute cap)' if inc else 'complete after resuming initial 3 h cap; one unparsed response', verdict='DOES NOT PASS', resume=dict(initial_variant_calls=774, initial_run_seconds=12317, completion_variant_calls=204, completion_run_seconds=1631, retried_unparsed_response=True, retry_seconds=26, exceeded_initial_cap=True), model='mlx-community/gemma-2-9b-it-4bit', variants=['c1', 'c2'], test_pairs=R['pairs']['test'], planned_test_pairs=GM.D_TEST, val_pairs=R['pairs']['val'], unparsed=unparsed), open(D.P('run_info.json'), 'w'), indent=1)
