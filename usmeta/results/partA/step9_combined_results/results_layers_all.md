# Every scorer x every dataset, grouped by layer (Part A, bench_v2d)

AUROC = chance that a planted error scores LOWER than a harmless rewording of the same case (1.0 perfect, 0.5 chance, below 0.5 = the scorer prefers the error). Three harmless comparisons: **small** = synonyms / sentence reorder / unit rewrite (5-36% of tokens changed), **matched** = ONE-word synonym (about the same edit size as an error), **large** = style swap. `identical` must be 1.0. Layers 0-2 use bench_v2d (150 cases per dataset, 256 BrEaST; Layer 2 only 20 cases per dataset: wide intervals). Layer 3 uses its own benchmark with boxes (table at the end).

**Keep visible:** reports are templated from labels (synthetic but fact-correct); severity is provisional pending a clinician; template sources are marked "to confirm" and must be verified before any paper claim; results are per dataset only, never pooled; Layer 1 and the oracle row are upper bounds because their extractor is written for the same templates; Layer 3 Test 1 uses TRUE masks (circular for position/size). We found no ultrasound work that tests the scorers with planted errors, severity and harmless rewordings (our search was not exhaustive).

## breast

### BrEaST (256 cases)

| layer | scorer | AUROC vs small | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy "No abnormality." | idea borrowed from |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 word overlap | bleu | 0.25 | 0.60 | 0.08 | 0.38 | 0.85 | 0.38 | 1.0000 | 0.00 | standard n-gram metric (Papineni et al. 2002) |
| 0 word overlap | rougeL | 0.10 | 0.58 | 0.08 | 0.38 | 0.80 | 0.59 | 1.0000 | 0.04 | standard (Lin 2004) |
| 0 word overlap | chrf | 0.37 | 0.24 | 0.08 | 0.62 | 0.92 | 0.73 | 1.0000 | 0.02 | standard character n-gram (Popovic 2015) |
| 0 embedding similarity | bertscore[roberta-large] | 0.21 | 0.52 | 0.08 | 0.48 | 0.98 | 0.95 | 1.0000 | 0.84 | BERTScore (Zhang et al. 2020) |
| 0 radiology entities | ratescore | 0.44 | 0.63 | 0.13 | 0.67 | 0.92 | 0.83 | 1.0000 | 0.50 | RaTEScore (built for chest/CT; run unchanged) |
| 1 structured facts | finding_f1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.01 | ours: findings schema from the BI-RADS / TI-RADS lexicons; precision/recall over attributes (graded credit for numbers) |
| 2 AI judge | sentence_f1 (n=20) | 0.86 | 0.94 | 0.78 | 0.96 | 0.96 | 0.88 | 1.0000 | — | RadFact protocol (sentence support both ways), our own Gemma-2-9B prompt, not the original RadFact |
| 2 AI judge | judge_score (n=20) | 0.89 | 0.99 | 0.55 | 0.96 | 0.87 | 0.47 | 1.0000 | — | ours: severity-weighted error list from the judge (penalties 0.6 / 0.3 / 0.1) |

### BUS-BRA (151 cases)

| layer | scorer | AUROC vs small | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy "No abnormality." | idea borrowed from |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 word overlap | bleu | 0.21 | 0.75 | 0.09 | 0.30 | 0.82 | 0.54 | 1.0000 | 0.00 | standard n-gram metric (Papineni et al. 2002) |
| 0 word overlap | rougeL | 0.09 | 0.67 | 0.09 | 0.30 | 0.78 | 0.69 | 1.0000 | 0.00 | standard (Lin 2004) |
| 0 word overlap | chrf | 0.30 | 0.37 | 0.09 | 0.51 | 0.88 | 0.74 | 1.0000 | 0.02 | standard character n-gram (Popovic 2015) |
| 0 embedding similarity | bertscore[roberta-large] | 0.09 | 0.42 | 0.09 | 0.30 | 0.97 | 0.95 | 1.0000 | 0.84 | BERTScore (Zhang et al. 2020) |
| 0 radiology entities | ratescore | 0.54 | 0.67 | 0.22 | 0.61 | 0.92 | 0.87 | 1.0000 | 0.50 | RaTEScore (built for chest/CT; run unchanged) |
| 1 structured facts | finding_f1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.00 | ours: findings schema from the BI-RADS / TI-RADS lexicons; precision/recall over attributes (graded credit for numbers) |
| 2 AI judge | sentence_f1 (n=20) | 0.61 | 0.95 | 0.95 | 0.72 | 0.84 | 1.00 | 1.0000 | — | RadFact protocol (sentence support both ways), our own Gemma-2-9B prompt, not the original RadFact |
| 2 AI judge | judge_score (n=20) | 0.60 | 1.00 | 1.00 | 0.58 | 0.57 | 1.00 | 1.0000 | — | ours: severity-weighted error list from the judge (penalties 0.6 / 0.3 / 0.1) |

### BUSI (150 cases)

| layer | scorer | AUROC vs small | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy "No abnormality." | idea borrowed from |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 word overlap | bleu | 0.63 | 0.82 | 0.27 | 0.78 | 0.80 | 0.48 | 1.0000 | 0.01 | standard n-gram metric (Papineni et al. 2002) |
| 0 word overlap | rougeL | 0.30 | 0.74 | 0.27 | 0.58 | 0.85 | 0.65 | 1.0000 | 0.04 | standard (Lin 2004) |
| 0 word overlap | chrf | 0.63 | 0.54 | 0.27 | 0.79 | 0.88 | 0.71 | 1.0000 | 0.05 | standard character n-gram (Popovic 2015) |
| 0 embedding similarity | bertscore[roberta-large] | 0.27 | 0.51 | 0.27 | 0.58 | 0.97 | 0.95 | 1.0000 | 0.86 | BERTScore (Zhang et al. 2020) |
| 0 radiology entities | ratescore | 0.60 | 0.68 | 0.59 | 0.78 | 0.91 | 0.86 | 1.0000 | 0.50 | RaTEScore (built for chest/CT; run unchanged) |
| 1 structured facts | finding_f1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.11 | ours: findings schema from the BI-RADS / TI-RADS lexicons; precision/recall over attributes (graded credit for numbers) |
| 2 AI judge | sentence_f1 (n=20) | 0.66 | 0.86 | 0.86 | 0.96 | 0.87 | 1.00 | 1.0000 | — | RadFact protocol (sentence support both ways), our own Gemma-2-9B prompt, not the original RadFact |
| 2 AI judge | judge_score (n=20) | 1.00 | 1.00 | 1.00 | 1.00 | 0.98 | 1.00 | 1.0000 | — | ours: severity-weighted error list from the judge (penalties 0.6 / 0.3 / 0.1) |

### UDIAT (150 cases)

| layer | scorer | AUROC vs small | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy "No abnormality." | idea borrowed from |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 word overlap | bleu | 0.50 | 0.78 | 0.11 | 0.75 | 0.83 | 0.52 | 1.0000 | 0.00 | standard n-gram metric (Papineni et al. 2002) |
| 0 word overlap | rougeL | 0.11 | 0.67 | 0.11 | 0.50 | 0.84 | 0.65 | 1.0000 | 0.00 | standard (Lin 2004) |
| 0 word overlap | chrf | 0.50 | 0.44 | 0.11 | 0.75 | 0.89 | 0.74 | 1.0000 | 0.03 | standard character n-gram (Popovic 2015) |
| 0 embedding similarity | bertscore[roberta-large] | 0.11 | 0.52 | 0.11 | 0.50 | 0.97 | 0.95 | 1.0000 | 0.85 | BERTScore (Zhang et al. 2020) |
| 0 radiology entities | ratescore | 0.53 | 0.64 | 0.51 | 0.75 | 0.92 | 0.86 | 1.0000 | 0.50 | RaTEScore (built for chest/CT; run unchanged) |
| 1 structured facts | finding_f1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.00 | ours: findings schema from the BI-RADS / TI-RADS lexicons; precision/recall over attributes (graded credit for numbers) |
| 2 AI judge | sentence_f1 (n=20) | 0.50 | 0.94 | 0.75 | 0.83 | 0.80 | 0.91 | 1.0000 | — | RadFact protocol (sentence support both ways), our own Gemma-2-9B prompt, not the original RadFact |
| 2 AI judge | judge_score (n=20) | 0.60 | 1.00 | 0.84 | 0.61 | 0.54 | 0.76 | 1.0000 | — | ours: severity-weighted error list from the judge (penalties 0.6 / 0.3 / 0.1) |

### BUS-UCLM (152 cases)

| layer | scorer | AUROC vs small | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy "No abnormality." | idea borrowed from |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 word overlap | bleu | 0.84 | 0.92 | 0.68 | 0.90 | 0.76 | 0.43 | 1.0000 | 0.02 | standard n-gram metric (Papineni et al. 2002) |
| 0 word overlap | rougeL | 0.69 | 0.89 | 0.68 | 0.81 | 0.82 | 0.65 | 1.0000 | 0.14 | standard (Lin 2004) |
| 0 word overlap | chrf | 0.84 | 0.79 | 0.68 | 0.91 | 0.87 | 0.68 | 1.0000 | 0.11 | standard character n-gram (Popovic 2015) |
| 0 embedding similarity | bertscore[roberta-large] | 0.68 | 0.78 | 0.68 | 0.81 | 0.97 | 0.95 | 1.0000 | 0.87 | BERTScore (Zhang et al. 2020) |
| 0 radiology entities | ratescore | 0.83 | 0.86 | 0.82 | 0.90 | 0.96 | 0.86 | 1.0000 | 0.50 | RaTEScore (built for chest/CT; run unchanged) |
| 1 structured facts | finding_f1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.42 | ours: findings schema from the BI-RADS / TI-RADS lexicons; precision/recall over attributes (graded credit for numbers) |
| 2 AI judge | sentence_f1 (n=20) | 0.88 | 0.94 | 0.94 | 0.98 | 0.90 | 1.00 | 1.0000 | — | RadFact protocol (sentence support both ways), our own Gemma-2-9B prompt, not the original RadFact |
| 2 AI judge | judge_score (n=20) | 1.00 | 1.00 | 1.00 | 1.00 | 0.98 | 1.00 | 1.0000 | — | ours: severity-weighted error list from the judge (penalties 0.6 / 0.3 / 0.1) |

## thyroid

### TN3K (150 cases)

| layer | scorer | AUROC vs small | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy "No abnormality." | idea borrowed from |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 word overlap | bleu | 0.58 | 0.82 | 0.16 | 1.00 | 0.80 | 0.44 | 1.0000 | 0.00 | standard n-gram metric (Papineni et al. 2002) |
| 0 word overlap | rougeL | 0.16 | 0.73 | 0.16 | 1.00 | 0.84 | 0.63 | 1.0000 | 0.00 | standard (Lin 2004) |
| 0 word overlap | chrf | 0.58 | 0.45 | 0.16 | 1.00 | 0.86 | 0.70 | 1.0000 | 0.03 | standard character n-gram (Popovic 2015) |
| 0 embedding similarity | bertscore[roberta-large] | 0.16 | 0.58 | 0.16 | 1.00 | 0.97 | 0.94 | 1.0000 | 0.86 | BERTScore (Zhang et al. 2020) |
| 0 radiology entities | ratescore | 0.56 | 0.53 | 0.32 | 1.00 | 0.88 | 0.74 | 1.0000 | 0.50 | RaTEScore (built for chest/CT; run unchanged) |
| 1 structured facts | finding_f1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.00 | ours: findings schema from the BI-RADS / TI-RADS lexicons; precision/recall over attributes (graded credit for numbers) |
| 2 AI judge | sentence_f1 (n=20) | 1.00 | 1.00 | 0.94 | 1.00 | 1.00 | 0.82 | 1.0000 | — | RadFact protocol (sentence support both ways), our own Gemma-2-9B prompt, not the original RadFact |
| 2 AI judge | judge_score (n=20) | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.88 | 1.0000 | — | ours: severity-weighted error list from the judge (penalties 0.6 / 0.3 / 0.1) |

### TN5000 (150 cases)

| layer | scorer | AUROC vs small | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy "No abnormality." | idea borrowed from |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 word overlap | bleu | 0.58 | 0.82 | 0.15 | 1.00 | 0.80 | 0.44 | 1.0000 | 0.00 | standard n-gram metric (Papineni et al. 2002) |
| 0 word overlap | rougeL | 0.15 | 0.73 | 0.15 | 1.00 | 0.84 | 0.63 | 1.0000 | 0.00 | standard (Lin 2004) |
| 0 word overlap | chrf | 0.58 | 0.46 | 0.15 | 1.00 | 0.86 | 0.71 | 1.0000 | 0.03 | standard character n-gram (Popovic 2015) |
| 0 embedding similarity | bertscore[roberta-large] | 0.15 | 0.55 | 0.15 | 1.00 | 0.97 | 0.94 | 1.0000 | 0.86 | BERTScore (Zhang et al. 2020) |
| 0 radiology entities | ratescore | 0.58 | 0.54 | 0.33 | 1.00 | 0.88 | 0.76 | 1.0000 | 0.50 | RaTEScore (built for chest/CT; run unchanged) |
| 1 structured facts | finding_f1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.00 | ours: findings schema from the BI-RADS / TI-RADS lexicons; precision/recall over attributes (graded credit for numbers) |
| 2 AI judge | sentence_f1 (n=20) | 0.99 | 0.99 | 0.89 | 1.00 | 1.00 | 0.78 | 1.0000 | — | RadFact protocol (sentence support both ways), our own Gemma-2-9B prompt, not the original RadFact |
| 2 AI judge | judge_score (n=20) | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.87 | 1.0000 | — | ours: severity-weighted error list from the judge (penalties 0.6 / 0.3 / 0.1) |

### DDTI (150 cases)

| layer | scorer | AUROC vs small | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy "No abnormality." | idea borrowed from |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 word overlap | bleu | 0.45 | 0.67 | 0.10 | 0.70 | 0.80 | 0.43 | 1.0000 | 0.00 | standard n-gram metric (Papineni et al. 2002) |
| 0 word overlap | rougeL | 0.12 | 0.66 | 0.12 | 0.72 | 0.73 | 0.61 | 1.0000 | 0.02 | standard (Lin 2004) |
| 0 word overlap | chrf | 0.44 | 0.36 | 0.11 | 0.70 | 0.87 | 0.68 | 1.0000 | 0.02 | standard character n-gram (Popovic 2015) |
| 0 embedding similarity | bertscore[roberta-large] | 0.13 | 0.53 | 0.11 | 0.72 | 0.97 | 0.95 | 1.0000 | 0.84 | BERTScore (Zhang et al. 2020) |
| 0 radiology entities | ratescore | 0.50 | 0.56 | 0.23 | 0.77 | 0.88 | 0.76 | 1.0000 | 0.50 | RaTEScore (built for chest/CT; run unchanged) |
| 1 structured facts | finding_f1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.02 | ours: findings schema from the BI-RADS / TI-RADS lexicons; precision/recall over attributes (graded credit for numbers) |
| 2 AI judge | sentence_f1 (n=20) | 0.75 | 0.94 | 0.76 | 1.00 | 0.85 | 0.80 | 1.0000 | — | RadFact protocol (sentence support both ways), our own Gemma-2-9B prompt, not the original RadFact |
| 2 AI judge | judge_score (n=20) | 0.96 | 1.00 | 0.95 | 1.00 | 0.89 | 0.84 | 1.0000 | — | ours: severity-weighted error list from the judge (penalties 0.6 / 0.3 / 0.1) |

## fetal

### HC18 (150 cases)

| layer | scorer | AUROC vs small | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy "No abnormality." | idea borrowed from |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 word overlap | bleu | 0.33 | 0.50 | 0.00 | 0.33 | 0.58 | 0.20 | 1.0000 | 0.05 | standard n-gram metric (Papineni et al. 2002) |
| 0 word overlap | rougeL | 0.17 | 0.50 | 0.00 | 0.17 | 0.72 | 0.68 | 1.0000 | 0.00 | standard (Lin 2004) |
| 0 word overlap | chrf | 0.33 | 0.00 | 0.00 | 0.33 | 0.85 | 0.45 | 1.0000 | 0.05 | standard character n-gram (Popovic 2015) |
| 0 embedding similarity | bertscore[roberta-large] | 0.00 | 0.00 | 0.00 | 0.00 | 0.97 | 0.93 | 1.0000 | 0.87 | BERTScore (Zhang et al. 2020) |
| 0 radiology entities | ratescore | 0.42 | 0.11 | 0.05 | 0.51 | 0.89 | 0.61 | 1.0000 | 0.50 | RaTEScore (built for chest/CT; run unchanged) |
| 1 structured facts | finding_f1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.00 | ours: findings schema from the BI-RADS / TI-RADS lexicons; precision/recall over attributes (graded credit for numbers) |
| 2 AI judge | sentence_f1 (n=20) | 0.85 | 1.00 | 0.50 | 0.88 | 0.85 | 0.50 | 1.0000 | — | RadFact protocol (sentence support both ways), our own Gemma-2-9B prompt, not the original RadFact |
| 2 AI judge | judge_score (n=20) | 0.93 | 1.00 | 0.50 | 1.00 | 0.86 | 0.50 | 1.0000 | — | ours: severity-weighted error list from the judge (penalties 0.6 / 0.3 / 0.1) |

### FetalHead (151 cases)

| layer | scorer | AUROC vs small | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy "No abnormality." | idea borrowed from |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 word overlap | bleu | 0.37 | 0.55 | 0.00 | 0.33 | 0.79 | 0.35 | 1.0000 | 0.01 | standard n-gram metric (Papineni et al. 2002) |
| 0 word overlap | rougeL | 0.17 | 0.50 | 0.00 | 0.17 | 0.72 | 0.79 | 1.0000 | 0.00 | standard (Lin 2004) |
| 0 word overlap | chrf | 0.55 | 0.21 | 0.05 | 0.50 | 0.93 | 0.70 | 1.0000 | 0.04 | standard character n-gram (Popovic 2015) |
| 0 embedding similarity | bertscore[roberta-large] | 0.13 | 0.21 | 0.10 | 0.00 | 0.97 | 0.95 | 1.0000 | 0.84 | BERTScore (Zhang et al. 2020) |
| 0 radiology entities | ratescore | 0.49 | 0.38 | 0.11 | 0.52 | 0.93 | 0.63 | 1.0000 | 0.50 | RaTEScore (built for chest/CT; run unchanged) |
| 1 structured facts | finding_f1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.00 | ours: findings schema from the BI-RADS / TI-RADS lexicons; precision/recall over attributes (graded credit for numbers) |
| 2 AI judge | sentence_f1 (n=20) | 0.94 | 1.00 | 1.00 | 1.00 | 0.90 | 1.00 | 1.0000 | — | RadFact protocol (sentence support both ways), our own Gemma-2-9B prompt, not the original RadFact |
| 2 AI judge | judge_score (n=20) | 0.79 | 1.00 | 1.00 | 1.00 | 0.91 | 1.00 | 1.0000 | — | ours: severity-weighted error list from the judge (penalties 0.6 / 0.3 / 0.1) |

## AUROC per error category (vs harmless_small / vs matched one-word synonym)

Only categories a dataset supports appear. Layer 2 cells use ~40 errors per dataset.

**BrEaST**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| bleu | 0.49 / 0.86 | 0.88 / 0.95 | 0.00 / 0.50 | 0.00 / 0.50 | 0.17 / 0.50 |
| rougeL | 0.09 / 0.84 | 0.85 / 0.93 | 0.00 / 0.42 | 0.00 / 0.42 | 0.02 / 0.50 |
| chrf | 0.50 / 0.12 | 0.88 / 0.89 | 0.67 / 0.00 | 0.01 / 0.00 | 0.37 / 0.27 |
| bertscore[roberta-large] | 0.26 / 0.80 | 0.86 / 0.94 | 0.00 / 0.20 | 0.00 / 0.07 | 0.16 / 0.55 |
| ratescore | 0.42 / 0.65 | 0.89 / 0.91 | 0.17 / 0.18 | 0.34 / 0.76 | 0.43 / 0.57 |
| finding_f1 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 |
| sentence_f1 | 0.88 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 0.38 / 0.50 | 0.90 / 0.97 |
| judge_score | 0.92 / 1.00 | 0.92 / 1.00 | 1.00 / 1.00 | 0.75 / 1.00 | 0.87 / 0.97 |

**BUS-BRA**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| bleu | 0.50 / 1.00 | 1.00 / 1.00 | 0.00 / 0.67 | 0.00 / 0.67 | 0.17 / 0.74 |
| rougeL | 0.00 / 1.00 | 1.00 / 1.00 | 0.00 / 0.50 | 0.00 / 0.50 | 0.00 / 0.69 |
| chrf | 0.50 / 0.33 | 1.00 / 1.00 | 0.16 / 0.33 | 0.00 / 0.00 | 0.37 / 0.53 |
| bertscore[roberta-large] | 0.00 / 1.00 | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.60 |
| ratescore | 0.49 / 0.68 | 1.00 / 1.00 | 0.42 / 0.54 | 0.50 / 0.68 | 0.51 / 0.64 |
| finding_f1 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 |
| sentence_f1 | 0.40 / 1.00 | 1.00 / 1.00 | 0.62 / 1.00 | 0.55 / 0.80 | 0.59 / 1.00 |
| judge_score | 0.50 / 1.00 | 0.80 / 1.00 | 0.75 / 1.00 | 0.65 / 1.00 | 0.50 / 1.00 |

**BUSI**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| bleu | 0.58 / 1.00 | 1.00 / 1.00 | 0.50 / 0.75 | 0.50 / 0.75 | 0.49 / 0.62 |
| rougeL | 0.17 / 1.00 | 1.00 / 1.00 | 0.00 / 0.50 | 0.00 / 0.50 | 0.12 / 0.75 |
| chrf | 0.58 / 0.58 | 1.00 / 1.00 | 0.50 / 0.50 | 0.49 / 0.00 | 0.50 / 0.83 |
| bertscore[roberta-large] | 0.17 / 0.99 | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.64 |
| ratescore | 0.58 / 0.73 | 1.00 / 1.00 | 0.21 / 0.25 | 0.48 / 0.60 | 0.48 / 0.59 |
| finding_f1 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 |
| sentence_f1 | 0.67 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 0.36 / 0.61 | 0.75 / 1.00 |
| judge_score | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 |

**UDIAT**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| bleu | 0.50 / 1.00 | 1.00 / 1.00 | 0.50 / 0.75 | 0.50 / 0.75 | 0.33 / 0.67 |
| rougeL | 0.00 / 1.00 | 1.00 / 1.00 | 0.00 / 0.50 | 0.00 / 0.50 | 0.00 / 0.67 |
| chrf | 0.50 / 0.50 | 1.00 / 1.00 | 0.50 / 0.50 | 0.42 / 0.00 | 0.40 / 0.67 |
| bertscore[roberta-large] | 0.00 / 1.00 | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.85 |
| ratescore | 0.47 / 0.66 | 1.00 / 1.00 | 0.22 / 0.25 | 0.50 / 0.62 | 0.50 / 0.63 |
| finding_f1 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 |
| sentence_f1 | 0.67 / 1.00 | 1.00 / 1.00 | 0.75 / 1.00 | 0.25 / 0.84 | 0.45 / 1.00 |
| judge_score | 1.00 / 1.00 | 0.92 / 1.00 | 0.88 / 1.00 | 0.56 / 1.00 | 0.27 / 1.00 |

**BUS-UCLM**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| bleu | 0.82 / 1.00 | 1.00 / 1.00 | 0.50 / 0.75 | 0.50 / 0.75 | 0.49 / 0.62 |
| rougeL | 0.63 / 1.00 | 1.00 / 1.00 | 0.00 / 0.50 | 0.00 / 0.50 | 0.12 / 0.75 |
| chrf | 0.82 / 0.82 | 1.00 / 1.00 | 0.50 / 0.50 | 0.49 / 0.00 | 0.50 / 0.82 |
| bertscore[roberta-large] | 0.63 / 1.00 | 1.00 / 1.00 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.60 |
| ratescore | 0.82 / 0.87 | 1.00 / 1.00 | 0.24 / 0.25 | 0.48 / 0.59 | 0.48 / 0.58 |
| finding_f1 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 |
| sentence_f1 | 1.00 / 1.00 | 1.00 / 1.00 | 0.88 / 1.00 | 0.20 / 0.50 | 0.90 / 1.00 |
| judge_score | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 |

**TN3K**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| bleu | 0.50 / 1.00 | 1.00 / 1.00 | 0.50 / 0.66 | 0.50 / 0.67 | 0.50 / 1.00 |
| rougeL | 0.00 / 1.00 | 1.00 / 1.00 | 0.00 / 0.50 | 0.00 / 0.50 | 0.00 / 1.00 |
| chrf | 0.50 / 1.00 | 1.00 / 1.00 | 0.50 / 0.00 | 0.50 / 0.00 | 0.50 / 1.00 |
| bertscore[roberta-large] | 0.00 / 1.00 | 1.00 / 1.00 | 0.00 / 0.19 | 0.00 / 0.25 | 0.00 / 1.00 |
| ratescore | 0.66 / 0.62 | 1.00 / 1.00 | 0.33 / 0.26 | 0.30 / 0.24 | 0.94 / 0.90 |
| finding_f1 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 |
| sentence_f1 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 |
| judge_score | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 |

**TN5000**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| bleu | 0.50 / 1.00 | 1.00 / 1.00 | 0.50 / 0.67 | 0.50 / 0.67 | 0.50 / 1.00 |
| rougeL | 0.00 / 1.00 | 1.00 / 1.00 | 0.00 / 0.50 | 0.00 / 0.50 | 0.00 / 1.00 |
| chrf | 0.50 / 1.00 | 1.00 / 1.00 | 0.50 / 0.00 | 0.50 / 0.00 | 0.50 / 1.00 |
| bertscore[roberta-large] | 0.00 / 1.00 | 1.00 / 1.00 | 0.00 / 0.21 | 0.00 / 0.16 | 0.00 / 1.00 |
| ratescore | 0.76 / 0.72 | 1.00 / 1.00 | 0.30 / 0.19 | 0.30 / 0.26 | 0.95 / 0.92 |
| finding_f1 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 |
| sentence_f1 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 0.96 / 0.96 | 1.00 / 1.00 |
| judge_score | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 |

**DDTI**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| bleu | 0.49 / 1.00 | 0.88 / 1.00 | 0.50 / 0.64 | 0.50 / 0.63 | 0.32 / 0.59 |
| rougeL | 0.03 / 0.89 | 0.75 / 0.88 | 0.00 / 0.50 | 0.00 / 0.50 | 0.00 / 0.74 |
| chrf | 0.49 / 0.80 | 0.88 / 1.00 | 0.50 / 0.00 | 0.48 / 0.00 | 0.31 / 0.46 |
| bertscore[roberta-large] | 0.08 / 1.00 | 0.79 / 1.00 | 0.00 / 0.10 | 0.00 / 0.16 | 0.00 / 0.65 |
| ratescore | 0.54 / 0.75 | 0.87 / 0.97 | 0.36 / 0.32 | 0.31 / 0.29 | 0.57 / 0.66 |
| finding_f1 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 |
| sentence_f1 | 0.83 / 1.00 | 0.94 / 1.00 | 0.67 / 1.00 | 0.64 / 0.77 | 0.71 / 1.00 |
| judge_score | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 0.91 / 1.00 | 0.96 / 1.00 |

**HC18**

| scorer | wrong measurement |
|---|---|
| bleu | 0.33 / 0.50 |
| rougeL | 0.17 / 0.50 |
| chrf | 0.33 / 0.00 |
| bertscore[roberta-large] | 0.00 / 0.00 |
| ratescore | 0.42 / 0.11 |
| finding_f1 | 1.00 / 1.00 |
| sentence_f1 | 0.85 / 1.00 |
| judge_score | 0.93 / 1.00 |

**FetalHead**

| scorer | wrong measurement | wrong severity/category |
|---|---|---|
| bleu | 0.33 / 0.50 | 0.50 / 0.75 |
| rougeL | 0.17 / 0.50 | 0.17 / 0.50 |
| chrf | 0.43 / 0.00 | 1.00 / 1.00 |
| bertscore[roberta-large] | 0.00 / 0.00 | 0.67 / 1.00 |
| ratescore | 0.47 / 0.32 | 0.59 / 0.56 |
| finding_f1 | 1.00 / 1.00 | 1.00 / 1.00 |
| sentence_f1 | 0.88 / 1.00 | 1.00 / 1.00 |
| judge_score | 0.88 / 1.00 | 0.70 / 1.00 |

## Layer 3: image / location check against the TRUE masks (own benchmark `bench_loc`, text + box; 100 cases per dataset)

Groups: box-only = text unchanged, box moved (text scorers cannot see it: by construction); text pos = wrong position sentence, correct box; text pos + box = wrong sentence and box moved to match; size = wrong size in text, correct box. Harmless = jittered box, jittered box + reworded text.

| dataset | scorer | AUROC box-only | text pos | text pos + box | size | harmless mean | identical mean | idea borrowed from |
|---|---|---|---|---|---|---|---|---|
| BrEaST | bleu | 0.25 | 0.50 | 0.50 | 0.50 | 0.84 | 1.0000 | standard n-gram metric (Papineni et al. 2002) |
| BrEaST | bertscore[roberta-large] | 0.25 | 0.50 | 0.50 | 0.50 | 0.99 | 1.0000 | BERTScore (Zhang et al. 2020) |
| BrEaST | oracle_label_check | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | old evidence_check idea: text vs dataset labels (upper bound) |
| BrEaST | mask_verified_facts | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | ours: text claims checked against the true mask |
| BrEaST | semacc | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | UltraG-Bench SemAcc (presence, category, location, size yes/no) |
| BrEaST | location_check | 1.00 | 0.00 | 1.00 | 0.00 | 0.90 | 1.0000 | box IoU as in grounded chest X-ray reporting (MAIRA-2 / RadFact line; to confirm); true masks |
| BrEaST | grounded_check | 1.00 | 0.24 | 1.00 | 0.16 | 0.90 | 1.0000 | ours: finding_f1 x box IoU |
| BrEaST | box_support_gtbox | 0.81 | 0.50 | 1.00 | 0.50 | 1.00 | 1.0000 | spatial support rule (>= 50% of the box in the true region) |
| BUS-BRA | bleu | 0.25 | 0.50 | 0.50 | 0.50 | 0.86 | 1.0000 | standard n-gram metric (Papineni et al. 2002) |
| BUS-BRA | bertscore[roberta-large] | 0.25 | 0.50 | 0.50 | 0.50 | 0.99 | 1.0000 | BERTScore (Zhang et al. 2020) |
| BUS-BRA | oracle_label_check | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | old evidence_check idea: text vs dataset labels (upper bound) |
| BUS-BRA | mask_verified_facts | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | ours: text claims checked against the true mask |
| BUS-BRA | semacc | 0.50 | 1.00 | 1.00 | 0.97 | 1.00 | 1.0000 | UltraG-Bench SemAcc (presence, category, location, size yes/no) |
| BUS-BRA | location_check | 1.00 | 0.00 | 1.00 | 0.00 | 0.90 | 1.0000 | box IoU as in grounded chest X-ray reporting (MAIRA-2 / RadFact line; to confirm); true masks |
| BUS-BRA | grounded_check | 1.00 | 0.61 | 1.00 | 0.53 | 0.90 | 1.0000 | ours: finding_f1 x box IoU |
| BUS-BRA | box_support_gtbox | 0.80 | 0.50 | 1.00 | 0.50 | 1.00 | 1.0000 | spatial support rule (>= 50% of the box in the true region) |
| BUSI | bleu | 0.25 | 0.50 | 0.50 | 0.50 | 0.85 | 1.0000 | standard n-gram metric (Papineni et al. 2002) |
| BUSI | bertscore[roberta-large] | 0.25 | 0.50 | 0.50 | 0.50 | 0.99 | 1.0000 | BERTScore (Zhang et al. 2020) |
| BUSI | oracle_label_check | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | old evidence_check idea: text vs dataset labels (upper bound) |
| BUSI | mask_verified_facts | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | ours: text claims checked against the true mask |
| BUSI | semacc | 0.50 | 1.00 | 1.00 | 0.98 | 1.00 | 1.0000 | UltraG-Bench SemAcc (presence, category, location, size yes/no) |
| BUSI | location_check | 1.00 | 0.00 | 1.00 | 0.00 | 0.90 | 1.0000 | box IoU as in grounded chest X-ray reporting (MAIRA-2 / RadFact line; to confirm); true masks |
| BUSI | grounded_check | 1.00 | 1.00 | 1.00 | 0.97 | 0.90 | 1.0000 | ours: finding_f1 x box IoU |
| BUSI | box_support_gtbox | 0.82 | 0.50 | 1.00 | 0.50 | 1.00 | 1.0000 | spatial support rule (>= 50% of the box in the true region) |
| UDIAT | bleu | 0.25 | 0.50 | 0.50 | 0.50 | 0.86 | 1.0000 | standard n-gram metric (Papineni et al. 2002) |
| UDIAT | bertscore[roberta-large] | 0.25 | 0.50 | 0.50 | 0.50 | 0.99 | 1.0000 | BERTScore (Zhang et al. 2020) |
| UDIAT | oracle_label_check | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | old evidence_check idea: text vs dataset labels (upper bound) |
| UDIAT | mask_verified_facts | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | ours: text claims checked against the true mask |
| UDIAT | semacc | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | UltraG-Bench SemAcc (presence, category, location, size yes/no) |
| UDIAT | location_check | 1.00 | 0.00 | 1.00 | 0.00 | 0.89 | 1.0000 | box IoU as in grounded chest X-ray reporting (MAIRA-2 / RadFact line; to confirm); true masks |
| UDIAT | grounded_check | 1.00 | 0.88 | 1.00 | 0.89 | 0.89 | 1.0000 | ours: finding_f1 x box IoU |
| UDIAT | box_support_gtbox | 0.83 | 0.50 | 1.00 | 0.50 | 1.00 | 1.0000 | spatial support rule (>= 50% of the box in the true region) |
| BUS-UCLM | bleu | 0.25 | 0.50 | 0.50 | 0.50 | 0.85 | 1.0000 | standard n-gram metric (Papineni et al. 2002) |
| BUS-UCLM | bertscore[roberta-large] | 0.25 | 0.50 | 0.50 | 0.50 | 0.99 | 1.0000 | BERTScore (Zhang et al. 2020) |
| BUS-UCLM | oracle_label_check | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | old evidence_check idea: text vs dataset labels (upper bound) |
| BUS-UCLM | mask_verified_facts | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | ours: text claims checked against the true mask |
| BUS-UCLM | semacc | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | UltraG-Bench SemAcc (presence, category, location, size yes/no) |
| BUS-UCLM | location_check | 1.00 | 0.00 | 1.00 | 0.00 | 0.89 | 1.0000 | box IoU as in grounded chest X-ray reporting (MAIRA-2 / RadFact line; to confirm); true masks |
| BUS-UCLM | grounded_check | 1.00 | 1.00 | 1.00 | 0.99 | 0.89 | 1.0000 | ours: finding_f1 x box IoU |
| BUS-UCLM | box_support_gtbox | 0.82 | 0.50 | 1.00 | 0.50 | 1.00 | 1.0000 | spatial support rule (>= 50% of the box in the true region) |
| TN3K | bleu | 0.25 | 0.50 | 0.50 | 0.50 | 0.83 | 1.0000 | standard n-gram metric (Papineni et al. 2002) |
| TN3K | bertscore[roberta-large] | 0.25 | 0.50 | 0.50 | 0.50 | 0.98 | 1.0000 | BERTScore (Zhang et al. 2020) |
| TN3K | oracle_label_check | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | old evidence_check idea: text vs dataset labels (upper bound) |
| TN3K | mask_verified_facts | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | ours: text claims checked against the true mask |
| TN3K | semacc | 0.50 | 1.00 | 1.00 | 0.98 | 1.00 | 1.0000 | UltraG-Bench SemAcc (presence, category, location, size yes/no) |
| TN3K | location_check | 1.00 | 0.00 | 1.00 | 0.00 | 0.89 | 1.0000 | box IoU as in grounded chest X-ray reporting (MAIRA-2 / RadFact line; to confirm); true masks |
| TN3K | grounded_check | 1.00 | 1.00 | 1.00 | 0.96 | 0.89 | 1.0000 | ours: finding_f1 x box IoU |
| TN3K | box_support_gtbox | 0.82 | 0.50 | 1.00 | 0.50 | 1.00 | 1.0000 | spatial support rule (>= 50% of the box in the true region) |
| TN5000 | bleu | 0.25 | 0.50 | 0.50 | 0.50 | 0.83 | 1.0000 | standard n-gram metric (Papineni et al. 2002) |
| TN5000 | bertscore[roberta-large] | 0.25 | 0.50 | 0.50 | 0.50 | 0.98 | 1.0000 | BERTScore (Zhang et al. 2020) |
| TN5000 | oracle_label_check | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | old evidence_check idea: text vs dataset labels (upper bound) |
| TN5000 | mask_verified_facts | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | ours: text claims checked against the true mask |
| TN5000 | semacc | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | UltraG-Bench SemAcc (presence, category, location, size yes/no) |
| TN5000 | location_check | 1.00 | 0.00 | 1.00 | 0.00 | 0.90 | 1.0000 | box IoU as in grounded chest X-ray reporting (MAIRA-2 / RadFact line; to confirm); true masks |
| TN5000 | grounded_check | 1.00 | 1.00 | 1.00 | 0.99 | 0.90 | 1.0000 | ours: finding_f1 x box IoU |
| TN5000 | box_support_gtbox | 0.83 | 0.50 | 1.00 | 0.50 | 1.00 | 1.0000 | spatial support rule (>= 50% of the box in the true region) |
| DDTI | bleu | 0.25 | 0.50 | 0.50 | 0.50 | 0.84 | 1.0000 | standard n-gram metric (Papineni et al. 2002) |
| DDTI | bertscore[roberta-large] | 0.25 | 0.50 | 0.50 | 0.50 | 0.99 | 1.0000 | BERTScore (Zhang et al. 2020) |
| DDTI | oracle_label_check | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | old evidence_check idea: text vs dataset labels (upper bound) |
| DDTI | mask_verified_facts | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | ours: text claims checked against the true mask |
| DDTI | semacc | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | UltraG-Bench SemAcc (presence, category, location, size yes/no) |
| DDTI | location_check | 1.00 | 0.00 | 1.00 | 0.00 | 0.89 | 1.0000 | box IoU as in grounded chest X-ray reporting (MAIRA-2 / RadFact line; to confirm); true masks |
| DDTI | grounded_check | 1.00 | 0.56 | 1.00 | 0.51 | 0.89 | 1.0000 | ours: finding_f1 x box IoU |
| DDTI | box_support_gtbox | 0.84 | 0.50 | 0.99 | 0.50 | 1.00 | 1.0000 | spatial support rule (>= 50% of the box in the true region) |
| HC18 | bleu | 0.25 | — | — | 0.50 | 0.75 | 1.0000 | standard n-gram metric (Papineni et al. 2002) |
| HC18 | bertscore[roberta-large] | 0.25 | — | — | 0.50 | 0.99 | 1.0000 | BERTScore (Zhang et al. 2020) |
| HC18 | oracle_label_check | 0.50 | — | — | 1.00 | 1.00 | 1.0000 | old evidence_check idea: text vs dataset labels (upper bound) |
| HC18 | mask_verified_facts | 0.50 | — | — | 1.00 | 1.00 | 0.9992 | ours: text claims checked against the true mask |
| HC18 | semacc | 0.50 | — | — | 0.70 | 1.00 | 1.0000 | UltraG-Bench SemAcc (presence, category, location, size yes/no) |
| HC18 | location_check | 1.00 | — | — | 0.00 | 0.90 | 1.0000 | box IoU as in grounded chest X-ray reporting (MAIRA-2 / RadFact line; to confirm); true masks |
| HC18 | grounded_check | 1.00 | — | — | 1.00 | 0.90 | 1.0000 | ours: finding_f1 x box IoU |
| HC18 | box_support_gtbox | 0.79 | — | — | 0.50 | 1.00 | 1.0000 | spatial support rule (>= 50% of the box in the true region) |
| FetalHead | bleu | 0.25 | — | — | 0.50 | 0.88 | 1.0000 | standard n-gram metric (Papineni et al. 2002) |
| FetalHead | bertscore[roberta-large] | 0.25 | — | — | 0.50 | 0.99 | 1.0000 | BERTScore (Zhang et al. 2020) |
| FetalHead | oracle_label_check | 0.50 | — | — | 1.00 | 1.00 | 1.0000 | old evidence_check idea: text vs dataset labels (upper bound) |
| FetalHead | mask_verified_facts | 0.50 | — | — | 1.00 | 1.00 | 1.0000 | ours: text claims checked against the true mask |
| FetalHead | semacc | 0.50 | — | — | 0.62 | 1.00 | 1.0000 | UltraG-Bench SemAcc (presence, category, location, size yes/no) |
| FetalHead | location_check | 1.00 | — | — | 0.00 | 0.89 | 1.0000 | box IoU as in grounded chest X-ray reporting (MAIRA-2 / RadFact line; to confirm); true masks |
| FetalHead | grounded_check | 1.00 | — | — | 0.78 | 0.89 | 1.0000 | ours: finding_f1 x box IoU |
| FetalHead | box_support_gtbox | 0.79 | — | — | 0.50 | 1.00 | 1.0000 | spatial support rule (>= 50% of the box in the true region) |

Not run yet: GREEN (7B model too large for 16 GB), Claude judge (no credit), original RadFact, SAM/MedSAM predicted masks (Part B), real VLM-written reports on bench_v2d, any clinician-confirmed severity.

---
Limitations: see [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md) (templated reports, upper bounds, prompt-sensitive judge, provisional severity, possible exposure). 
