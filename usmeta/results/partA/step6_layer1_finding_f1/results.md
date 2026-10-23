# Step 6: Layer 1 structured fact check (`finding_f1`) on bench_v2d (plain-language summary)

**What was built.** `usmeta/schema.py`: an ultrasound finding schema (entity -> attributes, status present/absent; breast = BI-RADS lexicon terms, thyroid = TI-RADS terms, fetal = HC mm + plane), a rule-based extractor for our templated wording, a local-LLM extractor for free text that must quote its evidence, and the scorers `finding_f1`, `finding_precision`, `finding_recall`. Attributes match as exact categories; size and head circumference get graded credit (size credit falls to 0 at 50% relative error; HC at 20 mm, the old fact_checker's tolerance). A "No lesion" answer to a report with a lesion gets precision 0, recall 0. The old `fact_checker` / `fact_f1` are kept for comparison. Run on **bench_v2d** (31,976 rows; supersedes bench_v2b/v2c after the BUS-BRA fix, see step5 rerun3), so the brief's "bench_v2b" is replaced by "bench_v2d".

**Headline (templated reports):**
- `finding_f1` AUROC is **1.00 on all 10 datasets**, against harmless_small, the matched one-word synonym and harmless_large alike; critical-only AUROC 1.00. Harmless rewordings score 1.00 on average and identical copies exactly 1.0000. Detection rate of every planted error field is >= 0.99 (table below). For comparison, the best Layer 0 scorer reached 0.63 on BrEaST (RaTEScore, matched synonym).
- **This is an upper bound, not a finding about free text.** The extractor is written for the same wording that generated the reports (field agreement with the dataset labels: **99.99% of 126,840 fields** over all styles and rewordings). The real question is whether it holds when a model writes the report; that needs the free-text extractor below.
- The size-error blind spot of Layer 0 is gone: size x0.5/x1.5/x2 get credit 0/0.0-0.8/0 so they score < 1. Severity Spearman is -0.27 to -0.99 (weak on breast, -0.99 on HC18): `finding_f1` counts every attribute equally, so a one-word shape change costs as much as a changed diagnosis. A severity-weighted version is the obvious next step.
- **Lazy "No abnormality." report:** 0.00-0.11 on every dataset except BUS-UCLM (0.42), where 419 of 683 cases are normal studies and "No abnormality" is the correct answer there.
- **Old `fact_checker` / `fact_f1` fail the wiring gate on this benchmark:** identical-copy mean 0.12-0.99 instead of 1.0 (it only parses our v1 wording, so it extracts nothing from v2 text). This is the expected reason, not a wiring bug in the new scorer; its AUROC columns are meaningless here and are kept only to show why the extractor must match the report wording. `finding_f1` passes the gate (min 1.0000).

**Extractor validation (the 85% stop rule).**
- Rule-based extractor vs dataset labels, per field, on every identical/harmless candidate: **99.99%** (126,840 fields). One failure mode found and fixed on the way: our own synonym rewording turned "in a mass" into "in a lesion", which the extractor now reads back as "in a mass".
- Local LLM extractor (Gemma-2-9B-it 4-bit via MLX, quotes its evidence, a value is dropped if the quote is not in the report): **first run on 30 cases x 3 styles (531 fields): 82.9% = below the 85% stop rule.** The misses were wording, not understanding (e.g. returns "no calcifications" for "no", boolean for the halo, copies the prompt's option list for position). I added a value-normalisation map and a clearer prompt, and no model call changed. Same 30 cases after normalisation: 97.0% (tuned on that sample, so not a fair number). **Fresh sample, never seen (20 cases x 3 styles, 342 fields, final prompt): 98.5%**, with 0 unquoted values and 0 parse failures. Remaining error: it multiplies head circumference by 10 for 3 of 12 HC values (260.4 mm -> 2604) and truncates one position phrase. Not yet run on real free-text VLM reports with ground truth.
- Time: about 20-25 seconds per report with the 9B model, so the LLM extractor is not used for the 31,976-row table (the rule-based one is).

**Caveats (keep visible).** Reports are templated from labels (synthetic but fact-correct); severity is provisional pending clinician; template sources are "to confirm"; per dataset only; `finding_f1` 1.00 is an upper bound (extractor = template); 150 cases per dataset (256 BrEaST); the LLM extractor is validated on 50 templated reports only.

---


## LLM extractor per-field agreement on the fresh sample (seed 1)

lesion 1.00, count 1.00, pos 0.95, orient 1.00, size_mm 1.00, shape 1.00, margin 1.00, echo 1.00, post 1.00, calc 1.00, halo 1.00, birads 1.00, path 1.00, size_pct 1.00, side 1.00, hist 1.00, comp 1.00, foci 1.00, tirads 1.00, hc_mm 0.75, plane 1.00

## breast

### BrEaST (256 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| finding_f1 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.01 | -0.31 | count —, size -0.12, birads 0.00 |
| finding_precision | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.02 | -0.31 | count —, size -0.12, birads 0.00 |
| finding_recall | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.01 | -0.29 | count —, size -0.12, birads 0.00 |
| legacy_fact_checker | 0.74 (0.74–0.75) | 0.76 (0.76–0.76) | 0.52 (0.51–0.53) | 1.00 / 1.00 / 0.93 | 0.92 | 0.93 | 0.84 | 0.9192 | 0.00 | -0.52 | count —, size 0.00, birads -0.01 |
| legacy_fact_f1 | 0.74 (0.73–0.75) | 0.76 (0.75–0.76) | 0.51 (0.50–0.52) | 0.98 / 1.00 / 0.82 | 0.87 | 0.88 | 0.80 | 0.8726 | 0.00 | -0.40 | count —, size 0.00, birads -0.01 |

### BUS-BRA (151 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| finding_f1 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.00 | -0.27 | count —, size -0.12, birads -0.00 |
| finding_precision | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.00 | -0.27 | count —, size -0.12, birads -0.00 |
| finding_recall | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.00 | -0.27 | count —, size -0.12, birads -0.00 |
| legacy_fact_checker | 0.65 (0.65–0.66) | 0.65 (0.65–0.66) | 0.65 (0.65–0.66) | 0.89 / 0.89 / 0.89 | 0.38 | 0.38 | 0.38 | 0.3846 | 0.00 | -0.57 | count —, size —, birads — |
| legacy_fact_f1 | 0.65 (0.65–0.66) | 0.65 (0.65–0.66) | 0.65 (0.65–0.66) | 0.89 / 0.89 / 0.89 | 0.25 | 0.25 | 0.25 | 0.2500 | 0.00 | -0.54 | count —, size —, birads — |

### BUSI (150 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| finding_f1 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.11 | -0.52 | count —, size -0.16 |
| finding_precision | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.16 | -0.52 | count —, size -0.16 |
| finding_recall | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.08 | -0.52 | count —, size -0.16 |
| legacy_fact_checker | 0.69 (0.67–0.71) | 0.69 (0.67–0.71) | 0.69 (0.67–0.71) | 1.00 / 1.00 / 1.00 | 0.23 | 0.23 | 0.23 | 0.2308 | 0.00 | -0.82 | count —, size — |
| legacy_fact_f1 | 0.69 (0.67–0.71) | 0.69 (0.67–0.71) | 0.69 (0.67–0.71) | 1.00 / 1.00 / 1.00 | 0.12 | 0.12 | 0.12 | 0.1250 | 0.00 | -0.82 | count —, size — |

### UDIAT (150 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| finding_f1 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.00 | -0.48 | count —, size -0.17 |
| finding_precision | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.00 | -0.48 | count —, size -0.17 |
| finding_recall | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.00 | -0.48 | count —, size -0.17 |
| legacy_fact_checker | 0.61 (0.61–0.62) | 0.61 (0.61–0.62) | 0.61 (0.61–0.62) | 1.00 / 1.00 / 1.00 | 0.23 | 0.23 | 0.23 | 0.2308 | 0.00 | -0.78 | count —, size — |
| legacy_fact_f1 | 0.61 (0.61–0.62) | 0.61 (0.61–0.62) | 0.61 (0.61–0.62) | 1.00 / 1.00 / 1.00 | 0.12 | 0.12 | 0.12 | 0.1250 | 0.00 | -0.78 | count —, size — |

### BUS-UCLM (152 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| finding_f1 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.42 | -0.69 | count —, size -0.18 |
| finding_precision | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.62 | -0.69 | count —, size -0.18 |
| finding_recall | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.31 | -0.69 | count —, size -0.18 |
| legacy_fact_checker | 0.86 (0.84–0.89) | 0.86 (0.84–0.89) | 0.86 (0.84–0.89) | 1.00 / 1.00 / 1.00 | 0.23 | 0.23 | 0.23 | 0.2308 | 0.00 | -0.90 | count —, size — |
| legacy_fact_f1 | 0.86 (0.84–0.89) | 0.86 (0.84–0.89) | 0.86 (0.84–0.89) | 1.00 / 1.00 / 1.00 | 0.12 | 0.12 | 0.12 | 0.1250 | 0.00 | -0.90 | count —, size — |

## thyroid

### TN3K (150 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| finding_f1 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.00 | -0.55 | count —, size -0.18 |
| finding_precision | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.00 | -0.55 | count —, size -0.18 |
| finding_recall | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.00 | -0.55 | count —, size -0.18 |
| legacy_fact_checker | 0.40 (0.39–0.40) | 0.48 (0.48–0.49) | 0.65 (0.64–0.65) | 0.75 / 0.83 / 1.00 | 0.12 | 0.17 | 0.25 | 0.2500 | 0.00 | -0.68 | count —, size — |
| legacy_fact_f1 | 0.40 (0.39–0.40) | 0.48 (0.48–0.49) | 0.65 (0.64–0.65) | 0.75 / 0.83 / 1.00 | 0.12 | 0.17 | 0.25 | 0.2500 | 0.00 | -0.68 | count —, size — |

### TN5000 (150 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| finding_f1 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.00 | -0.57 | count —, size -0.17 |
| finding_precision | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.00 | -0.57 | count —, size -0.17 |
| finding_recall | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.00 | -0.57 | count —, size -0.17 |
| legacy_fact_checker | 0.40 (0.40–0.41) | 0.49 (0.48–0.49) | 0.65 (0.65–0.66) | 0.75 / 0.83 / 1.00 | 0.12 | 0.17 | 0.25 | 0.2500 | 0.00 | -0.68 | count —, size — |
| legacy_fact_f1 | 0.40 (0.40–0.41) | 0.49 (0.48–0.49) | 0.65 (0.65–0.66) | 0.75 / 0.83 / 1.00 | 0.12 | 0.17 | 0.25 | 0.2500 | 0.00 | -0.68 | count —, size — |

### DDTI (150 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| finding_f1 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.02 | -0.28 | count —, size -0.03, tirads 0.00 |
| finding_precision | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.02 | -0.27 | count —, size -0.03, tirads 0.00 |
| finding_recall | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.02 | -0.28 | count —, size -0.03, tirads 0.00 |
| legacy_fact_checker | 0.33 (0.33–0.34) | 0.45 (0.44–0.45) | 0.58 (0.57–0.58) | 0.60 / 0.71 / 0.85 | 0.12 | 0.18 | 0.24 | 0.2450 | 0.00 | -0.46 | count —, size —, tirads — |
| legacy_fact_f1 | 0.33 (0.33–0.34) | 0.45 (0.44–0.45) | 0.58 (0.57–0.58) | 0.60 / 0.71 / 0.85 | 0.12 | 0.18 | 0.24 | 0.2450 | 0.00 | -0.46 | count —, size —, tirads — |

## fetal

### HC18 (150 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| finding_f1 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.00 | -0.99 | hc_mm -0.99 |
| finding_precision | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.00 | -0.99 | hc_mm -0.99 |
| finding_recall | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.00 | -0.99 | hc_mm -0.99 |
| legacy_fact_checker | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.00 | -0.99 | hc_mm -0.99 |
| legacy_fact_f1 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.00 | -0.99 | hc_mm -0.99 |

### FetalHead (151 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| finding_f1 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.00 | -0.82 | hc_mm -1.00 |
| finding_precision | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.00 | -0.82 | hc_mm -1.00 |
| finding_recall | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.00 | -0.82 | hc_mm -1.00 |
| legacy_fact_checker | 0.90 (0.90–0.90) | 0.90 (0.89–0.90) | 0.90 (0.89–0.90) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 0.99 | 0.9934 | 0.00 | -0.69 | hc_mm -1.00 |
| legacy_fact_f1 | 0.90 (0.90–0.90) | 0.90 (0.89–0.90) | 0.90 (0.89–0.90) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 0.99 | 0.9934 | 0.00 | -0.69 | hc_mm -1.00 |

## AUROC by error category (vs harmless_small / vs matched 1-word / vs harmless_large)

**BrEaST**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| finding_f1 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| finding_precision | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| finding_recall | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| legacy_fact_checker | 0.65 / 0.67 / 0.41 | 0.94 / 0.95 / 0.91 | 0.47 / 0.49 / 0.23 | 0.47 / 0.50 / 0.24 | 0.86 / 0.88 / 0.61 |
| legacy_fact_f1 | 0.65 / 0.67 / 0.40 | 0.94 / 0.95 / 0.91 | 0.47 / 0.49 / 0.23 | 0.47 / 0.50 / 0.24 | 0.85 / 0.87 / 0.60 |

**BUS-BRA**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| finding_f1 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| finding_precision | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| finding_recall | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| legacy_fact_checker | 0.50 / 0.50 / 0.50 | 1.00 / 1.00 / 1.00 | 0.50 / 0.50 / 0.50 | 0.50 / 0.50 / 0.50 | 0.75 / 0.75 / 0.75 |
| legacy_fact_f1 | 0.50 / 0.50 / 0.50 | 1.00 / 1.00 / 1.00 | 0.50 / 0.50 / 0.50 | 0.50 / 0.50 / 0.50 | 0.75 / 0.75 / 0.75 |

**BUSI**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| finding_f1 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| finding_precision | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| finding_recall | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| legacy_fact_checker | 0.58 / 0.58 / 0.58 | 1.00 / 1.00 / 1.00 | 0.50 / 0.50 / 0.50 | 0.50 / 0.50 / 0.50 | 0.75 / 0.75 / 0.75 |
| legacy_fact_f1 | 0.58 / 0.58 / 0.58 | 1.00 / 1.00 / 1.00 | 0.50 / 0.50 / 0.50 | 0.50 / 0.50 / 0.50 | 0.75 / 0.75 / 0.75 |

**UDIAT**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| finding_f1 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| finding_precision | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| finding_recall | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| legacy_fact_checker | 0.50 / 0.50 / 0.50 | 1.00 / 1.00 / 1.00 | 0.50 / 0.50 / 0.50 | 0.50 / 0.50 / 0.50 | 0.67 / 0.67 / 0.67 |
| legacy_fact_f1 | 0.50 / 0.50 / 0.50 | 1.00 / 1.00 / 1.00 | 0.50 / 0.50 / 0.50 | 0.50 / 0.50 / 0.50 | 0.67 / 0.67 / 0.67 |

**BUS-UCLM**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| finding_f1 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| finding_precision | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| finding_recall | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| legacy_fact_checker | 0.82 / 0.82 / 0.82 | 1.00 / 1.00 / 1.00 | 0.50 / 0.50 / 0.50 | 0.50 / 0.50 / 0.50 | 0.75 / 0.75 / 0.75 |
| legacy_fact_f1 | 0.82 / 0.82 / 0.82 | 1.00 / 1.00 / 1.00 | 0.50 / 0.50 / 0.50 | 0.50 / 0.50 / 0.50 | 0.75 / 0.75 / 0.75 |

**TN3K**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| finding_f1 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| finding_precision | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| finding_recall | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| legacy_fact_checker | 0.75 / 0.83 / 1.00 | 0.75 / 0.83 / 1.00 | 0.25 / 0.33 / 0.50 | 0.25 / 0.33 / 0.50 | 0.25 / 0.33 / 0.50 |
| legacy_fact_f1 | 0.75 / 0.83 / 1.00 | 0.75 / 0.83 / 1.00 | 0.25 / 0.33 / 0.50 | 0.25 / 0.33 / 0.50 | 0.25 / 0.33 / 0.50 |

**TN5000**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| finding_f1 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| finding_precision | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| finding_recall | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| legacy_fact_checker | 0.75 / 0.83 / 1.00 | 0.75 / 0.83 / 1.00 | 0.25 / 0.33 / 0.50 | 0.25 / 0.33 / 0.50 | 0.25 / 0.33 / 0.50 |
| legacy_fact_f1 | 0.75 / 0.83 / 1.00 | 0.75 / 0.83 / 1.00 | 0.25 / 0.33 / 0.50 | 0.25 / 0.33 / 0.50 | 0.25 / 0.33 / 0.50 |

**DDTI**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| finding_f1 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| finding_precision | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| finding_recall | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| legacy_fact_checker | 0.63 / 0.74 / 0.87 | 0.63 / 0.74 / 0.88 | 0.25 / 0.36 / 0.50 | 0.25 / 0.36 / 0.50 | 0.25 / 0.36 / 0.50 |
| legacy_fact_f1 | 0.63 / 0.74 / 0.87 | 0.63 / 0.74 / 0.88 | 0.25 / 0.36 / 0.50 | 0.25 / 0.36 / 0.50 | 0.25 / 0.36 / 0.50 |

**HC18**

| scorer | wrong measurement |
|---|---|
| finding_f1 | 1.00 / 1.00 / 1.00 |
| finding_precision | 1.00 / 1.00 / 1.00 |
| finding_recall | 1.00 / 1.00 / 1.00 |
| legacy_fact_checker | 1.00 / 1.00 / 1.00 |
| legacy_fact_f1 | 1.00 / 1.00 / 1.00 |

**FetalHead**

| scorer | wrong measurement | wrong severity/category |
|---|---|---|
| finding_f1 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| finding_precision | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| finding_recall | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| legacy_fact_checker | 1.00 / 1.00 / 1.00 | 0.50 / 0.50 / 0.50 |
| legacy_fact_f1 | 1.00 / 1.00 / 1.00 | 0.50 / 0.50 / 0.50 |

## AUROC against each harmless group separately (errors vs that group only)

**BrEaST**

| scorer | synonym1 | synonyms | reorder | unit_cm | style_terse | style_long | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|---|---|---|---|---|---|
| finding_f1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| finding_precision | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| finding_recall | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| legacy_fact_checker | 0.76 | 0.70 | 0.76 | 0.76 | 0.29 | 0.75 | 0.34 | 0.76 | 0.30 | 0.76 |
| legacy_fact_f1 | 0.76 | 0.69 | 0.76 | 0.76 | 0.29 | 0.73 | 0.34 | 0.76 | 0.30 | 0.76 |

**BUS-BRA**

| scorer | synonym1 | synonyms | reorder | unit_cm | style_terse | style_long | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|---|---|---|---|---|---|
| finding_f1 | 1.00 | 1.00 | 1.00 | — | 1.00 | 1.00 | — | 1.00 | 1.00 | 1.00 |
| finding_precision | 1.00 | 1.00 | 1.00 | — | 1.00 | 1.00 | — | 1.00 | 1.00 | 1.00 |
| finding_recall | 1.00 | 1.00 | 1.00 | — | 1.00 | 1.00 | — | 1.00 | 1.00 | 1.00 |
| legacy_fact_checker | 0.65 | 0.65 | 0.65 | — | 0.65 | 0.65 | — | 0.65 | 0.65 | 0.65 |
| legacy_fact_f1 | 0.65 | 0.65 | 0.65 | — | 0.65 | 0.65 | — | 0.65 | 0.65 | 0.65 |

**BUSI**

| scorer | synonym1 | synonyms | reorder | unit_cm | style_terse | style_long | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|---|---|---|---|---|---|
| finding_f1 | 1.00 | 1.00 | 1.00 | — | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| finding_precision | 1.00 | 1.00 | 1.00 | — | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| finding_recall | 1.00 | 1.00 | 1.00 | — | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| legacy_fact_checker | 0.69 | 0.69 | 0.69 | — | 0.69 | 0.69 | 1.00 | 0.69 | 0.69 | 0.69 |
| legacy_fact_f1 | 0.69 | 0.69 | 0.69 | — | 0.69 | 0.69 | 1.00 | 0.69 | 0.69 | 0.69 |

**UDIAT**

| scorer | synonym1 | synonyms | reorder | unit_cm | style_terse | style_long | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|---|---|---|---|---|---|
| finding_f1 | 1.00 | 1.00 | 1.00 | — | 1.00 | 1.00 | — | 1.00 | 1.00 | 1.00 |
| finding_precision | 1.00 | 1.00 | 1.00 | — | 1.00 | 1.00 | — | 1.00 | 1.00 | 1.00 |
| finding_recall | 1.00 | 1.00 | 1.00 | — | 1.00 | 1.00 | — | 1.00 | 1.00 | 1.00 |
| legacy_fact_checker | 0.61 | 0.61 | 0.61 | — | 0.61 | 0.61 | — | 0.61 | 0.61 | 0.61 |
| legacy_fact_f1 | 0.61 | 0.61 | 0.61 | — | 0.61 | 0.61 | — | 0.61 | 0.61 | 0.61 |

**BUS-UCLM**

| scorer | synonym1 | synonyms | reorder | unit_cm | style_terse | style_long | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|---|---|---|---|---|---|
| finding_f1 | 1.00 | 1.00 | 1.00 | — | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| finding_precision | 1.00 | 1.00 | 1.00 | — | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| finding_recall | 1.00 | 1.00 | 1.00 | — | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| legacy_fact_checker | 0.86 | 0.86 | 0.86 | — | 0.86 | 0.86 | 1.00 | 0.86 | 0.86 | 0.86 |
| legacy_fact_f1 | 0.86 | 0.86 | 0.86 | — | 0.86 | 0.86 | 1.00 | 0.86 | 0.86 | 0.86 |

**TN3K**

| scorer | synonym1 | synonyms | reorder | unit_cm | style_terse | style_long | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|---|---|---|---|---|---|
| finding_f1 | 1.00 | 1.00 | 1.00 | — | 1.00 | 1.00 | — | 1.00 | 1.00 | 1.00 |
| finding_precision | 1.00 | 1.00 | 1.00 | — | 1.00 | 1.00 | — | 1.00 | 1.00 | 1.00 |
| finding_recall | 1.00 | 1.00 | 1.00 | — | 1.00 | 1.00 | — | 1.00 | 1.00 | 1.00 |
| legacy_fact_checker | 0.48 | 0.15 | 0.65 | — | 0.65 | 0.65 | — | 0.65 | 0.65 | 0.65 |
| legacy_fact_f1 | 0.48 | 0.15 | 0.65 | — | 0.65 | 0.65 | — | 0.65 | 0.65 | 0.65 |

**TN5000**

| scorer | synonym1 | synonyms | reorder | unit_cm | style_terse | style_long | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|---|---|---|---|---|---|
| finding_f1 | 1.00 | 1.00 | 1.00 | — | 1.00 | 1.00 | — | 1.00 | 1.00 | 1.00 |
| finding_precision | 1.00 | 1.00 | 1.00 | — | 1.00 | 1.00 | — | 1.00 | 1.00 | 1.00 |
| finding_recall | 1.00 | 1.00 | 1.00 | — | 1.00 | 1.00 | — | 1.00 | 1.00 | 1.00 |
| legacy_fact_checker | 0.49 | 0.15 | 0.65 | — | 0.65 | 0.65 | — | 0.65 | 0.65 | 0.65 |
| legacy_fact_f1 | 0.49 | 0.15 | 0.65 | — | 0.65 | 0.65 | — | 0.65 | 0.65 | 0.65 |

**DDTI**

| scorer | synonym1 | synonyms | reorder | unit_cm | style_terse | style_long | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|---|---|---|---|---|---|
| finding_f1 | 1.00 | 1.00 | 1.00 | — | 1.00 | 1.00 | — | 1.00 | 1.00 | 1.00 |
| finding_precision | 1.00 | 1.00 | 1.00 | — | 1.00 | 1.00 | — | 1.00 | 1.00 | 1.00 |
| finding_recall | 1.00 | 1.00 | 1.00 | — | 1.00 | 1.00 | — | 1.00 | 1.00 | 1.00 |
| legacy_fact_checker | 0.45 | 0.09 | 0.58 | — | 0.58 | 0.58 | — | 0.58 | 0.58 | 0.58 |
| legacy_fact_f1 | 0.45 | 0.09 | 0.58 | — | 0.58 | 0.58 | — | 0.58 | 0.58 | 0.58 |

**HC18**

| scorer | synonym1 | synonyms | reorder | unit_cm | style_terse | style_long | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|---|---|---|---|---|---|
| finding_f1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | — | 1.00 | 1.00 | 1.00 |
| finding_precision | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | — | 1.00 | 1.00 | 1.00 |
| finding_recall | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | — | 1.00 | 1.00 | 1.00 |
| legacy_fact_checker | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | — | 1.00 | 1.00 | 1.00 |
| legacy_fact_f1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | — | 1.00 | 1.00 | 1.00 |

**FetalHead**

| scorer | synonym1 | synonyms | reorder | unit_cm | style_terse | style_long | negation | hedge | pad1 | pad3 |
|---|---|---|---|---|---|---|---|---|---|---|
| finding_f1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | — | 1.00 | 1.00 | 1.00 |
| finding_precision | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | — | 1.00 | 1.00 | 1.00 |
| finding_recall | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | — | 1.00 | 1.00 | 1.00 |
| legacy_fact_checker | 0.90 | 0.90 | 0.90 | 0.90 | 0.90 | 0.90 | — | 0.90 | 0.90 | 0.90 |
| legacy_fact_f1 | 0.90 | 0.90 | 0.90 | 0.90 | 0.90 | 0.90 | — | 0.90 | 0.90 | 0.90 |


## Attribute accuracy on identical + harmless candidates (wiring check)

| dataset | attribute | accuracy | n |
|---|---|---|---|
| BUS-BRA | assessment.birads | 1.000 | 1661 |
| BUS-BRA | lesion.count | 1.000 | 1661 |
| BUS-BRA | lesion.orient | 1.000 | 1661 |
| BUS-BRA | lesion.pos | 1.000 | 1661 |
| BUS-BRA | lesion.side | 1.000 | 1342 |
| BUS-BRA | lesion.size_pct | 1.000 | 1661 |
| BUS-BRA | lesion.status | 1.000 | 1661 |
| BUS-BRA | pathology.hist | 1.000 | 1661 |
| BUS-BRA | pathology.path | 1.000 | 1661 |
| BUS-UCLM | lesion.count | 1.000 | 570 |
| BUS-UCLM | lesion.orient | 1.000 | 570 |
| BUS-UCLM | lesion.pos | 1.000 | 570 |
| BUS-UCLM | lesion.size_pct | 1.000 | 570 |
| BUS-UCLM | lesion.status | 1.000 | 1520 |
| BUS-UCLM | pathology.path | 1.000 | 1520 |
| BUSI | lesion.count | 1.000 | 1260 |
| BUSI | lesion.orient | 1.000 | 1260 |
| BUSI | lesion.pos | 1.000 | 1260 |
| BUSI | lesion.size_pct | 1.000 | 1260 |
| BUSI | lesion.status | 1.000 | 1500 |
| BUSI | pathology.path | 1.000 | 1500 |
| BrEaST | assessment.birads | 1.000 | 4067 |
| BrEaST | calcifications.status | 1.000 | 4027 |
| BrEaST | calcifications.type | 1.000 | 427 |
| BrEaST | halo.status | 1.000 | 4027 |
| BrEaST | lesion.count | 1.000 | 4027 |
| BrEaST | lesion.echo | 1.000 | 4027 |
| BrEaST | lesion.margin | 1.000 | 4027 |
| BrEaST | lesion.orient | 1.000 | 4027 |
| BrEaST | lesion.pos | 1.000 | 4027 |
| BrEaST | lesion.post | 1.000 | 4027 |
| BrEaST | lesion.shape | 1.000 | 4027 |
| BrEaST | lesion.size_mm | 1.000 | 4027 |
| BrEaST | lesion.status | 1.000 | 4067 |
| BrEaST | pathology.path | 1.000 | 4067 |
| DDTI | assessment.tirads | 1.000 | 1320 |
| DDTI | foci.status | 1.000 | 1320 |
| DDTI | foci.type | 1.000 | 876 |
| DDTI | lesion.comp | 1.000 | 912 |
| DDTI | lesion.count | 1.000 | 1727 |
| DDTI | lesion.echo | 1.000 | 912 |
| DDTI | lesion.margin | 1.000 | 1296 |
| DDTI | lesion.orient | 1.000 | 1727 |
| DDTI | lesion.pos | 1.000 | 1727 |
| DDTI | lesion.size_pct | 1.000 | 1727 |
| DDTI | lesion.status | 1.000 | 1754 |
| FetalHead | head.hc_mm | 1.000 | 1650 |
| FetalHead | head.plane | 1.000 | 1657 |
| HC18 | head.hc_mm | 1.000 | 1650 |
| TN3K | lesion.count | 1.000 | 1650 |
| TN3K | lesion.orient | 1.000 | 1650 |
| TN3K | lesion.pos | 1.000 | 1650 |
| TN3K | lesion.size_pct | 1.000 | 1650 |
| TN3K | lesion.status | 1.000 | 1650 |
| TN5000 | lesion.count | 1.000 | 1650 |
| TN5000 | lesion.orient | 1.000 | 1650 |
| TN5000 | lesion.pos | 1.000 | 1650 |
| TN5000 | lesion.size_pct | 1.000 | 1650 |
| TN5000 | lesion.status | 1.000 | 1650 |
| UDIAT | lesion.count | 1.000 | 1500 |
| UDIAT | lesion.orient | 1.000 | 1500 |
| UDIAT | lesion.pos | 1.000 | 1500 |
| UDIAT | lesion.size_pct | 1.000 | 1500 |
| UDIAT | lesion.status | 1.000 | 1500 |
| UDIAT | pathology.hist | 1.000 | 1500 |
| UDIAT | pathology.path | 1.000 | 1500 |

## Detection rate by planted error field (share of errors where finding_f1 < 1)

| dataset | planted field | detected | n |
|---|---|---|---|
| BUS-BRA | birads | 1.000 | 210 |
| BUS-BRA | count | 1.000 | 151 |
| BUS-BRA | hist | 1.000 | 151 |
| BUS-BRA | lesion | 1.000 | 151 |
| BUS-BRA | orient | 1.000 | 151 |
| BUS-BRA | path | 1.000 | 151 |
| BUS-BRA | pos | 1.000 | 87 |
| BUS-BRA | side | 1.000 | 122 |
| BUS-BRA | size_pct | 1.000 | 453 |
| BUS-UCLM | count | 1.000 | 55 |
| BUS-UCLM | lesion | 1.000 | 152 |
| BUS-UCLM | orient | 1.000 | 57 |
| BUS-UCLM | path | 1.000 | 57 |
| BUS-UCLM | pos | 1.000 | 33 |
| BUS-UCLM | size_pct | 1.000 | 171 |
| BUSI | count | 1.000 | 121 |
| BUSI | lesion | 1.000 | 150 |
| BUSI | orient | 1.000 | 126 |
| BUSI | path | 1.000 | 126 |
| BUSI | pos | 1.000 | 97 |
| BUSI | size_pct | 1.000 | 378 |
| BrEaST | birads | 1.000 | 770 |
| BrEaST | calc | 1.000 | 252 |
| BrEaST | count | 1.000 | 252 |
| BrEaST | echo | 1.000 | 157 |
| BrEaST | halo | 1.000 | 252 |
| BrEaST | lesion | 1.000 | 256 |
| BrEaST | margin | 1.000 | 252 |
| BrEaST | orient | 1.000 | 252 |
| BrEaST | path | 1.000 | 252 |
| BrEaST | pos | 1.000 | 144 |
| BrEaST | post | 1.000 | 86 |
| BrEaST | shape | 1.000 | 252 |
| BrEaST | size_mm | 1.000 | 756 |
| DDTI | comp | 1.000 | 76 |
| DDTI | count | 1.000 | 92 |
| DDTI | echo | 1.000 | 76 |
| DDTI | foci | 1.000 | 110 |
| DDTI | lesion | 1.000 | 150 |
| DDTI | margin | 1.000 | 108 |
| DDTI | orient | 1.000 | 147 |
| DDTI | pos | 1.000 | 98 |
| DDTI | size_pct | 1.000 | 441 |
| DDTI | tirads | 1.000 | 353 |
| FetalHead | hc_mm | 1.000 | 600 |
| FetalHead | plane | 1.000 | 151 |
| HC18 | hc_mm | 1.000 | 600 |
| TN3K | count | 1.000 | 136 |
| TN3K | lesion | 1.000 | 150 |
| TN3K | orient | 1.000 | 150 |
| TN3K | pos | 1.000 | 99 |
| TN3K | size_pct | 1.000 | 442 |
| TN5000 | count | 1.000 | 150 |
| TN5000 | lesion | 1.000 | 150 |
| TN5000 | orient | 1.000 | 150 |
| TN5000 | pos | 1.000 | 90 |
| TN5000 | size_pct | 1.000 | 450 |
| UDIAT | count | 1.000 | 150 |
| UDIAT | hist | 1.000 | 150 |
| UDIAT | lesion | 1.000 | 150 |
| UDIAT | orient | 1.000 | 150 |
| UDIAT | path | 1.000 | 150 |
| UDIAT | pos | 1.000 | 115 |
| UDIAT | size_pct | 1.000 | 450 |

---
Limitations: see [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md) (templated reports, upper bounds, prompt-sensitive judge, provisional severity, possible exposure). 
