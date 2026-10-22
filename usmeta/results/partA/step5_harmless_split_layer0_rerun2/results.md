# Step 5 re-run 2: matched-edit-size harmless group added (plain-language summary)

**Why this re-run.** In Step 5 even `harmless_small` (synonyms, reorder) changed 5-10 times more text than a planted error (17-36% of tokens vs 2-4%), so AUROC mixed "did a fact change" with "how much text changed". This re-run adds **`synonym1`** (harmless_type `matched`): the reference with exactly ONE substitution (mass -> lesion, margins -> borders, Assessment: -> Impression:, is seen -> is demonstrated, about <-> approximately; fetal: Head -> Cranial). New file **bench_v2c.jsonl** = bench_v2b + 4,812 matched rows (bench_v2 and bench_v2b untouched). Only the 3,839 new text pairs were scored (cached scores reused for the rest, pair-checked). Scorers: BLEU, ROUGE-L, chrF, BERTScore roberta-large, RaTEScore.

**Wiring gate:** identical-copy score 1.0000 for every scorer on every dataset (min 0.9999997).

**Edit size is now matched.** Share of tokens changed: `synonym1` vs planted errors: BrEaST 2.5% vs 2.3-2.6%; BUS-BRA 3.2% vs 3.2-4.2%; TN5000 4.3% vs 4.3-8.7%. (HC18 is not matched: its text is only ~6 tokens, so one word is 17%; read fetal rows with that in mind.)

**Result (AUROC of planted error vs the matched harmless synonym; 0.5 = chance):**
- **BLEU and ROUGE-L move above chance**: BrEaST 0.60 / 0.58, BUS-BRA 0.75 / 0.66, BUSI 0.82 / 0.74, TN3K 0.82 / 0.73, BUS-UCLM 0.92 / 0.89. RaTEScore 0.52-0.66 on breast, 0.53-0.56 on thyroid.
- **chrF stays below chance** (BrEaST 0.24, BUS-BRA 0.37, TN3K 0.45): changing a word ("mass" -> "lesion") alters many characters, changing a number alters one.
- **BERTScore is at chance** on breast and thyroid (BrEaST 0.52, BUS-BRA 0.42, UDIAT 0.52, TN3K 0.58, DDTI 0.53).
- **So the earlier below-chance numbers were mostly an edit-size effect**, but removing it does not make the scorers good: the best they reach on BrEaST is 0.63 (RaTEScore).
- **By error category (vs matched synonym), BrEaST:** wrong measurement BLEU **0.50 exactly** (a pure tie: the scorer gives the size error and the synonym the same score, i.e. it cannot tell them apart), chrF 0.00, BERTScore 0.07, RaTEScore 0.76; wrong location BLEU 0.50, chrF 0.00, BERTScore 0.20, RaTEScore 0.18; wrong severity/category 0.50 / 0.27 / 0.55 / 0.57. Missed and false findings are caught (0.65-0.95) because they are big edits.
- **Wrong measurement stays unseen:** size-error score is identical for x0.5, x1.5, x2 (BLEU 0.952 on BrEaST) and rho ~ 0.

**Honest reading.** When edit size is matched, word-overlap scorers go from "systematically wrong" to "roughly chance to modest", and they are decided by how many characters or tokens differ, not by clinical meaning. Style swaps (harmless_large) remain a failure at 0.00-0.33 for every scorer. Which harmless group is the "right" comparison is a design choice we should agree on before quoting one AUROC.

**Caveats (keep visible).** Templated, label-derived reports (synthetic but fact-correct); severity provisional pending clinician; template sources "to confirm" (usmeta/docs/templates_sources.md); per dataset only, never pooled; datasets support different error types; critical-only 1.00 on TN3K/TN5000 comes from missed/false lesion being the only severity-3 error; RaTEScore is built for chest/CT; 150 cases per dataset (256 BrEaST).

---

## Share of tokens changed vs the reference (mean)

**BrEaST**: ERR:false finding 0.04, ERR:missed finding 0.73, ERR:wrong location 0.02, ERR:wrong measurement 0.02, ERR:wrong severity/category 0.03, hedge 0.08, negation 0.08, pad1 0.06, pad3 0.16, reorder 0.36, style_long 0.54, style_terse 0.64, synonym1 0.02, synonyms 0.18, unit_cm 0.05
**BUS-BRA**: ERR:false finding 0.06, ERR:missed finding 0.95, ERR:wrong location 0.03, ERR:wrong measurement 0.03, ERR:wrong severity/category 0.04, hedge 0.10, pad1 0.07, pad3 0.20, reorder 0.24, style_long 0.38, style_terse 0.44, synonym1 0.03, synonyms 0.17
**TN5000**: ERR:false finding 0.11, ERR:missed finding 0.86, ERR:wrong location 0.04, ERR:wrong measurement 0.04, ERR:wrong severity/category 0.09, hedge 0.13, pad1 0.10, pad3 0.26, reorder 0.13, style_long 0.33, style_terse 0.66, synonym1 0.04, synonyms 0.18

## breast

### BrEaST (256 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.25 (0.24–0.26) | 0.60 (0.60–0.61) | 0.08 (0.07–0.09) | 0.38 / 0.51 / 0.38 | 0.85 | 0.95 | 0.38 | 1.0000 | 0.00 | -0.12 | count —, size 0.00, birads -0.02 |
| rougeL | 0.10 (0.09–0.12) | 0.58 (0.57–0.59) | 0.08 (0.07–0.09) | 0.38 / 0.64 / 0.38 | 0.80 | 0.98 | 0.59 | 1.0000 | 0.04 | -0.21 | count —, size 0.00, birads -0.02 |
| chrf | 0.37 (0.36–0.38) | 0.24 (0.23–0.25) | 0.08 (0.07–0.09) | 0.62 / 0.44 / 0.38 | 0.92 | 0.96 | 0.73 | 1.0000 | 0.02 | -0.33 | count —, size -0.06, birads -0.22 |
| bertscore[roberta-large] | 0.21 (0.19–0.22) | 0.52 (0.52–0.53) | 0.08 (0.07–0.09) | 0.48 / 0.71 / 0.38 | 0.98 | 1.00 | 0.95 | 1.0000 | 0.84 | -0.35 | count —, size -0.03, birads -0.39 |
| ratescore | 0.44 (0.43–0.45) | 0.63 (0.63–0.64) | 0.13 (0.12–0.15) | 0.67 / 0.72 / 0.46 | 0.92 | 0.97 | 0.83 | 1.0000 | 0.50 | -0.38 | count —, size -0.01, birads 0.02 |

### BUS-BRA (151 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.20 (0.19–0.21) | 0.75 (0.74–0.76) | 0.09 (0.09–0.09) | 0.28 / 0.76 / 0.28 | 0.82 | 0.95 | 0.54 | 1.0000 | 0.00 | -0.05 | count —, size 0.00, birads 0.02 |
| rougeL | 0.09 (0.09–0.09) | 0.66 (0.66–0.67) | 0.09 (0.09–0.09) | 0.28 / 0.64 / 0.28 | 0.79 | 0.97 | 0.70 | 1.0000 | 0.00 | -0.01 | count —, size 0.00, birads 0.02 |
| chrf | 0.31 (0.30–0.31) | 0.37 (0.37–0.38) | 0.09 (0.09–0.09) | 0.50 / 0.58 / 0.28 | 0.88 | 0.95 | 0.74 | 1.0000 | 0.02 | -0.27 | count —, size -0.00, birads -0.46 |
| bertscore[roberta-large] | 0.09 (0.09–0.09) | 0.42 (0.41–0.43) | 0.09 (0.09–0.09) | 0.28 / 0.46 / 0.28 | 0.97 | 0.99 | 0.95 | 1.0000 | 0.84 | -0.27 | count —, size 0.00, birads -0.68 |
| ratescore | 0.53 (0.52–0.54) | 0.66 (0.65–0.67) | 0.20 (0.18–0.21) | 0.60 / 0.70 / 0.31 | 0.92 | 0.96 | 0.87 | 1.0000 | 0.50 | -0.17 | count —, size -0.01, birads -0.00 |

### BUSI (150 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.63 (0.61–0.66) | 0.82 (0.80–0.83) | 0.27 (0.22–0.32) | 0.78 / 0.69 / 0.58 | 0.80 | 0.90 | 0.48 | 1.0000 | 0.01 | -0.09 | count —, size 0.00 |
| rougeL | 0.30 (0.25–0.35) | 0.74 (0.72–0.76) | 0.27 (0.22–0.32) | 0.58 / 0.79 / 0.58 | 0.85 | 0.95 | 0.65 | 1.0000 | 0.04 | -0.23 | count —, size 0.00 |
| chrf | 0.63 (0.61–0.66) | 0.54 (0.51–0.58) | 0.27 (0.22–0.32) | 0.79 / 0.86 / 0.58 | 0.88 | 0.93 | 0.71 | 1.0000 | 0.05 | -0.37 | count —, size 0.00 |
| bertscore[roberta-large] | 0.27 (0.22–0.32) | 0.51 (0.48–0.55) | 0.27 (0.22–0.32) | 0.58 / 0.84 / 0.58 | 0.97 | 0.99 | 0.95 | 1.0000 | 0.86 | -0.50 | count —, size -0.03 |
| ratescore | 0.60 (0.57–0.63) | 0.68 (0.66–0.71) | 0.59 (0.55–0.62) | 0.78 / 0.86 / 0.79 | 0.91 | 0.93 | 0.86 | 1.0000 | 0.50 | -0.80 | count —, size -0.00 |

### UDIAT (150 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.50 (0.50–0.50) | 0.78 (0.78–0.78) | 0.11 (0.11–0.12) | 0.75 / 0.88 / 0.50 | 0.83 | 0.94 | 0.52 | 1.0000 | 0.00 | -0.17 | count —, size — |
| rougeL | 0.11 (0.11–0.12) | 0.67 (0.67–0.67) | 0.11 (0.11–0.12) | 0.50 / 0.75 / 0.50 | 0.84 | 0.96 | 0.65 | 1.0000 | 0.00 | -0.14 | count —, size — |
| chrf | 0.50 (0.49–0.51) | 0.44 (0.44–0.44) | 0.11 (0.11–0.12) | 0.75 / 1.00 / 0.50 | 0.89 | 0.95 | 0.74 | 1.0000 | 0.03 | -0.32 | count —, size 0.01 |
| bertscore[roberta-large] | 0.11 (0.11–0.12) | 0.52 (0.51–0.53) | 0.11 (0.11–0.12) | 0.50 / 0.93 / 0.50 | 0.97 | 0.99 | 0.95 | 1.0000 | 0.85 | -0.55 | count —, size -0.03 |
| ratescore | 0.53 (0.53–0.54) | 0.64 (0.62–0.66) | 0.51 (0.50–0.52) | 0.75 / 0.85 / 0.75 | 0.92 | 0.94 | 0.86 | 1.0000 | 0.50 | -0.71 | count —, size 0.00 |

### BUS-UCLM (152 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.84 (0.80–0.87) | 0.92 (0.90–0.93) | 0.68 (0.61–0.74) | 0.90 / 0.86 / 0.81 | 0.76 | 0.80 | 0.43 | 1.0000 | 0.02 | -0.37 | count —, size 0.00 |
| rougeL | 0.69 (0.63–0.75) | 0.89 (0.86–0.91) | 0.68 (0.61–0.74) | 0.81 / 0.91 / 0.81 | 0.82 | 0.91 | 0.65 | 1.0000 | 0.14 | -0.48 | count —, size 0.00 |
| chrf | 0.84 (0.80–0.87) | 0.79 (0.75–0.84) | 0.68 (0.61–0.74) | 0.91 / 0.93 / 0.81 | 0.87 | 0.87 | 0.68 | 1.0000 | 0.11 | -0.60 | count —, size -0.02 |
| bertscore[roberta-large] | 0.68 (0.61–0.74) | 0.78 (0.74–0.83) | 0.68 (0.61–0.74) | 0.81 / 0.92 / 0.81 | 0.97 | 0.99 | 0.95 | 1.0000 | 0.87 | -0.65 | count —, size 0.05 |
| ratescore | 0.83 (0.79–0.86) | 0.86 (0.83–0.89) | 0.82 (0.78–0.86) | 0.90 / 0.94 / 0.90 | 0.96 | 0.96 | 0.86 | 1.0000 | 0.50 | -0.84 | count —, size 0.02 |

## thyroid

### TN3K (150 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.58 (0.58–0.58) | 0.82 (0.81–0.82) | 0.16 (0.15–0.16) | 1.00 / 1.00 / 1.00 | 0.80 | 0.90 | 0.44 | 1.0000 | 0.00 | -0.36 | count —, size 0.00 |
| rougeL | 0.16 (0.15–0.16) | 0.73 (0.72–0.73) | 0.16 (0.15–0.16) | 1.00 / 1.00 / 1.00 | 0.84 | 0.96 | 0.63 | 1.0000 | 0.00 | -0.48 | count —, size 0.00 |
| chrf | 0.58 (0.58–0.58) | 0.45 (0.44–0.46) | 0.16 (0.15–0.16) | 1.00 / 1.00 / 1.00 | 0.86 | 0.92 | 0.70 | 1.0000 | 0.03 | -0.26 | count —, size 0.05 |
| bertscore[roberta-large] | 0.16 (0.15–0.16) | 0.58 (0.57–0.60) | 0.16 (0.15–0.16) | 1.00 / 1.00 / 1.00 | 0.97 | 0.99 | 0.94 | 1.0000 | 0.86 | -0.38 | count —, size -0.02 |
| ratescore | 0.56 (0.55–0.57) | 0.53 (0.51–0.55) | 0.32 (0.31–0.33) | 1.00 / 1.00 / 1.00 | 0.88 | 0.88 | 0.74 | 1.0000 | 0.50 | -0.32 | count —, size -0.09 |

### TN5000 (150 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.58 (0.58–0.58) | 0.82 (0.82–0.82) | 0.15 (0.15–0.16) | 1.00 / 1.00 / 1.00 | 0.80 | 0.90 | 0.44 | 1.0000 | 0.00 | -0.36 | count —, size — |
| rougeL | 0.15 (0.15–0.16) | 0.73 (0.73–0.73) | 0.15 (0.15–0.16) | 1.00 / 1.00 / 1.00 | 0.84 | 0.96 | 0.63 | 1.0000 | 0.00 | -0.50 | count —, size — |
| chrf | 0.58 (0.58–0.58) | 0.46 (0.45–0.47) | 0.15 (0.15–0.16) | 1.00 / 1.00 / 1.00 | 0.86 | 0.92 | 0.71 | 1.0000 | 0.03 | -0.27 | count —, size -0.02 |
| bertscore[roberta-large] | 0.15 (0.15–0.16) | 0.55 (0.54–0.56) | 0.15 (0.15–0.16) | 1.00 / 1.00 / 1.00 | 0.97 | 0.99 | 0.94 | 1.0000 | 0.86 | -0.33 | count —, size -0.05 |
| ratescore | 0.58 (0.57–0.59) | 0.54 (0.53–0.56) | 0.33 (0.32–0.34) | 1.00 / 1.00 / 1.00 | 0.88 | 0.89 | 0.76 | 1.0000 | 0.50 | -0.37 | count —, size -0.11 |

### DDTI (150 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.45 (0.43–0.46) | 0.67 (0.65–0.68) | 0.10 (0.09–0.10) | 0.70 / 0.73 / 0.70 | 0.80 | 0.93 | 0.43 | 1.0000 | 0.00 | -0.31 | count —, size 0.00, tirads 0.02 |
| rougeL | 0.12 (0.10–0.14) | 0.66 (0.65–0.67) | 0.12 (0.10–0.14) | 0.72 / 0.86 / 0.72 | 0.73 | 0.97 | 0.61 | 1.0000 | 0.02 | -0.31 | count —, size 0.00, tirads 0.03 |
| chrf | 0.44 (0.43–0.46) | 0.36 (0.34–0.38) | 0.11 (0.10–0.12) | 0.70 / 0.72 / 0.71 | 0.87 | 0.95 | 0.68 | 1.0000 | 0.02 | -0.35 | count —, size -0.01, tirads -0.22 |
| bertscore[roberta-large] | 0.13 (0.11–0.15) | 0.53 (0.51–0.54) | 0.11 (0.10–0.12) | 0.72 / 0.79 / 0.71 | 0.97 | 1.00 | 0.95 | 1.0000 | 0.84 | -0.60 | count —, size -0.01, tirads -0.44 |
| ratescore | 0.50 (0.48–0.52) | 0.56 (0.54–0.57) | 0.23 (0.20–0.26) | 0.77 / 0.80 / 0.70 | 0.88 | 0.92 | 0.76 | 1.0000 | 0.50 | -0.38 | count —, size -0.02, tirads -0.01 |

## fetal

### HC18 (150 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.33 (0.33–0.33) | 0.50 (0.50–0.50) | 0.00 (0.00–0.00) | 0.33 / 0.50 / 0.00 | 0.58 | 0.60 | 0.20 | 1.0000 | 0.05 | — | hc_mm — |
| rougeL | 0.17 (0.17–0.17) | 0.50 (0.50–0.50) | 0.00 (0.00–0.00) | 0.17 / 0.50 / 0.00 | 0.72 | 0.86 | 0.68 | 1.0000 | 0.00 | — | hc_mm — |
| chrf | 0.33 (0.33–0.34) | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | 0.33 / 0.00 / 0.00 | 0.85 | 0.79 | 0.45 | 1.0000 | 0.05 | -0.26 | hc_mm -0.26 |
| bertscore[roberta-large] | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | 0.00 / 0.00 / 0.00 | 0.97 | 0.98 | 0.93 | 1.0000 | 0.87 | -0.34 | hc_mm -0.34 |
| ratescore | 0.42 (0.41–0.44) | 0.11 (0.08–0.14) | 0.05 (0.04–0.07) | 0.51 / 0.18 / 0.10 | 0.89 | 0.83 | 0.61 | 1.0000 | 0.50 | -0.42 | hc_mm -0.42 |

### FetalHead (151 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.37 (0.37–0.37) | 0.55 (0.55–0.56) | 0.00 (0.00–0.01) | 0.33 / 0.50 / 0.00 | 0.79 | 0.80 | 0.35 | 1.0000 | 0.01 | 0.00 | hc_mm — |
| rougeL | 0.17 (0.17–0.17) | 0.50 (0.50–0.50) | 0.00 (0.00–0.01) | 0.17 / 0.50 / 0.00 | 0.72 | 0.90 | 0.79 | 1.0000 | 0.00 | 0.00 | hc_mm — |
| chrf | 0.55 (0.53–0.56) | 0.21 (0.20–0.22) | 0.05 (0.04–0.06) | 0.50 / 0.00 / 0.00 | 0.93 | 0.89 | 0.70 | 1.0000 | 0.04 | -0.33 | hc_mm -0.47 |
| bertscore[roberta-large] | 0.13 (0.13–0.13) | 0.21 (0.20–0.22) | 0.10 (0.10–0.11) | 0.00 / 0.00 / 0.00 | 0.97 | 0.98 | 0.95 | 1.0000 | 0.84 | -0.23 | hc_mm -0.32 |
| ratescore | 0.49 (0.47–0.51) | 0.38 (0.35–0.40) | 0.11 (0.08–0.13) | 0.52 / 0.38 / 0.07 | 0.93 | 0.91 | 0.63 | 1.0000 | 0.50 | -0.13 | hc_mm -0.16 |

## AUROC by error category (vs harmless_small / vs matched 1-word / vs harmless_large)

**BrEaST**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| bleu | 0.49 / 0.86 / 0.02 | 0.88 / 0.95 / 0.84 | 0.00 / 0.50 / 0.00 | 0.00 / 0.50 / 0.00 | 0.17 / 0.50 / 0.00 |
| rougeL | 0.09 / 0.84 / 0.02 | 0.85 / 0.93 / 0.84 | 0.00 / 0.42 / 0.00 | 0.00 / 0.42 / 0.00 | 0.02 / 0.50 / 0.00 |
| chrf | 0.50 / 0.12 / 0.02 | 0.88 / 0.89 / 0.84 | 0.67 / 0.00 / 0.00 | 0.01 / 0.00 / 0.00 | 0.37 / 0.27 / 0.00 |
| bertscore[roberta-large] | 0.26 / 0.80 / 0.02 | 0.86 / 0.94 / 0.84 | 0.00 / 0.20 / 0.00 | 0.00 / 0.07 / 0.00 | 0.16 / 0.55 / 0.00 |
| ratescore | 0.42 / 0.65 / 0.07 | 0.89 / 0.91 / 0.85 | 0.17 / 0.18 / 0.00 | 0.34 / 0.76 / 0.01 | 0.43 / 0.57 / 0.08 |

**BUS-BRA**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| bleu | 0.50 / 1.00 / 0.00 | 1.00 / 1.00 / 1.00 | 0.00 / 0.67 / 0.00 | 0.00 / 0.67 / 0.00 | 0.17 / 0.74 / 0.00 |
| rougeL | 0.00 / 1.00 / 0.00 | 1.00 / 1.00 / 1.00 | 0.00 / 0.50 / 0.00 | 0.00 / 0.50 / 0.00 | 0.00 / 0.69 / 0.00 |
| chrf | 0.50 / 0.33 / 0.00 | 1.00 / 1.00 / 1.00 | 0.21 / 0.38 / 0.00 | 0.00 / 0.00 / 0.00 | 0.37 / 0.53 / 0.00 |
| bertscore[roberta-large] | 0.00 / 1.00 / 0.00 | 1.00 / 1.00 / 1.00 | 0.00 / 0.06 / 0.00 | 0.00 / 0.00 / 0.00 | 0.00 / 0.60 / 0.00 |
| ratescore | 0.48 / 0.65 / 0.03 | 1.00 / 1.00 / 1.00 | 0.43 / 0.57 / 0.03 | 0.50 / 0.67 / 0.06 | 0.50 / 0.63 / 0.21 |

**BUSI**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| bleu | 0.58 / 1.00 / 0.17 | 1.00 / 1.00 / 1.00 | 0.50 / 0.75 / 0.00 | 0.50 / 0.75 / 0.00 | 0.49 / 0.62 / 0.00 |
| rougeL | 0.17 / 1.00 / 0.17 | 1.00 / 1.00 / 1.00 | 0.00 / 0.50 / 0.00 | 0.00 / 0.50 / 0.00 | 0.12 / 0.75 / 0.00 |
| chrf | 0.58 / 0.58 / 0.17 | 1.00 / 1.00 / 1.00 | 0.50 / 0.50 / 0.00 | 0.49 / 0.00 / 0.00 | 0.50 / 0.83 / 0.00 |
| bertscore[roberta-large] | 0.17 / 0.99 / 0.17 | 1.00 / 1.00 / 1.00 | 0.00 / 0.00 / 0.00 | 0.00 / 0.00 / 0.00 | 0.00 / 0.64 / 0.00 |
| ratescore | 0.58 / 0.73 / 0.58 | 1.00 / 1.00 / 1.00 | 0.21 / 0.25 / 0.00 | 0.48 / 0.60 / 0.48 | 0.48 / 0.59 / 0.49 |

**UDIAT**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| bleu | 0.50 / 1.00 / 0.00 | 1.00 / 1.00 / 1.00 | 0.50 / 0.75 / 0.00 | 0.50 / 0.75 / 0.00 | 0.33 / 0.67 / 0.00 |
| rougeL | 0.00 / 1.00 / 0.00 | 1.00 / 1.00 / 1.00 | 0.00 / 0.50 / 0.00 | 0.00 / 0.50 / 0.00 | 0.00 / 0.67 / 0.00 |
| chrf | 0.50 / 0.50 / 0.00 | 1.00 / 1.00 / 1.00 | 0.50 / 0.50 / 0.00 | 0.42 / 0.00 / 0.00 | 0.40 / 0.67 / 0.00 |
| bertscore[roberta-large] | 0.00 / 1.00 / 0.00 | 1.00 / 1.00 / 1.00 | 0.00 / 0.00 / 0.00 | 0.00 / 0.00 / 0.00 | 0.00 / 0.85 / 0.00 |
| ratescore | 0.47 / 0.66 / 0.45 | 1.00 / 1.00 / 1.00 | 0.22 / 0.25 / 0.00 | 0.50 / 0.62 / 0.50 | 0.50 / 0.63 / 0.50 |

**BUS-UCLM**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| bleu | 0.82 / 1.00 / 0.63 | 1.00 / 1.00 / 1.00 | 0.50 / 0.75 / 0.00 | 0.50 / 0.75 / 0.00 | 0.49 / 0.62 / 0.00 |
| rougeL | 0.63 / 1.00 / 0.63 | 1.00 / 1.00 / 1.00 | 0.00 / 0.50 / 0.00 | 0.00 / 0.50 / 0.00 | 0.12 / 0.75 / 0.00 |
| chrf | 0.82 / 0.82 / 0.63 | 1.00 / 1.00 / 1.00 | 0.50 / 0.50 / 0.00 | 0.49 / 0.00 / 0.00 | 0.50 / 0.82 / 0.00 |
| bertscore[roberta-large] | 0.63 / 1.00 / 0.63 | 1.00 / 1.00 / 1.00 | 0.00 / 0.00 / 0.00 | 0.00 / 0.00 / 0.00 | 0.00 / 0.60 / 0.00 |
| ratescore | 0.82 / 0.87 / 0.82 | 1.00 / 1.00 / 1.00 | 0.24 / 0.25 / 0.00 | 0.48 / 0.59 / 0.48 | 0.48 / 0.58 / 0.49 |

**TN3K**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| bleu | 0.50 / 1.00 / 0.00 | 1.00 / 1.00 / 1.00 | 0.50 / 0.66 / 0.00 | 0.50 / 0.67 / 0.00 | 0.50 / 1.00 / 0.00 |
| rougeL | 0.00 / 1.00 / 0.00 | 1.00 / 1.00 / 1.00 | 0.00 / 0.50 / 0.00 | 0.00 / 0.50 / 0.00 | 0.00 / 1.00 / 0.00 |
| chrf | 0.50 / 1.00 / 0.00 | 1.00 / 1.00 / 1.00 | 0.50 / 0.00 / 0.00 | 0.50 / 0.00 / 0.00 | 0.50 / 1.00 / 0.00 |
| bertscore[roberta-large] | 0.00 / 1.00 / 0.00 | 1.00 / 1.00 / 1.00 | 0.00 / 0.19 / 0.00 | 0.00 / 0.25 / 0.00 | 0.00 / 1.00 / 0.00 |
| ratescore | 0.66 / 0.62 / 0.25 | 1.00 / 1.00 / 1.00 | 0.33 / 0.26 / 0.01 | 0.30 / 0.24 / 0.00 | 0.94 / 0.90 / 0.80 |

**TN5000**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| bleu | 0.50 / 1.00 / 0.00 | 1.00 / 1.00 / 1.00 | 0.50 / 0.67 / 0.00 | 0.50 / 0.67 / 0.00 | 0.50 / 1.00 / 0.00 |
| rougeL | 0.00 / 1.00 / 0.00 | 1.00 / 1.00 / 1.00 | 0.00 / 0.50 / 0.00 | 0.00 / 0.50 / 0.00 | 0.00 / 1.00 / 0.00 |
| chrf | 0.50 / 1.00 / 0.00 | 1.00 / 1.00 / 1.00 | 0.50 / 0.00 / 0.00 | 0.50 / 0.00 / 0.00 | 0.50 / 1.00 / 0.00 |
| bertscore[roberta-large] | 0.00 / 1.00 / 0.00 | 1.00 / 1.00 / 1.00 | 0.00 / 0.21 / 0.00 | 0.00 / 0.16 / 0.00 | 0.00 / 1.00 / 0.00 |
| ratescore | 0.76 / 0.72 / 0.41 | 1.00 / 1.00 / 1.00 | 0.30 / 0.19 / 0.00 | 0.30 / 0.26 / 0.01 | 0.95 / 0.92 / 0.74 |

**DDTI**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| bleu | 0.49 / 1.00 / 0.00 | 0.88 / 1.00 / 0.75 | 0.50 / 0.64 / 0.00 | 0.50 / 0.63 / 0.00 | 0.32 / 0.59 / 0.00 |
| rougeL | 0.03 / 0.89 / 0.03 | 0.75 / 0.88 / 0.75 | 0.00 / 0.50 / 0.00 | 0.00 / 0.50 / 0.00 | 0.00 / 0.74 / 0.00 |
| chrf | 0.49 / 0.80 / 0.01 | 0.88 / 1.00 / 0.75 | 0.50 / 0.00 / 0.00 | 0.48 / 0.00 / 0.00 | 0.31 / 0.46 / 0.00 |
| bertscore[roberta-large] | 0.08 / 1.00 / 0.01 | 0.79 / 1.00 / 0.75 | 0.00 / 0.10 / 0.00 | 0.00 / 0.16 / 0.00 | 0.00 / 0.65 / 0.00 |
| ratescore | 0.54 / 0.75 / 0.23 | 0.87 / 0.97 / 0.78 | 0.36 / 0.32 / 0.02 | 0.31 / 0.29 / 0.00 | 0.57 / 0.66 / 0.31 |

**HC18**

| scorer | wrong measurement |
|---|---|
| bleu | 0.33 / 0.50 / 0.00 |
| rougeL | 0.17 / 0.50 / 0.00 |
| chrf | 0.33 / 0.00 / 0.00 |
| bertscore[roberta-large] | 0.00 / 0.00 / 0.00 |
| ratescore | 0.42 / 0.11 / 0.05 |

**FetalHead**

| scorer | wrong measurement | wrong severity/category |
|---|---|---|
| bleu | 0.33 / 0.50 / 0.00 | 0.50 / 0.75 / 0.00 |
| rougeL | 0.17 / 0.50 / 0.00 | 0.17 / 0.50 / 0.00 |
| chrf | 0.43 / 0.00 / 0.00 | 1.00 / 1.00 / 0.21 |
| bertscore[roberta-large] | 0.00 / 0.00 / 0.00 | 0.67 / 1.00 / 0.50 |
| ratescore | 0.47 / 0.32 / 0.08 | 0.59 / 0.56 / 0.21 |

## AUROC against each harmless group separately (errors vs that group only)

**BrEaST**

| scorer | synonym1 | synonyms | reorder | unit_cm | style_terse | style_long | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.60 | 0.08 | 0.33 | 0.32 | 0.08 | 0.08 | 0.14 | 0.10 | 0.20 | 0.08 |
| rougeL | 0.58 | 0.08 | 0.08 | 0.14 | 0.08 | 0.08 | 0.14 | 0.08 | 0.08 | 0.08 |
| chrf | 0.24 | 0.08 | 0.52 | 0.52 | 0.08 | 0.08 | 0.19 | 0.42 | 0.35 | 0.10 |
| bertscore[roberta-large] | 0.52 | 0.08 | 0.08 | 0.45 | 0.08 | 0.08 | 0.25 | 0.09 | 0.08 | 0.08 |
| ratescore | 0.63 | 0.08 | 0.86 | 0.37 | 0.19 | 0.08 | 0.32 | 0.86 | 0.86 | 0.86 |

**BUS-BRA**

| scorer | synonym1 | synonyms | reorder | unit_cm | style_terse | style_long | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.75 | 0.09 | 0.31 | — | 0.09 | 0.09 | — | 0.09 | 0.09 | 0.09 |
| rougeL | 0.66 | 0.09 | 0.09 | — | 0.09 | 0.09 | — | 0.09 | 0.09 | 0.09 |
| chrf | 0.37 | 0.09 | 0.52 | — | 0.09 | 0.09 | — | 0.43 | 0.38 | 0.09 |
| bertscore[roberta-large] | 0.42 | 0.09 | 0.09 | — | 0.09 | 0.09 | — | 0.09 | 0.09 | 0.09 |
| ratescore | 0.66 | 0.14 | 0.92 | — | 0.23 | 0.17 | — | 0.91 | 0.91 | 0.91 |

**BUSI**

| scorer | synonym1 | synonyms | reorder | unit_cm | style_terse | style_long | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.82 | 0.27 | 1.00 | — | 0.27 | 0.27 | 1.00 | 0.27 | 0.27 | 0.27 |
| rougeL | 0.74 | 0.27 | 0.32 | — | 0.27 | 0.27 | 1.00 | 0.27 | 0.27 | 0.27 |
| chrf | 0.54 | 0.27 | 1.00 | — | 0.27 | 0.27 | 1.00 | 0.50 | 0.41 | 0.27 |
| bertscore[roberta-large] | 0.51 | 0.27 | 0.27 | — | 0.27 | 0.27 | 1.00 | 0.27 | 0.27 | 0.27 |
| ratescore | 0.68 | 0.27 | 0.93 | — | 0.90 | 0.27 | 1.00 | 0.96 | 0.96 | 0.96 |

**UDIAT**

| scorer | synonym1 | synonyms | reorder | unit_cm | style_terse | style_long | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.78 | 0.11 | 0.89 | — | 0.11 | 0.11 | — | 0.11 | 0.11 | 0.11 |
| rougeL | 0.67 | 0.11 | 0.11 | — | 0.11 | 0.11 | — | 0.11 | 0.11 | 0.11 |
| chrf | 0.44 | 0.11 | 0.88 | — | 0.11 | 0.11 | — | 0.35 | 0.34 | 0.11 |
| bertscore[roberta-large] | 0.52 | 0.11 | 0.11 | — | 0.11 | 0.11 | — | 0.11 | 0.11 | 0.11 |
| ratescore | 0.64 | 0.12 | 0.95 | — | 0.90 | 0.11 | — | 0.95 | 0.95 | 0.95 |

**BUS-UCLM**

| scorer | synonym1 | synonyms | reorder | unit_cm | style_terse | style_long | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.92 | 0.68 | 1.00 | — | 0.68 | 0.68 | 1.00 | 0.68 | 0.68 | 0.68 |
| rougeL | 0.89 | 0.68 | 0.70 | — | 0.68 | 0.68 | 1.00 | 0.68 | 0.68 | 0.68 |
| chrf | 0.79 | 0.68 | 1.00 | — | 0.68 | 0.68 | 1.00 | 0.78 | 0.74 | 0.68 |
| bertscore[roberta-large] | 0.78 | 0.68 | 0.68 | — | 0.68 | 0.68 | 1.00 | 0.68 | 0.68 | 0.68 |
| ratescore | 0.86 | 0.68 | 0.98 | — | 0.97 | 0.68 | 1.00 | 0.99 | 0.99 | 0.99 |

**TN3K**

| scorer | synonym1 | synonyms | reorder | unit_cm | style_terse | style_long | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.82 | 0.16 | 1.00 | — | 0.16 | 0.16 | — | 0.16 | 0.16 | 0.16 |
| rougeL | 0.73 | 0.16 | 0.16 | — | 0.16 | 0.16 | — | 0.16 | 0.30 | 0.16 |
| chrf | 0.45 | 0.16 | 1.00 | — | 0.16 | 0.16 | — | 0.47 | 0.45 | 0.16 |
| bertscore[roberta-large] | 0.58 | 0.16 | 0.16 | — | 0.16 | 0.16 | — | 0.16 | 0.16 | 0.16 |
| ratescore | 0.53 | 0.34 | 0.78 | — | 0.36 | 0.28 | — | 0.77 | 0.77 | 0.77 |

**TN5000**

| scorer | synonym1 | synonyms | reorder | unit_cm | style_terse | style_long | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.82 | 0.15 | 1.00 | — | 0.15 | 0.15 | — | 0.15 | 0.15 | 0.15 |
| rougeL | 0.73 | 0.15 | 0.15 | — | 0.15 | 0.15 | — | 0.15 | 0.31 | 0.15 |
| chrf | 0.46 | 0.15 | 1.00 | — | 0.15 | 0.15 | — | 0.47 | 0.46 | 0.15 |
| bertscore[roberta-large] | 0.55 | 0.15 | 0.15 | — | 0.15 | 0.15 | — | 0.15 | 0.15 | 0.15 |
| ratescore | 0.54 | 0.38 | 0.78 | — | 0.42 | 0.25 | — | 0.77 | 0.77 | 0.77 |

**DDTI**

| scorer | synonym1 | synonyms | reorder | unit_cm | style_terse | style_long | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.67 | 0.10 | 0.81 | — | 0.10 | 0.10 | — | 0.12 | 0.18 | 0.10 |
| rougeL | 0.66 | 0.12 | 0.10 | — | 0.12 | 0.12 | — | 0.12 | 0.18 | 0.12 |
| chrf | 0.36 | 0.10 | 0.80 | — | 0.10 | 0.12 | — | 0.44 | 0.42 | 0.15 |
| bertscore[roberta-large] | 0.53 | 0.13 | 0.11 | — | 0.12 | 0.10 | — | 0.17 | 0.14 | 0.10 |
| ratescore | 0.56 | 0.21 | 0.78 | — | 0.24 | 0.21 | — | 0.77 | 0.77 | 0.77 |

**HC18**

| scorer | synonym1 | synonyms | reorder | unit_cm | style_terse | style_long | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.50 | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 | — | 0.00 | 0.00 | 0.00 |
| rougeL | 0.50 | 0.50 | 0.00 | 0.00 | 0.00 | 0.00 | — | 0.00 | 0.00 | 0.00 |
| chrf | 0.00 | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 | — | 0.00 | 0.00 | 0.00 |
| bertscore[roberta-large] | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | — | 0.00 | 0.00 | 0.00 |
| ratescore | 0.11 | 0.07 | 1.00 | 0.20 | 0.00 | 0.10 | — | 1.00 | 1.00 | 1.00 |

**FetalHead**

| scorer | synonym1 | synonyms | reorder | unit_cm | style_terse | style_long | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.55 | 0.10 | 1.00 | 0.00 | 0.00 | 0.01 | — | 0.00 | 0.00 | 0.00 |
| rougeL | 0.50 | 0.50 | 0.00 | 0.00 | 0.00 | 0.01 | — | 0.00 | 0.00 | 0.00 |
| chrf | 0.21 | 0.20 | 1.00 | 0.44 | 0.01 | 0.09 | — | 0.21 | 0.21 | 0.00 |
| bertscore[roberta-large] | 0.21 | 0.20 | 0.00 | 0.20 | 0.00 | 0.21 | — | 0.00 | 0.00 | 0.00 |
| ratescore | 0.38 | 0.09 | 1.00 | 0.38 | 0.00 | 0.21 | — | 1.00 | 1.00 | 1.00 |
