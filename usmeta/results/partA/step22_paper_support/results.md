# Step 22: paper-support tables (saved results only, no model calls)

All numbers come from saved result files (paths given). Test split, group bootstrap (1,000 resamples, seed 0), † = fewer than 30 groups: too small to compare. `finding_f1` is an upper bound on templated text.

## Table 1. Paired preference accuracy by error type, per organ (Step 19a method, test)

### breast

Paired preference = share of (planted error, harmless rewording) pairs of the same reference in which the error scores LOWER; ties (shown as strict preference) count as not preferred; AUROC = strict + ½ ties. n = test cases with that error type (groups in the CSV). † = fewer than 30 groups: too small to compare. Judge column: judged subset only.

| error type | n cases | BLEU | ROUGE-L | chrF | BERTScore | RaTEScore | Gemma judge (judge_score) | finding_f1 (upper bound) |
|---|---|---|---|---|---|---|---|---|
| lesion present / absent | 646 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.98 | 1.00 |
| number of lesions | 491 | 0.57 | 0.41 | 0.29 | 0.41 | 0.51 | 0.91 | 1.00 |
| position | 282 | 0.24 | 0.00 | 0.26 | 0.02 | 0.01 | 0.91 | 1.00 |
| orientation | 502 | 0.57 | 0.41 | 0.49 | 0.32 | 0.50 | 0.86 | 1.00 |
| size (% of image width) | 401 | 0.26 | 0.00 | 0.10 | 0.00 | 0.49 | 0.90 | 1.00 |
| size (mm) | 101 | 0.09 | 0.00 | 0.00 | 0.04 | 0.51 | 0.75 † | 1.00 |
| BI-RADS category | 196 | 0.12 | 0.00 | 0.00 | 0.15 | 0.02 | 0.81 | 1.00 |
| pathology (benign / malignant) | 502 | 0.14 | 0.00 | 0.39 | 0.24 | 0.54 | 0.86 | 1.00 |
| histology | 216 | 0.19 | 0.14 | 0.35 | 0.40 | 0.73 | 0.78 † | 1.00 |
| side | 130 | 0.14 | 0.00 | 0.21 | 0.00 | 0.43 | 0.90 † | 1.00 |
| shape | 101 | 0.00 | 0.04 | 0.38 | 0.19 | 0.68 | — | 1.00 |
| margin | 101 | 0.73 | 0.26 | 0.55 | 0.64 | 0.65 | 0.89 † | 1.00 |
| echo pattern | 53 | 0.09 | 0.00 | 0.00 | 0.47 | 0.47 | 0.87 † | 1.00 |
| posterior features | 39 | 0.09 | 0.00 | 0.64 | 0.42 | 0.61 | 0.78 † | 1.00 |
| echogenic halo | 101 | 0.09 | 0.00 | 0.01 | 0.25 | 0.15 | 0.78 † | 1.00 |
| calcifications | 101 | 0.73 | 0.56 | 0.40 | 0.63 | 0.59 | 0.77 † | 1.00 |

### thyroid

Paired preference = share of (planted error, harmless rewording) pairs of the same reference in which the error scores LOWER; ties (shown as strict preference) count as not preferred; AUROC = strict + ½ ties. n = test cases with that error type (groups in the CSV). † = fewer than 30 groups: too small to compare. Judge column: judged subset only.

| error type | n cases | BLEU | ROUGE-L | chrF | BERTScore | RaTEScore | Gemma judge (judge_score) | finding_f1 (upper bound) |
|---|---|---|---|---|---|---|---|---|
| lesion present / absent | 450 | 1.00 | 1.00 | 1.00 | 1.00 | 0.99 | 1.00 | 1.00 |
| number of lesions | 385 | 0.58 | 0.44 | 0.56 | 0.44 | 0.59 | 1.00 | 1.00 |
| position | 212 | 0.28 | 0.00 | 0.14 | 0.07 | 0.09 | 1.00 | 1.00 |
| orientation | 448 | 0.58 | 0.45 | 0.55 | 0.42 | 0.83 | 0.94 | 1.00 |
| size (% of image width) | 448 | 0.28 | 0.00 | 0.14 | 0.08 | 0.04 | 0.97 | 1.00 |
| TI-RADS category | 112 | 0.00 | 0.00 | 0.00 | 0.11 | 0.02 | 0.88 † | 1.00 |
| margin | 110 | 0.58 | 0.44 | 0.51 | 0.47 | 0.66 | 0.83 † | 1.00 |
| echo pattern | 67 | 0.27 | 0.03 | 0.13 | 0.39 | 0.59 | 1.00 † | 1.00 |
| composition | 67 | 0.25 | 0.00 | 0.31 | 0.44 | 0.74 | 0.89 † | 1.00 |
| echogenic foci | 112 | 0.62 | 0.00 | 0.58 | 0.55 | 0.68 | 1.00 † | 1.00 |

### fetal head

Paired preference = share of (planted error, harmless rewording) pairs of the same reference in which the error scores LOWER; ties (shown as strict preference) count as not preferred; AUROC = strict + ½ ties. n = test cases with that error type (groups in the CSV). † = fewer than 30 groups: too small to compare. Judge column: judged subset only.

| error type | n cases | BLEU | ROUGE-L | chrF | BERTScore | RaTEScore | Gemma judge (judge_score) | finding_f1 (upper bound) |
|---|---|---|---|---|---|---|---|---|
| head circumference (mm) | 300 | 0.29 | 0.00 | 0.16 | 0.00 | 0.27 | 0.92 | 1.00 |
| fetal plane | 153 | 0.29 | 0.01 | 0.79 | 0.71 | 0.48 | 0.94 | 1.00 |

## Table 2. Failure taxonomy

| failure type | scorer(s) | metric and number | dataset scope | result file |
|---|---|---|---|---|
| Lexical sensitivity (scores follow how much text changed, not what changed) | BLEU, ROUGE-L, chrF, BERTScore, RaTEScore | Step 10d, BrEaST, AUROC vs matched one-word synonym: BLEU 0.61, chrF 0.25, BERTScore 0.53; Step 19a strict preference breast: BLEU 0.51, ROUGE-L 0.38, chrF 0.47, BERTScore 0.42 | BrEaST, BUS-BRA (Step 10d); breast, thyroid, fetal head (19a) | `results/partA/step10d_test_results/results.md; results/partA/step19a_pairs/cells.json` |
| Factual insensitivity (the scorer does not register which fact changed or by how much) | BLEU, ROUGE-L, chrF, BERTScore, RaTEScore; Step 18 all text scorers | Step 21b: BLEU/ROUGE-L dose-response flat (rho -0.01 breast); chrF AUROC 0.00 and BERTScore 0.02 on breast size errors at x2 (error scored as more similar than a synonym); Step 18: equal-size errors that cross vs do not cross a TI-RADS cut-off differ by 0 (BLEU, ROUGE-L, finding_f1) to 0.001 (chrF, BERTScore) [synthetic sizes] | size errors; breast, thyroid, fetal head (21b); DDTI synthetic size (18) | `results/partA/step21b_dose/dose_results.json; results/partA/step18_threshold_crossing/results.md` |
| Prompt instability (the judge changes with prompt wording or order) | Gemma-2-9B sentence_check (judge_score) | Step 21c: judge_score changes by more than 0.1 in 21% (swap), 18% (paraphrase A), 26% (paraphrase B) of pairs; AUROC breast 0.85 -> 0.96; repeat with the same prompt: 0 of 93 pairs changed. Step 7 (rerun 2): AUROC vs harmless small changed by up to 0.30 between two prompts (BUS-BRA 0.91 -> 0.61) | Step 21c: 89 test cases (10 per dataset; per-dataset cells too small); Step 7: 20 cases per dataset (dev) | `results/partA/step21c_judge_sens/sens_results.json; results/partA/step7_layer2_sentence_check_gemma_rerun2/results.md` |
| Benchmark circularity (a scorer scores perfectly because it reads the same template or mask that built the reference) | finding_f1; true-mask image check | finding_f1: AUROC 1.00 and false-alarm rate 0.00 on all 10 datasets (Step 19a) and 1.00 down to a x0.95 size error (Step 21b); true-mask check mask_verified_facts 1.00 by construction (Step 8) | all 10 datasets (templated reports) | `results/partA/step19a_pairs/cells.json; results/partA/step21b_dose/dose_results.json; results/partA/step8_layer3_location_true_masks/results.md` |
| Evidence dependence (the image check works only when handed the lesion location) | predicted-mask image check (MedSAM) | Position AUROC 0.95 with the true-mask box, 0.47 whole-image box, 0.47 random box (Step 21a); size AUROC 0.86 exact box -> 0.53 (box shrunk 25%) -> 0.40 (50%) (Step 19b) | breast + thyroid, 228 test scans | `results/partA/step21a_localisation/results.md; results/partA/step19b_boxsweep/results.md` |
| Generalisation failure (does not carry to another dataset, organ or real text) | predicted-mask image check; cut-offs; word-overlap scorers on real text; VLM-report fact check | Image check on fetal head AUROC 0.46 (HC18) and 0.50 (FetalHead) (Step 16); a val cut-off borrowed from another dataset of the same organ changes the false-alarm rate by -0.72 to +0.62 for single pairs (Step 19a); HiSBreast real text: BLEU, ROUGE-L, chrF AUROC 0.04-0.24 against an LLM paraphrase (n=21) and BERTScore 0.43 overall (n=41) (Step 15); finding_f1 on Qwen reports 0.18-0.30 on BrEaST, BUS-BRA, TN3K, TN5000 (Steps 11, 14) | fetal head (16); within-organ pairs (19a); HiSBreast, 41 test exams (15); free-text VLM reports, 14-22 per dataset (11, 14) | `results/partA/step16_partB/results.md; results/partA/step19a_pairs/transfer.csv; results/partA/step15_hisbreast/results.md; results/partA/step11_qwen_real_reports_rerun2/results.md` |

## Table 3. Monotonicity: Spearman rho between error size (|log factor|) and score drop (1 − score), Step 21b

Positive = bigger errors score lower. Pooled over all error candidates (factors ×0.5 to ×2.0) of an organ, so it mixes errors that make the stated size larger and smaller. n = number of scored error candidates. Judge cells use the capped Step 21b sample; the image check covers the Step 16 scans only.

| scorer | breast ρ (n) | thyroid ρ (n) | fetal head ρ (n) |
|---|---|---|---|
| BLEU | -0.01 (3966) | +0.01 (3548) | +0.00 (2400) |
| ROUGE-L | -0.01 (3966) | +0.01 (3548) | +0.00 (2400) |
| chrF | +0.16 (3966) | +0.24 (3548) | +0.25 (2400) |
| BERTScore | +0.34 (3966) | +0.31 (3548) | +0.26 (2400) |
| RaTEScore | +0.29 (3966) | +0.02 (3548) | +0.27 (2400) |
| finding_f1 (upper bound) | +0.86 (3966) | +0.86 (3548) | +0.43 (2400) |
| Gemma judge (sentence_f1) | +0.30 (718) | +0.54 (609) | -0.05 (216) |
| Gemma judge (judge_score) | +0.67 (718) | +0.75 (609) | +0.26 (216) |
| image check (predicted masks, exact box) | +0.55 (808) | +0.18 (288) | +0.45 (144) |
