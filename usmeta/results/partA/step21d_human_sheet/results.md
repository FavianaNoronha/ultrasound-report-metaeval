# Step 21d — Human rewordings (scored)

30 test references were reworded by hand (sheet filled by the project team; file `reference to human.xlsx` uploaded to the repository, copied into `sheet.csv`; the blank sheet is kept as `sheet_blank.csv`). The rule-based fact extractor flagged 10 rewordings as changing a fact; I read each one against its reference: 9 (H02-H06, H08-H11) preserve every fact (the extractor only misreads free wording such as "wider in shape than in height") and were marked `OK` in the note column; **H01 was left flagged and excluded** (the reword drops "irregular" and changes "Combined posterior features" to "Associated posterior features"). 29 rewordings are scored; none is identical to its reference.

**Too small to compare:** 29 items overall (9 breast, 10 thyroid, 10 fetal head) is under 30 groups in every cell; the numbers below are point estimates with group-bootstrap intervals and must not be used for a significance claim. Planted errors are the test-split errors of the same reference (bench_test_v2d); judge = Gemma-2-9B prompt_v2 (greedy), run on the 29 rewordings only; the template columns are the project's own rewordings of the SAME references, scored in the same run, for a like-for-like comparison.

AUROC = share of error x rewording pairs in which the error scores lower (ties 0.5); 1.00 = every error scores below every rewording of that type.

## All three organs (n = 29 items)

| scorer | human rewording | template small | template matched | template large |
|---|---|---|---|---|
| BLEU | 0.08 (0.06–0.11) † | 0.43 (0.39–0.48) † | 0.67 (0.62–0.72) † | 0.08 (0.06–0.11) † |
| ROUGE-L | 0.13 (0.08–0.21) † | 0.15 (0.13–0.16) † | 0.62 (0.58–0.65) † | 0.08 (0.06–0.11) † |
| chrF | 0.09 (0.07–0.12) † | 0.47 (0.43–0.51) † | 0.30 (0.24–0.36) † | 0.09 (0.07–0.12) † |
| BERTScore | 0.09 (0.06–0.12) † | 0.11 (0.09–0.14) † | 0.35 (0.28–0.43) † | 0.10 (0.08–0.12) † |
| RaTEScore | 0.17 (0.08–0.27) † | 0.47 (0.42–0.51) † | 0.48 (0.40–0.56) † | 0.28 (0.21–0.34) † |
| finding_f1 (upper bound) | 0.94 (0.85–1.00) † | 1.00 (1.00–1.00) † | 1.00 (1.00–1.00) † | 1.00 (1.00–1.00) † |
| judge sentence_f1 | 0.78 (0.65–0.90) † | 0.77 (0.72–0.83) † | 0.95 (0.92–0.97) † | 0.76 (0.67–0.83) † |
| judge_score | 0.84 (0.72–0.95) † | 0.88 (0.83–0.93) † | 1.00 (0.99–1.00) † | 0.82 (0.74–0.90) † |

## Breast (n = 9)

| scorer | human rewording | template small | template matched | template large |
|---|---|---|---|---|
| BLEU | 0.12 (0.09–0.13) † | 0.42 (0.30–0.52) † | 0.75 (0.71–0.79) † | 0.12 (0.09–0.13) † |
| ROUGE-L | 0.12 (0.09–0.15) † | 0.13 (0.09–0.15) † | 0.66 (0.63–0.68) † | 0.12 (0.09–0.13) † |
| chrF | 0.12 (0.09–0.13) † | 0.45 (0.35–0.53) † | 0.39 (0.30–0.46) † | 0.12 (0.09–0.13) † |
| BERTScore | 0.12 (0.09–0.13) † | 0.13 (0.12–0.13) † | 0.39 (0.35–0.45) † | 0.12 (0.09–0.13) † |
| RaTEScore | 0.37 (0.14–0.60) † | 0.44 (0.33–0.52) † | 0.59 (0.53–0.66) † | 0.37 (0.24–0.48) † |
| finding_f1 (upper bound) | 0.81 (0.52–1.00) † | 1.00 (1.00–1.00) † | 1.00 (1.00–1.00) † | 1.00 (1.00–1.00) † |
| judge sentence_f1 | 0.81 (0.63–0.95) † | 0.59 (0.56–0.64) † | 0.91 (0.85–0.96) † | 0.80 (0.67–0.90) † |
| judge_score | 0.92 (0.80–1.00) † | 0.83 (0.70–0.95) † | 0.99 (0.98–1.00) † | 0.86 (0.72–0.98) † |

## Thyroid (n = 10)

| scorer | human rewording | template small | template matched | template large |
|---|---|---|---|---|
| BLEU | 0.14 (0.10–0.17) † | 0.52 (0.47–0.57) † | 0.74 (0.66–0.81) † | 0.14 (0.10–0.17) † |
| ROUGE-L | 0.17 (0.15–0.19) † | 0.14 (0.10–0.17) † | 0.70 (0.66–0.73) † | 0.14 (0.10–0.17) † |
| chrF | 0.17 (0.15–0.19) † | 0.52 (0.47–0.57) † | 0.42 (0.35–0.47) † | 0.14 (0.10–0.17) † |
| BERTScore | 0.15 (0.11–0.19) † | 0.15 (0.11–0.17) † | 0.57 (0.52–0.62) † | 0.14 (0.10–0.17) † |
| RaTEScore | 0.12 (0.03–0.23) † | 0.51 (0.44–0.58) † | 0.60 (0.56–0.62) † | 0.36 (0.32–0.39) † |
| finding_f1 (upper bound) | 1.00 (1.00–1.00) † | 1.00 (1.00–1.00) † | 1.00 (1.00–1.00) † | 1.00 (1.00–1.00) † |
| judge sentence_f1 | 0.83 (0.62–0.97) † | 0.85 (0.74–0.95) † | 0.93 (0.88–0.97) † | 0.72 (0.59–0.84) † |
| judge_score | 0.89 (0.74–1.00) † | 0.92 (0.83–0.97) † | 1.00 (1.00–1.00) † | 0.86 (0.72–0.96) † |

## Fetal head (n = 10)

| scorer | human rewording | template small | template matched | template large |
|---|---|---|---|---|
| BLEU | 0.00 (0.00–0.00) † | 0.35 (0.34–0.36) † | 0.53 (0.51–0.54) † | 0.00 (0.00–0.00) † |
| ROUGE-L | 0.10 (0.00–0.30) † | 0.17 (0.17–0.17) † | 0.50 (0.50–0.50) † | 0.00 (0.00–0.00) † |
| chrF | 0.00 (0.00–0.00) † | 0.44 (0.37–0.51) † | 0.10 (0.04–0.16) † | 0.03 (0.01–0.06) † |
| BERTScore | 0.00 (0.00–0.00) † | 0.07 (0.03–0.11) † | 0.10 (0.04–0.16) † | 0.05 (0.02–0.08) † |
| RaTEScore | 0.05 (0.00–0.15) † | 0.45 (0.39–0.53) † | 0.26 (0.14–0.40) † | 0.11 (0.02–0.22) † |
| finding_f1 (upper bound) | 1.00 (1.00–1.00) † | 1.00 (1.00–1.00) † | 1.00 (1.00–1.00) † | 1.00 (1.00–1.00) † |
| judge sentence_f1 | 0.70 (0.40–1.00) † | 0.86 (0.84–0.87) † | 1.00 (1.00–1.00) † | 0.75 (0.60–0.90) † |
| judge_score | 0.70 (0.40–1.00) † | 0.90 (0.87–0.92) † | 1.00 (1.00–1.00) † | 0.75 (0.60–0.90) † |

† too small to compare (fewer than 30 groups).

## Reading

- Word-overlap scorers rank the human rewordings like the project's own large rewrites, not like small ones: AUROC against human rewordings is 0.08 (BLEU), 0.13 (ROUGE-L), 0.09 (chrF), 0.09 (BERTScore), 0.17 (RaTEScore) over all organs, i.e. errors score HIGHER than a correct human rewording most of the time.
- The judge keeps separating errors from human rewordings: judge_score 0.84, sentence_f1 0.78; finding_f1 0.94 (upper bound: it reads the same template vocabulary, and a few free rewordings lose facts to its extractor).
- 29 items, one writer per sheet, 30 references only: this is a spot-check that the template rewordings are not unusually easy for the judge, not a replacement for a clinician-written set.
