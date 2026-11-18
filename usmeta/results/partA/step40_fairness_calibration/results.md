# Step 40: per-dataset fairness on all test scans and calibrated U-Net confidence

Pre-registration: [PREREG.md](PREREG.md) (committed before any new test read). Limitations: [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md). Code: `usmeta/step40_fairness_calibration.py`, `step40_report.py` (new files; Step 20 / 29 / 38 code imported unchanged; saved Step 29 models, no retraining). One new logged test read (`usmeta.step40_fairness_calibration`). Same Step 20 tolerance-aware rule (tau 0.3, adjacent position), group bootstrap 1,000, seed 0, † = under 30 groups.

## Decision lines

1. **(a) Per-dataset gap, 498 test scans of 8 datasets (not 228).** By the pre-registered rule (>= 30 groups AND the 95% CI of dataset-minus-the-rest position AUROC excludes 0): **no dataset shows a real gap (lower than the rest)**; **BrEaST, UDIAT score above the rest** (BrEaST +0.06 (+0.00 to +0.11); UDIAT +0.10 (+0.06 to +0.15)); no gap detected for BUSI, TN3K (interval includes 0). **Too small to decide (under 30 groups with a defined position AUROC): BUS-BRA, BUS-UCLM, DDTI, TN5000** — among them DDTI (-0.14 (-0.27 to -0.03), 28 groups) and TN5000 (-0.15 (-0.30 to -0.02), 27 groups) have intervals that exclude 0 on the low side but are indicative only under the rule (TN5000 is the dataset with no training images).
2. **(b) Calibration (Platt scaling per organ, fitted on 1246 val scans): ECE on test falls from 0.030 to 0.018 pooled (fall 0.013, 95% interval -0.013 to +0.025), from 0.039 to 0.030 for breast (fall 0.009, interval +0.004 to +0.013), and rises from 0.031 to 0.038 for thyroid (change -0.007, interval -0.032 to +0.043).** The pooled and thyroid falls are not distinguishable from 0; only breast shows a fall whose interval excludes 0. No decision rule was set beyond reporting the size of the fall (PREREG).
3. **Risk-coverage:** abstaining on calibrated probability (pooled ranking) gives position-check error 2.3% at 80% coverage and 0.3% at 60%; raw confidence ranked pooled gives 1.8% and 0.0%; the Step 38 within-organ raw ranking 2.8% and 1.3%; random abstention 4.6% (no abstention 4.6%). Only 23 of 498 scans have a wrong position, so these error rates rest on very few events.
4. **Relation to Step 38:** its 228 scans are all in the new set (228 of 228); re-running the saved models on them reproduced the saved Step 29 position AUROC exactly (0 of 228 differ). Step 38's per-dataset numbers are superseded by the larger table below, not contradicted.

## (a) Per-dataset gap table (Step 29 U-Net, all usable test scans with a planted checkable error)

Position AUROC and correct-report score: Step 20 tolerance-aware check (AUROC of planted errors vs harmless rewordings per scan; correct-report score = mean score of the identical copies). Dice only for scans with a true mask (TN5000 has boxes only). Detection = share of non-empty masks. Gap = mean per-scan position AUROC of the dataset minus that of all other datasets pooled, group bootstrap over all scans. Groups (position) = groups with a defined per-scan position AUROC; the rule needs >= 30.

| source | scans scored (planned) | detection rate | Dice | position AUROC | correct-report score | groups (position) | gap vs the rest (95% CI) | verdict |
|---|---|---|---|---|---|---|---|---|
| BrEaST (breast) | 101 (103) | 0.99 (0.97–1.00) | 0.75 (0.70–0.80) | 0.94 (0.89–0.98) | 0.94 (0.91–0.96) | 53 | +0.06 (+0.00 to +0.11) | better than the other datasets |
| BUS-BRA (breast) | 63 (63) | 1.00 (1.00–1.00) | 0.87 (0.83–0.90) | 0.99 (0.95–1.00) † | 0.97 (0.94–0.99) | 23 | +0.11 (+0.06 to +0.15) | too small (under 30 groups) |
| BUSI (breast) | 52 (58) | 0.96 (0.91–1.00) | 0.69 (0.58–0.78) | 0.86 (0.78–0.93) | 0.91 (0.86–0.96) | 31 | -0.04 (-0.12 to +0.05) | no gap detected (interval includes 0) |
| UDIAT (breast) | 60 (60) | 1.00 (1.00–1.00) | 0.84 (0.79–0.88) | 0.98 (0.94–1.00) | 0.97 (0.95–0.99) | 42 | +0.10 (+0.06 to +0.15) | better than the other datasets |
| BUS-UCLM (breast) | 49 (117) | 0.98 (0.93–1.00) † | 0.80 (0.74–0.89) † | 0.93 (0.67–1.00) † | 0.94 (0.87–0.99) † | 3 | +0.04 (-0.23 to +0.11) | too small (under 30 groups) |
| TN3K (thyroid) | 59 (59) | 1.00 (1.00–1.00) | 0.75 (0.68–0.82) | 0.84 (0.75–0.91) | 0.92 (0.88–0.95) | 35 | -0.06 (-0.15 to +0.02) | no gap detected (interval includes 0) |
| DDTI (thyroid) | 57 (57) | 0.98 (0.94–1.00) | 0.63 (0.55–0.70) | 0.77 (0.64–0.88) † | 0.88 (0.82–0.93) | 28 | -0.14 (-0.27 to -0.03) | too small (under 30 groups) |
| TN5000 (thyroid) — no training images | 57 (57) | 1.00 (1.00–1.00) | — † | 0.76 (0.62–0.88) † | 0.85 (0.81–0.89) | 27 | -0.15 (-0.30 to -0.02) | too small (under 30 groups) |
| **breast (all)** | 325 | 0.99 (0.97–1.00) | 0.79 (0.76–0.81) | 0.94 (0.92–0.96) | 0.95 (0.93–0.96) | 152 | | |
| **thyroid (all)** | 173 | 0.99 (0.98–1.00) | 0.69 (0.64–0.74) | 0.79 (0.72–0.85) | 0.88 (0.86–0.91) | 90 | | |
| **pooled** | 498 | 0.99 (0.98–1.00) | 0.76 (0.74–0.79) | 0.89 (0.86–0.92) | 0.93 (0.91–0.94) | 242 | | |

For comparison, Step 38 (30 scans per dataset): position AUROC BrEaST 0.91, BUS-BRA 1.00, BUSI 0.84, UDIAT 1.00, BUS-UCLM 0.94, TN3K 0.93, TN5000 0.69, DDTI 0.77 (all cells under 30 groups). Dataset gaps are not separable from lesion mix, image size, the number of training images per dataset or the scanner (scanner identity exists in the files of BUS-BRA only). BUS-UCLM has very few groups (patients) and cannot be decided.

## (b) Calibration of the confidence used for abstention

Event y = position check right (predicted position equals the reference position or is adjacent; an empty mask counts as wrong). Calibrator (stated in the PREREG before fitting): **Platt scaling** p = sigmoid(a * logit(c') + b), c' = clip(c, 0.001, 0.999), one pair per organ, L2 logistic regression (C = 1.0) on VAL scans only (1246 scored): breast a = 1.74, b = -1.62 (n = 554, 21 wrong); thyroid a = 0.98, b = 0.70 (n = 692, 44 wrong). ECE = 10 equal-width bins on [0, 1]; CIs: group bootstrap on test with the calibrator fixed.

| group | test scans | groups | position correct (test) | ECE before (95% CI) | ECE after (95% CI) | fall (before minus after, 95% CI) |
|---|---|---|---|---|---|---|
| pooled | 498 | 411 | 95.4% | 0.030 (0.019–0.047) | 0.018 (0.010–0.035) | +0.013 (-0.013 to +0.025) |
| breast | 325 | 252 | 97.8% | 0.039 (0.025–0.049) | 0.030 (0.016–0.042) | +0.009 (+0.004 to +0.013) |
| thyroid | 173 | 159 | 90.8% | 0.031 (0.018–0.076) | 0.038 (0.010–0.084) | -0.007 (-0.032 to +0.043) |

Val position-correct rate: breast 96.2%, thyroid 93.6%. Figures: `reliability.png` (reliability diagram, before and after, bin counts), `risk_coverage_calibrated.png`.

### Risk-coverage (error = position check wrong, share of kept scans)

| coverage | raw confidence, pooled ranking | calibrated probability, pooled ranking | raw confidence, within-organ ranking (Step 38 style) | random abstention |
|---|---|---|---|---|
| 100% | 4.6% | 4.6% | 4.6% | 4.6% |
| 90% | 3.1% | 3.6% | 3.6% | 4.6% |
| 80% | 1.8% | 2.3% | 2.8% | 4.6% |
| 70% | 0.9% | 1.1% | 2.0% | 4.6% |
| 60% | 0.0% | 0.3% | 1.3% | 4.5% |
| 50% | 0.0% | 0.0% | 1.2% | 4.6% |

## Deviations from the PREREG

- **The test set scored is 498 scans, not the 574 planned**: 76 scans have no usable true mask or box (BrEaST 2, BUSI 6, BUS-UCLM 68) and were skipped, as Step 29's selection (which required masks) did implicitly. The PREREG listed only size mismatches as a skip reason. Per-dataset planned counts are in the table. The same rule dropped 129 val scans (BUSI 28, BUS-UCLM 97, DDTI 4); 1246 of 1,375 val scans were used for the calibrator. No dataset exceeded 300, so no seeded sampling was done on test; val was capped at 300 per dataset (seed 0) as pre-registered.
- A smoke test of the code on 60 val scans (no test scan) was run before the test read. No other deviation known.

## Caveats

- Group counts: only BrEaST, BUSI, UDIAT and TN3K reach 30 groups with a defined position AUROC; BUS-BRA, BUS-UCLM, DDTI and TN5000 do not, so their gaps (including the two low ones) are indicative, not decided. Position AUROC exists only for scans with a planted position error.
- The calibrator was fitted on val scans on which the saved models had been early-stopped and post-processed, and the position-correct event is rare (about 4-5% wrong), so ECE rests on few events and is noisy; breast val and test position-correct rates differ by 1.6 points, thyroid by 2.8.
- Pooled ranking by calibrated probability uses organ-specific maps, so it is the only ranking that differs from raw confidence in the pooled curve; the within-organ raw ranking is shown for reference.
- Templated candidates, one seed, saved models; HC18 / FetalHead are not part of this check.
