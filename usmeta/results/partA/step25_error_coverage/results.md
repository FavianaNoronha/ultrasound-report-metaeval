# Step 25 — Error-type coverage (test split)

## Headline
- **Coverage:** the planted set covers laterality (breast only, 130 candidates, 65 groups), measurement, category and negation (finding present / absent, including "No focal lesion is seen."); count and position errors form `other`. **It has no omission type**, so 2,087 omission candidates were built from 1,394 test references (one non-first sentence dropped per candidate: mostly the pathology, assessment, histology or "wider than tall" sentence; fetal head loses its head-circumference sentence). Several dropped sentences are labels (pathology / assessment) rather than imaging findings, so "omission" here means "a stated item dropped while the rest stays".
- **Omission is poorly detected by the word scorers, except in the very short fetal-head reports.** AUROC vs harmless rewordings (breast / thyroid / fetal head): BLEU 0.57 / 0.60 / 0.93, ROUGE-L 0.41 / 0.46 / 0.93, chrF 0.67 / 0.63 / 0.93, BERTScore 0.46 / 0.50 / 0.80, RaTEScore 0.33 / 0.66 / 0.78; strict preference is lower still (breast RaTEScore 0.19: a report with a dropped finding scores ABOVE a harmless rewording in 4 of 5 pairs). The fetal head numbers are high because the dropped sentence is half of a two-sentence report, a big relative change. finding_f1 detects omission at 1.00 (upper bound; it reads the same templated vocabulary). The saved judge has no scores for the built candidates, so there is no judge number for omission.
- **Negation scores well on word scorers (breast 0.92-0.95, thyroid 0.91-0.95) but for the wrong reason:** most negation candidates replace the whole report by "No focal lesion is seen.", a 40%+ edit that shares few words with the reference (Step 21e).
- **Laterality, measurement and category are where the word scorers fail:** strict preference for laterality 0.00-0.43 (breast), measurement 0.00-0.49 (all organs), category 0.15-0.46 (breast), 0.36-0.77 (thyroid; RaTEScore 0.77) and 0.01-0.79 (fetal head; chrF 0.79, BERTScore 0.71) (BERTScore and ROUGE-L at 0.00-0.01 for laterality and measurement). The judge: judge_score measurement 0.87 / 0.97 / 0.93, category 0.84 / 0.94 / 0.94 (breast / thyroid / fetal head), negation 0.97-1.00; laterality is too small to compare (10 groups).
- **Looks off / limits:** `finding_f1` is 1.00 for every error group (templated upper bound). "Omission" candidates for thyroid and fetal head are mostly very short references. Judge columns cover only the judged subset; judge sentence_f1 is weak on breast measurement (AUROC 0.56, strict 0.34).

Questions: (1) which planted error types exist and how do they map onto laterality / measurement / category / negation / omission / other; (2) omission is not a planted type, so it was built and scored; (3) how do the scorers do on each group, same method as Step 19a (error x harmless small / matched / large pairs per case, group bootstrap 1,000, seed 0; under 30 groups: too small to compare). Code: `usmeta/step25_error_coverage.py`; omission candidates: `omission_bench.jsonl`; their scores: `scores_layer0.json`, `scores_layer1.json`.

## 1. Planted error types per organ and their mapping (test candidates and reference cases)

| organ | planted type (category / field) | group | candidates | cases |
|---|---|---|---|---|
| breast | false finding / calc | negation | 87 | 87 |
| breast | false finding / count | other | 491 | 491 |
| breast | false finding / halo | negation | 74 | 74 |
| breast | false finding / lesion | negation | 144 | 144 |
| breast | missed finding / calc | negation | 14 | 14 |
| breast | missed finding / halo | negation | 27 | 27 |
| breast | missed finding / lesion | negation | 502 | 502 |
| breast | wrong location / pos | other | 312 | 282 |
| breast | wrong location / side | laterality | 130 | 130 |
| breast | wrong measurement / size_mm | measurement | 303 | 101 |
| breast | wrong measurement / size_pct | measurement | 1203 | 401 |
| breast | wrong severity/category / birads | category | 541 | 196 |
| breast | wrong severity/category / echo | category | 53 | 53 |
| breast | wrong severity/category / hist | category | 216 | 216 |
| breast | wrong severity/category / margin | category | 101 | 101 |
| breast | wrong severity/category / orient | category | 502 | 502 |
| breast | wrong severity/category / path | category | 502 | 502 |
| breast | wrong severity/category / post | category | 39 | 39 |
| breast | wrong severity/category / shape | category | 101 | 101 |
| fetal head | wrong measurement / hc_mm | measurement | 1200 | 300 |
| fetal head | wrong severity/category / plane | category | 153 | 153 |
| thyroid | false finding / count | other | 385 | 385 |
| thyroid | false finding / foci | negation | 41 | 41 |
| thyroid | false finding / lesion | negation | 2 | 2 |
| thyroid | missed finding / foci | negation | 71 | 71 |
| thyroid | missed finding / lesion | negation | 448 | 448 |
| thyroid | wrong location / pos | other | 262 | 212 |
| thyroid | wrong measurement / size_pct | measurement | 1342 | 448 |
| thyroid | wrong severity/category / comp | category | 67 | 67 |
| thyroid | wrong severity/category / echo | category | 67 | 67 |
| thyroid | wrong severity/category / margin | category | 110 | 110 |
| thyroid | wrong severity/category / orient | category | 448 | 448 |
| thyroid | wrong severity/category / tirads | category | 357 | 112 |

| group | what it contains |
|---|---|
| laterality | wrong side (left / right breast) |
| measurement | wrong size (mm, % of image width) or head circumference |
| category | wrong BI-RADS / TI-RADS / pathology / histology / margin / echo / shape / composition / posterior features / orientation / fetal plane |
| negation | a finding stated present when absent or absent when present ("No focal lesion is seen", calcifications, halo, foci) |
| omission | a stated finding sentence dropped, the others stay (BUILT here) |
| other | lesion count and position in the image (not in the six requested groups) |

**Coverage gaps:** `omission` is not a planted type (the "missed finding" candidates either replace the whole report with "No focal lesion is seen." or flip one finding to "no X"; both are negation, not omission); the planted set has no candidate that simply drops a stated finding. Position and count errors sit in `other`.

## 2. Built omission candidates

2087 candidates from 1394 of 1,399 test references (references with at least two sentences; one sentence other than the first dropped per candidate): breast: 1227, thyroid: 560, fetal head: 300. Dropped sentences, by first words: "Pathology: benign." 317, "Head circumference" 300, "Wider than" 280, "Assessment: BI-RADS" 251, "Pathology: malignant." 185, "Pathology: normal." 144, "Assessment: TI-RADS" 112, "Histology: invasive" 61. The saved judge has no scores for them.

## 3. Paired preference accuracy (share of error x harmless pairs where the error scores LOWER; ties not preferred)

### breast

| scorer | laterality | measurement | category | negation | omission | other |
|---|---|---|---|---|---|---|
| BLEU | 0.14 (0.14–0.14) | 0.23 (0.21–0.24) | 0.29 (0.28–0.30) | 0.94 (0.92–0.95) | 0.57 (0.57–0.58) | 0.47 (0.46–0.49) |
| ROUGE-L | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | 0.15 (0.14–0.15) | 0.92 (0.90–0.94) | 0.41 (0.40–0.41) | 0.29 (0.27–0.31) |
| chrF | 0.21 (0.21–0.21) | 0.08 (0.07–0.09) | 0.36 (0.34–0.37) | 0.92 (0.89–0.94) | 0.67 (0.63–0.70) | 0.28 (0.27–0.29) |
| BERTScore | 0.00 (0.00–0.00) | 0.01 (0.01–0.01) | 0.26 (0.25–0.27) | 0.94 (0.93–0.96) | 0.46 (0.44–0.47) | 0.30 (0.28–0.31) |
| RaTEScore | 0.43 (0.43–0.43) | 0.49 (0.49–0.50) | 0.46 (0.45–0.47) | 0.93 (0.92–0.95) | 0.19 (0.16–0.22) | 0.36 (0.34–0.37) |
| finding_f1 (upper bound) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) |
| judge sentence_f1 | too small to compare (10 groups) | 0.34 (0.27–0.41) | 0.82 (0.79–0.85) | 0.98 (0.96–0.99) | — | 0.80 (0.77–0.84) |
| judge_score | too small to compare (10 groups) | 0.87 (0.84–0.90) | 0.84 (0.81–0.87) | 0.97 (0.95–0.98) | — | 0.91 (0.88–0.94) |

### thyroid

| scorer | laterality | measurement | category | negation | omission | other |
|---|---|---|---|---|---|---|
| BLEU | — | 0.28 (0.27–0.28) | 0.49 (0.47–0.50) | 0.95 (0.94–0.96) | 0.60 (0.60–0.61) | 0.49 (0.48–0.50) |
| ROUGE-L | — | 0.00 (0.00–0.00) | 0.36 (0.35–0.37) | 0.88 (0.85–0.90) | 0.46 (0.45–0.46) | 0.31 (0.29–0.32) |
| chrF | — | 0.14 (0.13–0.14) | 0.48 (0.46–0.50) | 0.95 (0.94–0.96) | 0.63 (0.62–0.64) | 0.42 (0.41–0.44) |
| BERTScore | — | 0.08 (0.08–0.09) | 0.39 (0.38–0.40) | 0.94 (0.93–0.95) | 0.50 (0.49–0.51) | 0.33 (0.31–0.34) |
| RaTEScore | — | 0.04 (0.03–0.05) | 0.77 (0.74–0.80) | 0.95 (0.94–0.96) | 0.63 (0.62–0.65) | 0.45 (0.43–0.47) |
| finding_f1 (upper bound) | — | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) |
| judge sentence_f1 | — | 0.71 (0.66–0.76) | 0.92 (0.89–0.95) | 0.96 (0.94–0.98) | — | 0.97 (0.95–0.99) |
| judge_score | — | 0.97 (0.95–0.98) | 0.92 (0.89–0.95) | 1.00 (1.00–1.00) | — | 1.00 (1.00–1.00) |

### fetal head

| scorer | laterality | measurement | category | negation | omission | other |
|---|---|---|---|---|---|---|
| BLEU | — | 0.29 (0.29–0.29) | 0.29 (0.29–0.30) | — | 0.93 (0.92–0.94) | — |
| ROUGE-L | — | 0.00 (0.00–0.00) | 0.01 (0.00–0.01) | — | 0.93 (0.92–0.94) | — |
| chrF | — | 0.16 (0.16–0.17) | 0.79 (0.78–0.80) | — | 0.93 (0.91–0.94) | — |
| BERTScore | — | 0.00 (0.00–0.00) | 0.71 (0.71–0.71) | — | 0.80 (0.79–0.81) | — |
| RaTEScore | — | 0.27 (0.25–0.28) | 0.48 (0.46–0.50) | — | 0.78 (0.76–0.80) | — |
| finding_f1 (upper bound) | — | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | — | 1.00 (1.00–1.00) | — |
| judge sentence_f1 | — | 0.87 (0.84–0.90) | 1.00 (1.00–1.00) | — | — | — |
| judge_score | — | 0.92 (0.90–0.94) | 0.94 (0.91–0.96) | — | — | — |

## 3. AUROC (= strict + 0.5 x tie share)

### breast

| scorer | laterality | measurement | category | negation | omission | other |
|---|---|---|---|---|---|---|
| BLEU | 0.29 (0.29–0.29) | 0.35 (0.34–0.36) | 0.35 (0.35–0.36) | 0.95 (0.93–0.96) | 0.57 (0.57–0.58) | 0.51 (0.50–0.52) |
| ROUGE-L | 0.21 (0.21–0.21) | 0.19 (0.19–0.20) | 0.28 (0.28–0.28) | 0.94 (0.92–0.95) | 0.41 (0.40–0.41) | 0.35 (0.34–0.36) |
| chrF | 0.21 (0.21–0.21) | 0.08 (0.07–0.09) | 0.36 (0.34–0.37) | 0.92 (0.89–0.94) | 0.67 (0.63–0.70) | 0.28 (0.27–0.29) |
| BERTScore | 0.00 (0.00–0.00) | 0.01 (0.01–0.01) | 0.26 (0.25–0.27) | 0.94 (0.93–0.96) | 0.46 (0.44–0.47) | 0.30 (0.28–0.31) |
| RaTEScore | 0.43 (0.43–0.43) | 0.49 (0.49–0.50) | 0.48 (0.47–0.49) | 0.94 (0.92–0.95) | 0.33 (0.31–0.34) | 0.41 (0.39–0.42) |
| finding_f1 (upper bound) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) |
| judge sentence_f1 | too small to compare (10 groups) | 0.56 (0.52–0.60) | 0.87 (0.84–0.89) | 0.99 (0.98–1.00) | — | 0.83 (0.80–0.86) |
| judge_score | too small to compare (10 groups) | 0.88 (0.85–0.91) | 0.85 (0.82–0.88) | 0.98 (0.97–0.99) | — | 0.93 (0.90–0.95) |

### thyroid

| scorer | laterality | measurement | category | negation | omission | other |
|---|---|---|---|---|---|---|
| BLEU | — | 0.43 (0.43–0.43) | 0.50 (0.49–0.51) | 0.95 (0.94–0.96) | 0.60 (0.60–0.61) | 0.54 (0.53–0.54) |
| ROUGE-L | — | 0.22 (0.22–0.22) | 0.40 (0.40–0.41) | 0.91 (0.89–0.93) | 0.46 (0.45–0.46) | 0.38 (0.37–0.39) |
| chrF | — | 0.14 (0.13–0.14) | 0.48 (0.46–0.50) | 0.95 (0.94–0.96) | 0.63 (0.62–0.64) | 0.42 (0.41–0.44) |
| BERTScore | — | 0.08 (0.08–0.09) | 0.39 (0.38–0.40) | 0.94 (0.93–0.95) | 0.50 (0.49–0.51) | 0.33 (0.31–0.34) |
| RaTEScore | — | 0.20 (0.20–0.21) | 0.79 (0.77–0.82) | 0.95 (0.94–0.96) | 0.66 (0.64–0.67) | 0.48 (0.46–0.50) |
| finding_f1 (upper bound) | — | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) |
| judge sentence_f1 | — | 0.83 (0.79–0.86) | 0.95 (0.92–0.97) | 0.98 (0.97–0.99) | — | 0.99 (0.97–0.99) |
| judge_score | — | 0.97 (0.95–0.98) | 0.94 (0.91–0.96) | 1.00 (1.00–1.00) | — | 1.00 (1.00–1.00) |

### fetal head

| scorer | laterality | measurement | category | negation | omission | other |
|---|---|---|---|---|---|---|
| BLEU | — | 0.29 (0.29–0.29) | 0.43 (0.43–0.44) | — | 0.93 (0.92–0.94) | — |
| ROUGE-L | — | 0.21 (0.21–0.21) | 0.22 (0.21–0.23) | — | 0.93 (0.92–0.94) | — |
| chrF | — | 0.16 (0.16–0.17) | 0.79 (0.78–0.80) | — | 0.93 (0.91–0.94) | — |
| BERTScore | — | 0.00 (0.00–0.00) | 0.71 (0.71–0.71) | — | 0.80 (0.79–0.81) | — |
| RaTEScore | — | 0.27 (0.25–0.28) | 0.48 (0.46–0.50) | — | 0.78 (0.76–0.80) | — |
| finding_f1 (upper bound) | — | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | — | 1.00 (1.00–1.00) | — |
| judge sentence_f1 | — | 0.91 (0.88–0.93) | 1.00 (1.00–1.00) | — | — | — |
| judge_score | — | 0.93 (0.91–0.95) | 0.94 (0.91–0.96) | — | — | — |

Cases / groups per cell (word scorers):

| organ | laterality | measurement | category | negation | omission | other |
|---|---|---|---|---|---|---|
| breast | 130 / 65 | 502 / 385 | 502 / 385 | 646 / 413 | 646 / 413 | 500 / 385 |
| thyroid | 0 / 0 | 448 / 415 | 448 / 415 | 450 / 417 | 448 / 415 | 441 / 409 |
| fetal head | 0 / 0 | 300 / 203 | 153 / 54 | 0 / 0 | 300 / 203 | 0 / 0 |

Judge columns use only candidates the saved judge scored (Steps 10d + 12 samples), so their groups are fewer; the omission column has no judge. `finding_f1` is the upper bound (it reads the same template vocabulary).
