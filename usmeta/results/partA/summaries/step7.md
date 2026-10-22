# Step 7: Layer 2 AI judge (local Gemma-2-9B) on a SUBSAMPLE of bench_v2d (plain-language summary)

**What was run.** The judge is **Gemma-2-9B-it, 4-bit, run locally with MLX (greedy decoding)**. No Claude, no API credit. One model call per (reference, candidate) pair returns: whether each candidate sentence is supported by the reference (precision), whether each reference sentence is covered (recall), and a list of discrepancies with severity and error category. `sentence_check` follows the **RadFact protocol** (sentence-level support in both directions) but is our own Gemma prompt, **not the original RadFact code or prompts**. Scorers reported: `sentence_f1` (+ precision, recall) and `judge_score` (1 minus 0.6/0.3/0.1 per critical/major/minor error, the same rule as the earlier judge).

**It is a subsample, as the brief allowed: 20 cases per dataset (not 50)**, because the model takes about 5 seconds per pair and 50 cases would have taken more than the 3-hour limit. Per case: 1 harmless_small, 1 matched one-word synonym, 1 harmless_large, 2 planted errors of different categories (so 20 cases = about 40 errors per dataset), plus an identical copy for 3 cases per dataset. 995 rows sampled, 925 unique pairs judged in 81 minutes; 3 pairs were unparseable and dropped (missing, not zero); in 95 of 922 replies the model returned a true/false list of the wrong length (scored as the share of true values, flagged). Confidence intervals are wide (20 cases); read differences of a few hundredths as noise. Which model judged: Gemma-2-9B. It never grades its own family's reports (these are templated, no VLM output).

**Headline (AUROC vs the three kinds of harmless rewording; 1.0 perfect, 0.5 chance):**
- `sentence_f1` against the **matched one-word synonym**: 0.95-1.00 on all 10 datasets (BrEaST 0.95, BUS-BRA 1.00, BUSI 0.99, UDIAT 0.99, TN3K/TN5000/DDTI 1.00). Layer 0 on the same comparison reached at best 0.63 on BrEaST, Layer 1 `finding_f1` 1.00.
- Against **harmless_small** (synonyms, reorder, unit) it is weaker: BrEaST 0.85, UDIAT 0.68, DDTI 0.72; BUS-BRA 0.91, HC18/FetalHead 0.95, others 0.95-1.00. The judge does mark some harmless rewrites as errors: harmless_small mean score 0.78-1.00 (UDIAT 0.78, DDTI 0.81, HC18 0.84, BrEaST 0.96).
- Against **harmless_large** (style swap): 0.72-1.00 mean score on TN3K/TN5000 (0.76, 0.72) because the terse and long forms drop or add sentences, which the judge counts as unsupported or uncovered. AUROC 0.80 (DDTI) to 1.00.
- `judge_score` (error-list score) behaves similarly but a bit lower on BUSI (0.90) and FetalHead (0.80 vs small); critical-only AUROC 0.86-1.00.
- Severity Spearman: -0.08 to -0.85 (HC18 `sentence_f1` +0.39, i.e. wrong direction; `judge_score` -0.62). Not reliable as a severity scale.
- **Error category accuracy** (judge lists the planted category): 0.80 overall, any error listed 0.94. Weak spots (small n): BUSI false finding 0.22 (it often does not flag the added finding), BrEaST wrong measurement 0.00 (n=4), FetalHead wrong severity/category (plane swap) 0.00 although detected (it labels it with another category), TN3K missed finding 0.33 (detects it, names it differently), UDIAT/BUS-UCLM wrong severity/category 0.45/0.33.

**Wiring gate: NOT clean.** Identical-copy `sentence_f1` is **0.93 on UDIAT** (1 of 3 identical copies: the judge said one reference sentence ("Histology: fa.") was not covered by an identical candidate). All other datasets 1.00, and `judge_score` is 1.00 on identical copies everywhere. An LLM judge cannot guarantee the identical-copy gate; this is a result about the judge, not a wiring bug (the same text was passed as both reports). Per the brief this is the kind of event to ask about; it is flagged here and in the status.

**Compared with before.** The old Gemma-2-9B judge scored AUROC 0.78 overall and 0.99 critical-only on the old benchmark (bench_judge, 1,254 pairs, different harmless mix, no matched synonym). Not like for like: the new numbers are per dataset on bench_v2d, 20 cases each.

**Caveats (keep visible).** Templated, label-derived reports; severity provisional; template sources "to confirm"; per dataset only; 20 cases per dataset; one judge model (Gemma-2-9B) with a prompt we wrote; the original RadFact was not run; Claude judge not run (no credit).

---

## breast

### BrEaST (20 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 0.85 (0.72–0.95) | 0.95 (0.89–1.00) | 0.93 (0.82–1.00) | 0.92 / 1.00 / 1.00 | 0.96 | 1.00 | 0.99 | 1.0000 | — | -0.27 | size -0.33, count —, birads — |
| sentence_precision | 0.86 (0.75–0.95) | 0.94 (0.88–0.99) | 0.91 (0.81–0.99) | 0.96 / 1.00 / 1.00 | 0.96 | 1.00 | 0.99 | 1.0000 | — | -0.46 | size —, count —, birads — |
| sentence_recall | 0.74 (0.64–0.84) | 0.80 (0.71–0.88) | 0.78 (0.66–0.88) | 0.81 / 0.85 / 0.85 | 0.96 | 1.00 | 0.99 | 1.0000 | — | -0.24 | size -0.33, count —, birads — |
| judge_score | 0.86 (0.78–0.94) | 0.91 (0.84–0.97) | 0.88 (0.75–0.97) | 0.92 / 1.00 / 1.00 | 0.89 | 1.00 | 0.95 | 1.0000 | — | -0.35 | size -0.33, count —, birads — |

### BUS-BRA (20 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 0.91 (0.85–0.97) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.94 / 1.00 / 1.00 | 0.92 | 1.00 | 1.00 | 1.0000 | — | -0.60 | size -0.27, count —, birads — |
| sentence_precision | 0.78 (0.66–0.89) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.89 / 1.00 / 1.00 | 0.88 | 1.00 | 1.00 | 1.0000 | — | -0.45 | size —, count —, birads — |
| sentence_recall | 0.78 (0.70–0.85) | 0.81 (0.74–0.89) | 0.81 (0.74–0.89) | 0.92 / 0.97 / 0.97 | 0.97 | 1.00 | 1.00 | 1.0000 | — | -0.50 | size -0.27, count —, birads — |
| judge_score | 0.93 (0.81–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.86 / 1.00 / 1.00 | 0.90 | 1.00 | 1.00 | 1.0000 | — | -0.80 | size -0.41, count —, birads -0.87 |

### BUSI (20 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 0.99 (0.96–1.00) | 0.99 (0.96–1.00) | 0.99 (0.96–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | — | -0.58 | size -0.25, count — |
| sentence_precision | 0.99 (0.96–1.00) | 0.99 (0.96–1.00) | 0.99 (0.96–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | — | -0.53 | size -0.09, count — |
| sentence_recall | 0.85 (0.79–0.91) | 0.85 (0.79–0.91) | 0.85 (0.79–0.91) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | — | -0.62 | size -0.25, count — |
| judge_score | 0.90 (0.85–0.95) | 0.90 (0.85–0.95) | 0.90 (0.85–0.95) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | — | -0.60 | size -0.45, count — |

### UDIAT (20 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 0.68 (0.57–0.78) | 0.99 (0.96–1.00) | 0.93 (0.85–0.99) | 0.89 / 1.00 / 1.00 | 0.78 | 0.98 | 0.87 | 0.9333 | — | -0.35 | count —, size 0.10 |
| sentence_precision | 0.62 (0.53–0.72) | 0.99 (0.96–1.00) | 0.99 (0.96–1.00) | 0.83 / 1.00 / 1.00 | 0.75 | 1.00 | 0.97 | 1.0000 | — | -0.39 | count —, size 0.17 |
| sentence_recall | 0.65 (0.56–0.74) | 0.82 (0.74–0.90) | 0.65 (0.56–0.74) | 0.89 / 1.00 / 0.89 | 0.82 | 0.97 | 0.80 | 0.8889 | — | -0.38 | count —, size 0.09 |
| judge_score | 0.68 (0.53–0.81) | 0.97 (0.94–1.00) | 0.90 (0.81–0.97) | 0.94 / 1.00 / 1.00 | 0.67 | 1.00 | 0.91 | 1.0000 | — | -0.42 | count —, size 0.00 |

### BUS-UCLM (20 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 0.99 (0.96–1.00) | 0.99 (0.96–1.00) | 0.99 (0.96–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | — | -0.84 | size 0.25, count — |
| sentence_precision | 0.99 (0.96–1.00) | 0.99 (0.96–1.00) | 0.99 (0.96–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | — | -0.83 | size 0.25, count — |
| sentence_recall | 0.94 (0.88–0.99) | 0.94 (0.88–0.99) | 0.94 (0.88–0.99) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | — | -0.85 | size 0.25, count — |
| judge_score | 0.96 (0.91–1.00) | 0.96 (0.91–1.00) | 0.96 (0.91–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | — | -0.61 | size -0.40, count — |

## thyroid

### TN3K (20 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 0.76 | 1.0000 | — | -0.85 | size —, count — |
| sentence_precision | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 0.82 | 1.0000 | — | -0.85 | size —, count — |
| sentence_recall | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.80 (0.70–0.89) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 0.72 | 1.0000 | — | -0.85 | size —, count — |
| judge_score | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.95 (0.88–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 0.79 | 1.0000 | — | -0.73 | size -0.82, count — |

### TN5000 (20 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 0.72 | 1.0000 | — | -0.83 | size —, count — |
| sentence_precision | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 0.78 | 1.0000 | — | -0.83 | size —, count — |
| sentence_recall | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.75 (0.65–0.84) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 0.68 | 1.0000 | — | -0.83 | size —, count — |
| judge_score | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.88 (0.78–0.95) | 1.00 / 1.00 / 1.00 | 1.00 | 1.00 | 0.76 | 1.0000 | — | -0.69 | size -0.39, count — |

### DDTI (20 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 0.72 (0.57–0.86) | 1.00 (1.00–1.00) | 0.80 (0.65–0.94) | 1.00 / 1.00 / 0.89 | 0.81 | 1.00 | 0.75 | 1.0000 | — | -0.52 | tirads —, size 0.35 |
| sentence_precision | 0.74 (0.59–0.88) | 1.00 (1.00–1.00) | 0.72 (0.53–0.90) | 1.00 / 1.00 / 0.89 | 0.78 | 1.00 | 0.70 | 1.0000 | — | -0.51 | tirads —, size 0.47 |
| sentence_recall | 0.79 (0.68–0.89) | 0.97 (0.94–1.00) | 0.85 (0.70–0.97) | 1.00 / 1.00 / 0.89 | 0.85 | 1.00 | 0.90 | 1.0000 | — | -0.52 | tirads —, size 0.35 |
| judge_score | 0.75 (0.59–0.90) | 1.00 (1.00–1.00) | 0.78 (0.60–0.93) | 1.00 / 1.00 / 0.89 | 0.72 | 1.00 | 0.75 | 1.0000 | — | -0.62 | tirads —, size -0.29 |

## fetal

### HC18 (20 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 0.95 (0.88–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.88 / 1.00 / 1.00 | 0.84 | 1.00 | 0.90 | 1.0000 | — | 0.39 | hc_mm 0.39 |
| sentence_precision | 0.78 (0.65–0.88) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.69 / 1.00 / 1.00 | 0.78 | 1.00 | 1.00 | 1.0000 | — | — | hc_mm — |
| sentence_recall | 0.88 (0.78–0.97) | 0.90 (0.80–0.97) | 0.75 (0.65–0.85) | 0.75 / 0.81 / 0.75 | 0.97 | 1.00 | 0.85 | 1.0000 | — | 0.39 | hc_mm 0.39 |
| judge_score | 0.95 (0.88–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.94 / 1.00 / 1.00 | 0.85 | 1.00 | 1.00 | 1.0000 | — | -0.62 | hc_mm -0.62 |

### FetalHead (20 cases)

| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 0.95 (0.90–0.99) | 1.00 (1.00–1.00) | 0.96 (0.93–1.00) | 1.00 / 1.00 / 0.75 | 0.90 | 1.00 | 0.93 | 1.0000 | — | -0.08 | hc_mm -0.06 |
| sentence_precision | 0.85 (0.75–0.95) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 0.85 | 1.00 | 1.00 | 1.0000 | — | — | hc_mm — |
| sentence_recall | 0.85 (0.80–0.90) | 0.85 (0.80–0.90) | 0.75 (0.64–0.85) | 0.75 / 0.75 / 0.50 | 1.00 | 1.00 | 0.90 | 1.0000 | — | -0.08 | hc_mm -0.06 |
| judge_score | 0.80 (0.65–0.93) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 / 1.00 | 0.91 | 1.00 | 1.00 | 1.0000 | — | -0.20 | hc_mm -0.71 |

## AUROC by error category (vs harmless_small / vs matched 1-word / vs harmless_large)

**BrEaST**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| sentence_f1 | 0.88 / 1.00 / 1.00 | 1.00 / 1.00 / 0.92 | 1.00 / 1.00 / 1.00 | 0.38 / 0.62 / 0.50 | 0.87 / 0.97 / 0.97 |
| sentence_precision | 0.88 / 1.00 / 1.00 | 1.00 / 1.00 / 0.92 | 1.00 / 1.00 / 1.00 | 0.38 / 0.50 / 0.38 | 0.90 / 0.97 / 0.97 |
| sentence_recall | 0.75 / 0.83 / 0.83 | 1.00 / 1.00 / 0.92 | 1.00 / 1.00 / 1.00 | 0.50 / 0.62 / 0.50 | 0.63 / 0.70 / 0.70 |
| judge_score | 0.83 / 0.88 / 0.88 | 1.00 / 1.00 / 0.83 | 1.00 / 1.00 / 1.00 | 0.50 / 0.62 / 0.50 | 0.90 / 0.97 / 0.97 |

**BUS-BRA**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| sentence_f1 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 0.88 / 1.00 / 1.00 | 0.80 / 1.00 / 1.00 | 0.94 / 1.00 / 1.00 |
| sentence_precision | 0.40 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 0.75 / 1.00 / 1.00 | 0.80 / 1.00 / 1.00 | 0.81 / 1.00 / 1.00 |
| sentence_recall | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 0.88 / 1.00 / 1.00 | 0.50 / 0.55 / 0.55 | 0.78 / 0.81 / 0.81 |
| judge_score | 1.00 / 1.00 / 1.00 | 0.90 / 1.00 / 1.00 | 0.75 / 1.00 / 1.00 | 0.90 / 1.00 / 1.00 | 0.97 / 1.00 / 1.00 |

**BUSI**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| sentence_f1 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 0.96 / 0.96 / 0.96 | 1.00 / 1.00 / 1.00 |
| sentence_precision | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 0.96 / 0.96 / 0.96 | 1.00 / 1.00 / 1.00 |
| sentence_recall | 0.61 / 0.61 / 0.61 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 0.89 / 0.89 / 0.89 | 0.80 / 0.80 / 0.80 |
| judge_score | 0.61 / 0.61 / 0.61 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 0.96 / 0.96 / 0.96 | 1.00 / 1.00 / 1.00 |

**UDIAT**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| sentence_f1 | 0.33 / 1.00 / 0.33 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 0.59 / 0.97 / 0.97 | 0.59 / 1.00 / 0.95 |
| sentence_precision | 0.33 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 0.62 / 1.00 / 1.00 | 0.56 / 0.97 / 0.97 | 0.59 / 1.00 / 1.00 |
| sentence_recall | 0.33 / 0.67 / 0.17 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 0.56 / 0.78 / 0.59 | 0.55 / 0.77 / 0.55 |
| judge_score | 0.50 / 0.83 / 0.50 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 0.44 / 0.97 / 0.84 | 0.77 / 1.00 / 1.00 |

**BUS-UCLM**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| sentence_f1 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 0.90 / 0.90 / 0.90 | 1.00 / 1.00 / 1.00 |
| sentence_precision | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 0.90 / 0.90 / 0.90 | 1.00 / 1.00 / 1.00 |
| sentence_recall | 0.92 / 0.92 / 0.92 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 0.90 / 0.90 / 0.90 | 0.67 / 0.67 / 0.67 |
| judge_score | 0.92 / 0.92 / 0.92 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 0.90 / 0.90 / 0.90 | 1.00 / 1.00 / 1.00 |

**TN3K**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| sentence_f1 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| sentence_precision | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| sentence_recall | 1.00 / 1.00 / 0.67 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 0.75 | 1.00 / 1.00 / 0.77 | 1.00 / 1.00 / 0.60 |
| judge_score | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 0.85 | 1.00 / 1.00 / 1.00 |

**TN5000**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| sentence_f1 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| sentence_precision | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| sentence_recall | 1.00 / 1.00 / 0.56 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 0.50 | 1.00 / 1.00 / 0.71 | 1.00 / 1.00 / 0.83 |
| judge_score | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 0.83 | 1.00 / 1.00 / 0.68 | 1.00 / 1.00 / 1.00 |

**DDTI**

| scorer | false finding | missed finding | wrong location | wrong measurement | wrong severity/category |
|---|---|---|---|---|---|
| sentence_f1 | 0.83 / 1.00 / 0.67 | 0.88 / 1.00 / 1.00 | 0.33 / 1.00 / 0.50 | 0.82 / 1.00 / 0.82 | 0.61 / 1.00 / 0.75 |
| sentence_precision | 0.83 / 1.00 / 0.33 | 0.88 / 1.00 / 1.00 | 0.33 / 1.00 / 0.33 | 0.86 / 1.00 / 0.82 | 0.61 / 1.00 / 0.64 |
| sentence_recall | 0.83 / 1.00 / 1.00 | 0.94 / 1.00 / 1.00 | 0.67 / 1.00 / 0.67 | 0.77 / 0.91 / 0.77 | 0.71 / 1.00 / 0.82 |
| judge_score | 0.67 / 1.00 / 1.00 | 0.88 / 1.00 / 1.00 | 0.33 / 1.00 / 0.33 | 0.91 / 1.00 / 0.64 | 0.64 / 1.00 / 0.79 |

**HC18**

| scorer | wrong measurement |
|---|---|
| sentence_f1 | 0.95 / 1.00 / 1.00 |
| sentence_precision | 0.78 / 1.00 / 1.00 |
| sentence_recall | 0.88 / 0.90 / 0.75 |
| judge_score | 0.95 / 1.00 / 1.00 |

**FetalHead**

| scorer | wrong measurement | wrong severity/category |
|---|---|---|
| sentence_f1 | 0.90 / 1.00 / 0.93 | 1.00 / 1.00 / 1.00 |
| sentence_precision | 0.85 / 1.00 / 1.00 | 0.85 / 1.00 / 1.00 |
| sentence_recall | 0.70 / 0.70 / 0.60 | 1.00 / 1.00 / 0.90 |
| judge_score | 0.88 / 1.00 / 1.00 | 0.72 / 1.00 / 1.00 |

## Judge category accuracy (planted category listed by the judge) and detection (judge lists any error)

| dataset | category | n | category accuracy | any error listed |
|---|---|---|---|---|
| BUS-BRA | false finding | 5 | 1.00 | 1.00 |
| BUS-BRA | missed finding | 5 | 1.00 | 1.00 |
| BUS-BRA | wrong location | 4 | 1.00 | 1.00 |
| BUS-BRA | wrong measurement | 10 | 1.00 | 1.00 |
| BUS-BRA | wrong severity/category | 16 | 0.69 | 1.00 |
| BUS-UCLM | false finding | 12 | 0.83 | 0.83 |
| BUS-UCLM | missed finding | 4 | 1.00 | 1.00 |
| BUS-UCLM | wrong location | 4 | 1.00 | 1.00 |
| BUS-UCLM | wrong measurement | 5 | 0.80 | 0.80 |
| BUS-UCLM | wrong severity/category | 3 | 0.33 | 1.00 |
| BUSI | false finding | 9 | 0.22 | 0.22 |
| BUSI | missed finding | 7 | 1.00 | 1.00 |
| BUSI | wrong location | 2 | 1.00 | 1.00 |
| BUSI | wrong measurement | 14 | 0.93 | 0.93 |
| BUSI | wrong severity/category | 5 | 0.60 | 1.00 |
| BrEaST | false finding | 12 | 0.75 | 0.75 |
| BrEaST | missed finding | 6 | 1.00 | 1.00 |
| BrEaST | wrong location | 1 | 1.00 | 1.00 |
| BrEaST | wrong measurement | 4 | 0.00 | 0.25 |
| BrEaST | wrong severity/category | 15 | 0.73 | 0.93 |
| DDTI | false finding | 3 | 1.00 | 1.00 |
| DDTI | missed finding | 8 | 0.75 | 1.00 |
| DDTI | wrong location | 3 | 1.00 | 1.00 |
| DDTI | wrong measurement | 11 | 1.00 | 1.00 |
| DDTI | wrong severity/category | 14 | 0.93 | 1.00 |
| FetalHead | wrong measurement | 20 | 1.00 | 1.00 |
| FetalHead | wrong severity/category | 20 | 0.00 | 1.00 |
| HC18 | wrong measurement | 20 | 1.00 | 1.00 |
| TN3K | false finding | 6 | 1.00 | 1.00 |
| TN3K | missed finding | 12 | 0.33 | 1.00 |
| TN3K | wrong location | 4 | 1.00 | 1.00 |
| TN3K | wrong measurement | 13 | 1.00 | 1.00 |
| TN3K | wrong severity/category | 5 | 1.00 | 1.00 |
| TN5000 | false finding | 9 | 1.00 | 1.00 |
| TN5000 | missed finding | 11 | 0.64 | 1.00 |
| TN5000 | wrong location | 3 | 1.00 | 1.00 |
| TN5000 | wrong measurement | 14 | 1.00 | 1.00 |
| TN5000 | wrong severity/category | 3 | 1.00 | 1.00 |
| UDIAT | false finding | 3 | 0.67 | 0.67 |
| UDIAT | missed finding | 6 | 1.00 | 1.00 |
| UDIAT | wrong location | 4 | 1.00 | 1.00 |
| UDIAT | wrong measurement | 16 | 0.94 | 0.94 |
| UDIAT | wrong severity/category | 11 | 0.45 | 1.00 |