# Step 45, Part D: claim-by-claim Gemma-2-9B judge

**DOES NOT PASS the pre-registered rule; the sampled run completed after resuming saved replies from the initial 3 h cap.** Rule: catch >= 71.3% with harmless flagged <= 5.6% at the val-fixed threshold, and flag agreement between the two prompt variants >= 90%. At the threshold fixed on val (c1: score <= 0.00; c2: <= 0.20) the claim-by-claim judge catches **8.9% (4.0-14.4)** (c1) and **8.9% (4.0-14.4)** (c2) of the planted errors in the test sample, flagging 0.0% (0.0-0.0) / 0.0% (0.0-0.0) of harmless rewordings and 0.0% (0.0-0.0) / 0.0% (0.0-0.0) of identical copies; variant flag agreement 100.0% (100.0-100.0). On the same sampled pairs the Step 44 holistic judge at its val threshold (0.4) catches 61.8% (52.7-70.1) with 7.9% (4.2-11.6) harmless flagged. **The pre-registered catch is far from reached.** The initial 3 h cap stopped after 247/350 planned test pairs; after resuming saved replies, 349/350 test and 139/139 val pairs parsed with both variants (1 unparsed response excluded).

Pre-registration: [../PREREG.md](../PREREG.md). Code: `usmeta/step45_gemma.py` (calls, prompts), `step45_partD.py`, `step45_partD_report.py`. All replies cached under `.llm_cache` (key = model + prompt) and in `gemma/d_c1.jsonl`, `d_c2.jsonl`.

## What was run

Gemma-2-9B-it 4-bit (MLX, greedy; the same model as Steps 12 / 39; the model was loaded once for Parts F and D). Two prompt variants (`CLAIM_V1`, `CLAIM_V2` in the code): split the candidate into claims, check each against the reference (supported / contradicted / unsupported), list reference facts omitted. Score = 1 - (candidate claims not supported + reference facts omitted) / (candidate claims + omitted); 1.0 = nothing wrong. Sample: a seeded random sample of the Step 44 judge subset (test: 350 planned; val: 139 planned from the val judge pool), same pairs for both variants; the Step 44 holistic scores for the same pairs are used for comparison. Flag threshold per variant: the largest observed val score with at most 5.6% of val harmless rewordings flagged.

## Results (test sample)

| judge | threshold | catch | harmless flagged | identical flagged |
|---|---|---|---|---|
| claim-by-claim, variant 1 | <= 0.00 | 8.9% (4.0-14.4) (n = 123) | 0.0% (0.0-0.0) (n = 215) | 0.0% (0.0-0.0) |
| claim-by-claim, variant 2 | <= 0.20 | 8.9% (4.0-14.4) (n = 123) | 0.0% (0.0-0.0) (n = 215) | 0.0% (0.0-0.0) |
| Step 44 holistic judge, same pairs | <= 0.40 | 61.8% (52.7-70.1) (n = 123) | 7.9% (4.2-11.6) | 0.0% (0.0-0.0) |

Flag agreement between the variants on the test sample: 100.0% (100.0-100.0) (planted errors 100.0% (100.0-100.0), harmless 100.0% (100.0-100.0)).

## Why the catch is so low (and an exploratory look that is NOT part of the verdict)

The claim scores take few distinct values (0, 0.33, 0.5, 0.67, 1.0 ...). On the val sample, 7 of 85 harmless rewordings score exactly 0.33, so the largest threshold that holds harmless flags at or below 5.6% is the next lower level (0 for c1, 0.2 for c2). The rule is followed as pre-registered; discrete scores and the small val sample make it a strict operating point. **Exploratory (not pre-registered, not used for any verdict):** AUROC (error vs harmless, pooled over pairs) is 0.932 (variant 1), 0.943 (variant 2), against 0.913 for the Step 44 holistic score on the same pairs. Thresholds chosen after seeing test would give (catch / harmless flagged): score <= 0.2: variant 1 8.9% / 0.0%, variant 2 8.9% / 0.0%; score <= 0.36: variant 1 26.0% / 5.1%, variant 2 26.0% / 5.6%; score <= 0.5: variant 1 59.3% / 5.6%, variant 2 36.6% / 7.0%. The best catch among these displayed thresholds is 59.3%; test-chosen thresholds are invalid for the pre-registered pass rule.

## Deviations from the PREREG

- The initial 3 h run stopped after 774 variant calls (247 test pairs and all 139 val pairs). Saved replies were resumed to finish the 489-pair sample; 349 test and 139 val pairs parsed with both variants. One c1 response remained unparsed after a retry. This extends compute beyond the initial cap.
- **A sample, not the full judge subset:** the PREREG says "the same judge test subset as Step 44" (4,729 pairs); two variants over that subset would need about 40 hours here, so a seeded random sample of 350 test pairs (and 139 val pairs for the threshold) was used. The Step 44 holistic numbers shown above are computed on the same parsed sample.
- Harmless flagged is computed over harmless rewordings (small, matched, large, other), as in Step 44; identical copies are reported separately.
- The test split was read via the Step 44 loader (`step19_pairs.load`, logged as `usmeta.step19_pairs`); no other test read for this part.

## Caveats

- One judge model family (Gemma-2-9B-it 4-bit); templated candidates (Step 44 judge subset), not the free-text set A; 1 unparsed response among 978 planned variant outputs, excluded from paired-variant scoring.
- 123 planted errors in the parsed test sample: every rate has an interval; cells under 30 groups would be marked too small (none are, at the pooled level).
