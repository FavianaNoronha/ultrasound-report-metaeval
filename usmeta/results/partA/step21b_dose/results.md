# Step 21b — Error-size dose-response (size / measurement errors; head circumference for fetal head)

New candidates from the SAME test references (`bench_test_v2d`) at multiplicative factors ×0.5, 0.7, 0.8, 0.9, 0.95, 1.3, 1.5, 2.0 of the stated size (size in mm or % of image width; head circumference in mm for fetal head), rendered with the Step 2 templates and compared with the matched one-word synonyms of the same reference (13,528 rows in `candidates.jsonl`). Code: `usmeta/step21_dose.py`. Intervals resample patient/exam groups (1,000, seed 0); † = fewer than 30 groups: too small to compare.

**Sample sizes (deviation, stated).** Text scorers and `finding_f1`: all test cases that have a size field (breast 502, thyroid 448, fetal head 300). **Judge: capped** to a subset of the Step 12 59-case sample (12 cases per dataset ≥ the cap; Step 12 replies are reused where the candidate text is identical, hence 27–123 cases per cell), 901 new judge calls (81 min, 0 unparseable) so the step stays under the ~3 h limit; the fetal-head judge cells (27 cases) are marked †. Image check: the Step 16 scans that appear in `bench_test_v2d` (exact box): breast 88–103, thyroid 36, fetal head 18 cases per cell, so thyroid and fetal-head cells are small.

## Headline (plain words)
- **`finding_f1` is 1.00 at every factor, down to ×0.95 — by construction, not evidence.** Any changed number lowers its credit and the synonyms keep 1.0; it is an upper bound on templated text and says nothing about real reports.
- **BLEU and ROUGE-L are flat: they cannot tell a 5% error from a 100% error.** AUROC against synonyms stays at 0.69 (×0.95) to 0.67 (×2) for BLEU on breast (ROUGE-L 0.49–0.48); Spearman ρ between error size and score drop is -0.01 (BLEU) and -0.01 (ROUGE-L). A changed number is one changed token whatever its size.
- **chrF and BERTScore score a size error as more similar than a one-word synonym** (AUROC 0.00 for chrF on breast, BERTScore 0.02–0.21), an edit-size artefact (the synonyms change more characters than a number). Their scores fall slightly with error size (ρ +0.16 to +0.34) but never cross the synonyms.
- **RaTEScore has only a weak dose-response:** breast 0.59 (×0.95) → 0.65 (×0.5), thyroid 0.26–0.30, below chance (it prefers the error), ρ +0.29 (breast), +0.02 (thyroid).
- **The judge's `judge_score` notices even a 5% change** (AUROC 0.97 breast, 0.87 thyroid at ×0.95; ≥ 0.98 for every larger error) but `sentence_f1` needs bigger errors (breast 0.54 at ×0.95 and 0.76 at ×2; thyroid 0.50 at ×0.95, 0.89–0.92 at ×0.5/×2). Scores fall roughly monotonically with error size (ρ judge_score +0.67 breast, +0.75 thyroid; sentence_f1 +0.30, +0.54). Same pattern as Step 18: the judge sees "the number differs", not whether it matters.
- **The image check is high for big errors and falls through chance for small ones.** AUROC for ×1.3–×2: breast 0.95, thyroid 0.85, fetal head 0.53. For smaller errors it drops: breast 0.67 (×0.7), 0.52, 0.33, 0.16 (×0.95); thyroid 0.26 → 0.08; fetal head 0.19–0.28. Values far below 0.5 mean the check scores a size that is 5–20% too small ABOVE the correct size. This is consistent with MedSAM under-estimating size (median −2 mm, 13% on BrEaST, Step 18; negative bias in Step 16); a planted size slightly below the truth lands closer to the measured size than the truth does. We did not test the mechanism directly.
- **Monotonic?** Mostly for the judge (ρ 0.54–0.75 for judge_score and sentence_f1 on thyroid, 0.3–0.67 breast) and finding_f1 (0.86, by construction); not for BLEU/ROUGE-L (≈ 0) or the image check on the small-error side. ρ is pooled over all error candidates of an organ, so it mixes the up (×1.3…) and down (×0.5…) sides.

## Full tables
### breast

AUROC of size errors of factor × (stated size) against the matched one-word synonyms of the same reference (95% CI, patient/exam groups; n cases in brackets; † = fewer than 30 groups: too small to compare). Spearman ρ = rank correlation between |log factor| and the score drop (1 − score) over all error candidates (positive = bigger errors score lower).

| scorer | ×0.5 | ×0.7 | ×0.8 | ×0.9 | ×0.95 | ×1.3 | ×1.5 | ×2.0 | all factors | Spearman ρ |
|---|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.67 (0.66–0.68) (502) | 0.67 (0.66–0.68) (502) | 0.67 (0.66–0.68) (502) | 0.68 (0.66–0.69) (500) | 0.69 (0.68–0.69) (454) | 0.67 (0.66–0.68) (502) | 0.67 (0.66–0.68) (502) | 0.67 (0.66–0.68) (502) | 0.67 (0.66–0.68) (502) | -0.01 |
| rougeL | 0.48 (0.48–0.49) (502) | 0.48 (0.48–0.49) (502) | 0.48 (0.48–0.49) (502) | 0.48 (0.48–0.49) (500) | 0.49 (0.48–0.49) (454) | 0.48 (0.48–0.49) (502) | 0.48 (0.48–0.49) (502) | 0.48 (0.48–0.49) (502) | 0.48 (0.48–0.49) (502) | -0.01 |
| chrf | 0.00 (0.00–0.00) (502) | 0.00 (0.00–0.00) (502) | 0.00 (0.00–0.00) (502) | 0.00 (0.00–0.00) (500) | 0.00 (0.00–0.00) (454) | 0.00 (0.00–0.00) (502) | 0.00 (0.00–0.00) (502) | 0.00 (0.00–0.00) (502) | 0.00 (0.00–0.00) (502) | +0.16 |
| bertscore[roberta-large] | 0.01 (0.01–0.02) (502) | 0.01 (0.01–0.02) (502) | 0.01 (0.01–0.01) (502) | 0.01 (0.00–0.01) (500) | 0.00 (0.00–0.01) (454) | 0.01 (0.01–0.02) (502) | 0.02 (0.01–0.02) (502) | 0.02 (0.01–0.02) (502) | 0.01 (0.01–0.01) (502) | +0.34 |
| ratescore | 0.65 (0.63–0.66) (502) | 0.63 (0.62–0.65) (502) | 0.61 (0.60–0.62) (502) | 0.60 (0.58–0.61) (500) | 0.59 (0.57–0.60) (454) | 0.61 (0.60–0.63) (502) | 0.63 (0.62–0.65) (502) | 0.65 (0.64–0.67) (502) | 0.62 (0.61–0.63) (502) | +0.29 |
| finding_f1 (UPPER BOUND, templated) | 1.00 (1.00–1.00) (502) | 1.00 (1.00–1.00) (502) | 1.00 (1.00–1.00) (502) | 1.00 (1.00–1.00) (500) | 1.00 (1.00–1.00) (454) | 1.00 (1.00–1.00) (502) | 1.00 (1.00–1.00) (502) | 1.00 (1.00–1.00) (502) | 1.00 (1.00–1.00) (502) | +0.86 |
| judge sentence_f1 | 0.62 (0.59–0.67) (108) | 0.57 (0.53–0.62) (77) | 0.55 (0.52–0.58) (77) | 0.53 (0.51–0.57) (77) | 0.54 (0.51–0.57) (67) | 0.65 (0.60–0.70) (82) | 0.74 (0.69–0.79) (113) | 0.76 (0.71–0.80) (117) | 0.68 (0.65–0.72) (174) | +0.30 |
| judge judge_score | 1.00 (1.00–1.00) (108) | 1.00 (1.00–1.00) (77) | 1.00 (1.00–1.00) (77) | 0.99 (0.98–1.00) (77) | 0.97 (0.94–0.99) (67) | 1.00 (1.00–1.00) (82) | 1.00 (1.00–1.00) (113) | 1.00 (1.00–1.00) (117) | 1.00 (1.00–1.00) (174) | +0.67 |
| image check (predicted masks, exact box) | 0.87 (0.80–0.93) (103) | 0.67 (0.58–0.76) (103) | 0.52 (0.43–0.62) (103) | 0.33 (0.25–0.42) (102) | 0.16 (0.09–0.23) (88) | 0.95 (0.92–0.98) (103) | 0.95 (0.92–0.98) (103) | 0.95 (0.92–0.98) (103) | 0.69 (0.64–0.74) (103) | +0.55 |

Mean score per factor (breast):

| scorer | ×0.5 | ×0.7 | ×0.8 | ×0.9 | ×0.95 | ×1.3 | ×1.5 | ×2.0 |
|---|---|---|---|---|---|---|---|---|
| bleu | 0.930 | 0.930 | 0.930 | 0.930 | 0.929 | 0.930 | 0.930 | 0.930 |
| rougeL | 0.966 | 0.966 | 0.966 | 0.966 | 0.965 | 0.966 | 0.966 | 0.966 |
| chrf | 0.969 | 0.970 | 0.971 | 0.973 | 0.973 | 0.970 | 0.969 | 0.969 |
| bertscore[roberta-large] | 0.999 | 0.999 | 0.999 | 0.999 | 0.999 | 0.998 | 0.998 | 0.998 |
| ratescore | 0.938 | 0.941 | 0.950 | 0.962 | 0.965 | 0.947 | 0.940 | 0.939 |
| finding_f1 (UPPER BOUND, templated) | 0.872 | 0.922 | 0.948 | 0.974 | 0.986 | 0.924 | 0.878 | 0.876 |
| judge sentence_f1 | 0.944 | 0.975 | 0.983 | 0.987 | 0.985 | 0.941 | 0.890 | 0.877 |
| judge judge_score | 0.453 | 0.652 | 0.726 | 0.853 | 0.869 | 0.685 | 0.629 | 0.552 |
| image check (predicted masks, exact box) | 0.799 | 0.881 | 0.910 | 0.922 | 0.915 | 0.800 | 0.769 | 0.767 |

### thyroid

AUROC of size errors of factor × (stated size) against the matched one-word synonyms of the same reference (95% CI, patient/exam groups; n cases in brackets; † = fewer than 30 groups: too small to compare). Spearman ρ = rank correlation between |log factor| and the score drop (1 − score) over all error candidates (positive = bigger errors score lower).

| scorer | ×0.5 | ×0.7 | ×0.8 | ×0.9 | ×0.95 | ×1.3 | ×1.5 | ×2.0 | all factors | Spearman ρ |
|---|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.66 (0.65–0.66) (448) | 0.66 (0.65–0.66) (448) | 0.66 (0.65–0.66) (448) | 0.66 (0.65–0.66) (448) | 0.65 (0.65–0.66) (415) | 0.66 (0.65–0.66) (447) | 0.66 (0.65–0.66) (447) | 0.66 (0.65–0.66) (447) | 0.66 (0.65–0.66) (448) | +0.01 |
| rougeL | 0.50 (0.50–0.50) (448) | 0.50 (0.50–0.50) (448) | 0.50 (0.50–0.50) (448) | 0.50 (0.50–0.50) (448) | 0.50 (0.50–0.50) (415) | 0.50 (0.50–0.50) (447) | 0.50 (0.50–0.50) (447) | 0.50 (0.50–0.50) (447) | 0.50 (0.50–0.50) (448) | +0.01 |
| chrf | 0.00 (0.00–0.00) (448) | 0.00 (0.00–0.00) (448) | 0.00 (0.00–0.00) (448) | 0.00 (0.00–0.00) (448) | 0.00 (0.00–0.00) (415) | 0.00 (0.00–0.00) (447) | 0.00 (0.00–0.00) (447) | 0.00 (0.00–0.00) (447) | 0.00 (0.00–0.00) (448) | +0.24 |
| bertscore[roberta-large] | 0.15 (0.14–0.17) (448) | 0.15 (0.13–0.16) (448) | 0.12 (0.10–0.13) (448) | 0.10 (0.09–0.11) (448) | 0.06 (0.05–0.07) (415) | 0.16 (0.14–0.18) (447) | 0.20 (0.19–0.22) (447) | 0.21 (0.20–0.23) (447) | 0.14 (0.13–0.15) (448) | +0.31 |
| ratescore | 0.30 (0.28–0.31) (448) | 0.29 (0.27–0.30) (448) | 0.27 (0.26–0.29) (448) | 0.27 (0.25–0.28) (448) | 0.26 (0.25–0.28) (415) | 0.27 (0.25–0.28) (447) | 0.27 (0.25–0.28) (447) | 0.27 (0.26–0.28) (447) | 0.27 (0.26–0.29) (448) | +0.02 |
| finding_f1 (UPPER BOUND, templated) | 1.00 (1.00–1.00) (448) | 1.00 (1.00–1.00) (448) | 1.00 (1.00–1.00) (448) | 1.00 (1.00–1.00) (448) | 1.00 (1.00–1.00) (415) | 1.00 (1.00–1.00) (447) | 1.00 (1.00–1.00) (447) | 1.00 (1.00–1.00) (447) | 1.00 (1.00–1.00) (448) | +0.86 |
| judge sentence_f1 | 0.89 (0.85–0.93) (110) | 0.72 (0.65–0.79) (53) | 0.62 (0.57–0.68) (53) | 0.50 (0.50–0.50) (53) | 0.50 (0.50–0.50) (41) | 0.86 (0.81–0.92) (60) | 0.91 (0.88–0.94) (123) | 0.92 (0.88–0.95) (116) | 0.87 (0.84–0.90) (199) | +0.54 |
| judge judge_score | 1.00 (1.00–1.00) (110) | 1.00 (1.00–1.00) (53) | 1.00 (1.00–1.00) (53) | 0.98 (0.95–1.00) (53) | 0.87 (0.80–0.93) (41) | 1.00 (1.00–1.00) (60) | 1.00 (1.00–1.00) (123) | 1.00 (1.00–1.00) (116) | 1.00 (0.99–1.00) (199) | +0.75 |
| image check (predicted masks, exact box) | 0.46 (0.31–0.61) (36) | 0.26 (0.16–0.40) (36) | 0.12 (0.04–0.24) (36) | 0.10 (0.04–0.17) (36) | 0.08 (0.03–0.15) (36) | 0.85 (0.77–0.92) (36) | 0.85 (0.77–0.92) (36) | 0.85 (0.77–0.92) (36) | 0.45 (0.40–0.50) (36) | +0.18 |

Mean score per factor (thyroid):

| scorer | ×0.5 | ×0.7 | ×0.8 | ×0.9 | ×0.95 | ×1.3 | ×1.5 | ×2.0 |
|---|---|---|---|---|---|---|---|---|
| bleu | 0.909 | 0.909 | 0.909 | 0.909 | 0.910 | 0.909 | 0.909 | 0.909 |
| rougeL | 0.960 | 0.960 | 0.960 | 0.960 | 0.960 | 0.960 | 0.960 | 0.960 |
| chrf | 0.960 | 0.962 | 0.963 | 0.965 | 0.966 | 0.962 | 0.960 | 0.960 |
| bertscore[roberta-large] | 0.998 | 0.998 | 0.998 | 0.999 | 0.999 | 0.998 | 0.998 | 0.997 |
| ratescore | 0.982 | 0.984 | 0.987 | 0.987 | 0.990 | 0.991 | 0.989 | 0.987 |
| finding_f1 (UPPER BOUND, templated) | 0.826 | 0.894 | 0.929 | 0.965 | 0.981 | 0.897 | 0.833 | 0.830 |
| judge sentence_f1 | 0.733 | 0.855 | 0.918 | 1.000 | 1.000 | 0.761 | 0.727 | 0.721 |
| judge judge_score | 0.423 | 0.602 | 0.736 | 0.885 | 0.927 | 0.713 | 0.637 | 0.481 |
| image check (predicted masks, exact box) | 0.772 | 0.846 | 0.835 | 0.807 | 0.790 | 0.704 | 0.700 | 0.700 |

### fetal head

AUROC of size errors of factor × (stated size) against the matched one-word synonyms of the same reference (95% CI, patient/exam groups; n cases in brackets; † = fewer than 30 groups: too small to compare). Spearman ρ = rank correlation between |log factor| and the score drop (1 − score) over all error candidates (positive = bigger errors score lower).

| scorer | ×0.5 | ×0.7 | ×0.8 | ×0.9 | ×0.95 | ×1.3 | ×1.5 | ×2.0 | all factors | Spearman ρ |
|---|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.50 (0.50–0.50) (300) | 0.50 (0.50–0.50) (300) | 0.50 (0.50–0.50) (300) | 0.50 (0.50–0.50) (300) | 0.50 (0.50–0.50) (300) | 0.50 (0.50–0.50) (300) | 0.50 (0.50–0.50) (300) | 0.50 (0.50–0.50) (300) | 0.50 (0.50–0.50) (300) | +0.00 |
| rougeL | 0.73 (0.69–0.78) (300) | 0.71 (0.67–0.75) (300) | 0.71 (0.67–0.75) (300) | 0.72 (0.68–0.76) (300) | 0.73 (0.69–0.78) (300) | 0.72 (0.68–0.77) (300) | 0.72 (0.68–0.76) (300) | 0.72 (0.69–0.77) (300) | 0.72 (0.68–0.76) (300) | +0.00 |
| chrf | 0.00 (0.00–0.00) (300) | 0.00 (0.00–0.00) (300) | 0.00 (0.00–0.00) (300) | 0.00 (0.00–0.00) (300) | 0.00 (0.00–0.00) (300) | 0.00 (0.00–0.00) (300) | 0.00 (0.00–0.00) (300) | 0.00 (0.00–0.00) (300) | 0.00 (0.00–0.00) (300) | +0.25 |
| bertscore[roberta-large] | 0.00 (0.00–0.00) (300) | 0.00 (0.00–0.00) (300) | 0.00 (0.00–0.00) (300) | 0.00 (0.00–0.00) (300) | 0.00 (0.00–0.00) (300) | 0.00 (0.00–0.01) (300) | 0.02 (0.01–0.03) (300) | 0.03 (0.02–0.04) (300) | 0.01 (0.00–0.01) (300) | +0.26 |
| ratescore | 0.41 (0.36–0.45) (300) | 0.43 (0.39–0.47) (300) | 0.35 (0.30–0.39) (300) | 0.28 (0.23–0.32) (300) | 0.21 (0.17–0.25) (300) | 0.43 (0.39–0.47) (300) | 0.47 (0.43–0.50) (300) | 0.48 (0.44–0.52) (300) | 0.38 (0.35–0.41) (300) | +0.27 |
| finding_f1 (UPPER BOUND, templated) | 1.00 (1.00–1.00) (300) | 1.00 (1.00–1.00) (300) | 1.00 (1.00–1.00) (300) | 1.00 (1.00–1.00) (300) | 1.00 (1.00–1.00) (300) | 1.00 (1.00–1.00) (300) | 1.00 (1.00–1.00) (300) | 1.00 (1.00–1.00) (300) | 1.00 (1.00–1.00) (300) | +0.43 |
| judge sentence_f1 | 1.00 (1.00–1.00) (27) † | 1.00 (1.00–1.00) (27) † | 1.00 (1.00–1.00) (27) † | 1.00 (1.00–1.00) (27) † | 1.00 (1.00–1.00) (27) † | 1.00 (1.00–1.00) (27) † | 1.00 (1.00–1.00) (27) † | 1.00 (1.00–1.00) (27) † | 1.00 (1.00–1.00) (27) † | -0.05 |
| judge judge_score | 1.00 (1.00–1.00) (27) † | 1.00 (1.00–1.00) (27) † | 1.00 (1.00–1.00) (27) † | 1.00 (1.00–1.00) (27) † | 1.00 (1.00–1.00) (27) † | 1.00 (1.00–1.00) (27) † | 1.00 (1.00–1.00) (27) † | 1.00 (1.00–1.00) (27) † | 1.00 (1.00–1.00) (27) † | +0.26 |
| image check (predicted masks, exact box) | 0.47 (0.37–0.55) (18) † | 0.47 (0.41–0.50) (18) † | 0.19 (0.09–0.30) (18) † | 0.22 (0.12–0.33) (18) † | 0.28 (0.17–0.38) (18) † | 0.53 (0.50–0.58) (18) † | 0.53 (0.50–0.58) (18) † | 0.53 (0.50–0.58) (18) † | 0.40 (0.35–0.45) (18) † | +0.45 |

Mean score per factor (fetal head):

| scorer | ×0.5 | ×0.7 | ×0.8 | ×0.9 | ×0.95 | ×1.3 | ×1.5 | ×2.0 |
|---|---|---|---|---|---|---|---|---|
| bleu | 0.693 | 0.693 | 0.693 | 0.693 | 0.693 | 0.693 | 0.693 | 0.693 |
| rougeL | 0.812 | 0.819 | 0.819 | 0.816 | 0.812 | 0.815 | 0.816 | 0.814 |
| chrf | 0.863 | 0.876 | 0.877 | 0.879 | 0.882 | 0.864 | 0.862 | 0.862 |
| bertscore[roberta-large] | 0.992 | 0.992 | 0.992 | 0.993 | 0.993 | 0.992 | 0.991 | 0.990 |
| ratescore | 0.883 | 0.881 | 0.886 | 0.903 | 0.917 | 0.879 | 0.874 | 0.872 |
| finding_f1 (UPPER BOUND, templated) | 0.250 | 0.251 | 0.273 | 0.364 | 0.631 | 0.251 | 0.250 | 0.250 |
| judge sentence_f1 | 0.500 | 0.500 | 0.500 | 0.506 | 0.580 | 0.549 | 0.549 | 0.605 |
| judge judge_score | 0.400 | 0.400 | 0.400 | 0.400 | 0.467 | 0.400 | 0.400 | 0.400 |
| image check (predicted masks, exact box) | 0.092 | 0.048 | 0.260 | 0.394 | 0.153 | 0.000 | 0.000 | 0.000 |

## Limits
Templated references; judge cells use a capped sample (fetal head 27 cases, †); the image check covers the Step 16 scans only (thyroid 36, fetal head 18 cases per cell, fetal head fails for other reasons, Step 16); the matched synonym is not matched in characters (chrF/BERTScore/RaTEScore comparisons are affected by edit size); factors are multiplicative so a given factor is a different absolute change for small and large nodules (see Step 18 for absolute mm); MedSAM and the judge may have seen the public datasets; one machine. `finding_f1` is an upper bound.
