# Step 19 — Routing table: which layer wins for which kind of mistake (saved TEST results, no new model runs)

**Not a combined scorer.** This only reads existing test results (bench_v2d scorers, Steps 10d + 12 judge, Step 16 image check) and shows, per dataset and error category, how each scorer does. Nothing was retrained, tuned or re-run. See `docs/LIMITATIONS.md`.

## Headline (plain words)
- **22 of the 43 dataset × category cells have 30 or more cases; the other 21 are "too small to compare" and get no winner.** (Test judge sample: 59 cases per dataset, 2 error categories per case.)
- **In the 22 comparable cells the AI judge (Layer 2) has the highest score in 20; a word-overlap scorer (BLEU) wins 2** (missed finding on TN3K and TN5000, where it ties with the judge: the missing sentence is a big edit, so edit-size scorers look good there, consistent with the edit-size finding).
- **The judge is clearly above every word-overlap scorer in 18 of the 22 cells** (CIs do not overlap); it is not clearly better than the best word scorer in the 2 BLEU cells and in TN3K "wrong severity/category" (RaTEScore).
- **Where the judge is weakest (point estimate below 0.90):** BrEaST (false finding 0.81, wrong severity/category 0.84), UDIAT (wrong measurement 0.81, wrong severity/category 0.88), DDTI (0.85–0.86), BUS-BRA (0.86), HC18 wrong measurement 0.87. So breast and DDTI are where a second check would add the most.
- **`finding_f1` is 1.00 everywhere but is an upper bound on templated text and is never named a winner.**
- **The predicted-mask image check (MedSAM boxes handed from the TRUE masks, Step 16)** is far above every text scorer for wrong location and wrong size on breast and thyroid (0.69–1.00; DDTI size 0.69 is its weakest) but only 0.46 and 0.50 on fetal head. Different scans from the judge sample, so read it next to the table, not against it. Position cells have n < 30 everywhere (too small to compare).
- **The judge's two scores disagree on size errors:** `sentence_f1` is 0.30–0.56 on BrEaST/BUSI/DDTI size errors while `judge_score` is 0.75–0.99; the winner column picks the higher of the two, so it is a little optimistic (best-of-7 scorers, 2 of them the same judge call).

## How to read
AUROC = chance a planted error of that category scores lower than a harmless rewording of the same case (1 = always, 0.5 = chance). Harmless set = small + matched + large rewordings. All scorers in a cell are evaluated on the same cases (those the judge saw for that category). 95% CIs resample patient/exam groups (1,000, seed 0).

# Full tables

Per dataset and error category: AUROC (planted errors of that category vs harmless rewordings of the same case; 95% CI, group bootstrap), for the cases the Gemma judge saw in Steps 10d + 12 (every scorer on the same cases). **n < 30 cases: too small to compare** (no winner is named). "Winner" = highest point estimate among scorers; if another layer's CI overlaps it, that is said. This is a description of where each layer works, **not** a combined scorer. `finding_f1` is an **upper bound on templated text** (it reads the template that wrote the reference), so it is shown but never named winner; the winner is the best of the other scorers (best-of-7, so its point estimate is optimistic). The two judge columns are two scores of the same judge call.

## BUS-BRA

| error category | n cases | bleu | rougeL | chrf | bertscore[roberta-large] | ratescore | finding_f1 | sentence_f1 | judge_score | winner |
|---|---|---|---|---|---|---|---|---|---|---|
| false finding † | 12 | 0.50 (0.42–0.58) | 0.33 (0.33–0.33) | 0.31 (0.17–0.44) | 0.33 (0.33–0.33) | 0.36 (0.25–0.47) | 1.00 (1.00–1.00) | 0.83 (0.75–0.92) | 0.89 (0.81–0.96) | too small to compare |
| missed finding † | 15 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.96 (0.92–0.99) | too small to compare |
| wrong location † | 16 | 0.26 (0.22–0.29) | 0.17 (0.17–0.18) | 0.23 (0.12–0.34) | 0.00 (0.00–0.00) | 0.28 (0.19–0.37) | 1.00 (1.00–1.00) | 0.87 (0.81–0.93) | 0.92 (0.87–0.98) | too small to compare |
| wrong severity/category | 43 | 0.27 (0.23–0.31) | 0.22 (0.20–0.24) | 0.26 (0.18–0.34) | 0.17 (0.12–0.22) | 0.42 (0.33–0.51) | 1.00 (1.00–1.00) | 0.86 (0.82–0.90) | 0.86 (0.81–0.90) | sentence_f1 (L2) 0.86; CI separate from every other layer |
| wrong measurement | 36 | 0.21 (0.19–0.23) | 0.17 (0.17–0.17) | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | 0.44 (0.38–0.50) | 1.00 (1.00–1.00) | 0.75 (0.66–0.82) | 0.86 (0.81–0.91) | judge_score (L2) 0.86; CI separate from every other layer |

## BUS-UCLM

| error category | n cases | bleu | rougeL | chrf | bertscore[roberta-large] | ratescore | finding_f1 | sentence_f1 | judge_score | winner |
|---|---|---|---|---|---|---|---|---|---|---|
| false finding | 120 | 0.99 (0.97–1.00) | 0.98 (0.96–1.00) | 0.98 (0.95–1.00) | 0.98 (0.96–1.00) | 0.98 (0.96–1.00) | 1.00 (1.00–1.00) | 1.00 (0.99–1.00) | 1.00 (1.00–1.00) | judge_score (L2) 1.00; CI separate from every other layer |
| missed finding † | 10 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.98 (0.94–1.00) | 0.98 (0.94–1.00) | too small to compare |
| wrong location † | 8 | 0.52 (0.25–0.62) | 0.17 (0.17–0.17) | 0.50 (0.17–0.62) | 0.00 (0.00–0.00) | 0.12 (0.07–0.17) | 1.00 (1.00–1.00) | 0.90 (0.86–1.00) | 1.00 (1.00–1.00) | too small to compare |
| wrong severity/category † | 12 | 0.37 (0.32–0.45) | 0.26 (0.20–0.29) | 0.49 (0.41–0.65) | 0.32 (0.28–0.37) | 0.63 (0.54–0.75) | 1.00 (1.00–1.00) | 0.93 (0.74–1.00) | 0.97 (0.88–1.00) | too small to compare |
| wrong measurement † | 19 | 0.46 (0.37–0.55) | 0.17 (0.17–0.18) | 0.20 (0.10–0.29) | 0.00 (0.00–0.00) | 0.43 (0.32–0.53) | 1.00 (1.00–1.00) | 0.52 (0.37–0.69) | 0.96 (0.89–1.00) | too small to compare |

## BUSI

| error category | n cases | bleu | rougeL | chrf | bertscore[roberta-large] | ratescore | finding_f1 | sentence_f1 | judge_score | winner |
|---|---|---|---|---|---|---|---|---|---|---|
| false finding | 46 | 0.76 (0.68–0.83) | 0.69 (0.59–0.78) | 0.67 (0.55–0.78) | 0.69 (0.59–0.78) | 0.78 (0.70–0.85) | 1.00 (1.00–1.00) | 0.94 (0.91–0.97) | 1.00 (1.00–1.00) | judge_score (L2) 1.00; CI separate from every other layer |
| missed finding † | 17 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | too small to compare |
| wrong location † | 11 | 0.56 (0.48–0.63) | 0.17 (0.17–0.17) | 0.52 (0.42–0.61) | 0.00 (0.00–0.00) | 0.17 (0.11–0.23) | 1.00 (1.00–1.00) | 0.86 (0.78–0.93) | 0.97 (0.91–1.00) | too small to compare |
| wrong severity/category † | 29 | 0.42 (0.35–0.50) | 0.32 (0.28–0.37) | 0.48 (0.42–0.54) | 0.21 (0.16–0.26) | 0.52 (0.44–0.61) | 1.00 (1.00–1.00) | 0.87 (0.82–0.91) | 1.00 (1.00–1.00) | too small to compare |
| wrong measurement | 43 | 0.41 (0.35–0.46) | 0.16 (0.16–0.17) | 0.16 (0.12–0.21) | 0.00 (0.00–0.00) | 0.48 (0.41–0.54) | 1.00 (1.00–1.00) | 0.56 (0.49–0.63) | 0.99 (0.98–1.00) | judge_score (L2) 0.99; CI separate from every other layer |

## BrEaST

| error category | n cases | bleu | rougeL | chrf | bertscore[roberta-large] | ratescore | finding_f1 | sentence_f1 | judge_score | winner |
|---|---|---|---|---|---|---|---|---|---|---|
| false finding | 30 | 0.52 (0.43–0.61) | 0.35 (0.28–0.43) | 0.29 (0.20–0.38) | 0.40 (0.32–0.48) | 0.47 (0.37–0.57) | 1.00 (1.00–1.00) | 0.77 (0.69–0.84) | 0.81 (0.73–0.87) | judge_score (L2) 0.81; CI separate from every other layer |
| missed finding † | 16 | 0.69 (0.50–0.86) | 0.67 (0.47–0.85) | 0.62 (0.40–0.83) | 0.67 (0.48–0.85) | 0.64 (0.42–0.83) | 1.00 (1.00–1.00) | 0.93 (0.83–0.99) | 0.89 (0.80–0.95) | too small to compare |
| wrong location † | 5 | 0.17 (0.17–0.17) | 0.17 (0.17–0.17) | 0.27 (0.13–0.33) | 0.07 (0.00–0.20) | 0.10 (0.03–0.17) | 1.00 (1.00–1.00) | 0.90 (0.77–1.00) | 0.90 (0.83–0.97) | too small to compare |
| wrong severity/category | 44 | 0.28 (0.22–0.35) | 0.19 (0.16–0.23) | 0.20 (0.13–0.28) | 0.30 (0.23–0.36) | 0.36 (0.29–0.44) | 1.00 (1.00–1.00) | 0.84 (0.78–0.89) | 0.75 (0.68–0.82) | sentence_f1 (L2) 0.84; CI separate from every other layer |
| wrong measurement † | 25 | 0.17 (0.13–0.21) | 0.14 (0.12–0.16) | 0.00 (0.00–0.00) | 0.03 (0.00–0.07) | 0.35 (0.25–0.44) | 1.00 (1.00–1.00) | 0.30 (0.27–0.33) | 0.75 (0.68–0.82) | too small to compare |

## DDTI

| error category | n cases | bleu | rougeL | chrf | bertscore[roberta-large] | ratescore | finding_f1 | sentence_f1 | judge_score | winner |
|---|---|---|---|---|---|---|---|---|---|---|
| false finding † | 19 | 0.45 (0.39–0.51) | 0.38 (0.29–0.49) | 0.45 (0.36–0.54) | 0.37 (0.32–0.42) | 0.56 (0.43–0.69) | 1.00 (1.00–1.00) | 0.94 (0.88–0.98) | 1.00 (1.00–1.00) | too small to compare |
| missed finding † | 19 | 0.79 (0.67–0.89) | 0.61 (0.39–0.78) | 0.79 (0.67–0.89) | 0.70 (0.56–0.86) | 0.72 (0.58–0.86) | 1.00 (1.00–1.00) | 0.91 (0.85–0.96) | 1.00 (1.00–1.00) | too small to compare |
| wrong location † | 9 | 0.35 (0.25–0.44) | 0.16 (0.16–0.17) | 0.16 (0.08–0.25) | 0.07 (0.00–0.19) | 0.22 (0.07–0.42) | 1.00 (1.00–1.00) | 0.91 (0.81–0.98) | 1.00 (1.00–1.00) | too small to compare |
| wrong severity/category | 47 | 0.32 (0.24–0.40) | 0.23 (0.21–0.26) | 0.27 (0.19–0.35) | 0.22 (0.17–0.26) | 0.52 (0.42–0.62) | 1.00 (1.00–1.00) | 0.84 (0.79–0.89) | 0.86 (0.78–0.92) | judge_score (L2) 0.86; CI separate from every other layer |
| wrong measurement | 41 | 0.35 (0.30–0.41) | 0.17 (0.16–0.18) | 0.13 (0.08–0.18) | 0.07 (0.03–0.11) | 0.18 (0.13–0.24) | 1.00 (1.00–1.00) | 0.55 (0.45–0.66) | 0.85 (0.78–0.91) | judge_score (L2) 0.85; CI separate from every other layer |

## FetalHead

| error category | n cases | bleu | rougeL | chrf | bertscore[roberta-large] | ratescore | finding_f1 | sentence_f1 | judge_score | winner |
|---|---|---|---|---|---|---|---|---|---|---|
| wrong severity/category | 79 | 0.47 (0.43–0.51) | 0.28 (0.25–0.30) | 0.81 (0.78–0.85) | 0.76 (0.72–0.81) | 0.46 (0.40–0.51) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.94 (0.91–0.96) | sentence_f1 (L2) 1.00; CI separate from every other layer |
| wrong measurement | 77 | 0.27 (0.20–0.32) | 0.26 (0.25–0.28) | 0.13 (0.10–0.17) | 0.00 (0.00–0.00) | 0.31 (0.25–0.37) | 1.00 (1.00–1.00) | 0.97 (0.95–0.98) | 0.99 (0.98–1.00) | judge_score (L2) 0.99; CI separate from every other layer |

## HC18

| error category | n cases | bleu | rougeL | chrf | bertscore[roberta-large] | ratescore | finding_f1 | sentence_f1 | judge_score | winner |
|---|---|---|---|---|---|---|---|---|---|---|
| wrong measurement | 63 | 0.26 (0.21–0.31) | 0.25 (0.24–0.27) | 0.10 (0.07–0.13) | 0.00 (0.00–0.00) | 0.22 (0.15–0.28) | 1.00 (1.00–1.00) | 0.84 (0.79–0.88) | 0.87 (0.83–0.91) | judge_score (L2) 0.87; CI separate from every other layer |

## TN3K

| error category | n cases | bleu | rougeL | chrf | bertscore[roberta-large] | ratescore | finding_f1 | sentence_f1 | judge_score | winner |
|---|---|---|---|---|---|---|---|---|---|---|
| false finding | 32 | 0.54 (0.48–0.58) | 0.35 (0.33–0.37) | 0.54 (0.48–0.58) | 0.35 (0.33–0.37) | 0.70 (0.59–0.81) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | sentence_f1 (L2) 1.00; CI separate from every other layer |
| missed finding | 31 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | bleu (L0) 1.00; not clearly better than judge_score, sentence_f1 |
| wrong location † | 16 | 0.42 (0.35–0.48) | 0.17 (0.16–0.17) | 0.18 (0.11–0.25) | 0.02 (0.00–0.06) | 0.28 (0.18–0.39) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | too small to compare |
| wrong severity/category | 39 | 0.48 (0.44–0.53) | 0.33 (0.32–0.35) | 0.48 (0.44–0.53) | 0.33 (0.32–0.35) | 0.97 (0.92–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (0.99–1.00) | sentence_f1 (L2) 1.00; not clearly better than ratescore |
| wrong measurement | 69 | 0.39 (0.35–0.43) | 0.17 (0.17–0.18) | 0.17 (0.14–0.20) | 0.09 (0.07–0.13) | 0.20 (0.17–0.23) | 1.00 (1.00–1.00) | 0.92 (0.89–0.94) | 1.00 (1.00–1.00) | judge_score (L2) 1.00; CI separate from every other layer |

## TN5000

| error category | n cases | bleu | rougeL | chrf | bertscore[roberta-large] | ratescore | finding_f1 | sentence_f1 | judge_score | winner |
|---|---|---|---|---|---|---|---|---|---|---|
| false finding | 53 | 0.55 (0.52–0.58) | 0.36 (0.34–0.37) | 0.55 (0.52–0.58) | 0.36 (0.34–0.37) | 0.66 (0.59–0.72) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | sentence_f1 (L2) 1.00; CI separate from every other layer |
| missed finding | 49 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | bleu (L0) 1.00; not clearly better than judge_score, sentence_f1 |
| wrong location † | 13 | 0.43 (0.34–0.53) | 0.16 (0.15–0.17) | 0.21 (0.13–0.28) | 0.05 (0.00–0.13) | 0.14 (0.09–0.20) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | too small to compare |
| wrong severity/category | 51 | 0.50 (0.46–0.53) | 0.35 (0.33–0.36) | 0.50 (0.46–0.53) | 0.35 (0.33–0.36) | 0.96 (0.93–0.99) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.97 (0.94–0.99) | sentence_f1 (L2) 1.00; CI separate from every other layer |
| wrong measurement | 80 | 0.40 (0.37–0.44) | 0.17 (0.17–0.18) | 0.16 (0.14–0.19) | 0.06 (0.03–0.09) | 0.19 (0.16–0.21) | 1.00 (1.00–1.00) | 0.89 (0.87–0.92) | 1.00 (1.00–1.00) | judge_score (L2) 1.00; CI separate from every other layer |

## UDIAT

| error category | n cases | bleu | rougeL | chrf | bertscore[roberta-large] | ratescore | finding_f1 | sentence_f1 | judge_score | winner |
|---|---|---|---|---|---|---|---|---|---|---|
| false finding † | 21 | 0.53 (0.47–0.60) | 0.34 (0.33–0.35) | 0.34 (0.27–0.40) | 0.34 (0.33–0.35) | 0.53 (0.40–0.66) | 1.00 (1.00–1.00) | 0.81 (0.74–0.87) | 0.98 (0.95–1.00) | too small to compare |
| missed finding † | 19 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.99 (0.97–1.00) | too small to compare |
| wrong location † | 15 | 0.42 (0.34–0.49) | 0.17 (0.17–0.18) | 0.32 (0.23–0.40) | 0.00 (0.00–0.00) | 0.18 (0.13–0.24) | 1.00 (1.00–1.00) | 0.91 (0.87–0.94) | 0.93 (0.89–0.97) | too small to compare |
| wrong severity/category | 39 | 0.34 (0.27–0.41) | 0.22 (0.19–0.24) | 0.37 (0.29–0.45) | 0.30 (0.27–0.33) | 0.64 (0.57–0.71) | 1.00 (1.00–1.00) | 0.88 (0.84–0.92) | 0.81 (0.75–0.86) | sentence_f1 (L2) 0.88; CI separate from every other layer |
| wrong measurement | 34 | 0.42 (0.36–0.48) | 0.17 (0.17–0.17) | 0.17 (0.11–0.22) | 0.00 (0.00–0.00) | 0.63 (0.53–0.71) | 1.00 (1.00–1.00) | 0.59 (0.51–0.66) | 0.81 (0.74–0.87) | judge_score (L2) 0.81; CI separate from every other layer |

## Image check (Step 16: MedSAM masks from TRUE boxes) on position and size errors

Different case sample from the judge (30 scans per dataset, Step 16), so read it next to, not against, the table above. † n < 30: too small to compare.

| dataset | error category | n cases | mvf_exact (predicted masks) | BLEU | ROUGE-L | chrF | BERTScore | RaTEScore |
|---|---|---|---|---|---|---|---|---|
| BrEaST | wrong location † | 17 | 0.97 (0.91–1.00) | 0.20 (0.20–0.20) | 0.17 (0.17–0.17) | 0.13 (0.13–0.13) | 0.09 (0.08–0.11) | 0.20 (0.19–0.20) |
| BrEaST | wrong measurement | 30 | 0.88 (0.78–0.96) | 0.20 (0.20–0.20) | 0.17 (0.17–0.17) | 0.00 (0.00–0.00) | 0.04 (0.02–0.05) | 0.60 (0.58–0.61) |
| BUS-BRA | wrong location † | 17 | 0.94 (0.85–1.00) | 0.20 (0.20–0.20) | 0.15 (0.15–0.15) | 0.10 (0.10–0.10) | 0.00 (0.00–0.00) | 0.30 (0.28–0.32) |
| BUS-BRA | wrong measurement | 30 | 0.83 (0.73–0.91) | 0.20 (0.20–0.20) | 0.15 (0.15–0.15) | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | 0.61 (0.60–0.62) |
| BUSI | wrong location † | 19 | 0.92 (0.84–1.00) | 0.28 (0.28–0.28) | 0.11 (0.11–0.11) | 0.22 (0.22–0.22) | 0.00 (0.00–0.00) | 0.27 (0.26–0.28) |
| BUSI | wrong measurement | 30 | 0.93 (0.84–1.00) | 0.28 (0.28–0.28) | 0.11 (0.11–0.11) | 0.11 (0.11–0.11) | 0.00 (0.00–0.00) | 0.69 (0.67–0.71) |
| UDIAT | wrong location † | 23 | 1.00 (1.00–1.00) | 0.28 (0.28–0.28) | 0.11 (0.11–0.11) | 0.23 (0.22–0.25) | 0.00 (0.00–0.00) | 0.27 (0.26–0.28) |
| UDIAT | wrong measurement | 30 | 0.98 (0.95–1.00) | 0.28 (0.28–0.28) | 0.11 (0.11–0.11) | 0.10 (0.09–0.11) | 0.00 (0.00–0.00) | 0.70 (0.69–0.71) |
| BUS-UCLM | wrong location † | 8 | 1.00 (1.00–1.00) | 0.28 (0.28–0.28) | 0.11 (0.11–0.11) | 0.23 (0.22–0.24) | 0.00 (0.00–0.00) | 0.27 (0.26–0.28) |
| BUS-UCLM | wrong measurement † | 18 | 0.91 (0.76–1.00) | 0.28 (0.28–0.28) | 0.11 (0.11–0.11) | 0.10 (0.09–0.11) | 0.00 (0.00–0.00) | 0.66 (0.63–0.71) |
| TN3K | wrong location † | 17 | 0.94 (0.85–1.00) | 0.30 (0.29–0.30) | 0.15 (0.15–0.15) | 0.12 (0.10–0.14) | 0.05 (0.03–0.07) | 0.31 (0.26–0.37) |
| TN3K | wrong measurement | 30 | 0.84 (0.74–0.92) | 0.30 (0.29–0.30) | 0.15 (0.15–0.15) | 0.10 (0.10–0.10) | 0.08 (0.07–0.09) | 0.30 (0.29–0.32) |
| DDTI | wrong location † | 16 | 0.84 (0.72–0.97) | 0.31 (0.31–0.32) | 0.17 (0.16–0.18) | 0.11 (0.09–0.13) | 0.05 (0.02–0.07) | 0.34 (0.29–0.41) |
| DDTI | wrong measurement | 30 | 0.69 (0.59–0.80) | 0.31 (0.31–0.32) | 0.17 (0.17–0.18) | 0.09 (0.08–0.09) | 0.06 (0.05–0.07) | 0.32 (0.29–0.35) |
| TN5000 | wrong location † | 17 | 0.97 (0.91–1.00) | 0.30 (0.30–0.30) | 0.15 (0.15–0.15) | 0.12 (0.11–0.14) | 0.04 (0.02–0.07) | 0.30 (0.25–0.35) |
| TN5000 | wrong measurement | 30 | 0.82 (0.72–0.89) | 0.30 (0.30–0.30) | 0.15 (0.15–0.15) | 0.10 (0.10–0.10) | 0.04 (0.02–0.05) | 0.32 (0.29–0.36) |
| HC18 | wrong measurement | 30 | 0.46 (0.43–0.49) | 0.20 (0.20–0.20) | 0.15 (0.15–0.15) | 0.10 (0.10–0.10) | 0.00 (0.00–0.00) | 0.44 (0.42–0.46) |
| FetalHead | wrong measurement | 30 | 0.50 (0.48–0.52) | 0.20 (0.20–0.20) | 0.15 (0.15–0.15) | 0.12 (0.12–0.13) | 0.00 (0.00–0.00) | 0.54 (0.51–0.57) |
