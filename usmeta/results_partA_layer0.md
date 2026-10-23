# Step 4: Layer 0 baseline: headline (plain language)

Scorers tested: BLEU, ROUGE-L, chrF (word/letter overlap), BERTScore roberta-large (embedding similarity), RaTEScore (radiology entity scorer, built for chest/CT). 23,759 unique report pairs from bench_v2 (27,193 rows). **Identical-copy gate passed: every scorer gives 1.0000 on identical copies on every dataset.**

**Headline numbers (AUROC: 1.0 perfect, 0.5 chance, below 0.5 = the scorer prefers the planted error to a harmless rewording):**
- On the datasets with the richest reports, **BrEaST**: BLEU 0.18, ROUGE-L 0.09, chrF 0.26, BERTScore 0.15, RaTEScore 0.32. On **BUS-BRA**: 0.15 / 0.09 / 0.20 / 0.09 / 0.36. Every scorer is below chance. A harmless rewording is penalised more than a changed fact.
- The best case is **BUS-UCLM** (BLEU 0.76, chrF 0.76, RaTEScore 0.82) and **BUSI** with RaTEScore (0.59). Those reports contain almost nothing but a mass, its position and its size, so the few errors left are big text edits, e.g. a missed lesion.
- **Wrong measurement** (size x0.5, x1.5, x2; HC +-3 to 30 mm) is the clearest failure: AUROC 0.00 for BLEU and BERTScore on BrEaST and BUS-BRA, 0.20/0.00 on HC18, RaTEScore 0.16-0.28. Size correlation with score (magnitude rho) is about 0 for all scorers: a 2x size error costs no more than a 1.5x one.
- **Missed finding** (report says "no lesion") is caught (AUROC 0.85-1.00), but only because the whole report text changes; this is a big edit, not evidence of understanding.
- **Critical-only** AUROC is 1.00 on TN3K and TN5000 for every scorer, for the same reason: on those datasets the only severity-3 errors are missed/false lesion.
- **Lazy answer** ("No abnormality.", no image): BERTScore gives **0.84-0.87**, similar to its 0.96 on a correct rewording; RaTEScore gives a flat 0.50 for every case (it finds no entities); BLEU/ROUGE-L about 0-0.14, chrF 0.02-0.11.
- Severity rho is negative (good direction) but weak: -0.01 to -0.84 depending on dataset and scorer; BLEU is near 0 on several datasets.

**Caveats:** reports are templated from labels (limitation 1); severity is provisional (pending clinician ranking); orientation and position are mask-derived proxies; BrEaST size is approximate; "missed finding" results are inflated by how big that edit is; datasets are never pooled and have different error types, so compare scorers within a dataset, not across. RaTEScore is built for chest/CT text, not ultrasound. No GREEN, no judge in this step (Layers 1-3 next).

---

# Step 4: Layer 0 baseline on bench_v2

What was run: BLEU, ROUGE-L, chrF (CPU), BERTScore (roberta-large, Apple GPU), RaTEScore (Apple GPU) on every (reference, candidate) pair of bench_v2.jsonl, plus a no-image "lazy" answer (`No abnormality.`) scored against every reference. Scores are per unique pair; analysis is per dataset (never pooled across datasets).

How to read: **AUROC** = chance that a planted error scores LOWER than a harmless rewording of the same case (paired per case, averaged over cases; 1.0 perfect, 0.5 chance, 0.0 backwards); 95% CI by bootstrap over cases (1,000). **Critical-only** uses severity-3 errors only. **Harmless mean** = mean score on primary harmless rewordings (should be high). **Identical mean** must be 1.0. **Severity ρ / magnitude ρ** = Spearman correlation of score with provisional severity / error size (negative is good). Magnitude: size = |ln ratio|, birads/tirads = steps, hc_mm = shift in mm.

Gate: lowest identical-copy score over all scorers and datasets = 1.0000 (must be about 1.0).

### BrEaST (n=256 cases)

| scorer | AUROC (95% CI) | critical-only AUROC | harmless mean | identical mean | lazy "No abnormality." mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|
| bleu | 0.18 (0.17–0.19) | 0.38 | 0.66 | 1.0000 | 0.00 | -0.12 | count —, size 0.00, birads -0.02 |
| rougeL | 0.09 (0.08–0.11) | 0.38 | 0.72 | 1.0000 | 0.04 | -0.21 | count —, size 0.00, birads -0.02 |
| chrf | 0.26 (0.25–0.27) | 0.53 | 0.84 | 1.0000 | 0.02 | -0.33 | count —, size -0.06, birads -0.22 |
| bertscore[roberta-large] | 0.15 (0.14–0.17) | 0.44 | 0.97 | 1.0000 | 0.84 | -0.35 | count —, size -0.03, birads -0.39 |
| ratescore | 0.32 (0.31–0.33) | 0.58 | 0.89 | 1.0000 | 0.50 | -0.38 | count —, size -0.01, birads 0.02 |

### BUS-BRA (n=151 cases)

| scorer | AUROC (95% CI) | critical-only AUROC | harmless mean | identical mean | lazy "No abnormality." mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|
| bleu | 0.15 (0.14–0.15) | 0.28 | 0.68 | 1.0000 | 0.00 | -0.05 | count —, size 0.00, birads 0.02 |
| rougeL | 0.09 (0.09–0.09) | 0.28 | 0.74 | 1.0000 | 0.00 | -0.01 | count —, size 0.00, birads 0.02 |
| chrf | 0.20 (0.20–0.20) | 0.39 | 0.81 | 1.0000 | 0.02 | -0.27 | count —, size -0.00, birads -0.46 |
| bertscore[roberta-large] | 0.09 (0.09–0.09) | 0.28 | 0.96 | 1.0000 | 0.84 | -0.27 | count —, size 0.00, birads -0.68 |
| ratescore | 0.36 (0.35–0.37) | 0.45 | 0.89 | 1.0000 | 0.50 | -0.17 | count —, size -0.01, birads -0.00 |

### BUSI (n=150 cases)

| scorer | AUROC (95% CI) | critical-only AUROC | harmless mean | identical mean | lazy "No abnormality." mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|
| bleu | 0.45 (0.41–0.49) | 0.68 | 0.64 | 1.0000 | 0.01 | -0.09 | count —, size 0.00 |
| rougeL | 0.28 (0.23–0.33) | 0.58 | 0.75 | 1.0000 | 0.04 | -0.23 | count —, size 0.00 |
| chrf | 0.45 (0.41–0.49) | 0.69 | 0.79 | 1.0000 | 0.05 | -0.37 | count —, size 0.00 |
| bertscore[roberta-large] | 0.27 (0.22–0.32) | 0.58 | 0.96 | 1.0000 | 0.86 | -0.50 | count —, size -0.03 |
| ratescore | 0.59 (0.56–0.63) | 0.79 | 0.89 | 1.0000 | 0.50 | -0.80 | count —, size -0.00 |

### UDIAT (n=150 cases)

| scorer | AUROC (95% CI) | critical-only AUROC | harmless mean | identical mean | lazy "No abnormality." mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|
| bleu | 0.31 (0.31–0.31) | 0.62 | 0.67 | 1.0000 | 0.00 | -0.17 | count —, size — |
| rougeL | 0.11 (0.11–0.12) | 0.50 | 0.75 | 1.0000 | 0.00 | -0.14 | count —, size — |
| chrf | 0.31 (0.30–0.31) | 0.62 | 0.81 | 1.0000 | 0.03 | -0.32 | count —, size 0.01 |
| bertscore[roberta-large] | 0.11 (0.11–0.12) | 0.50 | 0.96 | 1.0000 | 0.85 | -0.55 | count —, size -0.03 |
| ratescore | 0.52 (0.52–0.53) | 0.75 | 0.89 | 1.0000 | 0.50 | -0.71 | count —, size 0.00 |

### BUS-UCLM (n=152 cases)

| scorer | AUROC (95% CI) | critical-only AUROC | harmless mean | identical mean | lazy "No abnormality." mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|
| bleu | 0.76 (0.71–0.80) | 0.86 | 0.59 | 1.0000 | 0.02 | -0.37 | count —, size 0.00 |
| rougeL | 0.68 (0.62–0.74) | 0.81 | 0.74 | 1.0000 | 0.14 | -0.48 | count —, size 0.00 |
| chrf | 0.76 (0.71–0.80) | 0.86 | 0.77 | 1.0000 | 0.11 | -0.60 | count —, size -0.02 |
| bertscore[roberta-large] | 0.68 (0.61–0.74) | 0.81 | 0.96 | 1.0000 | 0.87 | -0.65 | count —, size 0.05 |
| ratescore | 0.82 (0.79–0.86) | 0.90 | 0.91 | 1.0000 | 0.50 | -0.84 | count —, size 0.02 |

### TN3K (n=150 cases)

| scorer | AUROC (95% CI) | critical-only AUROC | harmless mean | identical mean | lazy "No abnormality." mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|
| bleu | 0.37 (0.36–0.37) | 1.00 | 0.62 | 1.0000 | 0.00 | -0.36 | count —, size 0.00 |
| rougeL | 0.16 (0.15–0.16) | 1.00 | 0.74 | 1.0000 | 0.00 | -0.48 | count —, size 0.00 |
| chrf | 0.37 (0.36–0.37) | 1.00 | 0.78 | 1.0000 | 0.03 | -0.26 | count —, size 0.05 |
| bertscore[roberta-large] | 0.16 (0.15–0.16) | 1.00 | 0.96 | 1.0000 | 0.86 | -0.38 | count —, size -0.02 |
| ratescore | 0.44 (0.43–0.45) | 1.00 | 0.81 | 1.0000 | 0.50 | -0.32 | count —, size -0.09 |

### TN5000 (n=150 cases)

| scorer | AUROC (95% CI) | critical-only AUROC | harmless mean | identical mean | lazy "No abnormality." mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|
| bleu | 0.36 (0.36–0.37) | 1.00 | 0.62 | 1.0000 | 0.00 | -0.36 | count —, size — |
| rougeL | 0.15 (0.15–0.16) | 1.00 | 0.74 | 1.0000 | 0.00 | -0.50 | count —, size — |
| chrf | 0.36 (0.36–0.37) | 1.00 | 0.78 | 1.0000 | 0.03 | -0.27 | count —, size -0.02 |
| bertscore[roberta-large] | 0.15 (0.15–0.16) | 1.00 | 0.96 | 1.0000 | 0.86 | -0.33 | count —, size -0.05 |
| ratescore | 0.46 (0.45–0.46) | 1.00 | 0.82 | 1.0000 | 0.50 | -0.37 | count —, size -0.11 |

### DDTI (n=150 cases)

| scorer | AUROC (95% CI) | critical-only AUROC | harmless mean | identical mean | lazy "No abnormality." mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|
| bleu | 0.27 (0.26–0.28) | 0.70 | 0.62 | 1.0000 | 0.00 | -0.31 | count —, size 0.00, tirads 0.02 |
| rougeL | 0.12 (0.10–0.14) | 0.72 | 0.67 | 1.0000 | 0.02 | -0.31 | count —, size 0.00, tirads 0.03 |
| chrf | 0.28 (0.27–0.29) | 0.70 | 0.78 | 1.0000 | 0.02 | -0.35 | count —, size -0.01, tirads -0.22 |
| bertscore[roberta-large] | 0.12 (0.10–0.13) | 0.71 | 0.96 | 1.0000 | 0.84 | -0.60 | count —, size -0.01, tirads -0.44 |
| ratescore | 0.36 (0.34–0.38) | 0.73 | 0.82 | 1.0000 | 0.50 | -0.38 | count —, size -0.02, tirads -0.01 |

### HC18 (n=150 cases)

| scorer | AUROC (95% CI) | critical-only AUROC | harmless mean | identical mean | lazy "No abnormality." mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|
| bleu | 0.20 (0.20–0.20) | 0.20 | 0.43 | 1.0000 | 0.05 | — | hc_mm — |
| rougeL | 0.10 (0.10–0.10) | 0.10 | 0.70 | 1.0000 | 0.00 | — | hc_mm — |
| chrf | 0.20 (0.20–0.20) | 0.20 | 0.69 | 1.0000 | 0.05 | -0.26 | hc_mm -0.26 |
| bertscore[roberta-large] | 0.00 (0.00–0.00) | 0.00 | 0.95 | 1.0000 | 0.87 | -0.34 | hc_mm -0.34 |
| ratescore | 0.27 (0.26–0.29) | 0.34 | 0.78 | 1.0000 | 0.50 | -0.42 | hc_mm -0.42 |

### FetalHead (n=151 cases)

| scorer | AUROC (95% CI) | critical-only AUROC | harmless mean | identical mean | lazy "No abnormality." mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|
| bleu | 0.22 (0.22–0.23) | 0.20 | 0.61 | 1.0000 | 0.01 | 0.00 | hc_mm — |
| rougeL | 0.10 (0.10–0.11) | 0.10 | 0.75 | 1.0000 | 0.00 | 0.00 | hc_mm — |
| chrf | 0.35 (0.34–0.36) | 0.30 | 0.84 | 1.0000 | 0.04 | -0.33 | hc_mm -0.47 |
| bertscore[roberta-large] | 0.12 (0.12–0.13) | 0.00 | 0.96 | 1.0000 | 0.84 | -0.23 | hc_mm -0.32 |
| ratescore | 0.34 (0.32–0.35) | 0.34 | 0.81 | 1.0000 | 0.50 | -0.13 | hc_mm -0.16 |

## AUROC by error category (per dataset; 1.0 perfect)

**BrEaST**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| bleu | 0.30 | 0.86 | 0.00 | 0.00 | 0.10 |
| rougeL | 0.06 | 0.85 | 0.00 | 0.00 | 0.01 |
| chrf | 0.31 | 0.86 | 0.40 | 0.00 | 0.22 |
| bertscore[roberta-large] | 0.16 | 0.85 | 0.00 | 0.00 | 0.10 |
| ratescore | 0.28 | 0.88 | 0.10 | 0.21 | 0.29 |

**BUS-BRA**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| bleu | 0.25 | 1.00 | 0.00 | 0.00 | 0.09 |
| rougeL | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 |
| chrf | 0.25 | 1.00 | 0.11 | 0.00 | 0.19 |
| bertscore[roberta-large] | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 |
| ratescore | 0.26 | 1.00 | 0.23 | 0.28 | 0.35 |

**BUSI**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| bleu | 0.37 | 1.00 | 0.25 | 0.25 | 0.25 |
| rougeL | 0.17 | 1.00 | 0.00 | 0.00 | 0.06 |
| chrf | 0.37 | 1.00 | 0.25 | 0.25 | 0.25 |
| bertscore[roberta-large] | 0.17 | 1.00 | 0.00 | 0.00 | 0.00 |
| ratescore | 0.58 | 1.00 | 0.11 | 0.48 | 0.48 |

**UDIAT**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| bleu | 0.25 | 1.00 | 0.25 | 0.25 | 0.17 |
| rougeL | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 |
| chrf | 0.25 | 1.00 | 0.25 | 0.21 | 0.20 |
| bertscore[roberta-large] | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 |
| ratescore | 0.46 | 1.00 | 0.11 | 0.50 | 0.50 |

**BUS-UCLM**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| bleu | 0.72 | 1.00 | 0.25 | 0.25 | 0.25 |
| rougeL | 0.63 | 1.00 | 0.00 | 0.00 | 0.06 |
| chrf | 0.72 | 1.00 | 0.25 | 0.25 | 0.25 |
| bertscore[roberta-large] | 0.63 | 1.00 | 0.00 | 0.00 | 0.00 |
| ratescore | 0.82 | 1.00 | 0.12 | 0.48 | 0.48 |

**TN3K**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| bleu | 0.25 | 1.00 | 0.25 | 0.25 | 0.25 |
| rougeL | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 |
| chrf | 0.25 | 1.00 | 0.25 | 0.25 | 0.25 |
| bertscore[roberta-large] | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 |
| ratescore | 0.46 | 1.00 | 0.17 | 0.15 | 0.87 |

**TN5000**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| bleu | 0.25 | 1.00 | 0.25 | 0.25 | 0.25 |
| rougeL | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 |
| chrf | 0.25 | 1.00 | 0.25 | 0.25 | 0.25 |
| bertscore[roberta-large] | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 |
| ratescore | 0.59 | 1.00 | 0.15 | 0.16 | 0.84 |

**DDTI**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| bleu | 0.24 | 0.81 | 0.25 | 0.25 | 0.16 |
| rougeL | 0.03 | 0.75 | 0.00 | 0.00 | 0.00 |
| chrf | 0.25 | 0.81 | 0.25 | 0.24 | 0.16 |
| bertscore[roberta-large] | 0.04 | 0.77 | 0.00 | 0.00 | 0.00 |
| ratescore | 0.39 | 0.82 | 0.19 | 0.16 | 0.44 |

**HC18**

| scorer | wrong measurement |
|---|---|
| bleu | 0.20 |
| rougeL | 0.10 |
| chrf | 0.20 |
| bertscore[roberta-large] | 0.00 |
| ratescore | 0.27 |

**FetalHead**

| scorer | wrong measurement | wrong severity/category |
|---|---|---|
| bleu | 0.20 | 0.30 |
| rougeL | 0.10 | 0.10 |
| chrf | 0.26 | 0.68 |
| bertscore[roberta-large] | 0.00 | 0.60 |
| ratescore | 0.31 | 0.44 |

## Secondary harmless groups (mean score; primary=false, not in the AUROC)

**BrEaST**

| scorer | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|
| bleu | 0.85 | 0.87 | 0.90 | 0.73 |
| rougeL | 0.93 | 0.93 | 0.95 | 0.85 |
| chrf | 0.95 | 0.97 | 0.97 | 0.92 |
| bertscore[roberta-large] | 0.99 | 0.98 | 0.98 | 0.97 |
| ratescore | 0.94 | 1.00 | 1.00 | 1.00 |

**BUS-BRA**

| scorer | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|
| bleu | — | 0.84 | 0.88 | 0.69 |
| rougeL | — | 0.90 | 0.93 | 0.80 |
| chrf | — | 0.96 | 0.96 | 0.89 |
| bertscore[roberta-large] | — | 0.98 | 0.97 | 0.97 |
| ratescore | — | 1.00 | 1.00 | 1.00 |

**BUSI**

| scorer | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|
| bleu | 0.59 | 0.74 | 0.79 | 0.56 |
| rougeL | 0.80 | 0.84 | 0.88 | 0.71 |
| chrf | 0.86 | 0.93 | 0.92 | 0.80 |
| bertscore[roberta-large] | 0.99 | 0.96 | 0.96 | 0.95 |
| ratescore | 0.79 | 1.00 | 1.00 | 1.00 |

**UDIAT**

| scorer | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|
| bleu | — | 0.81 | 0.85 | 0.64 |
| rougeL | — | 0.88 | 0.91 | 0.76 |
| chrf | — | 0.95 | 0.94 | 0.85 |
| bertscore[roberta-large] | — | 0.97 | 0.97 | 0.96 |
| ratescore | — | 1.00 | 1.00 | 1.00 |

**BUS-UCLM**

| scorer | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|
| bleu | 0.59 | 0.62 | 0.68 | 0.42 |
| rougeL | 0.80 | 0.74 | 0.80 | 0.57 |
| chrf | 0.86 | 0.88 | 0.87 | 0.70 |
| bertscore[roberta-large] | 0.99 | 0.95 | 0.95 | 0.94 |
| ratescore | 0.79 | 1.00 | 1.00 | 1.00 |

**TN3K**

| scorer | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|
| bleu | — | 0.76 | 0.81 | 0.57 |
| rougeL | — | 0.87 | 0.90 | 0.74 |
| chrf | — | 0.94 | 0.93 | 0.82 |
| bertscore[roberta-large] | — | 0.97 | 0.97 | 0.95 |
| ratescore | — | 1.00 | 1.00 | 1.00 |

**TN5000**

| scorer | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|
| bleu | — | 0.76 | 0.81 | 0.57 |
| rougeL | — | 0.87 | 0.90 | 0.74 |
| chrf | — | 0.94 | 0.93 | 0.82 |
| bertscore[roberta-large] | — | 0.97 | 0.97 | 0.95 |
| ratescore | — | 1.00 | 1.00 | 1.00 |

**DDTI**

| scorer | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|
| bleu | — | 0.81 | 0.85 | 0.65 |
| rougeL | — | 0.89 | 0.92 | 0.79 |
| chrf | — | 0.96 | 0.95 | 0.87 |
| bertscore[roberta-large] | — | 0.98 | 0.97 | 0.96 |
| ratescore | — | 1.00 | 1.00 | 1.00 |

**HC18**

| scorer | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|
| bleu | — | 0.44 | 0.51 | 0.25 |
| rougeL | — | 0.67 | 0.74 | 0.47 |
| chrf | — | 0.84 | 0.82 | 0.61 |
| bertscore[roberta-large] | — | 0.93 | 0.93 | 0.93 |
| ratescore | — | 1.00 | 1.00 | 1.00 |

**FetalHead**

| scorer | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|
| bleu | — | 0.59 | 0.65 | 0.37 |
| rougeL | — | 0.74 | 0.80 | 0.55 |
| chrf | — | 0.91 | 0.90 | 0.75 |
| bertscore[roberta-large] | — | 0.94 | 0.94 | 0.94 |
| ratescore | — | 1.00 | 1.00 | 1.00 |

---
Limitations: see [docs/LIMITATIONS.md](docs/LIMITATIONS.md) (templated reports, upper bounds, prompt-sensitive judge, provisional severity, possible exposure). 
