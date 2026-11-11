# Step 33: edit-size law (saved scores only)

Limitations: [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md). Code: `usmeta/step33_edit_size_law.py`, `step33_report.py` (new files, no model call; test access logged under `usmeta.step33_edit_size_law`). Data: `bench_test_v2d`, saved test scores (Layer 0, judge replies of Steps 10d + 12, Step 27 pair scores for `llm_finding_f1`), and the 29 human rewordings of Step 21d (saved word-scorer scores; `llm_finding_f1` from the Step 27 extraction cache; no per-pair judge scores were saved for them, so judge rows have no human cell). Plot: `edit_size_law.png`; every cell: `cells.csv`.

**Method.** One point per (organ, harmless group) cell: **AUROC** of planted error vs harmless (per case, ties 0.5, mean over cases) and the **median edit-size ratio** (harmless edit size / error edit size over all error x harmless pairs; edit size = normalised character Levenshtein distance to the reference). Groups: small, matched one-word synonym, large style swap, other secondary variants, and the human rewordings of Step 21d. **Model per scorer: AUROC = a + b * ln(ratio)** by ordinary least squares over that scorer's cells (15 cells for the word scorers: 3 organs x 5 groups; 9 for the judge: small / matched / large only; 12 for `llm_finding_f1`: its judged subset plus the human cell). 95% intervals: group bootstrap (resample patient / exam groups, recompute all cells, refit; 1,000 resamples, seed 0). The primary fit uses all cells; the sensitivity fit drops cells with fewer than 30 groups (the three human cells and the fetal-head cells of the judge). **Decision rule: R² >= 0.6 means "scorer behaviour is largely predicted by edit size".**

## Decision line

**Edit size largely predicts BLEU and ROUGE-L (R² >= 0.6) and does not predict the others.** BLEU R² 0.62 (0.50 to 0.75), ROUGE-L R² 0.71 (0.60 to 0.78), chrF R² 0.21 (0.14 to 0.38), BERTScore R² 0.45 (0.36 to 0.58), RaTEScore R² 0.01 (0.00 to 0.11), judge_score R² 0.35 (0.15 to 0.56), judge sentence_f1 R² 0.13 (0.02 to 0.30), llm_finding_f1 R² 0.05 (0.00 to 0.24). Meeting the rule: BLEU, ROUGE-L. Below the rule: chrF, BERTScore, RaTEScore, judge_score, judge sentence_f1, llm_finding_f1. For BLEU and ROUGE-L, a doubling of the harmless-to-error edit ratio lowers the AUROC by 0.20 and 0.18. chrF, BERTScore, RaTEScore and the judge are less tied to the edit ratio, but that is not evidence that they track facts (see Steps 21e, 28): their cells are low or high for other reasons (e.g. a one-word synonym is scored as a change by chrF), and with 9-15 cells per scorer the fit is coarse. `llm_finding_f1` is flat (R² 0.05) because it is near 1.0 in every template cell (its one low cell is the 9-item human breast cell, 0.73).

## Fit per scorer (AUROC = a + b * ln(ratio))

| scorer | cells (>= 30 groups) | slope b (95% CI) | per doubling of the ratio | R² (95% CI) | R² >= 0.6 | sensitivity: slope / R² on cells with >= 30 groups |
|---|---|---|---|---|---|---|
| BLEU | 15 (12) | -0.292 (-0.296 to -0.249) | -0.202 | 0.62 (0.50 to 0.75) | yes | -0.282 / 0.72 |
| ROUGE-L | 15 (12) | -0.265 (-0.269 to -0.215) | -0.183 | 0.71 (0.60 to 0.78) | yes | -0.260 / 0.74 |
| chrF | 15 (12) | -0.126 (-0.153 to -0.100) | -0.087 | 0.21 (0.14 to 0.38) | no | -0.117 / 0.24 |
| BERTScore | 15 (12) | -0.169 (-0.175 to -0.140) | -0.117 | 0.45 (0.36 to 0.58) | no | -0.163 / 0.49 |
| RaTEScore | 15 (12) | -0.035 (-0.121 to -0.012) | -0.024 | 0.01 (0.00 to 0.11) | no | -0.019 / 0.00 |
| judge_score | 9 (9) | -0.039 (-0.059 to -0.019) | -0.027 | 0.35 (0.15 to 0.56) | no | -0.039 / 0.35 |
| judge sentence_f1 | 9 (9) | -0.030 (-0.052 to -0.009) | -0.021 | 0.13 (0.02 to 0.30) | no | -0.030 / 0.13 |
| llm_finding_f1 | 12 (9) | -0.021 (-0.060 to 0.000) | -0.015 | 0.05 (0.00 to 0.24) | no | -0.002 / 0.01 |

Slope is per unit of ln(ratio); a negative slope means the AUROC falls when the harmless rewording changes more text than the error does. Intervals are percentile intervals of the 1,000 group-bootstrap refits.

## The cells (organ x harmless group; † = under 30 groups: too small to compare)

### BLEU

| organ | group | cases / groups | median harmless / error edit ratio | AUROC |
|---|---|---|---|---|
| breast | small | 646 / 413 | 9.56 | 0.52 |
| breast | matched | 646 / 413 | 1.65 | 0.79 |
| breast | large | 646 / 413 | 18.19 | 0.30 |
| breast | other | 646 / 413 | 9.82 | 0.31 |
| breast | human | 9 / 9 † | 9.81 | 0.12 |
| fetal head | small | 300 / 203 | 5.58 | 0.35 |
| fetal head | matched | 303 / 204 | 5.58 | 0.53 |
| fetal head | large | 303 / 204 | 15.63 | 0.00 |
| fetal head | other | 303 / 204 | 20.25 | 0.00 |
| fetal head | human | 10 / 10 † | 10.73 | 0.00 |
| thyroid | small | 450 / 417 | 12.62 | 0.53 |
| thyroid | matched | 450 / 417 | 3.00 | 0.77 |
| thyroid | large | 450 / 417 | 23.06 | 0.14 |
| thyroid | other | 450 / 417 | 14.22 | 0.15 |
| thyroid | human | 10 / 10 † | 10.21 | 0.14 |

### ROUGE-L

| organ | group | cases / groups | median harmless / error edit ratio | AUROC |
|---|---|---|---|---|
| breast | small | 646 / 413 | 9.56 | 0.32 |
| breast | matched | 646 / 413 | 1.65 | 0.73 |
| breast | large | 646 / 413 | 18.19 | 0.30 |
| breast | other | 646 / 413 | 9.82 | 0.31 |
| breast | human | 9 / 9 † | 9.81 | 0.12 |
| fetal head | small | 300 / 203 | 5.58 | 0.17 |
| fetal head | matched | 303 / 204 | 5.58 | 0.50 |
| fetal head | large | 303 / 204 | 15.63 | 0.00 |
| fetal head | other | 303 / 204 | 20.25 | 0.00 |
| fetal head | human | 10 / 10 † | 10.73 | 0.10 |
| thyroid | small | 450 / 417 | 12.62 | 0.14 |
| thyroid | matched | 450 / 417 | 3.00 | 0.71 |
| thyroid | large | 450 / 417 | 23.06 | 0.14 |
| thyroid | other | 450 / 417 | 14.22 | 0.18 |
| thyroid | human | 10 / 10 † | 10.21 | 0.17 |

### chrF

| organ | group | cases / groups | median harmless / error edit ratio | AUROC |
|---|---|---|---|---|
| breast | small | 646 / 413 | 9.56 | 0.56 |
| breast | matched | 646 / 413 | 1.65 | 0.52 |
| breast | large | 646 / 413 | 18.19 | 0.30 |
| breast | other | 646 / 413 | 9.82 | 0.44 |
| breast | human | 9 / 9 † | 9.81 | 0.12 |
| fetal head | small | 300 / 203 | 5.58 | 0.44 |
| fetal head | matched | 303 / 204 | 5.58 | 0.11 |
| fetal head | large | 303 / 204 | 15.63 | 0.03 |
| fetal head | other | 303 / 204 | 20.25 | 0.07 |
| fetal head | human | 10 / 10 † | 10.73 | 0.00 |
| thyroid | small | 450 / 417 | 12.62 | 0.53 |
| thyroid | matched | 450 / 417 | 3.00 | 0.43 |
| thyroid | large | 450 / 417 | 23.06 | 0.14 |
| thyroid | other | 450 / 417 | 14.22 | 0.35 |
| thyroid | human | 10 / 10 † | 10.21 | 0.17 |

### BERTScore

| organ | group | cases / groups | median harmless / error edit ratio | AUROC |
|---|---|---|---|---|
| breast | small | 646 / 413 | 9.56 | 0.32 |
| breast | matched | 646 / 413 | 1.65 | 0.58 |
| breast | large | 646 / 413 | 18.19 | 0.30 |
| breast | other | 646 / 413 | 9.82 | 0.31 |
| breast | human | 9 / 9 † | 9.81 | 0.12 |
| fetal head | small | 300 / 203 | 5.58 | 0.07 |
| fetal head | matched | 303 / 204 | 5.58 | 0.11 |
| fetal head | large | 303 / 204 | 15.63 | 0.05 |
| fetal head | other | 303 / 204 | 20.25 | 0.00 |
| fetal head | human | 10 / 10 † | 10.73 | 0.00 |
| thyroid | small | 450 / 417 | 12.62 | 0.15 |
| thyroid | matched | 450 / 417 | 3.00 | 0.56 |
| thyroid | large | 450 / 417 | 23.06 | 0.14 |
| thyroid | other | 450 / 417 | 14.22 | 0.15 |
| thyroid | human | 10 / 10 † | 10.21 | 0.15 |

### RaTEScore

| organ | group | cases / groups | median harmless / error edit ratio | AUROC |
|---|---|---|---|---|
| breast | small | 646 / 413 | 9.56 | 0.62 |
| breast | matched | 646 / 413 | 1.65 | 0.71 |
| breast | large | 646 / 413 | 18.19 | 0.48 |
| breast | other | 646 / 413 | 9.82 | 0.92 |
| breast | human | 9 / 9 † | 9.81 | 0.37 |
| fetal head | small | 300 / 203 | 5.58 | 0.45 |
| fetal head | matched | 303 / 204 | 5.58 | 0.25 |
| fetal head | large | 303 / 204 | 15.63 | 0.07 |
| fetal head | other | 303 / 204 | 20.25 | 1.00 |
| fetal head | human | 10 / 10 † | 10.73 | 0.05 |
| thyroid | small | 450 / 417 | 12.62 | 0.54 |
| thyroid | matched | 450 / 417 | 3.00 | 0.55 |
| thyroid | large | 450 / 417 | 23.06 | 0.30 |
| thyroid | other | 450 / 417 | 14.22 | 0.76 |
| thyroid | human | 10 / 10 † | 10.21 | 0.12 |

### judge_score

| organ | group | cases / groups | median harmless / error edit ratio | AUROC |
|---|---|---|---|---|
| breast | small | 400 / 257 | 3.05 | 0.88 |
| breast | matched | 400 / 257 | 1.19 | 1.00 |
| breast | large | 400 / 257 | 6.72 | 0.91 |
| fetal head | small | 140 / 104 | 5.58 | 0.93 |
| fetal head | matched | 142 / 105 | 5.57 | 1.00 |
| fetal head | large | 142 / 105 | 15.48 | 0.83 |
| thyroid | small | 248 / 239 | 7.28 | 0.97 |
| thyroid | matched | 248 / 239 | 1.18 | 1.00 |
| thyroid | large | 248 / 239 | 11.53 | 0.94 |

### judge sentence_f1

| organ | group | cases / groups | median harmless / error edit ratio | AUROC |
|---|---|---|---|---|
| breast | small | 400 / 257 | 3.05 | 0.75 |
| breast | matched | 400 / 257 | 1.19 | 0.94 |
| breast | large | 400 / 257 | 6.72 | 0.88 |
| fetal head | small | 140 / 104 | 5.58 | 0.92 |
| fetal head | matched | 142 / 105 | 5.57 | 1.00 |
| fetal head | large | 142 / 105 | 15.48 | 0.83 |
| thyroid | small | 248 / 239 | 7.28 | 0.92 |
| thyroid | matched | 248 / 239 | 1.18 | 0.97 |
| thyroid | large | 248 / 239 | 11.53 | 0.85 |

### llm_finding_f1

| organ | group | cases / groups | median harmless / error edit ratio | AUROC |
|---|---|---|---|---|
| breast | small | 400 / 257 | 3.05 | 1.00 |
| breast | matched | 400 / 257 | 1.19 | 1.00 |
| breast | large | 400 / 257 | 6.72 | 1.00 |
| breast | human | 9 / 9 † | 9.81 | 0.73 |
| fetal head | small | 140 / 104 | 5.58 | 0.96 |
| fetal head | matched | 142 / 105 | 5.57 | 0.97 |
| fetal head | large | 142 / 105 | 15.48 | 1.00 |
| fetal head | human | 10 / 10 † | 10.73 | 1.00 |
| thyroid | small | 248 / 239 | 7.28 | 1.00 |
| thyroid | matched | 248 / 239 | 1.18 | 1.00 |
| thyroid | large | 248 / 239 | 11.53 | 1.00 |
| thyroid | human | 10 / 10 † | 10.21 | 0.96 |

## Caveats

- **Cells are not independent samples:** the same references and error candidates appear in every harmless group of an organ, the harmless groups differ mainly in how much text they change (that is the point), and organ is not modelled. 9-15 cells per scorer is a small regression; the bootstrap resamples groups, not cells, and does not capture the choice of groups.
- **Edit-size ratio is a median over pairs; fetal-head cells have very short texts** (a changed number is a large relative edit), so their ratios and AUROCs are extreme; the fit is shown with and without cells under 30 groups.
- **Judge and `llm_finding_f1` rows use the judged subset only** (59 cases per dataset); `llm_finding_f1` has no "other" group (not in the judged subset); no human cell for the judge (aggregates only were saved). R² compares scorers on different cell sets.
- **A high R² means edit size predicts the AUROC, not that the scorer is right or wrong**; a low R² for `llm_finding_f1` and the judge means they are not driven by edit size on these data, not that they are validated on free text.
- Human cells have 9-10 items each; the human rewordings are mostly large edits (Step 21e).
