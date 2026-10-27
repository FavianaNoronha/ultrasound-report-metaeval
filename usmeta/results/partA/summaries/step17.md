# Step 17: final consolidation (combined table + plain-language summary)

Limitations: [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md). Nothing was re-run: `usmeta/final_table.py` reads the saved result files of Steps 10d, 11 (rerun2), 12, 14, 15 and 16 and writes the table below (also saved as `usmeta/results_layers_all_final.md`). The older Step 9 table (`step9_combined_results`, all splits, 20-case judge sample) is kept unchanged. The plain-language write-up is `usmeta/RESULTS_SUMMARY.md` (copied here).

**What changed vs Step 9.** Test-split numbers only; Layer 2 is the 59-case Step 12 judge; Layer 3 shows true-mask (upper bound, templated) next to predicted-mask (Step 16) results; new sections for real VLM reports (Qwen2.5-VL, MedGemma; per-writer graders differ) and for HiSBreast real text; every row carries n (groups), CIs, and a "too small to compare" mark for n < 30 cases or groups.

---

# Every scorer, every layer, locked test split: final combined table (Part A + Part B + real text)

Supersedes `results_layers_all.md` (Step 9, which pooled all splits and a 20-case judge sample; kept unchanged). Built by `python3 -m usmeta.final_table` from the SAVED result files of Steps 10d, 11 (rerun2), 12, 14, 15 and 16: no number here is typed by hand. Tuning and choices were on dev/val only; all numbers below are test-split numbers (Step 16 and Step 15 also test).

**Marks used.** ⚠ *too small to compare* = fewer than 30 cases or fewer than 30 patient/exam groups. **upper bound, templated** = the checker reads the same template (Layer 1 `finding_f1`) or the same masks (Layer 3 with true masks) as the reference was built from, so it cannot fail on templated text. **Per dataset, never pooled** (pooled rows only where stated). Templated references, provisional severity, no clinician: see `docs/LIMITATIONS.md`.

## A. Templated benchmark on the LOCKED TEST split (Layers 0–3)

AUROC = chance that a planted error scores LOWER than a harmless rewording of the same report (1.0 perfect, 0.5 chance, below 0.5 = the scorer prefers the error). small = synonyms / reorder / unit rewrite, matched = ONE-word synonym (same edit size as an error), large = style swap. Cells: AUROC (95% CI, resampling patient/exam groups). n = cases (groups). Layers 0–1: Step 10d (frozen code, all test cases of the 150-case sample); Layer 2: Step 12 (Gemma-2-9B, prompt_v2, 59 cases per dataset); Layer 3: Step 10d (true masks, case-level CIs) and Step 16 (predicted masks).

### breast

#### BrEaST

| layer | scorer | n (groups) | vs small | vs matched | vs large | identical mean | status |
|---|---|---|---|---|---|---|---|
| 0 word overlap / embedding | bleu | 103 (103) | 0.25 (0.24–0.27) | 0.61 (0.60–0.62) | 0.08 (0.06–0.11) | 1.0000 | measured |
| 0 word overlap / embedding | rougeL | 103 (103) | 0.10 (0.08–0.13) | 0.58 (0.57–0.60) | 0.08 (0.06–0.11) | 1.0000 | measured |
| 0 word overlap / embedding | chrf | 103 (103) | 0.38 (0.36–0.40) | 0.25 (0.22–0.27) | 0.08 (0.06–0.11) | 1.0000 | measured |
| 0 word overlap / embedding | bertscore[roberta-large] | 103 (103) | 0.21 (0.19–0.23) | 0.53 (0.52–0.54) | 0.08 (0.06–0.11) | 1.0000 | measured |
| 0 word overlap / embedding | ratescore | 103 (103) | 0.45 (0.43–0.47) | 0.64 (0.63–0.66) | 0.13 (0.11–0.16) | 1.0000 | measured |
| 1 structured facts | finding_f1 | 103 (103) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.0000 | **upper bound, templated** |
| 2 AI judge (Gemma-2-9B, prompt_v2) | sentence_f1 | 59 (59) | 0.67 (0.59–0.75) | 0.89 (0.86–0.92) | 0.61 (0.52–0.69) | 1.0000 | measured, one judge, one prompt |
| 2 AI judge (Gemma-2-9B, prompt_v2) | judge_score | 59 (59) | 0.85 (0.77–0.93) | 1.00 (0.99–1.00) | 0.51 (0.42–0.62) | 1.0000 | measured, one judge, one prompt |

#### BUS-BRA

| layer | scorer | n (groups) | vs small | vs matched | vs large | identical mean | status |
|---|---|---|---|---|---|---|---|
| 0 word overlap / embedding | bleu | 150 (85) | 0.21 (0.20–0.22) | 0.75 (0.74–0.76) | 0.09 (0.09–0.10) | 1.0000 | measured |
| 0 word overlap / embedding | rougeL | 150 (85) | 0.09 (0.09–0.10) | 0.66 (0.66–0.67) | 0.09 (0.09–0.10) | 1.0000 | measured |
| 0 word overlap / embedding | chrf | 150 (85) | 0.30 (0.29–0.31) | 0.36 (0.35–0.38) | 0.09 (0.09–0.10) | 1.0000 | measured |
| 0 word overlap / embedding | bertscore[roberta-large] | 150 (85) | 0.09 (0.09–0.10) | 0.42 (0.41–0.43) | 0.09 (0.09–0.10) | 1.0000 | measured |
| 0 word overlap / embedding | ratescore | 150 (85) | 0.52 (0.51–0.53) | 0.66 (0.65–0.67) | 0.20 (0.18–0.22) | 1.0000 | measured |
| 1 structured facts | finding_f1 | 150 (85) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.0000 | **upper bound, templated** |
| 2 AI judge (Gemma-2-9B, prompt_v2) | sentence_f1 | 59 (50) | 0.60 (0.50–0.71) | 0.96 (0.94–0.98) | 0.96 (0.94–0.98) | 1.0000 | measured, one judge, one prompt |
| 2 AI judge (Gemma-2-9B, prompt_v2) | judge_score | 59 (50) | 0.64 (0.54–0.75) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.0000 | measured, one judge, one prompt |

#### BUSI

| layer | scorer | n (groups) | vs small | vs matched | vs large | identical mean | status |
|---|---|---|---|---|---|---|---|
| 0 word overlap / embedding | bleu | 150 (133) | 0.64 (0.61–0.67) | 0.82 (0.81–0.83) | 0.28 (0.22–0.33) | 1.0000 | measured |
| 0 word overlap / embedding | rougeL | 150 (133) | 0.30 (0.25–0.36) | 0.75 (0.73–0.77) | 0.28 (0.22–0.33) | 1.0000 | measured |
| 0 word overlap / embedding | chrf | 150 (133) | 0.64 (0.61–0.67) | 0.55 (0.51–0.58) | 0.28 (0.22–0.33) | 1.0000 | measured |
| 0 word overlap / embedding | bertscore[roberta-large] | 150 (133) | 0.28 (0.22–0.33) | 0.52 (0.48–0.56) | 0.28 (0.22–0.33) | 1.0000 | measured |
| 0 word overlap / embedding | ratescore | 150 (133) | 0.61 (0.58–0.64) | 0.68 (0.65–0.71) | 0.60 (0.57–0.63) | 1.0000 | measured |
| 1 structured facts | finding_f1 | 150 (133) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.0000 | **upper bound, templated** |
| 2 AI judge (Gemma-2-9B, prompt_v2) | sentence_f1 | 59 (57) | 0.67 (0.57–0.75) | 0.89 (0.86–0.92) | 0.88 (0.83–0.91) | 1.0000 | measured, one judge, one prompt |
| 2 AI judge (Gemma-2-9B, prompt_v2) | judge_score | 59 (57) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.98 (0.95–1.00) | 1.0000 | measured, one judge, one prompt |

#### UDIAT

| layer | scorer | n (groups) | vs small | vs matched | vs large | identical mean | status |
|---|---|---|---|---|---|---|---|
| 0 word overlap / embedding | bleu | 66 (64) | 0.50 (0.50–0.50) | 0.78 (0.78–0.78) | 0.11 (0.11–0.12) | 1.0000 | measured |
| 0 word overlap / embedding | rougeL | 66 (64) | 0.11 (0.11–0.12) | 0.67 (0.67–0.67) | 0.11 (0.11–0.12) | 1.0000 | measured |
| 0 word overlap / embedding | chrf | 66 (64) | 0.50 (0.49–0.51) | 0.44 (0.44–0.44) | 0.11 (0.11–0.12) | 1.0000 | measured |
| 0 word overlap / embedding | bertscore[roberta-large] | 66 (64) | 0.11 (0.11–0.12) | 0.52 (0.50–0.53) | 0.11 (0.11–0.12) | 1.0000 | measured |
| 0 word overlap / embedding | ratescore | 66 (64) | 0.53 (0.52–0.54) | 0.63 (0.60–0.66) | 0.51 (0.50–0.52) | 1.0000 | measured |
| 1 structured facts | finding_f1 | 66 (64) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.0000 | **upper bound, templated** |
| 2 AI judge (Gemma-2-9B, prompt_v2) | sentence_f1 | 59 (57) | 0.61 (0.52–0.70) | 0.95 (0.93–0.98) | 0.87 (0.83–0.92) | 1.0000 | measured, one judge, one prompt |
| 2 AI judge (Gemma-2-9B, prompt_v2) | judge_score | 59 (57) | 0.69 (0.60–0.79) | 1.00 (1.00–1.00) | 0.93 (0.89–0.97) | 1.0000 | measured, one judge, one prompt |

#### BUS-UCLM

| layer | scorer | n (groups) | vs small | vs matched | vs large | identical mean | status |
|---|---|---|---|---|---|---|---|
| 0 word overlap / embedding | bleu | 177 (9) | 0.85 (0.81–0.90) | 0.92 (0.90–0.95) | 0.71 (0.62–0.80) | 1.0000 | ⚠ too small to compare |
| 0 word overlap / embedding | rougeL | 177 (9) | 0.72 (0.63–0.80) | 0.89 (0.87–0.93) | 0.71 (0.62–0.80) | 1.0000 | ⚠ too small to compare |
| 0 word overlap / embedding | chrf | 177 (9) | 0.85 (0.81–0.90) | 0.82 (0.77–0.87) | 0.71 (0.62–0.80) | 1.0000 | ⚠ too small to compare |
| 0 word overlap / embedding | bertscore[roberta-large] | 177 (9) | 0.71 (0.62–0.80) | 0.81 (0.76–0.87) | 0.71 (0.62–0.80) | 1.0000 | ⚠ too small to compare |
| 0 word overlap / embedding | ratescore | 177 (9) | 0.83 (0.78–0.88) | 0.86 (0.82–0.91) | 0.83 (0.78–0.88) | 1.0000 | ⚠ too small to compare |
| 1 structured facts | finding_f1 | 177 (9) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.0000 | **upper bound, templated** ⚠ too small to compare |
| 2 AI judge (Gemma-2-9B, prompt_v2) | sentence_f1 | 59 (9) | 0.91 (0.87–0.96) | 0.97 (0.96–0.99) | 0.95 (0.91–0.99) | 1.0000 | ⚠ too small to compare |
| 2 AI judge (Gemma-2-9B, prompt_v2) | judge_score | 59 (9) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.97 (0.92–1.00) | 1.0000 | ⚠ too small to compare |

### thyroid

#### TN3K

| layer | scorer | n (groups) | vs small | vs matched | vs large | identical mean | status |
|---|---|---|---|---|---|---|---|
| 0 word overlap / embedding | bleu | 150 (150) | 0.58 (0.58–0.58) | 0.82 (0.81–0.82) | 0.16 (0.15–0.16) | 1.0000 | measured |
| 0 word overlap / embedding | rougeL | 150 (150) | 0.16 (0.15–0.16) | 0.73 (0.72–0.73) | 0.16 (0.15–0.16) | 1.0000 | measured |
| 0 word overlap / embedding | chrf | 150 (150) | 0.58 (0.58–0.58) | 0.45 (0.44–0.46) | 0.16 (0.15–0.16) | 1.0000 | measured |
| 0 word overlap / embedding | bertscore[roberta-large] | 150 (150) | 0.16 (0.15–0.16) | 0.59 (0.57–0.60) | 0.16 (0.15–0.16) | 1.0000 | measured |
| 0 word overlap / embedding | ratescore | 150 (150) | 0.56 (0.55–0.57) | 0.55 (0.53–0.56) | 0.33 (0.31–0.34) | 1.0000 | measured |
| 1 structured facts | finding_f1 | 150 (150) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.0000 | **upper bound, templated** |
| 2 AI judge (Gemma-2-9B, prompt_v2) | sentence_f1 | 59 (59) | 0.99 (0.98–1.00) | 0.99 (0.98–1.00) | 0.92 (0.89–0.95) | 1.0000 | measured, one judge, one prompt |
| 2 AI judge (Gemma-2-9B, prompt_v2) | judge_score | 59 (59) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (0.99–1.00) | 1.0000 | measured, one judge, one prompt |

#### TN5000

| layer | scorer | n (groups) | vs small | vs matched | vs large | identical mean | status |
|---|---|---|---|---|---|---|---|
| 0 word overlap / embedding | bleu | 150 (149) | 0.58 (0.58–0.58) | 0.82 (0.82–0.82) | 0.16 (0.15–0.16) | 1.0000 | measured |
| 0 word overlap / embedding | rougeL | 150 (149) | 0.16 (0.15–0.16) | 0.73 (0.73–0.74) | 0.16 (0.15–0.16) | 1.0000 | measured |
| 0 word overlap / embedding | chrf | 150 (149) | 0.58 (0.58–0.58) | 0.47 (0.46–0.47) | 0.16 (0.15–0.16) | 1.0000 | measured |
| 0 word overlap / embedding | bertscore[roberta-large] | 150 (149) | 0.16 (0.15–0.16) | 0.56 (0.54–0.57) | 0.16 (0.15–0.16) | 1.0000 | measured |
| 0 word overlap / embedding | ratescore | 150 (149) | 0.58 (0.57–0.59) | 0.56 (0.55–0.58) | 0.35 (0.34–0.36) | 1.0000 | measured |
| 1 structured facts | finding_f1 | 150 (149) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.0000 | **upper bound, templated** |
| 2 AI judge (Gemma-2-9B, prompt_v2) | sentence_f1 | 59 (59) | 1.00 (0.99–1.00) | 1.00 (0.99–1.00) | 0.90 (0.87–0.93) | 1.0000 | measured, one judge, one prompt |
| 2 AI judge (Gemma-2-9B, prompt_v2) | judge_score | 59 (59) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.99 (0.97–1.00) | 1.0000 | measured, one judge, one prompt |

#### DDTI

| layer | scorer | n (groups) | vs small | vs matched | vs large | identical mean | status |
|---|---|---|---|---|---|---|---|
| 0 word overlap / embedding | bleu | 150 (114) | 0.45 (0.43–0.46) | 0.66 (0.65–0.68) | 0.10 (0.09–0.10) | 1.0000 | measured |
| 0 word overlap / embedding | rougeL | 150 (114) | 0.11 (0.10–0.13) | 0.66 (0.65–0.67) | 0.11 (0.10–0.13) | 1.0000 | measured |
| 0 word overlap / embedding | chrf | 150 (114) | 0.44 (0.42–0.46) | 0.36 (0.34–0.37) | 0.10 (0.09–0.11) | 1.0000 | measured |
| 0 word overlap / embedding | bertscore[roberta-large] | 150 (114) | 0.13 (0.11–0.15) | 0.52 (0.50–0.54) | 0.10 (0.09–0.11) | 1.0000 | measured |
| 0 word overlap / embedding | ratescore | 150 (114) | 0.48 (0.46–0.50) | 0.55 (0.53–0.57) | 0.24 (0.21–0.26) | 1.0000 | measured |
| 1 structured facts | finding_f1 | 150 (114) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.0000 | **upper bound, templated** |
| 2 AI judge (Gemma-2-9B, prompt_v2) | sentence_f1 | 59 (52) | 0.71 (0.63–0.79) | 0.90 (0.87–0.93) | 0.69 (0.60–0.78) | 1.0000 | measured, one judge, one prompt |
| 2 AI judge (Gemma-2-9B, prompt_v2) | judge_score | 59 (52) | 0.89 (0.82–0.96) | 1.00 (1.00–1.00) | 0.82 (0.73–0.90) | 1.0000 | measured, one judge, one prompt |

### fetal

#### HC18

| layer | scorer | n (groups) | vs small | vs matched | vs large | identical mean | status |
|---|---|---|---|---|---|---|---|
| 0 word overlap / embedding | bleu | 150 (150) | 0.33 (0.33–0.33) | 0.50 (0.50–0.50) | 0.00 (0.00–0.00) | 1.0000 | measured |
| 0 word overlap / embedding | rougeL | 150 (150) | 0.17 (0.17–0.17) | 0.50 (0.50–0.50) | 0.00 (0.00–0.00) | 1.0000 | measured |
| 0 word overlap / embedding | chrf | 150 (150) | 0.34 (0.33–0.34) | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | 1.0000 | measured |
| 0 word overlap / embedding | bertscore[roberta-large] | 150 (150) | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | 1.0000 | measured |
| 0 word overlap / embedding | ratescore | 150 (150) | 0.42 (0.40–0.44) | 0.10 (0.07–0.13) | 0.04 (0.02–0.05) | 1.0000 | measured |
| 1 structured facts | finding_f1 | 150 (150) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.0000 | **upper bound, templated** |
| 2 AI judge (Gemma-2-9B, prompt_v2) | sentence_f1 | 59 (59) | 0.82 (0.76–0.89) | 1.00 (1.00–1.00) | 0.63 (0.49–0.75) | 1.0000 | measured, one judge, one prompt |
| 2 AI judge (Gemma-2-9B, prompt_v2) | judge_score | 59 (59) | 0.94 (0.90–0.97) | 1.00 (1.00–1.00) | 0.63 (0.49–0.75) | 1.0000 | measured, one judge, one prompt |

#### FetalHead

| layer | scorer | n (groups) | vs small | vs matched | vs large | identical mean | status |
|---|---|---|---|---|---|---|---|
| 0 word overlap / embedding | bleu | 153 (54) | 0.37 (0.37–0.37) | 0.56 (0.55–0.57) | 0.01 (0.00–0.02) | 1.0000 | measured |
| 0 word overlap / embedding | rougeL | 153 (54) | 0.17 (0.17–0.17) | 0.50 (0.50–0.50) | 0.01 (0.00–0.02) | 1.0000 | measured |
| 0 word overlap / embedding | chrf | 153 (54) | 0.55 (0.53–0.56) | 0.22 (0.20–0.24) | 0.07 (0.05–0.09) | 1.0000 | measured |
| 0 word overlap / embedding | bertscore[roberta-large] | 153 (54) | 0.13 (0.13–0.13) | 0.22 (0.20–0.24) | 0.11 (0.10–0.12) | 1.0000 | measured |
| 0 word overlap / embedding | ratescore | 153 (54) | 0.49 (0.47–0.50) | 0.39 (0.37–0.42) | 0.11 (0.09–0.14) | 1.0000 | measured |
| 1 structured facts | finding_f1 | 153 (54) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.0000 | **upper bound, templated** |
| 2 AI judge (Gemma-2-9B, prompt_v2) | sentence_f1 | 59 (37) | 0.94 (0.91–0.97) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.0000 | measured, one judge, one prompt |
| 2 AI judge (Gemma-2-9B, prompt_v2) | judge_score | 59 (37) | 0.85 (0.77–0.93) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.0000 | measured, one judge, one prompt |

### Layer 3: image check, true masks (circular) vs predicted masks (non-circular)

Different benchmarks, so the AUROC columns are not comparable across the two blocks. **True masks (Step 10d, `bench_loc`, 100 cases per dataset; case-level CIs):** the reference facts were measured from the same masks the check reads, so the check cannot fail on a true report: **upper bound, templated**. The first AUROC (all errors) includes box-only errors that a text check cannot see (0.5 by construction); the other two are the text errors the mask can verify. **Predicted masks (Step 16):** MedSAM, box prompts from the TRUE masks (exact box), test split, 30 scans per dataset (18 BUS-UCLM); AUROC of `mask_verified_facts` over all mask-checkable planted errors (position, size, lesion, count, orientation) vs harmless rewordings; IoU = predicted vs true mask.

| dataset | TRUE masks: n | mask_verified_facts AUROC: all errors / wrong text position / wrong size | grounded_check AUROC (all errors) | status | PREDICTED masks: n (groups) | IoU | mask_verified_facts AUROC (all checkable) | position errors | size errors | correct report scores | text scorer RaTEScore (same cases) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BrEaST | 100 | 0.78 (0.78–0.79) / 1.00 / 1.00 | 0.59 (0.56–0.62) | **upper bound, templated** | 30 | 0.74 (0.69–0.79) | 0.93 (0.88–0.97) (n=30) | 0.97 (0.91–1.00) (n=17, too small to compare) | 0.88 (0.78–0.96) (n=30) | 0.89 | 0.64 (0.62–0.65) (n=30) |
| BUS-BRA | 100 | 0.78 (0.77–0.78) / 1.00 / 1.00 | 0.75 (0.72–0.79) | **upper bound, templated** | 30 | 0.61 (0.56–0.66) | 0.91 (0.86–0.95) (n=30) | 0.94 (0.85–1.00) (n=17, too small to compare) | 0.83 (0.73–0.91) (n=30) | 0.86 | 0.64 (0.63–0.66) (n=30) |
| BUSI | 100 | 0.79 (0.79–0.80) / 1.00 / 1.00 | 0.98 (0.96–0.99) | **upper bound, templated** | 30 | 0.73 (0.68–0.77) | 0.95 (0.91–0.98) (n=30) | 0.92 (0.84–1.00) (n=19, too small to compare) | 0.93 (0.84–1.00) (n=30) | 0.89 | 0.70 (0.67–0.71) (n=30) |
| UDIAT | 66 | 0.80 (0.79–0.81) / 1.00 / 1.00 | 0.93 (0.91–0.96) | **upper bound, templated** | 30 | 0.80 (0.77–0.84) | 0.98 (0.96–1.00) (n=30) | 1.00 (1.00–1.00) (n=23, too small to compare) | 0.98 (0.95–1.00) (n=30) | 0.94 | 0.69 (0.67–0.70) (n=30) |
| BUS-UCLM | 60 | 0.79 (0.78–0.80) / 1.00 / 1.00 | 1.00 (1.00–1.00) | **upper bound, templated** | 18 ⚠ too small to compare | 0.66 (0.54–0.78) | 0.95 (0.87–0.99) (n=18, too small to compare) | 1.00 (1.00–1.00) (n=8, too small to compare) | 0.91 (0.76–1.00) (n=18, too small to compare) | 0.87 | 0.69 (0.65–0.72) (n=18, too small to compare) |
| TN3K | 100 | 0.78 (0.78–0.79) / 1.00 / 1.00 | 0.98 (0.96–0.99) | **upper bound, templated** | 30 | 0.60 (0.53–0.66) | 0.89 (0.84–0.93) (n=30) | 0.94 (0.85–1.00) (n=17, too small to compare) | 0.84 (0.74–0.92) (n=30) | 0.82 | 0.56 (0.55–0.58) (n=30) |
| TN5000 | 100 | 0.78 (0.77–0.78) / 1.00 / 1.00 | 1.00 (1.00–1.00) | **upper bound, templated** | 30 | box IoU 0.58 (0.52–0.65) (no true mask) | 0.88 (0.83–0.93) (n=30) | 0.97 (0.91–1.00) (n=17, too small to compare) | 0.82 (0.72–0.89) (n=30) | 0.82 | 0.58 (0.56–0.60) (n=30) |
| DDTI | 100 | 0.79 (0.78–0.80) / 1.00 / 1.00 | 0.77 (0.73–0.81) | **upper bound, templated** | 30 | 0.49 (0.43–0.54) | 0.82 (0.75–0.88) (n=30) | 0.84 (0.72–0.97) (n=16, too small to compare) | 0.69 (0.59–0.80) (n=30) | 0.71 | 0.52 (0.51–0.54) (n=30) |
| HC18 | 100 | 0.79 (0.79–0.79) / — / 1.00 | 1.00 (1.00–1.00) | **upper bound, templated** | 30 | 0.52 (0.44–0.59) | 0.46 (0.43–0.49) (n=30) | — (no such errors) | 0.46 (0.43–0.49) (n=30) | 0.01 | 0.44 (0.42–0.46) (n=30) |
| FetalHead | 100 | 0.79 (0.79–0.79) / — / 1.00 | 0.88 (0.87–0.88) | **upper bound, templated** | 30 | 0.44 (0.35–0.54) | 0.50 (0.48–0.52) (n=30) | — (no such errors) | 0.50 (0.48–0.52) (n=30) | 0.00 | 0.54 (0.51–0.57) (n=30) |
| **breast + thyroid pooled** | | | | | | | 0.91 (0.89–0.93) (n=228) | 0.95 (0.92–0.97) (n=134) | 0.86 (0.82–0.89) (n=228) | | RaTEScore 0.62 (0.61–0.63) (n=228) |
| **all 10 datasets pooled** | | | | | | | 0.82 (0.79–0.85) (n=288) | 0.95 (0.92–0.97) (n=134) | 0.78 (0.74–0.81) (n=288) | | RaTEScore 0.59 (0.58–0.61) (n=288) |

Reading: with predicted masks the check is no longer perfect and gives correct reports < 1.0 (column "correct report scores", mean score of identical copies; 1.000 with true masks). It beats the text scorers on breast and thyroid, and is at chance on fetal head (skull-ring annotation vs the interior MedSAM outlines). See `step16_partB/results.md`.

## B. Real VLM-written reports on the TEST split (Layers 1–3 against the templated true report)

**Possible training exposure, unverifiable** (both models may have seen BUS-BRA, BrEaST, TN3K, TN5000, HC18). **The two writers were graded by different model families (Qwen reports: Gemma-2-9B; MedGemma reports: Qwen2.5-7B), so `finding_f1` and `sentence_f1` columns are different measuring sticks and must not be ranked against each other.** Cells: mean (95% CI resampling groups). n = reports (groups). Every dataset has n < 30, so every row is **too small to compare**; the pooled rows in `step14_medgemma/results.md` only show whether scorers agree.

| dataset | writer | n (groups) | finding_f1 | sentence_f1 prompt_v2 (judge family) | box IoU | boxes IoU ≥ 0.5 | status |
|---|---|---|---|---|---|---|---|
| BrEaST | Qwen2.5-VL-3B | 19 (19) | 0.18 (0.14–0.21) | 0.37 (0.29–0.44) (Gemma) | 0.24 (0.14–0.34) | 24% | ⚠ too small to compare |
| BrEaST | MedGemma-1.5-4B (4-bit) | 19 (19) | 0.30 (0.21–0.40) | 0.42 (0.33–0.50) (Qwen2.5-7B) | 0.22 (0.13–0.32) | 16% | ⚠ too small to compare |
| BUS-BRA | Qwen2.5-VL-3B | 21 (21) | 0.24 (0.22–0.27) | 0.27 (0.17–0.36) (Gemma) | 0.21 (0.15–0.28) | 10% | ⚠ too small to compare |
| BUS-BRA | MedGemma-1.5-4B (4-bit) | 21 (21) | 0.28 (0.21–0.35) | 0.33 (0.22–0.44) (Qwen2.5-7B) | 0.26 (0.19–0.32) | 5% | ⚠ too small to compare |
| TN3K | Qwen2.5-VL-3B | 22 (22) | 0.23 (0.20–0.24) | 0.18 (0.10–0.27) (Gemma) | 0.30 (0.18–0.41) | 23% | ⚠ too small to compare |
| TN3K | MedGemma-1.5-4B (4-bit) | 22 (22) | 0.25 (0.19–0.29) | 0.06 (0.00–0.12) (Qwen2.5-7B) | 0.26 (0.18–0.34) | 9% | ⚠ too small to compare |
| TN5000 | Qwen2.5-VL-3B | 16 (16) | 0.20 (0.17–0.23) | 0.22 (0.14–0.29) (Gemma) | 0.12 (0.06–0.20) | 0% | ⚠ too small to compare |
| TN5000 | MedGemma-1.5-4B (4-bit) | 16 (16) | 0.23 (0.16–0.30) | 0.06 (0.02–0.11) (Qwen2.5-7B) | 0.17 (0.09–0.25) | 6% | ⚠ too small to compare |
| HC18 | Qwen2.5-VL-3B | 14 (14) | 0.00 (0.00–0.00) | 0.80 (0.71–0.87) (Gemma) | 0.77 (0.69–0.83) | 93% | ⚠ too small to compare |
| HC18 | MedGemma-1.5-4B (4-bit) | 14 (14) | 0.00 (0.00–0.00) | 0.42 (0.30–0.55) (Qwen2.5-7B) | 0.64 (0.56–0.72) | 71% | ⚠ too small to compare |

Layer 0 scorers (BLEU, ROUGE-L, chrF, BERTScore, RaTEScore) on the two writers are in `step14_medgemma/results.md` (paired differences with group-bootstrap CIs): the gaps are tiny (BLEU 0.00–0.01, BERTScore 0.00–0.02) and the scorers do not agree on a ranking. Layer 3 with predicted masks was NOT run on VLM reports (their boxes were too poor to prompt MedSAM; Step 16 used true-mask boxes).

## C. HiSBreast: real (machine-translated) clinician conclusions, test split

Text is local only (blank licence). **Machine-translated subset: 101 of 427 breast exams passed three automatic translation checks (no bilingual human review).** Planted errors and harmless rewordings built on the validated English text; splits by exam id. Cells: AUROC (95% CI resampling exams). A column with n < 30 is **too small to compare**.

| scorer | n exams | all harmless | vs small | vs matched one-word synonym | vs LLM paraphrase | identical mean | lazy "no abnormality" |
|---|---|---|---|---|---|---|---|
| bleu | 41 | 0.64 (0.57–0.71) (n=41) | 0.76 (0.68–0.84) (n=41) | 0.82 (0.67–0.95) (n=16, too small to compare) | 0.04 (0.00–0.10) (n=21, too small to compare) | 1.0000 | 0.04 |
| rougeL | 41 | 0.76 (0.71–0.81) (n=41) | 0.84 (0.79–0.89) (n=41) | 0.89 (0.75–0.98) (n=16, too small to compare) | 0.24 (0.08–0.42) (n=21, too small to compare) | 1.0000 | 0.10 |
| chrf | 41 | 0.72 (0.67–0.78) (n=41) | 0.88 (0.83–0.93) (n=41) | 0.42 (0.29–0.54) (n=16, too small to compare) | 0.11 (0.03–0.21) (n=21, too small to compare) | 1.0000 | 0.09 |
| bertscore[roberta-large] | 41 | 0.43 (0.38–0.50) (n=41) | 0.47 (0.40–0.54) (n=41) | 0.86 (0.78–0.95) (n=16, too small to compare) | 0.08 (0.02–0.15) (n=21, too small to compare) | 1.0000 | 0.86 |
| ratescore | 41 | 0.66 (0.58–0.73) (n=41) | 0.69 (0.61–0.78) (n=41) | 0.61 (0.46–0.77) (n=16, too small to compare) | 0.50 (0.33–0.67) (n=21, too small to compare) | 1.0000 | 0.50 |
| finding_f1_his (parser written for this text: optimistic) | 41 | 0.94 (0.91–0.97) (n=41) | 0.95 (0.93–0.98) (n=41) | 0.89 (0.84–0.93) (n=16, too small to compare) | 0.87 (0.78–0.94) (n=21, too small to compare) | 1.0000 | 0.01 |
| sentence_f1 (Qwen2.5-7B judge, prompt v2q) | 41 | 0.79 (0.74–0.84) (n=41) | 0.79 (0.74–0.84) (n=41) | 0.81 (0.76–0.86) (n=16, too small to compare) | 0.81 (0.74–0.87) (n=21, too small to compare) | 1.0000 | — |
| judge_score (Qwen2.5-7B judge, prompt v2q) | 41 | 0.82 (0.77–0.88) (n=41) | 0.81 (0.75–0.87) (n=41) | 0.90 (0.85–0.95) (n=16, too small to compare) | 0.89 (0.82–0.94) (n=21, too small to compare) | 1.0000 | — |

Looser set (passed check 1 plus check 2 or 3; 118 test exams) and the dev/val numbers are in `step15_hisbreast/results.md`. Parser agreement between the Vietnamese original and the English translation: side 1.00, BI-RADS 1.00, finding type only 0.50 (unreliable).

## Not run

GREEN (7B model too large for 16 GB), Claude judge (no credit), Jev (paid API, not approved), original RadFact, LLaVA-Med reports, SAM/MedSAM boxes from VLM output, clinician-confirmed severity, bilingual review of HiSBreast translations.
