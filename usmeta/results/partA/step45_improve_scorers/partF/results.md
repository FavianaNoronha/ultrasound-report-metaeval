# Step 45, Part F: tuned hybrid (extractor v5 / number checker, then the judge) on the free-text set A

**Completed after resuming saved replies from the initial 2 h cap: the results meet the pre-registered rule.** Rule: catch >= 80% at harmless flagged <= 5.6% on set A test, beating the judge alone on the same candidates with the CI of the paired difference excluding 0. Hybrid: catch **100.0% (100.0-100.0)** of 185 planted-error twins, harmless flagged **5.0% (3.0-7.3)** of 444; judge alone (same candidates, threshold fixed on dev/val): catch 71.4% (64.5-77.6), harmless flagged 4.5% (2.6-6.9); paired catch difference hybrid minus judge +28.6 points (95% CI +22.4 to +35.5). **The resumed run judged all 1030 planned pairs (test 629/629).** Note the upper end of the hybrid's harmless interval (7.3%) is above 5.6%; the point estimate is below it. The hybrid catches everything because the **rules do all the catching** (see below), and they are near-perfect only because the extractor reads writer-made text that states the supplied facts; a pass here is "better on writer-made free text", not clinical validation.

Pre-registration: [../PREREG.md](../PREREG.md). Code: `usmeta/step45_gemma.py` (calls), `step45_partF.py`, `step45_partF_report.py`. Set A: [../freetext/results.md](../freetext/results.md).

## Design and tuning (dev/val of set A; the judged dev/val subset)

Rules (flag if either fires): the Part C number checker (score < 1), or an extractor v5 mismatch between the candidate's extracted facts and the reference facts, in one of two modes fixed on dev/val: **conflict** (a field present in both differs) or **conflict + omission** (also a reference fact the extraction lacks). Candidates not flagged by the rules go to the frozen holistic Gemma-2-9B judge (prompt_v2, Step 7 / 12 / 39) and are flagged if its score is at or below a threshold. Both the mode and the threshold were chosen on the dev/val pairs (401 judged: 281 harmless, 120 twins) so that at most 5.6% of harmless reports are flagged. Result: mode **conflict_omission** (rules alone flag 0.7% of dev/val harmless, hybrid 5.3% harmless flagged, catch 100.0%); judge threshold 0.30. Judge alone at threshold 0.30: 5.0% harmless flagged, catch 68.3% on dev/val.

## Test results (set A test)

| monitor | catch of planted-error twins | harmless flagged |
|---|---|---|
| hybrid (rules, then judge) | 100.0% (100.0-100.0) | 5.0% (3.0-7.3) |
| judge alone | 71.4% (64.5-77.6) | 4.5% (2.6-6.9) |
| rules only (number checker + extractor v5) | 100.0% (100.0-100.0) | 0.9% (0.2-1.8) |

By organ (catch): breast hybrid 100% / judge 85% (n = 52), thyroid hybrid 100% / judge 64% (n = 44), fetal hybrid 100% / judge 67% (n = 89).

**What this shows:** rules alone catch 100.0% with 0.9% harmless flagged. Adding the judge does not increase catch and raises harmless flags to 5.0%. The judge alone catches 71.4%.

## Deviations from the PREREG

- The initial 2 h run stopped at 920/1,030 pairs. The saved replies were resumed; all 1030/1030 planned pairs are now judged. This extends compute beyond the initial cap. The PREREG's F also did not say how the judge's dev/val threshold would be set; here a 40-cases-per-organ dev/val subset was judged.
- Set A is smaller than the PREREG (Part A); the hybrid's extractor input is the Part B extractor v5 outputs (the frozen v5), the checker is Part C's (tolerance 0).
- Test read for this part: the set A test reports were already sampled in Part A and scored in Parts B, C and E; this part reads no additional test data (no new `splits.load`).

## Caveats

- **Writer-made text:** the writer states the supplied facts nearly verbatim, so extractor v5 gets 98-100% of fields exactly right and a one-field twin is found by comparison with the reference facts; real radiologist or VLM text would give a noisier extraction and a lower rule catch.
- The judge threshold was chosen on a small dev/val subset (281 harmless reports); the judge alone flagged 4.5% of test harmless reports.
- Twins: one planted error per case (field mix as in the benchmark); 185 test twins, 164 groups.
