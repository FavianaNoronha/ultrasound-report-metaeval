# Step 40 pre-registration: per-dataset fairness on all test scans and calibrated U-Net confidence (written 2026-11-18, before any new test read or number)

Extends Step 38 (30 test scans per dataset, 228 in all; uncalibrated U-Net confidence). Same image check (Step 20 tolerance-aware rule, tau 0.3, adjacent position; `tuning_devval.json`), same saved Step 29 models (breast, thyroid; **no retraining**), same confidence definition (mean probability of the pixels above the model's own threshold at 256 x 256; 0 if the mask is empty), same group bootstrap (1,000 resamples, seed 0). Code: `usmeta/step40_fairness_calibration.py` and a report script (new files; Step 20 / 29 / 38 code imported unchanged).

## (a) Per-dataset gap table on ALL test scans
- **Scans:** every test-split case of a dataset that has at least one planted, image-checkable error (fields count, hc_mm, lesion, orient, pos, size_mm, size_pct; `step20.CHECKABLE`) and an image. Counted before any scoring from `splits.jsonl` (membership only) and `bench_v2d.jsonl` (which fields were planted); no score or image was read for the count:

| dataset | test cases with a planted checkable error | distinct groups (before scoring) |
|---|---|---|
| BrEaST | 103 | 103 |
| BUS-BRA | 63 | 37 |
| BUSI | 58 | 56 |
| UDIAT | 60 | 58 |
| BUS-UCLM | 117 | 7 |
| TN3K | 59 | 59 |
| DDTI | 57 | 43 |
| TN5000 | 57 | 57 |
| **all** | **574** | |

  No dataset has more than 300, so **no sampling is done** (the seeded-300 rule, seed 0, is not triggered). HC18 and FetalHead are not part of this check (their image check is the head-circumference geometry of Step 29b, not the lesion U-Net; no U-Net lesion mask exists for them), as in Step 38. Scans whose image and mask sizes disagree are skipped as in Step 29 and the number skipped is reported.
- **Test read:** one new logged read, `splits.load('test', script='usmeta.step40_fairness_calibration')`. The saved Step 29 models are run on every scan (the 228 Step 38 scans are re-run, not reused from saved masks, so that all 574 are treated alike; the position AUROC of the overlap scans is compared with the saved Step 29 values as a consistency check and any difference is reported).
- **Columns, as Step 38 (a):** scans, detection rate, Dice (scans with a true mask; TN5000 has boxes only: none), position AUROC, correct-report score, groups (position), plus organ and pooled rows, plus the gap below. † = under 30 groups.
- **Rule for a real gap (fixed):** a dataset shows a real gap only if it has **>= 30 groups** (distinct groups with a defined per-scan position AUROC, as in Step 38) **AND** the 95% group-bootstrap CI of (mean per-scan position AUROC of the dataset - mean per-scan position AUROC of all the other datasets pooled) **excludes 0** (groups resampled jointly over all scans, 1,000, seed 0, percentile CI). Under 30 groups: "too small", reported, not decided. A dataset that meets both conditions with a negative difference is a "gap" (lower than the rest); with a positive difference it is "better than the rest". TN5000 is labelled as the one dataset with no training images (cross-dataset); BUS-UCLM has 7 groups (patients) and will be "too small" whatever the numbers.

## (b) Calibration of the U-Net confidence used for abstention
- **Event:** y = 1 if the image check gets the position right on the scan (predicted position equals the reference position or is adjacent, the Step 38 `pos_ok` definition; an empty mask counts as wrong), y = 0 otherwise. Confidence c = the Step 38 confidence of the organ's U-Net.
- **Calibrator, stated before fitting:** c is a mean probability, not a logit, so the temperature-scaling form does not apply directly: **Platt scaling** is used, p = sigmoid(a * logit(c') + b) with c' = clip(c, 0.001, 0.999) (an empty mask, c = 0, becomes 0.001), one pair (a, b) **per organ** (breast, thyroid; the two models have different confidence scales), fitted by L2-regularised logistic regression (strength C = 1.0, intercept unpenalised) on **VAL scans only**. "Before" = c itself read as a probability (p = c).
- **VAL scans:** all val cases of the eight datasets with an image and a usable mask, capped at 300 per dataset by a seeded random draw (seed 0): BrEaST 50, BUS-BRA 300 (of 375), BUSI 157, UDIAT 31, BUS-UCLM 141, TN3K 300 (of 697), DDTI 96, TN5000 300 (of 1,000) = 1,375 scans (counted from `splits.jsonl`, images exist). The saved models were early-stopped and post-processed on val images of their training datasets, so the val position-correct rate is a little optimistic; this is a stated limit.
- **Report on test (all scans of (a)):** expected calibration error (ECE, 10 equal-width bins on [0, 1], bin-size-weighted mean of |observed rate - mean predicted probability|) before and after, pooled and per organ, with group-bootstrap CIs (calibrator held fixed) and the bootstrap CI of the difference (before - after); a reliability diagram (before and after, bin counts shown) at `reliability.png`; the risk-coverage curve before and after: all test scans ranked pooled by raw c vs by calibrated p, error = 1 - y of the kept scans, with a random-abstention baseline, and the error at 80% and 60% coverage (the Step 38 within-organ ranking is shown for reference).
- **No decision rule beyond reporting how much ECE falls** (stated in advance): no threshold for "good calibration" and no verdict word beyond the size of the fall and its interval.

## (c) Relation to Step 38
Step 38's 228 scans are a subset of the new set (checked at run time and reported). The Step 38 per-dataset numbers (a) and its uncalibrated confidence are **superseded**, not contradicted: the new table is larger and uses the same check and models; where a dataset's numbers change, that is the larger sample.

## Caveats stated in advance
- Group counts are small for several datasets (BUS-BRA 37, DDTI 43 groups at the case level, fewer with a defined position AUROC; BUS-UCLM 7); position AUROC is defined only for scans with a planted position error, which lowers the groups used.
- Dataset gaps are not separable from lesion mix, image size, the number of training images per dataset, or scanner (scanner identity exists in the files of BUS-BRA only).
- The position-correct event is rare (11 of 228 wrong in Step 38), so the top reliability bins carry most scans and ECE is dominated by them; ECE with few errors is noisy and biased upward in small samples.
- Templated candidates only; one seed; saved models.

Outputs: `results.md` (decision lines first, per-dataset table, calibration table, figure path, deviations), `results.json`, `run_info.json`, `reliability.png`, `risk_coverage_calibrated.png`.
