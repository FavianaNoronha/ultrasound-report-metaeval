# Step 36: adversarial wording attack on the judge

Limitations: [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md). **Pre-registration (committed before any judge call): [PREREG.md](PREREG.md).** Code: `usmeta/step36_adversarial.py`, `step36_report.py` (new files; frozen Gemma judge, prompt_v2, greedy, imported unchanged). Test split read once (logged: `usmeta.step36_adversarial`).

**Hypothesis (verbatim):** "the judge can be raised by >= 0.2 on a wrong report by wording-only edits."

## Decision (pre-registered: supported iff the mean gain of the winning transform on the TEST wrong reports is >= 0.2)

**NOT SUPPORTED.** The winning transform on dev / val was **T5_reorder** (mean gain -0.10); run once on the test wrong reports (n = 100, 94 groups) it changed the judge score by **-0.13 (-0.18 to -0.09)** on average (maximum +0.30, median +0.00, 5% of reports gained >= 0.2). The untransformed wrong reports had a mean judge score of 0.39 (selected to be <= 0.7), leaving 0.3 to 1.0 of headroom. **Reading:** the fixed wording edits lowered the judge score on average (every transform on dev / val: mean gain -0.10 to -0.21; extra or reordered text is penalised), so no transform raised it by 0.2 on average; a minority of individual reports did gain (largest single gain +0.3 to +0.5 on dev / val, +0.30 on test), which shows the judge is unstable for single reports but is not a consistent hole.

**Overtaking** (the transformed wrong report scores strictly above its correct counterpart, the style-swap rewording of the same reference with the higher saved judge score): 6% of test wrong reports after T5_reorder against 9% before; against the lower-scoring style swap 6% after against 9% before.

## Dev / val: the five fixed transforms (exploratory; picks the winner)

96 wrong reports (up to 10 per dataset, saved judge score <= 0.7, one per case; dev + val together; per dataset: BUS-BRA 10, BUS-UCLM 6, BUSI 10, BrEaST 10, DDTI 10, FetalHead 10, HC18 10, TN3K 10, TN5000 10, UDIAT 10). Mean untransformed judge score 0.36. Gain = judge_score(transformed) - judge_score(original).

| transform | n | **max gain** | mean gain (95% CI, group bootstrap) | median gain | share with gain >= 0.2 | share with any gain | overtakes best correct counterpart | overtakes weaker counterpart |
|---|---|---|---|---|---|---|---|---|
| (untransformed) | 96 | — | — | — | — | — | 15% | 15% |
| T1_hedge | 96 | +0.50 | -0.13 (-0.18 to -0.08) | -0.10 | 14% | 16% | 5% | 5% |
| T2_recommendation | 96 | +0.30 | -0.18 (-0.22 to -0.13) | -0.20 | 4% | 8% | 12% | 12% |
| T3_double_filler | 96 | +0.30 | -0.21 (-0.25 to -0.16) | -0.20 | 3% | 5% | 10% | 10% |
| T4_confident | 96 | +0.50 | -0.14 (-0.19 to -0.09) | -0.10 | 14% | 18% | 5% | 5% |
| T5_reorder **(winner)** | 96 | +0.30 | -0.10 (-0.15 to -0.05) | +0.00 | 11% | 12% | 9% | 9% |

The five transforms are fixed in the PREREG (hedge, recommendation, double length with correct filler, confident phrasing, reorder): no fact is added, removed or changed. The winner is the highest mean gain.

## Test: the winning transform, once

Wrong reports from the test judged subset (Steps 10d + 12), up to 10 per dataset, saved judge score <= 0.7, seed 0: n = 100; per dataset (every cell is under 30 groups: **too small to compare**): BUS-BRA 10 (mean -0.15), BUS-UCLM 10 (mean -0.03), BUSI 10 (mean -0.39), BrEaST 10 (mean -0.27), DDTI 10 (mean -0.13), FetalHead 10 (mean -0.06), HC18 10 (mean -0.09), TN3K 10 (mean -0.00), TN5000 10 (mean +0.05), UDIAT 10 (mean -0.27).

## Caveats

- **Selection effect:** only wrong reports the judge already penalises (saved score <= 0.7) are used, so a gain is possible; errors the judge misses entirely are not part of this test. The sample is small (up to 10 per dataset; datasets with fewer qualifying reports use all of them).
- **Fixed, simple transforms on templated text**, not an optimised attack; a judge-in-the-loop search was not tried. The PREREG names "the large harmless rewording" as the correct counterpart; two exist (terse, long), so the one with the higher saved judge score is used (the stricter test) and the lower is also reported.
- Greedy decoding, one judge model, one prompt; the judge is known to depend on the prompt (Step 21c). Gains of a few hundredths are within that noise.
