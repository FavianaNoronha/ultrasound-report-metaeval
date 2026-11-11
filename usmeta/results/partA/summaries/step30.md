# Step 30: severity breakdown (saved scores only)

Limitations: [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md). Code: `usmeta/step30_severity.py`, `step30_report.py` (new files, no model call). Test split from saved scores (`bench_test_v2d.jsonl`, `scores_test_layer0/1.json`, judge replies of Steps 10d + 12) and, for the image check, `bench_v2d.jsonl` rows of the 228 scans of Steps 21a / 24 re-scored per candidate from SAVED masks (Step 16 oracle-box MedSAM and the Step 29 U-Net); no judge, writer or segmentation model was run.

**Severity is our own provisional label (1 minor, 2 major, 3 critical), assigned by rule from the error type, not confirmed by any clinician.** It is also **confounded with error type**: level 3 is mostly lesion present/absent, pathology, side and BI-RADS/TI-RADS jumps; level 1 is orientation, position, small size and small category shifts (field counts per level are in `results.json`). It is also confounded with how much text the edit changes (the "no focal lesion" rewrite is level 3 and 40%+ of the text; Step 21e).

**Method.** Per case, AUROC of the planted errors of one severity level against the harmless rewordings of one type (small / matched / large) of the same reference (ties 0.5); 95% CI by group bootstrap (1,000 resamples, seed 0); † = under 30 groups: too small to compare. Spearman = correlation between severity (1-3) and score drop (1 - score; identical copies score 1.0) over all error rows, CI by group bootstrap. Judge rows use the judged subset (59 cases per dataset); image-check rows use only errors in mask-checkable fields (lesion, count, position, orientation, size) on the 228 scans (breast and thyroid; fetal head is not in that scan set), and harmless rewordings state the same facts so they all score 1.0 (the three harmless columns of the image check are therefore the same).

## Headline

- **Severity does not order the word scorers the way a clinician would.** Their drop correlates only weakly with severity: Spearman 0.23-0.41 pooled (BLEU 0.23, ROUGE-L 0.25, chrF 0.29, BERTScore 0.41, RaTEScore 0.38), and that correlation comes mostly from edit size (level 3 contains the whole-report rewrite), not from clinical weight. Against a matched one-word synonym BLEU is 0.77 / 0.74 / 0.75 on breast for levels 1 / 2 / 3: flat. Against the small and large harmless groups the pooled AUROC of the word scorers is 0.00-0.50 at levels 1 and 2 (they prefer the error; RaTEScore reaches 0.47-0.50 vs small), and rises at level 3 (vs small 0.55-0.75 pooled, see the tables) only because of the whole-report rewrite.
- **Critical errors look safer to the word scorers against small harmless rewordings, but that is the rewrite, not severity.** Against small harmless: breast BLEU 0.33 / 0.34 / 0.63 and thyroid chrF 0.44 / 0.48 / 0.90 for levels 1 / 2 / 3 (thyroid level 3 is 0.90 for every word scorer): level 3 contains the 'No focal lesion / nodule is seen.' text, which differs from the reference in almost every word. Even against the matched synonym the thyroid level-3 value is high (chrF 0.28 / 0.35 / 0.90), because the error text is itself the much larger edit; in breast, where level 3 mixes rewrites with side / pathology / BI-RADS errors, BLEU vs matched stays flat (see the first bullet).
- **The Gemma judge's AUROC rises with severity and is weakest on levels 1-2.** Pooled `judge_score` AUROC vs small 0.91 / 0.89 / 0.94 (levels 1 / 2 / 3), Spearman 0.37; breast sentence_f1 vs small is 0.56 / 0.48 / 0.93.
- **`finding_f1` is 1.00 at every level (upper bound on templated text).** Its Spearman with severity is 0.30 (breast), 0.24 (thyroid), 0.84 (fetal head): the fact check scores a larger number change lower in fetal head (graded credit), and otherwise treats every wrong fact alike.
- **The image check is best at the critical level and lowest at levels 1-2 (level 2 for oracle-box MedSAM, level 1 for the U-Net).** Pooled AUROC 0.95 / 0.90 / 1.00 (oracle-box MedSAM) and 0.84 / 0.91 / 0.99 (label-free U-Net) for levels 1 / 2 / 3, because level 3 is mostly lesion-presence errors (a lesion that is there or not is easy to see), while levels 1-2 are position, orientation and size changes. Thyroid with the U-Net at level 1 is 0.77. This is an error-type effect as much as a severity effect.

## Cases per severity level (planted-error rows; groups = patients / exams or image ids)

| organ | level 1 | level 2 | level 3 |
|---|---|---|---|
| breast | 1738 rows, 385 groups | 2109 rows, 385 groups | 1495 rows, 413 groups |
| thyroid | 1166 rows, 415 groups | 1873 rows, 415 groups | 561 rows, 417 groups |
| fetal head | 300 rows, 203 groups | 753 rows, 204 groups | 300 rows, 203 groups |

Image check (228 scans, checkable fields only): breast level 1: 365 rows / 138 cases; breast level 2: 411 rows / 138 cases; breast level 3: 138 rows / 138 cases; thyroid level 1: 212 rows / 90 cases; thyroid level 2: 284 rows / 90 cases; thyroid level 3: 90 rows / 90 cases.

## Spearman between severity and score drop (all planted-error rows)

| scorer | breast | thyroid | fetal head | pooled |
|---|---|---|---|---|
| BLEU | 0.16 (0.13–0.19) | 0.25 (0.23–0.28) | 0.00 (0.00–0.00) | 0.23 (0.21–0.25) |
| ROUGE-L | 0.19 (0.16–0.23) | 0.30 (0.27–0.32) | 0.00 (0.00–0.00) | 0.25 (0.23–0.27) |
| chrF | 0.32 (0.29–0.35) | 0.26 (0.24–0.28) | 0.13 (0.10–0.17) | 0.29 (0.27–0.31) |
| BERTScore | 0.43 (0.40–0.46) | 0.45 (0.43–0.47) | 0.25 (0.22–0.28) | 0.41 (0.39–0.43) |
| RaTEScore | 0.44 (0.40–0.48) | 0.33 (0.31–0.35) | 0.15 (0.09–0.21) | 0.38 (0.35–0.40) |
| finding_f1 (upper bound) | 0.30 (0.27–0.32) | 0.24 (0.22–0.27) | 0.84 (0.83–0.86) | 0.34 (0.31–0.37) |
| judge sentence_f1 | 0.63 (0.52–0.72) | 0.32 (0.25–0.39) | 0.05 (-0.06–0.16) | 0.45 (0.36–0.53) |
| judge_score | 0.31 (0.22–0.41) | 0.56 (0.51–0.62) | 0.35 (0.24–0.45) | 0.37 (0.32–0.42) |
| image check, oracle-box MedSAM (Step 16 masks) | 0.37 (0.35–0.40) | 0.39 (0.36–0.43) | — | 0.38 (0.36–0.41) |
| image check, label-free U-Net (Step 29) | 0.41 (0.37–0.45) | 0.45 (0.41–0.49) | — | 0.43 (0.40–0.46) |

Positive = a more severe error gets a bigger drop (good). † = under 30 groups. Fetal head has no image-check rows (HC18 / FetalHead are not in the 228 scans).

## AUROC vs harmless small: breast

| scorer | level 1 (minor) | level 2 (major) | level 3 (critical) |
|---|---|---|---|
| BLEU | 0.33 (0.30–0.35) | 0.34 (0.32–0.36) | 0.63 (0.57–0.69) |
| ROUGE-L | 0.04 (0.03–0.04) | 0.01 (0.00–0.01) | 0.54 (0.48–0.60) |
| chrF | 0.34 (0.32–0.36) | 0.39 (0.37–0.40) | 0.73 (0.68–0.76) |
| BERTScore | 0.02 (0.02–0.03) | 0.03 (0.03–0.04) | 0.56 (0.49–0.61) |
| RaTEScore | 0.40 (0.39–0.41) | 0.50 (0.49–0.51) | 0.75 (0.72–0.78) |
| finding_f1 (upper bound) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) |
| judge sentence_f1 | 0.56 (0.50–0.63) | 0.48 (0.42–0.54) | 0.93 (0.88–0.96) |
| judge_score | 0.81 (0.74–0.86) | 0.80 (0.74–0.85) | 0.91 (0.85–0.95) |
| image check, oracle-box MedSAM (Step 16 masks) | 0.97 (0.95–0.99) | 0.94 (0.91–0.96) | 1.00 (1.00–1.00) |
| image check, label-free U-Net (Step 29) | 0.89 (0.85–0.92) | 0.94 (0.91–0.96) | 0.99 (0.96–1.00) |

## AUROC vs harmless matched: breast

| scorer | level 1 (minor) | level 2 (major) | level 3 (critical) |
|---|---|---|---|
| BLEU | 0.77 (0.77–0.78) | 0.74 (0.73–0.75) | 0.75 (0.72–0.77) |
| ROUGE-L | 0.65 (0.64–0.66) | 0.65 (0.64–0.65) | 0.76 (0.73–0.79) |
| chrF | 0.37 (0.35–0.38) | 0.20 (0.19–0.21) | 0.76 (0.72–0.80) |
| BERTScore | 0.30 (0.29–0.32) | 0.44 (0.42–0.45) | 0.76 (0.72–0.80) |
| RaTEScore | 0.50 (0.49–0.51) | 0.66 (0.65–0.68) | 0.82 (0.79–0.84) |
| finding_f1 (upper bound) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) |
| judge sentence_f1 | 0.93 (0.90–0.95) | 0.85 (0.81–0.88) | 1.00 (1.00–1.00) |
| judge_score | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) |
| image check, oracle-box MedSAM (Step 16 masks) | 0.97 (0.95–0.99) | 0.94 (0.91–0.96) | 1.00 (1.00–1.00) |
| image check, label-free U-Net (Step 29) | 0.89 (0.85–0.92) | 0.94 (0.91–0.96) | 0.99 (0.96–1.00) |

## AUROC vs harmless large: breast

| scorer | level 1 (minor) | level 2 (major) | level 3 (critical) |
|---|---|---|---|
| BLEU | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | 0.54 (0.48–0.60) |
| ROUGE-L | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | 0.54 (0.48–0.60) |
| chrF | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | 0.54 (0.48–0.60) |
| BERTScore | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | 0.54 (0.48–0.60) |
| RaTEScore | 0.20 (0.18–0.22) | 0.32 (0.30–0.34) | 0.65 (0.59–0.70) |
| finding_f1 (upper bound) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) |
| judge sentence_f1 | 0.83 (0.77–0.88) | 0.71 (0.66–0.77) | 0.99 (0.99–1.00) |
| judge_score | 0.85 (0.80–0.90) | 0.86 (0.81–0.90) | 0.96 (0.93–0.98) |
| image check, oracle-box MedSAM (Step 16 masks) | 0.97 (0.95–0.99) | 0.94 (0.91–0.96) | 1.00 (1.00–1.00) |
| image check, label-free U-Net (Step 29) | 0.89 (0.85–0.92) | 0.94 (0.91–0.96) | 0.99 (0.96–1.00) |

## AUROC vs harmless small: thyroid

| scorer | level 1 (minor) | level 2 (major) | level 3 (critical) |
|---|---|---|---|
| BLEU | 0.44 (0.43–0.45) | 0.49 (0.48–0.49) | 0.90 (0.87–0.92) |
| ROUGE-L | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | 0.90 (0.88–0.93) |
| chrF | 0.44 (0.43–0.45) | 0.48 (0.48–0.49) | 0.90 (0.87–0.92) |
| BERTScore | 0.00 (0.00–0.00) | 0.01 (0.01–0.01) | 0.90 (0.88–0.93) |
| RaTEScore | 0.48 (0.47–0.50) | 0.45 (0.44–0.46) | 0.92 (0.89–0.94) |
| finding_f1 (upper bound) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) |
| judge sentence_f1 | 0.96 (0.93–0.98) | 0.91 (0.88–0.94) | 0.99 (0.97–1.00) |
| judge_score | 0.99 (0.98–1.00) | 0.97 (0.94–0.99) | 1.00 (1.00–1.00) |
| image check, oracle-box MedSAM (Step 16 masks) | 0.91 (0.87–0.94) | 0.85 (0.82–0.89) | 1.00 (1.00–1.00) |
| image check, label-free U-Net (Step 29) | 0.77 (0.71–0.83) | 0.87 (0.83–0.90) | 1.00 (1.00–1.00) |

## AUROC vs harmless matched: thyroid

| scorer | level 1 (minor) | level 2 (major) | level 3 (critical) |
|---|---|---|---|
| BLEU | 0.68 (0.65–0.70) | 0.77 (0.76–0.77) | 0.91 (0.88–0.93) |
| ROUGE-L | 0.64 (0.63–0.65) | 0.67 (0.66–0.67) | 0.95 (0.94–0.96) |
| chrF | 0.28 (0.26–0.30) | 0.35 (0.34–0.36) | 0.90 (0.88–0.93) |
| BERTScore | 0.42 (0.40–0.44) | 0.51 (0.49–0.52) | 0.93 (0.91–0.95) |
| RaTEScore | 0.47 (0.45–0.49) | 0.47 (0.45–0.48) | 0.93 (0.91–0.95) |
| finding_f1 (upper bound) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) |
| judge sentence_f1 | 0.98 (0.96–0.99) | 0.96 (0.94–0.98) | 1.00 (1.00–1.00) |
| judge_score | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) |
| image check, oracle-box MedSAM (Step 16 masks) | 0.91 (0.87–0.94) | 0.85 (0.82–0.89) | 1.00 (1.00–1.00) |
| image check, label-free U-Net (Step 29) | 0.77 (0.71–0.83) | 0.87 (0.83–0.90) | 1.00 (1.00–1.00) |

## AUROC vs harmless large: thyroid

| scorer | level 1 (minor) | level 2 (major) | level 3 (critical) |
|---|---|---|---|
| BLEU | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | 0.90 (0.87–0.92) |
| ROUGE-L | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | 0.90 (0.88–0.93) |
| chrF | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | 0.90 (0.88–0.93) |
| BERTScore | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | 0.90 (0.88–0.93) |
| RaTEScore | 0.24 (0.22–0.26) | 0.15 (0.13–0.17) | 0.90 (0.87–0.92) |
| finding_f1 (upper bound) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) |
| judge sentence_f1 | 0.87 (0.84–0.91) | 0.81 (0.78–0.85) | 0.96 (0.91–0.99) |
| judge_score | 0.96 (0.93–0.98) | 0.94 (0.91–0.97) | 0.98 (0.95–1.00) |
| image check, oracle-box MedSAM (Step 16 masks) | 0.91 (0.87–0.94) | 0.85 (0.82–0.89) | 1.00 (1.00–1.00) |
| image check, label-free U-Net (Step 29) | 0.77 (0.71–0.83) | 0.87 (0.83–0.90) | 1.00 (1.00–1.00) |

## AUROC vs harmless small: fetal head

| scorer | level 1 (minor) | level 2 (major) | level 3 (critical) |
|---|---|---|---|
| BLEU | 0.33 (0.33–0.33) | 0.36 (0.36–0.37) | 0.33 (0.33–0.33) |
| ROUGE-L | 0.17 (0.17–0.17) | 0.17 (0.17–0.17) | 0.17 (0.17–0.17) |
| chrF | 0.39 (0.37–0.40) | 0.46 (0.44–0.48) | 0.43 (0.40–0.45) |
| BERTScore | 0.00 (0.00–0.00) | 0.11 (0.09–0.13) | 0.00 (0.00–0.00) |
| RaTEScore | 0.40 (0.39–0.42) | 0.46 (0.44–0.47) | 0.49 (0.47–0.51) |
| finding_f1 (upper bound) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) |
| judge sentence_f1 | 0.93 (0.87–0.98) † | 0.94 (0.91–0.96) | 0.92 (0.88–0.96) |
| judge_score | 0.93 (0.87–0.98) † | 0.92 (0.88–0.95) | 1.00 (1.00–1.00) |

## AUROC vs harmless matched: fetal head

| scorer | level 1 (minor) | level 2 (major) | level 3 (critical) |
|---|---|---|---|
| BLEU | 0.50 (0.50–0.50) | 0.55 (0.54–0.55) | 0.50 (0.50–0.50) |
| ROUGE-L | 0.50 (0.50–0.50) | 0.50 (0.50–0.50) | 0.50 (0.50–0.50) |
| chrF | 0.00 (0.00–0.00) | 0.17 (0.14–0.20) | 0.00 (0.00–0.00) |
| BERTScore | 0.00 (0.00–0.00) | 0.17 (0.14–0.20) | 0.00 (0.00–0.00) |
| RaTEScore | 0.18 (0.15–0.22) | 0.26 (0.22–0.30) | 0.26 (0.22–0.29) |
| finding_f1 (upper bound) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) |
| judge sentence_f1 | 1.00 (1.00–1.00) † | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) |
| judge_score | 1.00 (1.00–1.00) † | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) |

## AUROC vs harmless large: fetal head

| scorer | level 1 (minor) | level 2 (major) | level 3 (critical) |
|---|---|---|---|
| BLEU | 0.00 (0.00–0.00) | 0.00 (0.00–0.01) | 0.00 (0.00–0.00) |
| ROUGE-L | 0.00 (0.00–0.00) | 0.00 (0.00–0.01) | 0.00 (0.00–0.00) |
| chrF | 0.00 (0.00–0.00) | 0.05 (0.04–0.06) | 0.00 (0.00–0.00) |
| BERTScore | 0.00 (0.00–0.00) | 0.09 (0.07–0.10) | 0.00 (0.00–0.00) |
| RaTEScore | 0.05 (0.04–0.07) | 0.08 (0.06–0.10) | 0.07 (0.05–0.09) |
| finding_f1 (upper bound) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) |
| judge sentence_f1 | 0.85 (0.71–0.97) † | 0.89 (0.82–0.95) | 0.78 (0.63–0.90) |
| judge_score | 0.85 (0.71–0.97) † | 0.89 (0.82–0.95) | 0.78 (0.63–0.90) |

## AUROC vs harmless small: pooled

| scorer | level 1 (minor) | level 2 (major) | level 3 (critical) |
|---|---|---|---|
| BLEU | 0.37 (0.36–0.38) | 0.40 (0.39–0.41) | 0.66 (0.62–0.68) |
| ROUGE-L | 0.06 (0.05–0.06) | 0.04 (0.04–0.05) | 0.58 (0.54–0.61) |
| chrF | 0.39 (0.38–0.40) | 0.44 (0.43–0.45) | 0.72 (0.69–0.74) |
| BERTScore | 0.01 (0.01–0.01) | 0.04 (0.03–0.05) | 0.55 (0.51–0.58) |
| RaTEScore | 0.43 (0.42–0.44) | 0.47 (0.46–0.48) | 0.75 (0.73–0.77) |
| finding_f1 (upper bound) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) |
| judge sentence_f1 | 0.78 (0.74–0.82) | 0.75 (0.72–0.79) | 0.94 (0.92–0.96) |
| judge_score | 0.91 (0.88–0.93) | 0.89 (0.87–0.92) | 0.94 (0.91–0.96) |
| image check, oracle-box MedSAM (Step 16 masks) | 0.95 (0.93–0.96) | 0.90 (0.88–0.93) | 1.00 (1.00–1.00) |
| image check, label-free U-Net (Step 29) | 0.84 (0.81–0.87) | 0.91 (0.89–0.93) | 0.99 (0.98–1.00) |

## AUROC vs harmless matched: pooled

| scorer | level 1 (minor) | level 2 (major) | level 3 (critical) |
|---|---|---|---|
| BLEU | 0.67 (0.66–0.69) | 0.70 (0.69–0.71) | 0.75 (0.73–0.76) |
| ROUGE-L | 0.61 (0.60–0.62) | 0.62 (0.61–0.63) | 0.77 (0.75–0.79) |
| chrF | 0.25 (0.23–0.26) | 0.25 (0.24–0.26) | 0.64 (0.60–0.68) |
| BERTScore | 0.27 (0.26–0.29) | 0.40 (0.39–0.41) | 0.65 (0.61–0.69) |
| RaTEScore | 0.41 (0.40–0.43) | 0.50 (0.48–0.51) | 0.73 (0.70–0.76) |
| finding_f1 (upper bound) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) |
| judge sentence_f1 | 0.96 (0.95–0.97) | 0.93 (0.91–0.94) | 1.00 (1.00–1.00) |
| judge_score | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) |
| image check, oracle-box MedSAM (Step 16 masks) | 0.95 (0.93–0.96) | 0.90 (0.88–0.93) | 1.00 (1.00–1.00) |
| image check, label-free U-Net (Step 29) | 0.84 (0.81–0.87) | 0.91 (0.89–0.93) | 0.99 (0.98–1.00) |

## AUROC vs harmless large: pooled

| scorer | level 1 (minor) | level 2 (major) | level 3 (critical) |
|---|---|---|---|
| BLEU | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | 0.54 (0.50–0.58) |
| ROUGE-L | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | 0.54 (0.50–0.58) |
| chrF | 0.00 (0.00–0.00) | 0.01 (0.01–0.02) | 0.54 (0.50–0.58) |
| BERTScore | 0.00 (0.00–0.00) | 0.02 (0.02–0.03) | 0.54 (0.50–0.58) |
| RaTEScore | 0.18 (0.17–0.19) | 0.20 (0.19–0.21) | 0.60 (0.56–0.64) |
| finding_f1 (upper bound) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) |
| judge sentence_f1 | 0.85 (0.82–0.88) | 0.79 (0.76–0.82) | 0.97 (0.95–0.98) |
| judge_score | 0.90 (0.87–0.93) | 0.90 (0.87–0.92) | 0.95 (0.92–0.97) |
| image check, oracle-box MedSAM (Step 16 masks) | 0.95 (0.93–0.96) | 0.90 (0.88–0.93) | 1.00 (1.00–1.00) |
| image check, label-free U-Net (Step 29) | 0.84 (0.81–0.87) | 0.91 (0.89–0.93) | 0.99 (0.98–1.00) |

## Caveats

- **Severity is provisional and author-assigned** (never clinician-confirmed), and it is confounded with error type and with edit size, so no cell isolates "how bad" from "what kind" or "how many words changed". A clinician-confirmed ladder could reorder it.
- **Judge rows** use the judged subset only (59 cases per dataset); some cells have fewer than 30 groups (marked †). One judge model, one prompt.
- **Image-check rows** exclude non-checkable fields (BI-RADS, pathology, side, echo, margin, ...) by construction, so level 2 and 3 there are the checkable subset (level 3 is almost only lesion presence). Fetal head is not covered. The three harmless columns coincide.
- Fetal head severity is set by the size of the HC error (level 1 small, 3 large) plus plane errors; the word scorers are flat across levels there because a changed number is one token whatever its size.
- Per-case AUROC pools all errors of a level in a case; breast and thyroid have far more groups than fetal head. Pooled rows mix organs with different error mixes.
