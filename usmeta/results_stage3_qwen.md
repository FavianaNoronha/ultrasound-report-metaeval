Writer: Qwen/Qwen2.5-VL-3B-Instruct | extractor+judge: mlx-community/gemma-2-9b-it-4bit | judge items missing: 0

### BUS-BRA (n=50; possibly seen in training)

| scorer | mean |
|---|---|
| bleu | 0.01 |
| rougeL | 0.12 |
| chrf | 0.19 |
| fact_checker | 0.30 |
| fact_coverage | 0.66 |
| llm_judge[local:gemma-2-9b-it-4bit] | 0.04 |
| bertscore[roberta-large] | 0.83 |

### HC18 (n=50; possibly seen in training)

| scorer | mean |
|---|---|
| bleu | 0.01 |
| rougeL | 0.06 |
| chrf | 0.12 |
| fact_checker | 0.05 |
| fact_coverage | 0.96 |
| llm_judge[local:gemma-2-9b-it-4bit] | 0.43 |
| bertscore[roberta-large] | 0.81 |

### TN3K (n=50; possibly seen in training)

| scorer | mean |
|---|---|
| bleu | 0.01 |
| rougeL | 0.11 |
| chrf | 0.19 |
| fact_checker | 0.02 |
| fact_coverage | 0.29 |
| llm_judge[local:gemma-2-9b-it-4bit] | 0.00 |
| bertscore[roberta-large] | 0.82 |

### TN5000 (n=50; possibly seen in training)

| scorer | mean |
|---|---|
| bleu | 0.01 |
| rougeL | 0.11 |
| chrf | 0.19 |
| fact_checker | 0.02 |
| fact_coverage | 0.37 |
| llm_judge[local:gemma-2-9b-it-4bit] | 0.00 |
| bertscore[roberta-large] | 0.82 |

---
Limitations: see [docs/LIMITATIONS.md](docs/LIMITATIONS.md) (templated reports, upper bounds, prompt-sensitive judge, provisional severity, possible exposure). 
