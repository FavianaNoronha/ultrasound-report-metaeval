# Step 45, Part E: small learned scorer

**PASS the pre-registered rule** (AUROC on set A test at least 0.05 above the best single existing text scorer, CI of the paired difference excluding 0). Set A test (writer-made free text, planted-error twins vs the same case's harmless reports, 185 cases): logistic regression **0.895 (0.855-0.931)**, gradient boosting 0.863 (0.827-0.897), best single scorer (rougeL) 0.750 (0.703-0.799). Paired difference to rougeL: logistic regression +0.144 (95% CI +0.085 to +0.196), gradient boosting +0.113 (+0.065 to +0.159). Both win on free text, so this is not template overfitting by the PREREG's definition. **But the gain comes from the diff features, not from the existing scorers:** (exploratory, not pre-registered) a logistic regression on the five scorer outputs alone gets 0.595 (0.544-0.641) on set A test, below ROUGE-L alone. The advantage is the regex diff features (numbers removed / added / changed, negation words, side, category, pathology words), i.e. a number-and-category checker folded into a classifier. A pass on writer-made free text is not clinical validation.

Pre-registration: [../PREREG.md](../PREREG.md). Code: `usmeta/step45_partE.py`, `step45_partE_report.py` (new; saved Step 5-10 scorer outputs and the Part A set imported unchanged).

## What was trained

Features (14): BLEU, ROUGE-L, chrF, BERTScore (roberta-large), RaTEScore + diff features (numbers removed / added, negation-word change, side mismatch, category mismatch, pathology-word mismatch, relative size deviation, head-circumference deviation, count mismatch). Label 1 = planted error, 0 = harmless rewording of any type (small, matched, large, other: wording-only perturbations are the negatives). Trained on the DEV split of the templated benchmark (11,965 pairs), hyper-parameters tuned on VAL (15,307 pairs; mean per-case AUROC; logistic regression C = 10.0, gradient boosting depth / learning rate (5, 0.1)); group-disjoint by the locked splits. Set A dev/val was used only to REPORT transfer (logistic regression 0.881, gradient boosting 0.900; best single scorer 0.741), not for tuning.

## Test results (per-case AUROC, error vs harmless, ties 0.5; group bootstrap 1,000, seed 0)

| scorer | set A test (free text) | templated test |
|---|---|---|
| logistic regression | 0.895 (0.855-0.931) (185 cases) | 0.952 (0.949-0.955) (1399 cases) |
| gradient boosting | 0.863 (0.827-0.897) (185 cases) | 1.000 (1.000-1.000) (1399 cases) |
| bleu | 0.673 (0.624-0.723) (185 cases) | 0.498 (0.467-0.528) (1399 cases) |
| rougeL | 0.750 (0.703-0.799) (185 cases) | 0.395 (0.360-0.430) (1399 cases) |
| chrf | 0.717 (0.669-0.768) (185 cases) | 0.387 (0.350-0.424) (1399 cases) |
| bertscore[roberta-large] | 0.628 (0.573-0.685) (185 cases) | 0.317 (0.278-0.356) (1399 cases) |
| ratescore | 0.665 (0.610-0.718) (185 cases) | 0.506 (0.474-0.535) (1399 cases) |

On the templated test, gradient boosting reaches 1.000 and logistic regression 0.952, against at most 0.506 for any single word scorer (templated AUROCs below 0.5 mean the word scorers rank errors above harmless rewordings, as in Steps 5-10). Set A groups: 164.

## Exploratory ablation (not pre-registered)

Logistic regression with only the five scorer outputs (same training, same tuning): val AUROC (templated) 0.726, set A test 0.595 (0.544-0.641); with all 14 features 0.895 (0.855-0.931). Largest coefficients of the 14-feature model (standardised inputs): hc_abs +9.2, size_rel +6.9, neg_change +6.3, path_mismatch +3.9, side_mismatch +2.9, cat_mismatch +2.2.

## Deviations from the PREREG

- Set A is smaller than the PREREG (Part A results.md); the "best single existing text scorer" is chosen as the one with the highest AUROC on set A test (a conservative baseline: chosen on the test set it is compared against).
- The test split was read once for this part (`test_access.log`); the ablation reused the same reports.

## Caveats

- Writer-made free text copies the supplied numbers verbatim, so number-diff features are very informative here; on real radiologist or VLM text (two-dimensional sizes, number words, different rounding) they may be weaker.
- Planted-error twins: 1 per case, mixed fields; planted errors that change no number or category (lesion presence, position, orientation, histology) are caught only through the word scorers and the negation / pathology-word features.
- The learned scorers are trained on templated text only; free-text candidates are a distribution shift, which is why the set A numbers are lower than the templated ones.
