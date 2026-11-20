# Step 45, Part D: claim-by-claim Gemma-2-9B judge

**DOES NOT PASS the pre-registered rule, and the run is INCOMPLETE (compute cap).** Rule: catch >= 71.3% with harmless flagged <= 5.6% at the val-fixed threshold, and flag agreement between the two prompt variants >= 90%. At the threshold fixed on val (c1: score <= 0.00; c2: <= 0.20) the claim-by-claim judge catches **4.9% (1.2-9.8)** (c1) and **4.9% (1.2-9.8)** (c2) of the planted errors in the test sample, flagging 0.0% (0.0-0.0) / 0.0% (0.0-0.0) of harmless rewordings and 0% of identical copies; variant flag agreement 100.0% (100.0-100.0) (met, but only because both variants flag almost nothing). On the same sampled pairs the Step 44 holistic judge at its val threshold (0.4) catches 56.1% (46.4-65.9) with 8.2% (4.3-12.7) harmless flagged. **The pre-registered catch is far from reached.** The run stopped at its time cap: 247 of 350 planned test pairs and 139 of 139 val pairs were judged with both variants (1 unparsed reply excluded).

Pre-registration: [../PREREG.md](../PREREG.md). Code: `usmeta/step45_gemma.py` (calls, prompts), `step45_partD.py`, `step45_partD_report.py`. All replies cached under `.llm_cache` (key = model + prompt) and in `gemma/d_c1.jsonl`, `d_c2.jsonl`.

## What was run

Gemma-2-9B-it 4-bit (MLX, greedy; the same model as Steps 12 / 39; the model was loaded once for Parts F and D). Two prompt variants (`CLAIM_V1`, `CLAIM_V2` in the code): split the candidate into claims, check each against the reference (supported / contradicted / unsupported), list reference facts omitted. Score = 1 - (candidate claims not supported + reference facts omitted) / (candidate claims + omitted); 1.0 = nothing wrong. Sample: a seeded random sample of the Step 44 judge subset (test: 350 planned; val: 139 planned from the val judge pool), same pairs for both variants; the Step 44 holistic scores for the same pairs are used for comparison. Flag threshold per variant: the largest observed val score with at most 5.6% of val harmless rewordings flagged.

## Results (test sample)

| judge | threshold | catch | harmless flagged | identical flagged |
|---|---|---|---|---|
| claim-by-claim, variant 1 | <= 0.00 | 4.9% (1.2-9.8) (n = 82) | 0.0% (0.0-0.0) (n = 159) | 0.0% (0.0-0.0) |
| claim-by-claim, variant 2 | <= 0.20 | 4.9% (1.2-9.8) (n = 82) | 0.0% (0.0-0.0) (n = 159) | 0.0% (0.0-0.0) |
| Step 44 holistic judge, same pairs | <= 0.40 | 56.1% (46.4-65.9) (n = 82) | 8.2% (4.3-12.7) | 0.0% (0.0-0.0) |

Flag agreement between the variants on the test sample: 100.0% (100.0-100.0) (planted errors 100.0% (100.0-100.0), harmless 100.0% (100.0-100.0)).

## Why the catch is so low (and an exploratory look that is NOT part of the verdict)

The claim scores take few distinct values (0, 0.33, 0.5, 0.67, 1.0 ...). On the val sample 7 of 85 harmless rewordings score exactly 0.33, so the largest threshold that keeps harmless flagged at or below 5.6% is the next lower level (0 for c1, 0.2 for c2), which flags almost no planted error (val catch 18%, test 4.9%). The rule is followed as pre-registered; the discrete scores and the small val sample make it a very strict operating point. **Exploratory (not pre-registered, not used for any verdict):** the scores themselves separate errors from harmless rewordings well on the test sample: AUROC (error vs harmless, pooled over pairs) 0.944 (variant 1), 0.936 (variant 2), against 0.908 for the Step 44 holistic score on the same pairs. Flagging at a threshold chosen after seeing test would give (catch / harmless flagged): score <= 0.2: variant 1 5% / 0.0%, variant 2 5% / 0.0%; score <= 0.36: variant 1 22% / 3.8%, variant 2 23% / 5.7%; score <= 0.5: variant 1 57% / 3.8%, variant 2 34% / 7.5%. Even the most favourable of these (about 57% catch) is below the 71.3% bar, and a test-chosen threshold would not be a valid pass.

## Deviations from the PREREG

- **Incomplete:** the Gemma time cap (3 h for this part) stopped the run; 247 of 350 test pairs were judged with both variants (the order was shuffled, so the judged pairs are a random subset).
- **A sample, not the full judge subset:** the PREREG says "the same judge test subset as Step 44" (4,729 pairs); two variants over that subset would need about 40 hours here, so a seeded random sample of 350 test pairs (and 139 val pairs for the threshold) was used. The Step 44 holistic numbers on this sample (56% catch, 8% harmless flagged) are lower than on the full subset (71.3%, 5.6%): sample noise (82 errors) and the different sample mix.
- Harmless flagged is computed over harmless rewordings (small, matched, large, other), as in Step 44; identical copies are reported separately.
- The test split was read via the Step 44 loader (`step19_pairs.load`, logged as `usmeta.step19_pairs`); no other test read for this part.

## Caveats

- One judge model family (Gemma-2-9B-it 4-bit); templated candidates (Step 44 judge subset), not the free-text set A; the claim parser trusts the model's JSON (1 unparsed reply of 774 calls).
- 82 planted errors in the test sample: every rate has a wide interval; cells under 30 groups would be marked too small (none are, at the pooled level).
