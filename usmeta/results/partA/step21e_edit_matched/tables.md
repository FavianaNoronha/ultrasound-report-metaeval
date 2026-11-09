## Candidates per edit-size bin (test split)

| organ | candidates | 0-5% | 5-10% | 10-20% | 20-40% | 40%+ |
|---|---|---|---|---|---|---|
| breast | error | 3712 | 583 | 401 | 0 | 646 |
| breast | harmless | 1398 | 363 | 1443 | 1375 | 1988 |
| breast | harmless, small | 101 | 0 | 646 | 174 | 472 |
| breast | harmless, matched | 1262 | 296 | 144 | 0 | 0 |
| breast | harmless, large | 0 | 0 | 0 | 472 | 820 |
| breast | harmless, other | 35 | 67 | 653 | 729 | 696 |
| thyroid | error | 2360 | 706 | 84 | 0 | 450 |
| thyroid | harmless | 568 | 888 | 333 | 1871 | 948 |
| thyroid | harmless, small | 0 | 0 | 110 | 674 | 114 |
| thyroid | harmless, matched | 568 | 888 | 0 | 4 | 0 |
| thyroid | harmless, large | 0 | 0 | 0 | 410 | 490 |
| thyroid | harmless, other | 0 | 0 | 223 | 783 | 344 |
| fetal head | error | 1047 | 153 | 150 | 3 | 0 |
| fetal head | harmless | 150 | 597 | 456 | 679 | 1136 |
| fetal head | harmless, small | 150 | 297 | 153 | 0 | 300 |
| fetal head | harmless, matched | 0 | 300 | 303 | 0 | 0 |
| fetal head | harmless, large | 0 | 0 | 0 | 379 | 227 |
| fetal head | harmless, other | 0 | 0 | 0 | 300 | 609 |

Large harmless rewordings and large errors are rare at the two ends, so some bins have no pairs or too few groups; no extra rewordings were generated.

## Pairs and groups per bin (error x harmless pairs inside the same reference and bin)

| organ | 0-5% | 5-10% | 10-20% | 20-40% | 40%+ | all pairs (unmatched) |
|---|---|---|---|---|---|---|
| breast | 13494 pairs, 385 groups | 443 pairs, 278 groups | 720 pairs, 292 groups | 0 pairs, 0 groups † | 1988 pairs, 413 groups | 59055 pairs, 413 groups |
| thyroid | 4768 pairs, 255 groups | 1630 pairs, 339 groups | 249 pairs, 67 groups | 0 pairs, 0 groups † | 948 pairs, 417 groups | 37417 pairs, 417 groups |
| fetal head | 600 pairs, 53 groups | 151 pairs, 119 groups | 0 pairs, 0 groups † | 6 pairs, 3 groups † | 0 pairs, 0 groups † | 13518 pairs, 204 groups |

† under 30 groups: too small to compare.

## Paired preference accuracy (share of error x harmless pairs where the error scores LOWER; ties not counted as preferred)

### breast

| scorer | 0-5% | 5-10% | 10-20% | 20-40% | 40%+ | all pairs (unmatched) |
|---|---|---|---|---|---|---|
| BLEU | 0.58 (0.55–0.60) | 0.74 (0.68–0.80) | 0.02 (0.01–0.03) | — | 1.00 (1.00–1.00) | 0.45 (0.38–0.51) |
| ROUGE-L | 0.06 (0.05–0.07) | 0.74 (0.68–0.80) | 0.00 (0.00–0.01) | — | 1.00 (1.00–1.00) | 0.36 (0.27–0.43) |
| chrF | 0.28 (0.27–0.29) | 0.76 (0.71–0.82) | 0.02 (0.01–0.03) | — | 1.00 (1.00–1.00) | 0.46 (0.39–0.52) |
| BERTScore | 0.20 (0.18–0.21) | 0.93 (0.91–0.95) | 0.01 (0.01–0.03) | — | 1.00 (1.00–1.00) | 0.39 (0.31–0.46) |
| RaTEScore | 0.33 (0.30–0.36) | 0.90 (0.87–0.92) | 0.26 (0.22–0.30) | — | 1.00 (1.00–1.00) | 0.69 (0.64–0.72) |
| finding_f1 (upper bound) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | — | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) |
| judge sentence_f1 | 0.75 (0.69–0.80) | too small to compare (22 groups) | 1.00 (1.00–1.00) | — | 1.00 (0.99–1.00) | 0.80 (0.75–0.84) |
| judge_score | 0.99 (0.98–1.00) | too small to compare (22 groups) | 1.00 (1.00–1.00) | — | 0.96 (0.92–0.98) | 0.92 (0.89–0.94) |

### thyroid

| scorer | 0-5% | 5-10% | 10-20% | 20-40% | 40%+ | all pairs (unmatched) |
|---|---|---|---|---|---|---|
| BLEU | 0.74 (0.70–0.78) | 1.00 (1.00–1.00) | 0.33 (0.32–0.34) | — | 1.00 (0.99–1.00) | 0.36 (0.36–0.37) |
| ROUGE-L | 0.09 (0.08–0.11) | 1.00 (1.00–1.00) | 0.00 (0.00–0.00) | — | 1.00 (1.00–1.00) | 0.24 (0.23–0.25) |
| chrF | 0.07 (0.06–0.08) | 1.00 (1.00–1.00) | 0.67 (0.67–0.69) | — | 1.00 (1.00–1.00) | 0.37 (0.36–0.37) |
| BERTScore | 0.15 (0.13–0.18) | 1.00 (1.00–1.00) | 0.59 (0.50–0.67) | — | 1.00 (1.00–1.00) | 0.27 (0.27–0.28) |
| RaTEScore | 0.11 (0.10–0.13) | 0.89 (0.87–0.91) | 0.73 (0.70–0.77) | — | 1.00 (0.99–1.00) | 0.43 (0.43–0.44) |
| finding_f1 (upper bound) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | — | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) |
| judge sentence_f1 | 0.86 (0.80–0.91) | 1.00 (1.00–1.00) | too small to compare (5 groups) | — | 0.98 (0.94–1.00) | 0.85 (0.83–0.88) |
| judge_score | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | too small to compare (5 groups) | — | 1.00 (1.00–1.00) | 0.97 (0.95–0.98) |

### fetal head

| scorer | 0-5% | 5-10% | 10-20% | 20-40% | 40%+ | all pairs (unmatched) |
|---|---|---|---|---|---|---|
| BLEU | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | — | too small to compare (3 groups) | — | 0.20 (0.20–0.20) |
| ROUGE-L | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | — | too small to compare (3 groups) | — | 0.00 (0.00–0.00) |
| chrF | 0.29 (0.25–0.34) | 0.01 (0.00–0.03) | — | too small to compare (3 groups) | — | 0.18 (0.17–0.20) |
| BERTScore | 0.00 (0.00–0.01) | 0.00 (0.00–0.00) | — | too small to compare (3 groups) | — | 0.05 (0.04–0.06) |
| RaTEScore | 0.29 (0.25–0.33) | 0.35 (0.27–0.44) | — | too small to compare (3 groups) | — | 0.50 (0.49–0.51) |
| finding_f1 (upper bound) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | — | too small to compare (3 groups) | — | 1.00 (1.00–1.00) |
| judge sentence_f1 | too small to compare (14 groups) | too small to compare (6 groups) | — | too small to compare (2 groups) | — | 0.89 (0.85–0.92) |
| judge_score | too small to compare (14 groups) | too small to compare (6 groups) | — | too small to compare (2 groups) | — | 0.91 (0.88–0.93) |

## AUROC (= strict preference + 0.5 x tie share)

### breast

| scorer | 0-5% | 5-10% | 10-20% | 20-40% | 40%+ | all pairs (unmatched) |
|---|---|---|---|---|---|---|
| BLEU | 0.74 (0.72–0.76) | 0.74 (0.68–0.80) | 0.02 (0.01–0.03) | — | 1.00 (1.00–1.00) | 0.49 (0.42–0.55) |
| ROUGE-L | 0.50 (0.50–0.51) | 0.77 (0.72–0.82) | 0.00 (0.00–0.01) | — | 1.00 (1.00–1.00) | 0.43 (0.35–0.49) |
| chrF | 0.28 (0.27–0.29) | 0.76 (0.71–0.82) | 0.02 (0.01–0.03) | — | 1.00 (1.00–1.00) | 0.46 (0.39–0.52) |
| BERTScore | 0.20 (0.18–0.21) | 0.93 (0.91–0.95) | 0.01 (0.01–0.03) | — | 1.00 (1.00–1.00) | 0.39 (0.31–0.46) |
| RaTEScore | 0.36 (0.33–0.39) | 0.90 (0.87–0.92) | 0.26 (0.22–0.30) | — | 1.00 (1.00–1.00) | 0.72 (0.68–0.75) |
| finding_f1 (upper bound) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | — | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) |
| judge sentence_f1 | 0.87 (0.85–0.90) | too small to compare (22 groups) | 1.00 (1.00–1.00) | — | 1.00 (1.00–1.00) | 0.86 (0.83–0.89) |
| judge_score | 1.00 (0.99–1.00) | too small to compare (22 groups) | 1.00 (1.00–1.00) | — | 0.98 (0.96–0.99) | 0.93 (0.91–0.95) |

### thyroid

| scorer | 0-5% | 5-10% | 10-20% | 20-40% | 40%+ | all pairs (unmatched) |
|---|---|---|---|---|---|---|
| BLEU | 0.81 (0.78–0.84) | 1.00 (1.00–1.00) | 0.33 (0.32–0.34) | — | 1.00 (0.99–1.00) | 0.42 (0.41–0.42) |
| ROUGE-L | 0.55 (0.54–0.55) | 1.00 (1.00–1.00) | 0.00 (0.00–0.00) | — | 1.00 (1.00–1.00) | 0.33 (0.33–0.34) |
| chrF | 0.07 (0.06–0.08) | 1.00 (1.00–1.00) | 0.67 (0.67–0.69) | — | 1.00 (1.00–1.00) | 0.37 (0.36–0.37) |
| BERTScore | 0.15 (0.13–0.18) | 1.00 (1.00–1.00) | 0.59 (0.50–0.67) | — | 1.00 (1.00–1.00) | 0.27 (0.27–0.28) |
| RaTEScore | 0.19 (0.16–0.22) | 0.89 (0.87–0.91) | 0.73 (0.70–0.77) | — | 1.00 (0.99–1.00) | 0.56 (0.56–0.57) |
| finding_f1 (upper bound) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | — | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) |
| judge sentence_f1 | 0.93 (0.90–0.95) | 1.00 (1.00–1.00) | too small to compare (5 groups) | — | 0.99 (0.97–1.00) | 0.91 (0.89–0.93) |
| judge_score | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | too small to compare (5 groups) | — | 1.00 (1.00–1.00) | 0.97 (0.96–0.98) |

### fetal head

| scorer | 0-5% | 5-10% | 10-20% | 20-40% | 40%+ | all pairs (unmatched) |
|---|---|---|---|---|---|---|
| BLEU | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | — | too small to compare (3 groups) | — | 0.21 (0.21–0.21) |
| ROUGE-L | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | — | too small to compare (3 groups) | — | 0.15 (0.15–0.15) |
| chrF | 0.29 (0.25–0.34) | 0.01 (0.00–0.03) | — | too small to compare (3 groups) | — | 0.18 (0.17–0.20) |
| BERTScore | 0.00 (0.00–0.01) | 0.00 (0.00–0.00) | — | too small to compare (3 groups) | — | 0.05 (0.04–0.06) |
| RaTEScore | 0.29 (0.25–0.33) | 0.35 (0.27–0.44) | — | too small to compare (3 groups) | — | 0.50 (0.49–0.51) |
| finding_f1 (upper bound) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | — | too small to compare (3 groups) | — | 1.00 (1.00–1.00) |
| judge sentence_f1 | too small to compare (14 groups) | too small to compare (6 groups) | — | too small to compare (2 groups) | — | 0.92 (0.89–0.94) |
| judge_score | too small to compare (14 groups) | too small to compare (6 groups) | — | too small to compare (2 groups) | — | 0.92 (0.90–0.94) |

## Which error types fall in each edit-size bin (share of error candidates; test split)

| organ | error category | 0-5% | 5-10% | 10-20% | 20-40% | 40%+ |
|---|---|---|---|---|---|---|
| breast | false finding | 3% | 25% | 97% | — | 22% |
| breast | missed finding | 1% | 0% | 0% | — | 0% |
| breast | missed finding (field lesion: no focal lesion) | 0% | 0% | 0% | — | 78% |
| breast | wrong location | 12% | 0% | 0% | — | 0% |
| breast | wrong measurement | 41% | 0% | 0% | — | 0% |
| breast | wrong severity/category | 43% | 74% | 3% | — | 0% |
| thyroid | false finding | 3% | 43% | 46% | — | 0% |
| thyroid | missed finding | 0% | 4% | 54% | — | 0% |
| thyroid | missed finding (field lesion: no focal lesion) | 0% | 0% | 0% | — | 100% |
| thyroid | wrong location | 11% | 0% | 0% | — | 0% |
| thyroid | wrong measurement | 57% | 0% | 0% | — | 0% |
| thyroid | wrong severity/category | 29% | 53% | 0% | — | 0% |
| fetal head | wrong measurement | 100% | 100% | 0% | 0% | — |
| fetal head | wrong severity/category | 0% | 0% | 100% | 100% | — |

Error edit size is set by the error type, so a bin comparison is also an error-type comparison: the 40%+ bin is almost entirely the "No focal lesion is seen." rewrite.

## Same tables without the whole-report "no focal lesion" errors (field = lesion, missed finding): strict preference

### breast (excluding no-lesion errors)

| scorer | 0-5% | 5-10% | 10-20% | 20-40% | 40%+ | all pairs |
|---|---|---|---|---|---|---|
| BLEU | 0.58 (0.55–0.60) | 0.74 (0.68–0.80) | 0.02 (0.01–0.03) | — | 1.00 (1.00–1.00) | 0.39 (0.30–0.45) |
| ROUGE-L | 0.06 (0.05–0.07) | 0.74 (0.68–0.80) | 0.00 (0.00–0.01) | — | 1.00 (1.00–1.00) | 0.28 (0.19–0.36) |
| chrF | 0.28 (0.27–0.29) | 0.76 (0.71–0.82) | 0.02 (0.01–0.03) | — | 1.00 (1.00–1.00) | 0.40 (0.32–0.46) |
| BERTScore | 0.20 (0.18–0.21) | 0.93 (0.91–0.95) | 0.01 (0.01–0.03) | — | 1.00 (1.00–1.00) | 0.32 (0.23–0.39) |
| RaTEScore | 0.33 (0.30–0.36) | 0.90 (0.87–0.92) | 0.26 (0.22–0.30) | — | 1.00 (1.00–1.00) | 0.65 (0.61–0.69) |
| finding_f1 (upper bound) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | — | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) |

### thyroid (excluding no-lesion errors)

| scorer | 0-5% | 5-10% | 10-20% | 20-40% | 40%+ | all pairs |
|---|---|---|---|---|---|---|
| BLEU | 0.74 (0.70–0.78) | 1.00 (1.00–1.00) | 0.33 (0.32–0.34) | — | too small to compare (2 groups) | 0.26 (0.26–0.26) |
| ROUGE-L | 0.09 (0.08–0.11) | 1.00 (1.00–1.00) | 0.00 (0.00–0.00) | — | too small to compare (2 groups) | 0.12 (0.11–0.12) |
| chrF | 0.07 (0.06–0.08) | 1.00 (1.00–1.00) | 0.67 (0.67–0.69) | — | too small to compare (2 groups) | 0.27 (0.27–0.27) |
| BERTScore | 0.15 (0.13–0.18) | 1.00 (1.00–1.00) | 0.59 (0.50–0.67) | — | too small to compare (2 groups) | 0.16 (0.15–0.16) |
| RaTEScore | 0.11 (0.10–0.13) | 0.89 (0.87–0.91) | 0.73 (0.70–0.77) | — | too small to compare (2 groups) | 0.34 (0.33–0.35) |
| finding_f1 (upper bound) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | — | too small to compare (2 groups) | 1.00 (1.00–1.00) |

### fetal head (excluding no-lesion errors)

| scorer | 0-5% | 5-10% | 10-20% | 20-40% | 40%+ | all pairs |
|---|---|---|---|---|---|---|
| BLEU | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | — | too small to compare (3 groups) | — | 0.20 (0.20–0.20) |
| ROUGE-L | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | — | too small to compare (3 groups) | — | 0.00 (0.00–0.00) |
| chrF | 0.29 (0.25–0.34) | 0.01 (0.00–0.03) | — | too small to compare (3 groups) | — | 0.18 (0.17–0.20) |
| BERTScore | 0.00 (0.00–0.01) | 0.00 (0.00–0.00) | — | too small to compare (3 groups) | — | 0.05 (0.04–0.06) |
| RaTEScore | 0.29 (0.25–0.33) | 0.35 (0.27–0.44) | — | too small to compare (3 groups) | — | 0.50 (0.49–0.51) |
| finding_f1 (upper bound) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | — | too small to compare (3 groups) | — | 1.00 (1.00–1.00) |

## Human rewordings (Step 21d) against same-bin errors of the same reference (point estimates; far fewer than 30 groups: too small to compare)

| scorer | 0-5% | 5-10% | 10-20% | 20-40% | 40%+ |
|---|---|---|---|---|---|
| human rewordings in the bin | 0 | 2 | 5 | 6 | 16 |
| BLEU | — | 0.00 (n=2 items) | 0.00 (n=3 items) | — | 1.00 (n=11 items) |
| ROUGE-L | — | 1.00 (n=2 items) | 0.00 (n=3 items) | — | 1.00 (n=11 items) |
| chrF | — | 1.00 (n=2 items) | 0.00 (n=3 items) | — | 1.00 (n=11 items) |
| BERTScore | — | 0.00 (n=2 items) | 0.00 (n=3 items) | — | 1.00 (n=11 items) |
| RaTEScore | — | 0.50 (n=2 items) | 1.00 (n=3 items) | — | 0.55 (n=11 items) |
| finding_f1 (upper bound) | — | 1.00 (n=2 items) | 1.00 (n=3 items) | — | 1.00 (n=11 items) |

Judge scores of the human rewordings were not saved per pair (Step 21d keeps aggregates only), so there is no judge row here; see the Step 21d results for the aggregate.

Judge rows (`sentence_f1`, `judge_score`) use only pairs in which both candidates were judged (Steps 10d + 12 samples); their bins have far fewer groups.
