# Step 45, Part F: tuned hybrid (extractor v5 / number checker, then the judge) on the free-text set A

**INCOMPLETE (compute cap): on the pairs judged, the numbers meet the pre-registered rule (PASS if read as complete).** Rule: catch >= 80% at harmless flagged <= 5.6% on set A test, beating the judge alone on the same candidates with the CI of the paired difference excluding 0. Hybrid: catch **100.0% (100.0-100.0)** of 150 planted-error twins, harmless flagged **4.1% (2.1-6.5)** of 369; judge alone (same candidates, threshold fixed on dev/val): catch 72.7% (65.3-80.1), harmless flagged 3.5% (1.6-5.7); paired catch difference hybrid minus judge +27.3 points (95% CI +19.9 to +34.7). **The judge call stopped at its 2 h cap: 920 of 1030 planned pairs were judged (test 519 of 629; the order was shuffled, so the missing pairs are a random 17%).** Note the upper end of the hybrid's harmless interval (6.5%) is above 5.6%; the point estimate is below it. The hybrid catches everything because the **rules do all the catching** (see below), and they are near-perfect only because the extractor reads writer-made text that states the supplied facts; a pass here is "better on writer-made free text", not clinical validation.

Pre-registration: [../PREREG.md](../PREREG.md). Code: `usmeta/step45_gemma.py` (calls), `step45_partF.py`, `step45_partF_report.py`. Set A: [../freetext/results.md](../freetext/results.md).

## Design and tuning (dev/val of set A; the judged dev/val subset)

Rules (flag if either fires): the Part C number checker (score < 1), or an extractor v5 mismatch between the candidate's extracted facts and the reference facts, in one of two modes fixed on dev/val: **conflict** (a field present in both differs) or **conflict + omission** (also a reference fact the extraction lacks). Candidates not flagged by the rules go to the frozen holistic Gemma-2-9B judge (prompt_v2, Step 7 / 12 / 39) and are flagged if its score is at or below a threshold. Both the mode and the threshold were chosen on the dev/val pairs (401 judged: 281 harmless, 120 twins) so that at most 5.6% of harmless reports are flagged. Result: mode **conflict_omission** (rules alone flag 0.7% of dev/val harmless, hybrid 5.3% harmless flagged, catch 100.0%); judge threshold 0.30. Judge alone at threshold 0.30: 5.0% harmless flagged, catch 68.3% on dev/val.

## Test results (set A test)

| monitor | catch of planted-error twins | harmless flagged |
|---|---|---|
| hybrid (rules, then judge) | 100.0% (100.0-100.0) | 4.1% (2.1-6.5) |
| judge alone | 72.7% (65.3-80.1) | 3.5% (1.6-5.7) |
| rules only (number checker + extractor v5) | 100.0% (100.0-100.0) | 0.8% (0.0-1.9) |

By organ (catch): breast hybrid 100% / judge 85% (n = 47), thyroid hybrid 100% / judge 64% (n = 36), fetal hybrid 100% / judge 69% (n = 67).

**What this shows:** the rules alone reach the same catch with 0.8% harmless flagged; the judge stage only adds false alarms (its threshold spends the remaining harmless budget) and no catch. The judge alone misses about a quarter of the twins (72.7%), most in thyroid and fetal head.

## Deviations from the PREREG

- **Incomplete:** the Gemma calls stopped at the 2 h cap (920 of 1030 pairs). The PREREG's F also did not say how the judge's dev/val threshold would be set; here a 40-cases-per-organ dev/val subset was judged.
- Set A is smaller than the PREREG (Part A); the hybrid's extractor input is the Part B extractor v5 outputs (the frozen v5), the checker is Part C's (tolerance 0).
- Test read for this part: the set A test reports were already sampled in Part A and scored in Parts B, C and E; this part reads no additional test data (no new `splits.load`).

## Caveats

- **Writer-made text:** the writer states the supplied facts nearly verbatim, so extractor v5 gets 98-100% of fields exactly right and a one-field twin is found by comparison with the reference facts; real radiologist or VLM text would give a noisier extraction and a lower rule catch.
- The judge threshold was chosen on a small dev/val subset (281 harmless reports), so its flagged share on test (3.5%) differs from the 5.6% budget.
- Twins: one planted error per case (field mix as in the benchmark); 150 test twins, 164 groups.
