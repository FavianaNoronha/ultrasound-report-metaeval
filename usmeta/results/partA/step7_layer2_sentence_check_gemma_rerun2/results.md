# Step 7 re-run 2: stricter judge prompt (identical copies must get 1.0)

**Why.** In the first Step 7 run the Gemma-2-9B `sentence_check` gave one identical copy on UDIAT `sentence_f1` 0.80 (mean 0.93 over 3 copies): it said a reference sentence ("Histology: fa.") was not covered by an identical candidate. A judge model cannot be forced to be exact, but a prompt can tell it what identical means.

**What changed.** Only the prompt (`usmeta/judge2.py`, `PROMPT`; the first one is kept as `PROMPT_V1`). The new prompt tells the judge: compare only what the reports say, not plausibility; a sentence that appears word for word in the other report is supported/covered; if the two reports are identical every value is true and errors is empty; list an error only when a fact differs. Same sample (995 rows, 925 pairs, 20 cases per dataset), same model (Gemma-2-9B-it 4-bit, MLX, greedy), same scoring. I first tested the prompt only on identical copies: **100 of 100 identical copies (10 per dataset, all 10 datasets, different cases from the 3 used before) scored exactly 1.0** (`check_identical_gate.py`), then re-ran the whole step.

**Wiring gate: now clean.** Identical-copy `sentence_f1` and `judge_score` = 1.00 on all 10 datasets (min 1.0). 0 unparseable replies (the first run had 3); 41 of 925 replies had a wrong-length true/false list (95 before). The judge now lists at least one error for 99.7% of planted errors (94% before); the planted category is named in 81% (80% before).

**But the prompt changed the AUROCs, which is itself a finding.** `sentence_f1` AUROC (first prompt -> stricter prompt), planted error vs harmless_small / vs matched one-word synonym / vs harmless_large:
- BUS-BRA: 0.91 -> 0.61 / 1.00 -> 0.95 / 1.00 -> 0.95; BUSI: 0.99 -> 0.66 / 0.99 -> 0.86 / 0.99 -> 0.86; UDIAT: 0.68 -> 0.50 / 0.99 -> 0.94 / 0.93 -> 0.75; BUS-UCLM 0.99 -> 0.88 on harmless_small.
- Unchanged or within a few hundredths: BrEaST (0.85 -> 0.86 / 0.95 -> 0.94), TN3K, TN5000, DDTI (0.72 -> 0.75), FetalHead (0.95 -> 0.94), HC18 vs matched 1.00 (HC18 vs harmless_large 1.00 -> 0.50: with only ~6 tokens the terse form leaves too little for the judge to compare).
- Harmless_small mean score 0.80-1.00 (UDIAT 0.80, BUS-BRA 0.84, HC18 0.85, DDTI 0.85, BUSI 0.87): the judge still marks some synonym/reorder rewrites as differences, and now more of them on breast. A wording change of the instructions moved AUROC by up to 0.30 on 20 cases per dataset.
- **So the judge numbers are sensitive to the prompt and the sample; both runs are kept** (`step7_layer2_sentence_check_gemma` = prompt 1, this folder = prompt 2). Use this folder's numbers as the main judge result because it passes the wiring gate, and quote the range between the two prompts, not one number. I did not tune the prompt on the AUROCs, only on the identical-copy check, and did not try further prompts.

**Caveats (keep visible).** Templated, label-derived reports; severity provisional; template sources "to confirm"; per dataset only; 20 cases per dataset (wide intervals); one judge model with prompts we wrote; the original RadFact was not run; Claude judge not run (no credit).

---

## breast

### BrEaST (20 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 0.86 (0.75–0.95) | 0.94 (0.88–0.99) | 0.78 (0.64–0.89) | 0.96 / 1.00 / 0.98 | 0.96 | 1.00 | 0.88 | 1.0000 | — | -0.46 | size —, count —, birads — |
| sentence_precision | 0.86 (0.75–0.95) | 0.94 (0.88–0.99) | 0.70 (0.56–0.82) | 0.96 / 1.00 / 0.90 | 0.96 | 1.00 | 0.82 | 1.0000 | — | -0.46 | size —, count —, birads — |
| sentence_recall | 0.76 (0.65–0.86) | 0.82 (0.74–0.90) | 0.76 (0.66–0.85) | 0.96 / 1.00 / 0.98 | 0.96 | 1.00 | 0.95 | 1.0000 | — | -0.47 | size —, count —, birads — |
| judge_score | 0.89 (0.75–1.00) | 0.99 (0.96–1.00) | 0.55 (0.36–0.72) | 0.96 / 1.00 / 0.65 | 0.87 | 1.00 | 0.47 | 1.0000 | — | -0.11 | size -0.58, count —, birads — |

### BUS-BRA (20 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 0.61 (0.45–0.79) | 0.95 (0.90–0.99) | 0.95 (0.90–0.99) | 0.72 / 1.00 / 1.00 | 0.84 | 1.00 | 1.00 | 1.0000 | — | -0.42 | size 0.47, count —, birads — |
| sentence_precision | 0.62 (0.46–0.79) | 0.95 (0.90–0.99) | 0.95 (0.90–0.99) | 0.72 / 1.00 / 1.00 | 0.81 | 1.00 | 1.00 | 1.0000 | — | -0.22 | size 0.67, count —, birads — |
| sentence_recall | 0.55 (0.44–0.65) | 0.76 (0.69–0.84) | 0.76 (0.69–0.84) | 0.81 / 1.00 / 1.00 | 0.88 | 1.00 | 1.00 | 1.0000 | — | -0.57 | size -0.27, count —, birads — |
| judge_score | 0.60 (0.42–0.79) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.58 / 1.00 / 1.00 | 0.57 | 1.00 | 1.00 | 1.0000 | — | -0.37 | size -0.22, count —, birads — |

### BUSI (20 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 0.66 (0.51–0.81) | 0.86 (0.81–0.91) | 0.86 (0.81–0.91) | 0.96 / 1.00 / 1.00 | 0.87 | 1.00 | 1.00 | 1.0000 | — | -0.68 | size -0.10, count — |
| sentence_precision | 0.70 (0.56–0.81) | 0.86 (0.81–0.91) | 0.86 (0.81–0.91) | 0.96 / 1.00 / 1.00 | 0.85 | 1.00 | 1.00 | 1.0000 | — | -0.64 | size -0.10, count — |
| sentence_recall | 0.62 (0.50–0.75) | 0.71 (0.64–0.80) | 0.71 (0.64–0.80) | 0.96 / 1.00 / 1.00 | 0.90 | 1.00 | 1.00 | 1.0000 | — | -0.75 | size —, count — |
| judge_score | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 0.98 | 1.00 | 1.00 | 1.0000 | — | -0.62 | size -0.27, count — |

### UDIAT (20 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 0.50 (0.34–0.66) | 0.94 (0.89–0.97) | 0.75 (0.60–0.88) | 0.83 / 1.00 / 1.00 | 0.80 | 1.00 | 0.91 | 1.0000 | — | -0.50 | count —, size -0.13 |
| sentence_precision | 0.54 (0.41–0.66) | 0.82 (0.78–0.88) | 0.79 (0.71–0.85) | 0.83 / 1.00 / 1.00 | 0.80 | 1.00 | 0.97 | 1.0000 | — | -0.35 | count —, size -0.25 |
| sentence_recall | 0.55 (0.41–0.69) | 0.82 (0.75–0.90) | 0.65 (0.53–0.78) | 0.83 / 1.00 / 0.94 | 0.80 | 1.00 | 0.87 | 1.0000 | — | -0.57 | count —, size 0.05 |
| judge_score | 0.60 (0.44–0.76) | 1.00 (1.00–1.00) | 0.84 (0.71–0.95) | 0.61 / 1.00 / 0.94 | 0.54 | 1.00 | 0.76 | 1.0000 | — | -0.42 | count —, size 0.00 |

### BUS-UCLM (20 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 0.88 (0.78–0.95) | 0.94 (0.89–0.97) | 0.94 (0.89–0.97) | 0.98 / 1.00 / 1.00 | 0.90 | 1.00 | 1.00 | 1.0000 | — | -0.78 | size —, count — |
| sentence_precision | 0.88 (0.78–0.95) | 0.94 (0.89–0.97) | 0.94 (0.89–0.97) | 0.98 / 1.00 / 1.00 | 0.90 | 1.00 | 1.00 | 1.0000 | — | -0.76 | size —, count — |
| sentence_recall | 0.82 (0.72–0.93) | 0.89 (0.81–0.95) | 0.89 (0.81–0.95) | 0.98 / 1.00 / 1.00 | 0.90 | 1.00 | 1.00 | 1.0000 | — | -0.80 | size —, count — |
| judge_score | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 0.98 | 1.00 | 1.00 | 1.0000 | — | -0.13 | size -0.41, count — |

## thyroid

### TN3K (20 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.94 (0.89–0.99) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 0.82 | 1.0000 | — | -0.62 | size -0.16, count — |
| sentence_precision | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 0.82 | 1.0000 | — | -0.85 | size —, count — |
| sentence_recall | 0.85 (0.80–0.91) | 0.85 (0.80–0.91) | 0.79 (0.70–0.88) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 0.82 | 1.0000 | — | -0.62 | size -0.16, count — |
| judge_score | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 0.88 | 1.0000 | — | -0.75 | size -0.69, count — |

### TN5000 (20 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 0.99 (0.96–1.00) | 0.99 (0.96–1.00) | 0.89 (0.81–0.95) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 0.78 | 1.0000 | — | -0.66 | size 0.21, count — |
| sentence_precision | 0.99 (0.96–1.00) | 0.99 (0.96–1.00) | 0.97 (0.93–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 0.78 | 1.0000 | — | -0.79 | size 0.21, count — |
| sentence_recall | 0.82 (0.78–0.88) | 0.82 (0.78–0.88) | 0.72 (0.64–0.82) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 0.78 | 1.0000 | — | -0.67 | size —, count — |
| judge_score | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 0.87 | 1.0000 | — | -0.78 | size -0.69, count — |

### DDTI (20 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 0.75 (0.62–0.86) | 0.94 (0.88–0.99) | 0.76 (0.59–0.90) | 1.00 / 1.00 / 0.89 | 0.85 | 1.00 | 0.80 | 1.0000 | — | -0.59 | tirads —, size 0.47 |
| sentence_precision | 0.76 (0.65–0.86) | 0.94 (0.88–0.99) | 0.76 (0.57–0.93) | 1.00 / 1.00 / 0.89 | 0.85 | 1.00 | 0.77 | 1.0000 | — | -0.50 | tirads —, size 0.47 |
| sentence_recall | 0.68 (0.56–0.78) | 0.85 (0.78–0.91) | 0.82 (0.74–0.90) | 1.00 / 1.00 / 1.00 | 0.85 | 1.00 | 0.97 | 1.0000 | — | -0.64 | tirads —, size — |
| judge_score | 0.96 (0.89–1.00) | 1.00 (1.00–1.00) | 0.95 (0.85–1.00) | 1.00 / 1.00 / 0.89 | 0.89 | 1.00 | 0.84 | 1.0000 | — | -0.36 | tirads —, size 0.00 |

## fetal

### HC18 (20 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 0.85 (0.75–0.95) | 1.00 (1.00–1.00) | 0.50 (0.25–0.70) | 0.88 / 1.00 / 0.50 | 0.85 | 1.00 | 0.50 | 1.0000 | — | -0.55 | hc_mm -0.55 |
| sentence_precision | 0.78 (0.65–0.88) | 1.00 (1.00–1.00) | 0.55 (0.30–0.75) | 0.69 / 1.00 / 0.50 | 0.78 | 1.00 | 0.55 | 1.0000 | — | — | hc_mm — |
| sentence_recall | 0.60 (0.53–0.70) | 0.60 (0.53–0.70) | 0.30 (0.15–0.45) | 0.75 / 0.75 / 0.38 | 1.00 | 1.00 | 0.50 | 1.0000 | — | -0.55 | hc_mm -0.55 |
| judge_score | 0.93 (0.85–1.00) | 1.00 (1.00–1.00) | 0.50 (0.25–0.70) | 1.00 / 1.00 / 0.50 | 0.86 | 1.00 | 0.50 | 1.0000 | — | -0.83 | hc_mm -0.83 |

### FetalHead (20 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 0.94 (0.89–0.97) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 0.90 | 1.00 | 1.00 | 1.0000 | — | -0.06 | hc_mm -0.02 |
| sentence_precision | 0.85 (0.75–0.95) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 0.85 | 1.00 | 1.00 | 1.0000 | — | — | hc_mm — |
| sentence_recall | 0.76 (0.75–0.79) | 0.76 (0.75–0.79) | 0.76 (0.75–0.79) | 0.50 / 0.50 / 0.50 | 1.00 | 1.00 | 1.00 | 1.0000 | — | -0.06 | hc_mm -0.02 |
| judge_score | 0.79 (0.64–0.93) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 0.91 | 1.00 | 1.00 | 1.0000 | — | -0.17 | hc_mm -0.69 |

## AUROC by error category (vs harmless_small / vs matched 1-word / vs harmless_large)

**BrEaST**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| sentence_f1 | 0.88 / 1.00 / 0.92 | 1.00 / 1.00 / 0.92 | 1.00 / 1.00 / 1.00 | 0.38 / 0.50 / 0.12 | 0.90 / 0.97 / 0.73 |
| sentence_precision | 0.88 / 1.00 / 0.83 | 1.00 / 1.00 / 0.92 | 1.00 / 1.00 / 0.50 | 0.38 / 0.50 / 0.12 | 0.90 / 0.97 / 0.63 |
| sentence_recall | 0.71 / 0.79 / 0.79 | 1.00 / 1.00 / 0.92 | 1.00 / 1.00 / 1.00 | 0.38 / 0.50 / 0.38 | 0.77 / 0.83 / 0.73 |
| judge_score | 0.92 / 1.00 / 0.62 | 0.92 / 1.00 / 0.75 | 1.00 / 1.00 / 1.00 | 0.75 / 1.00 / 0.50 | 0.87 / 0.97 / 0.33 |

**BUS-BRA**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| sentence_f1 | 0.40 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 0.62 / 1.00 / 1.00 | 0.55 / 0.80 / 0.80 | 0.59 / 1.00 / 1.00 |
| sentence_precision | 0.40 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 0.62 / 1.00 / 1.00 | 0.55 / 0.80 / 0.80 | 0.62 / 1.00 / 1.00 |
| sentence_recall | 0.20 / 0.50 / 0.50 | 1.00 / 1.00 / 1.00 | 0.75 / 1.00 / 1.00 | 0.35 / 0.55 / 0.55 | 0.59 / 0.84 / 0.84 |
| judge_score | 0.50 / 1.00 / 1.00 | 0.80 / 1.00 / 1.00 | 0.75 / 1.00 / 1.00 | 0.65 / 1.00 / 1.00 | 0.50 / 1.00 / 1.00 |

**BUSI**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| sentence_f1 | 0.67 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 0.36 / 0.61 / 0.61 | 0.75 / 1.00 / 1.00 |
| sentence_precision | 0.67 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 0.43 / 0.61 / 0.61 | 0.83 / 1.00 / 1.00 |
| sentence_recall | 0.50 / 0.61 / 0.61 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 0.39 / 0.50 / 0.50 | 0.67 / 0.83 / 0.83 |
| judge_score | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |

**UDIAT**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| sentence_f1 | 0.67 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 0.75 / 1.00 / 1.00 | 0.25 / 0.84 / 0.53 | 0.45 / 1.00 / 0.77 |
| sentence_precision | 0.67 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 0.75 / 1.00 / 1.00 | 0.22 / 0.56 / 0.47 | 0.64 / 1.00 / 1.00 |
| sentence_recall | 0.67 / 0.83 / 0.50 | 1.00 / 1.00 / 1.00 | 0.75 / 1.00 / 1.00 | 0.44 / 0.78 / 0.56 | 0.36 / 0.73 / 0.50 |
| judge_score | 1.00 / 1.00 / 1.00 | 0.92 / 1.00 / 1.00 | 0.88 / 1.00 / 1.00 | 0.56 / 1.00 / 0.84 | 0.27 / 1.00 / 0.64 |

**BUS-UCLM**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| sentence_f1 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 0.88 / 1.00 / 1.00 | 0.20 / 0.50 / 0.50 | 0.90 / 1.00 / 1.00 |
| sentence_precision | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 0.88 / 1.00 / 1.00 | 0.20 / 0.50 / 0.50 | 0.90 / 1.00 / 1.00 |
| sentence_recall | 0.92 / 0.92 / 0.92 | 1.00 / 1.00 / 1.00 | 0.88 / 1.00 / 1.00 | 0.20 / 0.50 / 0.50 | 0.70 / 0.80 / 0.80 |
| judge_score | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |

**TN3K**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| sentence_f1 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 0.81 | 1.00 / 1.00 / 1.00 |
| sentence_precision | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| sentence_recall | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 0.54 / 0.54 / 0.35 | 1.00 / 1.00 / 1.00 |
| judge_score | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |

**TN5000**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| sentence_f1 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 0.96 / 0.96 / 0.68 | 1.00 / 1.00 / 1.00 |
| sentence_precision | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 0.96 / 0.96 / 0.93 | 1.00 / 1.00 / 1.00 |
| sentence_recall | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 0.50 / 0.50 / 0.21 | 1.00 / 1.00 / 1.00 |
| judge_score | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |

**DDTI**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| sentence_f1 | 0.83 / 1.00 / 0.50 | 0.94 / 1.00 / 1.00 | 0.67 / 1.00 / 1.00 | 0.64 / 0.77 / 0.59 | 0.71 / 1.00 / 0.75 |
| sentence_precision | 0.83 / 1.00 / 0.33 | 0.94 / 1.00 / 1.00 | 0.67 / 1.00 / 1.00 | 0.64 / 0.77 / 0.68 | 0.75 / 1.00 / 0.71 |
| sentence_recall | 0.83 / 1.00 / 1.00 | 0.94 / 1.00 / 1.00 | 0.67 / 1.00 / 1.00 | 0.36 / 0.50 / 0.41 | 0.71 / 0.96 / 0.96 |
| judge_score | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 0.91 / 1.00 / 0.91 | 0.96 / 1.00 / 0.93 |

**HC18**

| scorer | wrong measurement |
|---|---|
| sentence_f1 | 0.85 / 1.00 / 0.50 |
| sentence_precision | 0.78 / 1.00 / 0.55 |
| sentence_recall | 0.60 / 0.60 / 0.30 |
| judge_score | 0.93 / 1.00 / 0.50 |

**FetalHead**

| scorer | wrong measurement | wrong severity/category |
|---|---|---|
| sentence_f1 | 0.88 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| sentence_precision | 0.85 / 1.00 / 1.00 | 0.85 / 1.00 / 1.00 |
| sentence_recall | 0.53 / 0.53 / 0.53 | 1.00 / 1.00 / 1.00 |
| judge_score | 0.88 / 1.00 / 1.00 | 0.70 / 1.00 / 1.00 |

## Judge category accuracy (planted category listed by the judge) and detection (judge lists any error)

| dataset | category | n | category accuracy | any error listed |
|---|---|---|---|---|
| BUS-BRA | false finding | 5 | 1.00 | 1.00 |
| BUS-BRA | missed finding | 5 | 0.60 | 1.00 |
| BUS-BRA | wrong location | 4 | 1.00 | 1.00 |
| BUS-BRA | wrong measurement | 10 | 1.00 | 1.00 |
| BUS-BRA | wrong severity/category | 16 | 0.69 | 1.00 |
| BUS-UCLM | false finding | 12 | 1.00 | 1.00 |
| BUS-UCLM | missed finding | 4 | 1.00 | 1.00 |
| BUS-UCLM | wrong location | 4 | 1.00 | 1.00 |
| BUS-UCLM | wrong measurement | 5 | 1.00 | 1.00 |
| BUS-UCLM | wrong severity/category | 5 | 0.60 | 1.00 |
| BUSI | false finding | 9 | 1.00 | 1.00 |
| BUSI | missed finding | 7 | 1.00 | 1.00 |
| BUSI | wrong location | 2 | 1.00 | 1.00 |
| BUSI | wrong measurement | 14 | 1.00 | 1.00 |
| BUSI | wrong severity/category | 6 | 0.67 | 1.00 |
| BrEaST | false finding | 12 | 1.00 | 1.00 |
| BrEaST | missed finding | 6 | 1.00 | 1.00 |
| BrEaST | wrong location | 1 | 1.00 | 1.00 |
| BrEaST | wrong measurement | 4 | 1.00 | 1.00 |
| BrEaST | wrong severity/category | 15 | 0.67 | 0.93 |
| DDTI | false finding | 3 | 1.00 | 1.00 |
| DDTI | missed finding | 8 | 0.62 | 1.00 |
| DDTI | wrong location | 3 | 1.00 | 1.00 |
| DDTI | wrong measurement | 11 | 1.00 | 1.00 |
| DDTI | wrong severity/category | 14 | 1.00 | 1.00 |
| FetalHead | wrong measurement | 20 | 1.00 | 1.00 |
| FetalHead | wrong severity/category | 20 | 0.00 | 1.00 |
| HC18 | wrong measurement | 20 | 1.00 | 1.00 |
| TN3K | false finding | 6 | 1.00 | 1.00 |
| TN3K | missed finding | 12 | 0.00 | 1.00 |
| TN3K | wrong location | 4 | 1.00 | 1.00 |
| TN3K | wrong measurement | 13 | 1.00 | 1.00 |
| TN3K | wrong severity/category | 5 | 1.00 | 1.00 |
| TN5000 | false finding | 9 | 1.00 | 1.00 |
| TN5000 | missed finding | 11 | 0.00 | 1.00 |
| TN5000 | wrong location | 3 | 1.00 | 1.00 |
| TN5000 | wrong measurement | 14 | 1.00 | 1.00 |
| TN5000 | wrong severity/category | 3 | 1.00 | 1.00 |
| UDIAT | false finding | 3 | 1.00 | 1.00 |
| UDIAT | missed finding | 6 | 1.00 | 1.00 |
| UDIAT | wrong location | 4 | 1.00 | 1.00 |
| UDIAT | wrong measurement | 16 | 0.88 | 1.00 |
| UDIAT | wrong severity/category | 11 | 0.45 | 1.00 |

---
Limitations: see [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md) (templated reports, upper bounds, prompt-sensitive judge, provisional severity, possible exposure). 
