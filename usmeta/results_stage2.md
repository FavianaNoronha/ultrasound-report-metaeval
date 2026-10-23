### all

| grader | AUROC (95% CI) | critical-only AUROC | harmless mean | identical mean | severity ρ |
|---|---|---|---|---|---|
| bleu | 0.00 (0.00–0.00) | 0.00 | 0.41 | 1.00 | 0.11 |
| rougeL | 0.00 (0.00–0.00) | 0.00 | 0.59 | 1.00 | 0.02 |
| chrf | 0.00 (0.00–0.00) | 0.00 | 0.68 | 1.00 | 0.18 |
| fact_checker | 1.00 (1.00–1.00) | 1.00 | 1.00 | 1.00 | -0.74 |
| evidence_check | 1.00 (1.00–1.00) | 1.00 | 1.00 | 1.00 | -0.74 |
| bertscore[roberta-large] | 0.01 (0.01–0.01) | 0.00 | 0.96 | 1.00 | -0.06 |
| ratescore | 0.15 (0.14–0.16) | 0.15 | 0.76 | 1.00 | 0.02 |

### breast

| grader | AUROC (95% CI) | critical-only AUROC | harmless mean | identical mean | severity ρ |
|---|---|---|---|---|---|
| bleu | 0.00 (0.00–0.00) | 0.00 | 0.41 | 1.00 | 0.03 |
| rougeL | 0.00 (0.00–0.00) | 0.00 | 0.55 | 1.00 | 0.08 |
| chrf | 0.00 (0.00–0.00) | 0.00 | 0.70 | 1.00 | 0.09 |
| fact_checker | 1.00 (1.00–1.00) | 1.00 | 1.00 | 1.00 | -0.62 |
| evidence_check | 1.00 (1.00–1.00) | 1.00 | 1.00 | 1.00 | -0.62 |
| bertscore[roberta-large] | 0.02 (0.02–0.03) | 0.00 | 0.95 | 1.00 | 0.06 |
| ratescore | 0.13 (0.12–0.15) | 0.08 | 0.82 | 1.00 | 0.25 |

### fetal

| grader | AUROC (95% CI) | critical-only AUROC | harmless mean | identical mean | severity ρ |
|---|---|---|---|---|---|
| bleu | 0.00 (0.00–0.00) | 0.00 | 0.49 | 1.00 | — |
| rougeL | 0.00 (0.00–0.00) | 0.00 | 0.68 | 1.00 | -0.06 |
| chrf | 0.00 (0.00–0.00) | 0.00 | 0.74 | 1.00 | -0.10 |
| fact_checker | 1.00 (1.00–1.00) | 1.00 | 1.00 | 1.00 | -0.97 |
| evidence_check | 1.00 (1.00–1.00) | 1.00 | 1.00 | 1.00 | -0.95 |
| bertscore[roberta-large] | 0.00 (0.00–0.00) | 0.00 | 0.97 | 1.00 | -0.67 |
| ratescore | 0.24 (0.19–0.29) | 0.30 | 0.70 | 1.00 | -0.39 |

### thyroid

| grader | AUROC (95% CI) | critical-only AUROC | harmless mean | identical mean | severity ρ |
|---|---|---|---|---|---|
| bleu | 0.00 (0.00–0.00) | 0.00 | 0.37 | 1.00 | 0.47 |
| rougeL | 0.00 (0.00–0.00) | 0.00 | 0.58 | 1.00 | 0.00 |
| chrf | 0.00 (0.00–0.00) | 0.00 | 0.65 | 1.00 | 0.31 |
| fact_checker | 1.00 (1.00–1.00) | 1.00 | 1.00 | 1.00 | -1.00 |
| evidence_check | 1.00 (1.00–1.00) | 1.00 | 1.00 | 1.00 | -1.00 |
| bertscore[roberta-large] | 0.00 (0.00–0.00) | 0.00 | 0.96 | 1.00 | -0.17 |
| ratescore | 0.14 (0.13–0.15) | 0.14 | 0.75 | 1.00 | -0.49 |

---
Limitations: see [docs/LIMITATIONS.md](docs/LIMITATIONS.md) (templated reports, upper bounds, prompt-sensitive judge, provisional severity, possible exposure). 
