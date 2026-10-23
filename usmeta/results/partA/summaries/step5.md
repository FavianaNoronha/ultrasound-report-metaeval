# Step 5: harmless split + Layer 0 re-check (plain-language summary)

**What was done.** bench_v2 (untouched) was relabelled as **bench_v2b.jsonl**: `harmless_small` = synonyms, sentence reorder, unit rewrite (edits inside the standard style); `harmless_large` = style swap (terse or long-form text); `harmless_other` = negation, hedge, padding (reported separately). The old `harmless` label is their union. The Layer 0 scores are the same text pairs as Step 4 (checked pair by pair), so cached scores were reused, not recomputed. Scorers: BLEU, ROUGE-L, chrF, BERTScore (roberta-large), RaTEScore.

**Wiring gate:** identical-copy score = 1.0000 for every scorer on every dataset (lowest value 0.9999997, float rounding). No stop condition.

**Your hypothesis (style swaps cause the below-chance scores): half right.**
- Against `harmless_large` (style swap) AUROC is 0.00-0.33 for almost every scorer and dataset (BrEaST 0.08-0.13, BUS-BRA 0.09-0.20, HC18 0.00-0.05). Style swaps are what pushes it to the floor.
- Against `harmless_small` it improves but stays at or below chance on the richest datasets. BrEaST: BLEU 0.25, ROUGE-L 0.10, chrF 0.37, BERTScore 0.21, RaTEScore 0.44. BUS-BRA: 0.20 / 0.09 / 0.31 / 0.09 / 0.53. Above 0.5 only on BUSI, UDIAT, BUS-UCLM, TN3K, TN5000 with BLEU/chrF/RaTEScore (0.50-0.84), which are the datasets with the fewest facts per report.
- **Why `harmless_small` is still not small.** Share of tokens changed vs the reference (BrEaST / BUS-BRA): planted errors 2-4% (wrong measurement 2% / 3%, wrong location 2% / 3%, wrong category 3% / 4%), except a missed lesion 73% / 95%; unit rewrite 5%; hedge 8% / 10%; synonyms 18% / 17%; reorder 36% / 24%; style swap 38-64%. Our "small" synonym and reorder rewordings change 5-10 times more text than a planted error, so a text-overlap scorer ranks them as worse. The scorers track **how much text changed**, not whether a fact changed.
- Closest in edit size is the unit rewrite (5%) and hedging: BrEaST AUROC vs unit_cm: BLEU 0.32, chrF 0.52, BERTScore 0.45, RaTEScore 0.37. Still around or below chance. A fairer comparison would use harmless rewordings with a matched edit size (a one-word synonym): not done yet, a design question for you.

**What "size errors score about 0" means in numbers.** A size error replaces one number ("11 mm" -> "6 mm", "16 mm" or "22 mm"). On BrEaST BLEU scores all three at **0.952** and BERTScore at **0.999**; the mean BLEU on a synonym/reorder/unit rewording is 0.852 and BERTScore 0.979. So a size error looks **more similar to the reference than a harmless rewording**: AUROC 0.00. The score is identical for x0.5, x1.5 and x2 (BLEU 0.952 / 0.952 / 0.952), so the Spearman correlation between error size and score is 0.00: the scorer does not see the number at all. BUS-BRA: BLEU 0.940 for all three; TN5000: 0.899. (HC18 has no size errors: its errors are head-circumference shifts.)

**Lazy "No abnormality." report (no image):** BLEU/ROUGE-L 0.00-0.14, chrF 0.02-0.11, BERTScore 0.84-0.87, RaTEScore a flat 0.50 on every case.

**Caveats (keep visible).** Reports are templated from labels (synthetic but fact-correct); severity is provisional pending clinician; template sources are "to confirm" (usmeta/docs/templates_sources.md); all results are per dataset and never pooled; datasets support different error types; the critical-only AUROC of 1.00 on TN3K/TN5000 comes from missed/false lesion being the only severity-3 error there (a big text edit). RaTEScore is built for chest/CT text. 150 cases per dataset (256 for BrEaST).

---

## Share of tokens changed vs the reference, by candidate type (mean)

**BrEaST**: ERR:false finding 0.04, ERR:missed finding 0.73, ERR:wrong location 0.02, ERR:wrong measurement 0.02, ERR:wrong severity/category 0.03, hedge 0.08, negation 0.08, pad1 0.06, pad3 0.16, reorder 0.36, style_long 0.54, style_terse 0.64, synonyms 0.18, unit_cm 0.05
**BUS-BRA**: ERR:false finding 0.06, ERR:missed finding 0.95, ERR:wrong location 0.03, ERR:wrong measurement 0.03, ERR:wrong severity/category 0.04, hedge 0.10, pad1 0.07, pad3 0.20, reorder 0.24, style_long 0.38, style_terse 0.44, synonyms 0.17

## breast

### BrEaST (256 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs large (95% CI) | critical-only small / large | harmless_small mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.25 (0.24–0.26) | 0.08 (0.07–0.09) | 0.38 / 0.38 | 0.85 | 0.38 | 1.0000 | 0.00 | -0.12 | count —, size 0.00, birads -0.02 |
| rougeL | 0.10 (0.09–0.12) | 0.08 (0.07–0.09) | 0.38 / 0.38 | 0.80 | 0.59 | 1.0000 | 0.04 | -0.21 | count —, size 0.00, birads -0.02 |
| chrf | 0.37 (0.36–0.38) | 0.08 (0.07–0.09) | 0.62 / 0.38 | 0.92 | 0.73 | 1.0000 | 0.02 | -0.33 | count —, size -0.06, birads -0.22 |
| bertscore[roberta-large] | 0.21 (0.19–0.22) | 0.08 (0.07–0.09) | 0.48 / 0.38 | 0.98 | 0.95 | 1.0000 | 0.84 | -0.35 | count —, size -0.03, birads -0.39 |
| ratescore | 0.44 (0.43–0.45) | 0.13 (0.12–0.15) | 0.67 / 0.46 | 0.92 | 0.83 | 1.0000 | 0.50 | -0.38 | count —, size -0.01, birads 0.02 |

### BUS-BRA (151 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs large (95% CI) | critical-only small / large | harmless_small mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.20 (0.19–0.21) | 0.09 (0.09–0.09) | 0.28 / 0.28 | 0.82 | 0.54 | 1.0000 | 0.00 | -0.05 | count —, size 0.00, birads 0.02 |
| rougeL | 0.09 (0.09–0.09) | 0.09 (0.09–0.09) | 0.28 / 0.28 | 0.79 | 0.70 | 1.0000 | 0.00 | -0.01 | count —, size 0.00, birads 0.02 |
| chrf | 0.31 (0.30–0.31) | 0.09 (0.09–0.09) | 0.50 / 0.28 | 0.88 | 0.74 | 1.0000 | 0.02 | -0.27 | count —, size -0.00, birads -0.46 |
| bertscore[roberta-large] | 0.09 (0.09–0.09) | 0.09 (0.09–0.09) | 0.28 / 0.28 | 0.97 | 0.95 | 1.0000 | 0.84 | -0.27 | count —, size 0.00, birads -0.68 |
| ratescore | 0.53 (0.52–0.54) | 0.20 (0.18–0.21) | 0.60 / 0.31 | 0.92 | 0.87 | 1.0000 | 0.50 | -0.17 | count —, size -0.01, birads -0.00 |

### BUSI (150 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs large (95% CI) | critical-only small / large | harmless_small mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.63 (0.61–0.66) | 0.27 (0.22–0.32) | 0.78 / 0.58 | 0.80 | 0.48 | 1.0000 | 0.01 | -0.09 | count —, size 0.00 |
| rougeL | 0.30 (0.25–0.35) | 0.27 (0.22–0.32) | 0.58 / 0.58 | 0.85 | 0.65 | 1.0000 | 0.04 | -0.23 | count —, size 0.00 |
| chrf | 0.63 (0.61–0.66) | 0.27 (0.22–0.32) | 0.79 / 0.58 | 0.88 | 0.71 | 1.0000 | 0.05 | -0.37 | count —, size 0.00 |
| bertscore[roberta-large] | 0.27 (0.22–0.32) | 0.27 (0.22–0.32) | 0.58 / 0.58 | 0.97 | 0.95 | 1.0000 | 0.86 | -0.50 | count —, size -0.03 |
| ratescore | 0.60 (0.57–0.63) | 0.59 (0.55–0.62) | 0.78 / 0.79 | 0.91 | 0.86 | 1.0000 | 0.50 | -0.80 | count —, size -0.00 |

### UDIAT (150 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs large (95% CI) | critical-only small / large | harmless_small mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.50 (0.50–0.50) | 0.11 (0.11–0.12) | 0.75 / 0.50 | 0.83 | 0.52 | 1.0000 | 0.00 | -0.17 | count —, size — |
| rougeL | 0.11 (0.11–0.12) | 0.11 (0.11–0.12) | 0.50 / 0.50 | 0.84 | 0.65 | 1.0000 | 0.00 | -0.14 | count —, size — |
| chrf | 0.50 (0.49–0.51) | 0.11 (0.11–0.12) | 0.75 / 0.50 | 0.89 | 0.74 | 1.0000 | 0.03 | -0.32 | count —, size 0.01 |
| bertscore[roberta-large] | 0.11 (0.11–0.12) | 0.11 (0.11–0.12) | 0.50 / 0.50 | 0.97 | 0.95 | 1.0000 | 0.85 | -0.55 | count —, size -0.03 |
| ratescore | 0.53 (0.53–0.54) | 0.51 (0.50–0.52) | 0.75 / 0.75 | 0.92 | 0.86 | 1.0000 | 0.50 | -0.71 | count —, size 0.00 |

### BUS-UCLM (152 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs large (95% CI) | critical-only small / large | harmless_small mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.84 (0.80–0.87) | 0.68 (0.61–0.74) | 0.90 / 0.81 | 0.76 | 0.43 | 1.0000 | 0.02 | -0.37 | count —, size 0.00 |
| rougeL | 0.69 (0.63–0.75) | 0.68 (0.61–0.74) | 0.81 / 0.81 | 0.82 | 0.65 | 1.0000 | 0.14 | -0.48 | count —, size 0.00 |
| chrf | 0.84 (0.80–0.87) | 0.68 (0.61–0.74) | 0.91 / 0.81 | 0.87 | 0.68 | 1.0000 | 0.11 | -0.60 | count —, size -0.02 |
| bertscore[roberta-large] | 0.68 (0.61–0.74) | 0.68 (0.61–0.74) | 0.81 / 0.81 | 0.97 | 0.95 | 1.0000 | 0.87 | -0.65 | count —, size 0.05 |
| ratescore | 0.83 (0.79–0.86) | 0.82 (0.78–0.86) | 0.90 / 0.90 | 0.96 | 0.86 | 1.0000 | 0.50 | -0.84 | count —, size 0.02 |

## thyroid

### TN3K (150 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs large (95% CI) | critical-only small / large | harmless_small mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.58 (0.58–0.58) | 0.16 (0.15–0.16) | 1.00 / 1.00 | 0.80 | 0.44 | 1.0000 | 0.00 | -0.36 | count —, size 0.00 |
| rougeL | 0.16 (0.15–0.16) | 0.16 (0.15–0.16) | 1.00 / 1.00 | 0.84 | 0.63 | 1.0000 | 0.00 | -0.48 | count —, size 0.00 |
| chrf | 0.58 (0.58–0.58) | 0.16 (0.15–0.16) | 1.00 / 1.00 | 0.86 | 0.70 | 1.0000 | 0.03 | -0.26 | count —, size 0.05 |
| bertscore[roberta-large] | 0.16 (0.15–0.16) | 0.16 (0.15–0.16) | 1.00 / 1.00 | 0.97 | 0.94 | 1.0000 | 0.86 | -0.38 | count —, size -0.02 |
| ratescore | 0.56 (0.55–0.57) | 0.32 (0.31–0.33) | 1.00 / 1.00 | 0.88 | 0.74 | 1.0000 | 0.50 | -0.32 | count —, size -0.09 |

### TN5000 (150 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs large (95% CI) | critical-only small / large | harmless_small mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.58 (0.58–0.58) | 0.15 (0.15–0.16) | 1.00 / 1.00 | 0.80 | 0.44 | 1.0000 | 0.00 | -0.36 | count —, size — |
| rougeL | 0.15 (0.15–0.16) | 0.15 (0.15–0.16) | 1.00 / 1.00 | 0.84 | 0.63 | 1.0000 | 0.00 | -0.50 | count —, size — |
| chrf | 0.58 (0.58–0.58) | 0.15 (0.15–0.16) | 1.00 / 1.00 | 0.86 | 0.71 | 1.0000 | 0.03 | -0.27 | count —, size -0.02 |
| bertscore[roberta-large] | 0.15 (0.15–0.16) | 0.15 (0.15–0.16) | 1.00 / 1.00 | 0.97 | 0.94 | 1.0000 | 0.86 | -0.33 | count —, size -0.05 |
| ratescore | 0.58 (0.57–0.59) | 0.33 (0.32–0.34) | 1.00 / 1.00 | 0.88 | 0.76 | 1.0000 | 0.50 | -0.37 | count —, size -0.11 |

### DDTI (150 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs large (95% CI) | critical-only small / large | harmless_small mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.45 (0.43–0.46) | 0.10 (0.09–0.10) | 0.70 / 0.70 | 0.80 | 0.43 | 1.0000 | 0.00 | -0.31 | count —, size 0.00, tirads 0.02 |
| rougeL | 0.12 (0.10–0.14) | 0.12 (0.10–0.14) | 0.72 / 0.72 | 0.73 | 0.61 | 1.0000 | 0.02 | -0.31 | count —, size 0.00, tirads 0.03 |
| chrf | 0.44 (0.43–0.46) | 0.11 (0.10–0.12) | 0.70 / 0.71 | 0.87 | 0.68 | 1.0000 | 0.02 | -0.35 | count —, size -0.01, tirads -0.22 |
| bertscore[roberta-large] | 0.13 (0.11–0.15) | 0.11 (0.10–0.12) | 0.72 / 0.71 | 0.97 | 0.95 | 1.0000 | 0.84 | -0.60 | count —, size -0.01, tirads -0.44 |
| ratescore | 0.50 (0.48–0.52) | 0.23 (0.20–0.26) | 0.77 / 0.70 | 0.88 | 0.76 | 1.0000 | 0.50 | -0.38 | count —, size -0.02, tirads -0.01 |

## fetal

### HC18 (150 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs large (95% CI) | critical-only small / large | harmless_small mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.33 (0.33–0.33) | 0.00 (0.00–0.00) | 0.33 / 0.00 | 0.58 | 0.20 | 1.0000 | 0.05 | — | hc_mm — |
| rougeL | 0.17 (0.17–0.17) | 0.00 (0.00–0.00) | 0.17 / 0.00 | 0.72 | 0.68 | 1.0000 | 0.00 | — | hc_mm — |
| chrf | 0.33 (0.33–0.34) | 0.00 (0.00–0.00) | 0.33 / 0.00 | 0.85 | 0.45 | 1.0000 | 0.05 | -0.26 | hc_mm -0.26 |
| bertscore[roberta-large] | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | 0.00 / 0.00 | 0.97 | 0.93 | 1.0000 | 0.87 | -0.34 | hc_mm -0.34 |
| ratescore | 0.42 (0.41–0.44) | 0.05 (0.04–0.07) | 0.51 / 0.10 | 0.89 | 0.61 | 1.0000 | 0.50 | -0.42 | hc_mm -0.42 |

### FetalHead (151 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs large (95% CI) | critical-only small / large | harmless_small mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.37 (0.37–0.37) | 0.00 (0.00–0.01) | 0.33 / 0.00 | 0.79 | 0.35 | 1.0000 | 0.01 | 0.00 | hc_mm — |
| rougeL | 0.17 (0.17–0.17) | 0.00 (0.00–0.01) | 0.17 / 0.00 | 0.72 | 0.79 | 1.0000 | 0.00 | 0.00 | hc_mm — |
| chrf | 0.55 (0.53–0.56) | 0.05 (0.04–0.06) | 0.50 / 0.00 | 0.93 | 0.70 | 1.0000 | 0.04 | -0.33 | hc_mm -0.47 |
| bertscore[roberta-large] | 0.13 (0.13–0.13) | 0.10 (0.10–0.11) | 0.00 / 0.00 | 0.97 | 0.95 | 1.0000 | 0.84 | -0.23 | hc_mm -0.32 |
| ratescore | 0.49 (0.47–0.51) | 0.11 (0.08–0.13) | 0.52 / 0.07 | 0.93 | 0.63 | 1.0000 | 0.50 | -0.13 | hc_mm -0.16 |

## AUROC by error category (vs harmless_small / vs harmless_large)

**BrEaST**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| bleu | 0.49 / 0.02 | 0.88 / 0.84 | 0.00 / 0.00 | 0.00 / 0.00 | 0.17 / 0.00 |
| rougeL | 0.09 / 0.02 | 0.85 / 0.84 | 0.00 / 0.00 | 0.00 / 0.00 | 0.02 / 0.00 |
| chrf | 0.50 / 0.02 | 0.88 / 0.84 | 0.67 / 0.00 | 0.01 / 0.00 | 0.37 / 0.00 |
| bertscore[roberta-large] | 0.26 / 0.02 | 0.86 / 0.84 | 0.00 / 0.00 | 0.00 / 0.00 | 0.16 / 0.00 |
| ratescore | 0.42 / 0.07 | 0.89 / 0.85 | 0.17 / 0.00 | 0.34 / 0.01 | 0.43 / 0.08 |

**BUS-BRA**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| bleu | 0.50 / 0.00 | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.17 / 0.00 |
| rougeL | 0.00 / 0.00 | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 |
| chrf | 0.50 / 0.00 | 1.00 / 1.00 | 0.21 / 0.00 | 0.00 / 0.00 | 0.37 / 0.00 |
| bertscore[roberta-large] | 0.00 / 0.00 | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 |
| ratescore | 0.48 / 0.03 | 1.00 / 1.00 | 0.43 / 0.03 | 0.50 / 0.06 | 0.50 / 0.21 |

**BUSI**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| bleu | 0.58 / 0.17 | 1.00 / 1.00 | 0.50 / 0.00 | 0.50 / 0.00 | 0.49 / 0.00 |
| rougeL | 0.17 / 0.17 | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.12 / 0.00 |
| chrf | 0.58 / 0.17 | 1.00 / 1.00 | 0.50 / 0.00 | 0.49 / 0.00 | 0.50 / 0.00 |
| bertscore[roberta-large] | 0.17 / 0.17 | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 |
| ratescore | 0.58 / 0.58 | 1.00 / 1.00 | 0.21 / 0.00 | 0.48 / 0.48 | 0.48 / 0.49 |

**UDIAT**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| bleu | 0.50 / 0.00 | 1.00 / 1.00 | 0.50 / 0.00 | 0.50 / 0.00 | 0.33 / 0.00 |
| rougeL | 0.00 / 0.00 | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 |
| chrf | 0.50 / 0.00 | 1.00 / 1.00 | 0.50 / 0.00 | 0.42 / 0.00 | 0.40 / 0.00 |
| bertscore[roberta-large] | 0.00 / 0.00 | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 |
| ratescore | 0.47 / 0.45 | 1.00 / 1.00 | 0.22 / 0.00 | 0.50 / 0.50 | 0.50 / 0.50 |

**BUS-UCLM**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| bleu | 0.82 / 0.63 | 1.00 / 1.00 | 0.50 / 0.00 | 0.50 / 0.00 | 0.49 / 0.00 |
| rougeL | 0.63 / 0.63 | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.12 / 0.00 |
| chrf | 0.82 / 0.63 | 1.00 / 1.00 | 0.50 / 0.00 | 0.49 / 0.00 | 0.50 / 0.00 |
| bertscore[roberta-large] | 0.63 / 0.63 | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 |
| ratescore | 0.82 / 0.82 | 1.00 / 1.00 | 0.24 / 0.00 | 0.48 / 0.48 | 0.48 / 0.49 |

**TN3K**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| bleu | 0.50 / 0.00 | 1.00 / 1.00 | 0.50 / 0.00 | 0.50 / 0.00 | 0.50 / 0.00 |
| rougeL | 0.00 / 0.00 | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 |
| chrf | 0.50 / 0.00 | 1.00 / 1.00 | 0.50 / 0.00 | 0.50 / 0.00 | 0.50 / 0.00 |
| bertscore[roberta-large] | 0.00 / 0.00 | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 |
| ratescore | 0.66 / 0.25 | 1.00 / 1.00 | 0.33 / 0.01 | 0.30 / 0.00 | 0.94 / 0.80 |

**TN5000**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| bleu | 0.50 / 0.00 | 1.00 / 1.00 | 0.50 / 0.00 | 0.50 / 0.00 | 0.50 / 0.00 |
| rougeL | 0.00 / 0.00 | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 |
| chrf | 0.50 / 0.00 | 1.00 / 1.00 | 0.50 / 0.00 | 0.50 / 0.00 | 0.50 / 0.00 |
| bertscore[roberta-large] | 0.00 / 0.00 | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 |
| ratescore | 0.76 / 0.41 | 1.00 / 1.00 | 0.30 / 0.00 | 0.30 / 0.01 | 0.95 / 0.74 |

**DDTI**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| bleu | 0.49 / 0.00 | 0.88 / 0.75 | 0.50 / 0.00 | 0.50 / 0.00 | 0.32 / 0.00 |
| rougeL | 0.03 / 0.03 | 0.75 / 0.75 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 |
| chrf | 0.49 / 0.01 | 0.88 / 0.75 | 0.50 / 0.00 | 0.48 / 0.00 | 0.31 / 0.00 |
| bertscore[roberta-large] | 0.08 / 0.01 | 0.79 / 0.75 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 |
| ratescore | 0.54 / 0.23 | 0.87 / 0.78 | 0.36 / 0.02 | 0.31 / 0.00 | 0.57 / 0.31 |

**HC18**

| scorer | wrong measurement |
|---|---|
| bleu | 0.33 / 0.00 |
| rougeL | 0.17 / 0.00 |
| chrf | 0.33 / 0.00 |
| bertscore[roberta-large] | 0.00 / 0.00 |
| ratescore | 0.42 / 0.05 |

**FetalHead**

| scorer | wrong measurement | wrong severity/category |
|---|---|---|
| bleu | 0.33 / 0.00 | 0.50 / 0.00 |
| rougeL | 0.17 / 0.00 | 0.17 / 0.00 |
| chrf | 0.43 / 0.00 | 1.00 / 0.21 |
| bertscore[roberta-large] | 0.00 / 0.00 | 0.67 / 0.50 |
| ratescore | 0.47 / 0.08 | 0.59 / 0.21 |

## AUROC against each harmless group separately (errors vs that group only)

**BrEaST**

| scorer | synonyms | reorder | unit_cm | style_terse | style_long | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.08 | 0.33 | 0.32 | 0.08 | 0.08 | 0.14 | 0.10 | 0.20 | 0.08 |
| rougeL | 0.08 | 0.08 | 0.14 | 0.08 | 0.08 | 0.14 | 0.08 | 0.08 | 0.08 |
| chrf | 0.08 | 0.52 | 0.52 | 0.08 | 0.08 | 0.19 | 0.42 | 0.35 | 0.10 |
| bertscore[roberta-large] | 0.08 | 0.08 | 0.45 | 0.08 | 0.08 | 0.25 | 0.09 | 0.08 | 0.08 |
| ratescore | 0.08 | 0.86 | 0.37 | 0.19 | 0.08 | 0.32 | 0.86 | 0.86 | 0.86 |

**BUS-BRA**

| scorer | synonyms | reorder | unit_cm | style_terse | style_long | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.09 | 0.31 | — | 0.09 | 0.09 | — | 0.09 | 0.09 | 0.09 |
| rougeL | 0.09 | 0.09 | — | 0.09 | 0.09 | — | 0.09 | 0.09 | 0.09 |
| chrf | 0.09 | 0.52 | — | 0.09 | 0.09 | — | 0.43 | 0.38 | 0.09 |
| bertscore[roberta-large] | 0.09 | 0.09 | — | 0.09 | 0.09 | — | 0.09 | 0.09 | 0.09 |
| ratescore | 0.14 | 0.92 | — | 0.23 | 0.17 | — | 0.91 | 0.91 | 0.91 |

**BUSI**

| scorer | synonyms | reorder | unit_cm | style_terse | style_long | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.27 | 1.00 | — | 0.27 | 0.27 | 1.00 | 0.27 | 0.27 | 0.27 |
| rougeL | 0.27 | 0.32 | — | 0.27 | 0.27 | 1.00 | 0.27 | 0.27 | 0.27 |
| chrf | 0.27 | 1.00 | — | 0.27 | 0.27 | 1.00 | 0.50 | 0.41 | 0.27 |
| bertscore[roberta-large] | 0.27 | 0.27 | — | 0.27 | 0.27 | 1.00 | 0.27 | 0.27 | 0.27 |
| ratescore | 0.27 | 0.93 | — | 0.90 | 0.27 | 1.00 | 0.96 | 0.96 | 0.96 |

**UDIAT**

| scorer | synonyms | reorder | unit_cm | style_terse | style_long | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.11 | 0.89 | — | 0.11 | 0.11 | — | 0.11 | 0.11 | 0.11 |
| rougeL | 0.11 | 0.11 | — | 0.11 | 0.11 | — | 0.11 | 0.11 | 0.11 |
| chrf | 0.11 | 0.88 | — | 0.11 | 0.11 | — | 0.35 | 0.34 | 0.11 |
| bertscore[roberta-large] | 0.11 | 0.11 | — | 0.11 | 0.11 | — | 0.11 | 0.11 | 0.11 |
| ratescore | 0.12 | 0.95 | — | 0.90 | 0.11 | — | 0.95 | 0.95 | 0.95 |

**BUS-UCLM**

| scorer | synonyms | reorder | unit_cm | style_terse | style_long | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.68 | 1.00 | — | 0.68 | 0.68 | 1.00 | 0.68 | 0.68 | 0.68 |
| rougeL | 0.68 | 0.70 | — | 0.68 | 0.68 | 1.00 | 0.68 | 0.68 | 0.68 |
| chrf | 0.68 | 1.00 | — | 0.68 | 0.68 | 1.00 | 0.78 | 0.74 | 0.68 |
| bertscore[roberta-large] | 0.68 | 0.68 | — | 0.68 | 0.68 | 1.00 | 0.68 | 0.68 | 0.68 |
| ratescore | 0.68 | 0.98 | — | 0.97 | 0.68 | 1.00 | 0.99 | 0.99 | 0.99 |

**TN3K**

| scorer | synonyms | reorder | unit_cm | style_terse | style_long | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.16 | 1.00 | — | 0.16 | 0.16 | — | 0.16 | 0.16 | 0.16 |
| rougeL | 0.16 | 0.16 | — | 0.16 | 0.16 | — | 0.16 | 0.30 | 0.16 |
| chrf | 0.16 | 1.00 | — | 0.16 | 0.16 | — | 0.47 | 0.45 | 0.16 |
| bertscore[roberta-large] | 0.16 | 0.16 | — | 0.16 | 0.16 | — | 0.16 | 0.16 | 0.16 |
| ratescore | 0.34 | 0.78 | — | 0.36 | 0.28 | — | 0.77 | 0.77 | 0.77 |

**TN5000**

| scorer | synonyms | reorder | unit_cm | style_terse | style_long | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.15 | 1.00 | — | 0.15 | 0.15 | — | 0.15 | 0.15 | 0.15 |
| rougeL | 0.15 | 0.15 | — | 0.15 | 0.15 | — | 0.15 | 0.31 | 0.15 |
| chrf | 0.15 | 1.00 | — | 0.15 | 0.15 | — | 0.47 | 0.46 | 0.15 |
| bertscore[roberta-large] | 0.15 | 0.15 | — | 0.15 | 0.15 | — | 0.15 | 0.15 | 0.15 |
| ratescore | 0.38 | 0.78 | — | 0.42 | 0.25 | — | 0.77 | 0.77 | 0.77 |

**DDTI**

| scorer | synonyms | reorder | unit_cm | style_terse | style_long | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.10 | 0.81 | — | 0.10 | 0.10 | — | 0.12 | 0.18 | 0.10 |
| rougeL | 0.12 | 0.10 | — | 0.12 | 0.12 | — | 0.12 | 0.18 | 0.12 |
| chrf | 0.10 | 0.80 | — | 0.10 | 0.12 | — | 0.44 | 0.42 | 0.15 |
| bertscore[roberta-large] | 0.13 | 0.11 | — | 0.12 | 0.10 | — | 0.17 | 0.14 | 0.10 |
| ratescore | 0.21 | 0.78 | — | 0.24 | 0.21 | — | 0.77 | 0.77 | 0.77 |

**HC18**

| scorer | synonyms | reorder | unit_cm | style_terse | style_long | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 | — | 0.00 | 0.00 | 0.00 |
| rougeL | 0.50 | 0.00 | 0.00 | 0.00 | 0.00 | — | 0.00 | 0.00 | 0.00 |
| chrf | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 | — | 0.00 | 0.00 | 0.00 |
| bertscore[roberta-large] | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | — | 0.00 | 0.00 | 0.00 |
| ratescore | 0.07 | 1.00 | 0.20 | 0.00 | 0.10 | — | 1.00 | 1.00 | 1.00 |

**FetalHead**

| scorer | synonyms | reorder | unit_cm | style_terse | style_long | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.10 | 1.00 | 0.00 | 0.00 | 0.01 | — | 0.00 | 0.00 | 0.00 |
| rougeL | 0.50 | 0.00 | 0.00 | 0.00 | 0.01 | — | 0.00 | 0.00 | 0.00 |
| chrf | 0.20 | 1.00 | 0.44 | 0.01 | 0.09 | — | 0.21 | 0.21 | 0.00 |
| bertscore[roberta-large] | 0.20 | 0.00 | 0.20 | 0.00 | 0.21 | — | 0.00 | 0.00 | 0.00 |
| ratescore | 0.09 | 1.00 | 0.38 | 0.00 | 0.21 | — | 1.00 | 1.00 | 1.00 |
