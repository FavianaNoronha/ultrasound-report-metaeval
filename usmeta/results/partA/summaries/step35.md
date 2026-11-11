# Step 35: limit of detection

Limitations: [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md). Code: `usmeta/step35_lod.py`, `step35_report.py` (new files; Step 21b candidates and saved scores reused; frozen templates and scorers imported unchanged). Test split: the Step 21b test references (`bench_test_v2d`), saved scores reused, new candidates scored now.

**Definition.** For each scorer and field: the **smallest error level at which the AUROC of planted size (or head-circumference) errors against the matched one-word synonyms of the same reference reaches 0.80**. Size errors: multiplicative factors of the stated size (Step 21b ×0.5, 0.7, 0.8, 0.9, 0.95, 1.3, 1.5, 2.0 plus new ×1.05, 1.10, 1.25), pooled over both directions into the levels 5, 10, 20, 25, 30, 50 and 100% relative error. Head circumference: new additive shifts of ±1, 2, 5, 10, 20 mm (both signs pooled; the Step 21b factor errors for HC are not used here). AUROC per case (ties 0.5), mean over cases; the 95% interval of the limit of detection is the percentile range of the same rule over 1,000 group bootstrap resamples (seed 0; resamples where no level reaches 0.80 count as "above the largest level"). Non-monotone curves are flagged. Judge rows use the capped subset (12 cases per dataset for the new candidates, Step 21b replies reused); cells with fewer than 30 groups at a level are marked †.

## Headline

- **breast, size in mm (BrEaST only):** limit of detection (AUROC >= 0.80 vs matched synonyms): finding_f1 (upper bound) 5%, judge_score 5% (judge cells under 30 groups), image check, oracle-box MedSAM (Step 16 rule) 25%, image check, label-free U-Net (Step 20 rule) 50%; not reached at any level tested by BLEU, ROUGE-L, chrF, BERTScore, RaTEScore, judge sentence_f1.
- **breast, size as % of image width:** limit of detection (AUROC >= 0.80 vs matched synonyms): finding_f1 (upper bound) 5%, judge_score 5%, image check, oracle-box MedSAM (Step 16 rule) 25%, image check, label-free U-Net (Step 20 rule) 50%, judge sentence_f1 100%; not reached at any level tested by BLEU, ROUGE-L, chrF, BERTScore, RaTEScore.
- **thyroid, size as % of image width:** limit of detection (AUROC >= 0.80 vs matched synonyms): finding_f1 (upper bound) 5%, judge_score 5%, judge sentence_f1 25%, image check, oracle-box MedSAM (Step 16 rule) 25%, image check, label-free U-Net (Step 20 rule) 50%; not reached at any level tested by BLEU, ROUGE-L, chrF, BERTScore, RaTEScore.
- **fetal head, head circumference (mm shift):** limit of detection (AUROC >= 0.80 vs matched synonyms): finding_f1 (upper bound) 1 mm, judge sentence_f1 1 mm (judge cells under 30 groups), judge_score 1 mm (judge cells under 30 groups); not reached at any level tested by BLEU, ROUGE-L, chrF, BERTScore, RaTEScore, image check, oracle-box MedSAM (Step 16 rule).

A limit of detection of 5% is the smallest size error tested (head circumference: 1 mm). A scorer that "reaches" 0.80 at a level can still be below 0.80 at a larger level (flagged non-monotone), and `finding_f1` reads our template, so its limit is the smallest tested level by construction (upper bound).

## Breast, size in mm (BrEaST only)

| scorer | limit of detection (95% CI) | 5% | 10% | 20% | 25% | 30% | 50% | 100% |
|---|---|---|---|---|---|---|---|---|
| BLEU | not reached (> 100%) | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 |
| ROUGE-L | not reached (> 100%) | 0.42 | 0.42 | 0.42 | 0.42 | 0.42 | 0.42 | 0.42 |
| chrF | not reached (> 100%) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| BERTScore | not reached (> 100%) | 0.02 | 0.03 | 0.04 | 0.05 | 0.05 | 0.07 | 0.08 |
| RaTEScore | not reached (> 100%) | 0.72 | 0.72 | 0.75 | 0.75 | 0.75 | 0.77 | 0.76 |
| finding_f1 (upper bound) | 5% (5% to 5%) | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| judge sentence_f1 | not reached (> 100%) | 0.50 † | 0.50 † | 0.50 † | 0.50 † | 0.50 † | 0.50 † | 0.50 † |
| judge_score | 5% (5% to 5%) | 1.00 † | 1.00 † | 1.00 † | 1.00 † | 1.00 † | 1.00 † | 1.00 † |
| image check, oracle-box MedSAM (Step 16 rule) | 25% (25% to 25%) | 0.56 † | 0.63 † | 0.55 | 0.92 | 0.80 | 0.86 | 0.92 |
| image check, label-free U-Net (Step 20 rule) | 50% (50% to >1.0) | 0.51 † | 0.55 † | 0.58 | 0.60 | 0.68 | 0.82 | 0.87 |

AUROC (point estimates) by error level; † = fewer than 30 groups at that level. Confidence intervals of every AUROC are in `results.json`.

## Breast, size as % of image width

| scorer | limit of detection (95% CI) | 5% | 10% | 20% | 25% | 30% | 50% | 100% |
|---|---|---|---|---|---|---|---|---|
| BLEU | not reached (> 100%) | 0.72 | 0.72 | 0.72 | 0.72 | 0.72 | 0.72 | 0.72 |
| ROUGE-L | not reached (> 100%) | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 |
| chrF | not reached (> 100%) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| BERTScore | not reached (> 100%) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| RaTEScore | not reached (> 100%) | 0.56 | 0.56 | 0.57 | 0.57 | 0.59 | 0.61 | 0.63 |
| finding_f1 (upper bound) | 5% (5% to 5%) | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| judge sentence_f1 | 100% (100% to >1.0) | 0.55 | 0.57 | 0.55 | 0.66 | 0.64 | 0.73 | 0.81 |
| judge_score | 5% (5% to 5%) | 0.97 | 0.99 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| image check, oracle-box MedSAM (Step 16 rule) | 25% (25% to 25%) | 0.55 | 0.63 | 0.51 | 0.95 | 0.82 | 0.93 | 0.97 |
| image check, label-free U-Net (Step 20 rule) | 50% (50% to 50%) | 0.51 | 0.52 | 0.56 | 0.62 | 0.72 | 0.90 | 0.90 |

AUROC (point estimates) by error level; † = fewer than 30 groups at that level. Confidence intervals of every AUROC are in `results.json`.

## Thyroid, size as % of image width

| scorer | limit of detection (95% CI) | 5% | 10% | 20% | 25% | 30% | 50% | 100% |
|---|---|---|---|---|---|---|---|---|
| BLEU | not reached (> 100%) | 0.65 | 0.66 | 0.66 | 0.66 | 0.66 | 0.66 | 0.66 |
| ROUGE-L | not reached (> 100%) | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 |
| chrF | not reached (> 100%) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| BERTScore | not reached (> 100%) | 0.06 | 0.10 | 0.12 | 0.13 | 0.15 | 0.18 | 0.21 |
| RaTEScore | not reached (> 100%) | 0.27 | 0.27 | 0.27 | 0.27 | 0.28 | 0.28 | 0.27 |
| finding_f1 (upper bound) | 5% (5% to 5%) | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| judge sentence_f1 | 25% (25% to 50%) | 0.51 | 0.59 | 0.62 | 0.83 | 0.80 | 0.90 | 0.92 |
| judge_score | 5% (5% to 5%) | 0.93 | 0.99 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| image check, oracle-box MedSAM (Step 16 rule) | 25% (25% to >1.0) (non-monotone) | 0.47 | 0.47 | 0.12 | 0.85 | 0.56 | 0.65 | 0.85 |
| image check, label-free U-Net (Step 20 rule) | 50% (50% to >1.0) | 0.50 | 0.51 | 0.64 | 0.68 | 0.69 | 0.85 | 0.88 |

AUROC (point estimates) by error level; † = fewer than 30 groups at that level. Confidence intervals of every AUROC are in `results.json`.

## Fetal head, head circumference (mm shift)

| scorer | limit of detection (95% CI) | 1 mm | 2 mm | 5 mm | 10 mm | 20 mm |
|---|---|---|---|---|---|---|
| BLEU | not reached (> 20 mm) | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 |
| ROUGE-L | not reached (> 20 mm) | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 |
| chrF | not reached (> 20 mm) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| BERTScore | not reached (> 20 mm) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| RaTEScore | not reached (> 20 mm) | 0.19 | 0.20 | 0.22 | 0.22 | 0.23 |
| finding_f1 (upper bound) | 1 mm (1 mm to 1 mm) | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| judge sentence_f1 | 1 mm (1 mm to 1 mm) | 1.00 † | 1.00 † | 1.00 † | 1.00 | 1.00 † |
| judge_score | 1 mm (1 mm to 1 mm) | 1.00 † | 1.00 † | 1.00 † | 1.00 | 1.00 † |
| image check, oracle-box MedSAM (Step 16 rule) | not reached (> 20 mm) | 0.47 † | 0.46 † | 0.42 † | 0.39 † | 0.35 † |

AUROC (point estimates) by error level; † = fewer than 30 groups at that level. Confidence intervals of every AUROC are in `results.json`.

## Caveats

- **Templated text, matched synonyms as the harmless side:** the AUROC vs a one-word synonym measures whether a scorer separates a one-number change from a one-word change; word scorers' values follow edit size (Step 33 edit-size law), so a limit of detection is not "the smallest error a scorer understands".
- **Rounding:** size values are integers (mm or %), so small factors on small sizes round to the same value and the candidate is dropped; levels therefore have fewer cases for small sizes (case counts per level are in `results.json`).
- **Levels pool both directions** (×0.95 and ×1.05 are both "5%"); the image-check curve is asymmetric (Step 21b: sizes too small are scored as better), so its pooled value can hide one side.
- **Head circumference:** only the additive-shift candidates are used; the image checks for fetal head are Step 16 masks only (oracle box, exact rule); the Step 29 U-Net rows are breast and thyroid only.
- Judge rows: capped subset, one prompt, greedy; `llm_finding_f1` was not run here (extraction of every candidate was out of scope).
