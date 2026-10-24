# Step 10d: headline results on the LOCKED TEST split

Limitations: [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md). Test-split access is logged in `results/partA/test_access.log`; frozen code (`freeze-v1`) was not edited: new files `step10d.py`, `step10d_analysis.py`, `judge2_test.py`.

**What was run.** The frozen benchmark builder was run on test-split cases only (150 cases per dataset where available): `bench_test_v2d.jsonl`, 25,887 rows on 1,399 cases (BrEaST 103, BUS-BRA 150, BUSI 150, UDIAT 66, BUS-UCLM 177, TN3K 150, TN5000 150, DDTI 150, HC18 150, FetalHead 153). Layers 0, 1, 2, 3 were then scored with the frozen settings. Confidence intervals resample **groups** (patient / exam / near-duplicate cluster), not cases, 1,000 resamples (Layer 3 tables use the case-level bootstrap of the frozen Step 8 code; marked below). Number of groups matters: BUS-UCLM's test rows come from only 9 patients (wide intervals), FetalHead 54, BUS-BRA 85, DDTI 114; BrEaST, TN3K, HC18 have one group per case (no patient id). **Judge sample sizes:** the brief asked for up to 50 cases per dataset; at about 6 seconds per pair that needs more than 3 hours per prompt, so **prompt_v2 (the main judge) ran on 25 cases per dataset (1,116 pairs, 109 minutes) and prompt_v1 on the first 12 of those cases (564 pairs, 88 minutes)**. These are small; read differences of a few hundredths as noise. Thresholds (for D/R, flag rates) are not part of this step (Step 8b, on val).

**Wiring gate on test.** Identical-copy mean = 1.0000 for every scorer on every dataset: BLEU, ROUGE-L, chrF, BERTScore, RaTEScore, `finding_f1`, and the Gemma judge with prompt_v2 (`sentence_f1` and `judge_score`, all 10 datasets, 0 unparseable replies). Exceptions, all known: (1) Layer 3 `box_support` (mask rule) is 0.95 on BrEaST and 0.99 on BUS-BRA, BUSI and HC18 because a tight box around an irregular lesion can have under 50% of its area inside the mask; the frozen replacement `box_support_gtbox` is 1.0000. `mask_verified_facts` on HC18 is 0.9993 (graded credit on a rounded number). (2) **Judge prompt_v1 again fails the gate: identical copies on UDIAT score 0.80** (the Step 7 failure replicates on test), which is why prompt_v2 is the main judge. Your stop rule lists "identical mean not 1.0 on the test split"; I treated these as known, documented cases, not new wiring bugs, and did not stop.

**Headline on test (AUROC of planted error vs harmless; 1.0 perfect, 0.5 chance).**
- **Layer 0 conclusions are unchanged.** BrEaST: BLEU 0.25 / 0.61 / 0.08 (vs harmless small / matched one-word synonym / large style swap), chrF 0.38 / 0.25 / 0.08, BERTScore 0.21 / 0.53 / 0.08, RaTEScore 0.45 / 0.64 / 0.13. BUS-BRA BLEU 0.21 / 0.75 / 0.09; HC18 BERTScore 0.00 on all three. Size errors stay unseen.
- **Layer 1 `finding_f1` = 1.00 on all datasets** (upper bound under templated text: the extractor reads our own wording).
- **Layer 2 (Gemma-2-9B, prompt_v2, 25 cases per dataset):** vs matched one-word synonym 0.88-1.00 (BrEaST 0.91, BUS-BRA 0.92, BUSI 0.92, UDIAT 0.94, DDTI 0.88, TN3K 0.99, TN5000 1.00, HC18 and FetalHead 1.00); vs harmless_small it is weak on breast and DDTI (BrEaST 0.60, UDIAT 0.58, BUS-BRA 0.69, BUSI 0.71, DDTI 0.71; BUS-UCLM 0.95, TN3K 0.99, TN5000 1.00); vs harmless_large 0.56-1.00 (HC18 0.56, DDTI 0.61, BrEaST 0.62). It lists at least one error for 100% of planted errors; the planted category is named in 84% (mean over categories, small n); 50 of 1,116 replies had a wrong-length true/false list.
- **Prompt_v1 vs prompt_v2 on test (12 cases per dataset, same pairs as the first 12 of the 25):** v1 scores higher against harmless_small on BUS-BRA (0.94 vs 0.69) and BUSI (0.94 vs 0.71) and UDIAT (0.77 vs 0.58), lower on BrEaST (0.50 vs 0.60): the prompt-sensitivity seen on dev replicates in direction on test; magnitudes differ because the case samples differ (12 vs 25 cases).
- **Layer 3 with true masks (case-level bootstrap):** unchanged from Step 8. Example `grounded_check` AUROC on test (box-only / text position / text position + box moved / size): BrEaST 1.00 / 0.19 / 1.00 / 0.18; BUS-BRA 1.00 / 0.64 / 1.00 / 0.50; TN5000 1.00 / 1.00 / 1.00 / 1.00; HC18 1.00 / — / — / 1.00. `mask_verified_facts` is 1.00 on text position and size errors on every dataset (circular, see limitations).

**What changed vs the dev-era numbers (the three biggest differences).**
1. **Layers 0, 1, 3 did not move.** Mean absolute AUROC shift test vs the dev-era tables (Step 5 rerun3, Step 6) is 0.005 (largest 0.03, BUS-UCLM, 9 test patients). These scorers were not tuned; their behaviour is set by the template and edit-size mechanism, so a locked split changes almost nothing.
2. **The judge moved most, and the sample is small.** Mean absolute shift 0.04 over the three AUROC types and two judge scorers, but up to 0.26: BrEaST `sentence_f1` vs harmless_small 0.86 (dev, 20 cases) -> 0.60 (test, 25 cases); DDTI `judge_score` vs large 0.95 -> 0.78; BUS-BRA `judge_score` vs small 0.60 -> 0.76. So the dev-era headline "judge vs small 0.86 on BrEaST" was optimistic; on test it is 0.60. The qualitative picture holds: the judge separates errors from a one-word synonym (0.88-1.00) but is unreliable against heavier harmless rewordings on breast and DDTI.
3. **Prompt_v2 stays the main judge** because it passes the identical-copy gate on test (prompt_v1 fails it on UDIAT again), but its harmless_small mean score is 0.79-1.00 (UDIAT 0.79, BrEaST 0.87, BUSI 0.85): it still marks some harmless rewritings as differences.

The dev-era tables are kept in their original folders (`step5_harmless_split_layer0_rerun3`, `step6_layer1_finding_f1`, `step7_layer2_sentence_check_gemma_rerun2`, `step8_layer3_location_true_masks`), labelled there as dev-era (they sample all splits and the judge prompts were chosen on them): "dev, tuned". Do not mix them with the test tables below.

**Caveats.** Templated reports (synthetic but fact-correct); provisional severity; template sources "to confirm"; per dataset only; judge samples of 25 and 12 cases per dataset; one judge model; groups: five datasets have no patient id (image-level groups), so patient overlap between splits is possible; BUS-UCLM test = 9 patients.

---

## Test tables: Layers 0 and 1 (1,399 cases, group bootstrap)

### BrEaST (103 cases, 103 groups)

| scorer | AUROC vs small (95% CI, group bootstrap) | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy | severity ρ |
|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.25 (0.24–0.27) | 0.61 (0.60–0.62) | 0.08 (0.06–0.11) | 0.38 | 0.85 | 0.38 | 1.0000 | 0.00 | -0.12 |
| rougeL | 0.10 (0.08–0.13) | 0.58 (0.57–0.60) | 0.08 (0.06–0.11) | 0.38 | 0.80 | 0.59 | 1.0000 | 0.04 | -0.21 |
| chrf | 0.38 (0.36–0.40) | 0.25 (0.22–0.27) | 0.08 (0.06–0.11) | 0.62 | 0.92 | 0.73 | 1.0000 | 0.02 | -0.31 |
| bertscore[roberta-large] | 0.21 (0.19–0.23) | 0.53 (0.52–0.54) | 0.08 (0.06–0.11) | 0.47 | 0.98 | 0.95 | 1.0000 | 0.84 | -0.34 |
| ratescore | 0.45 (0.43–0.47) | 0.64 (0.63–0.66) | 0.13 (0.11–0.16) | 0.66 | 0.92 | 0.82 | 1.0000 | 0.50 | -0.36 |
| finding_f1 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 | 1.00 | 1.00 | 1.0000 | 0.01 | -0.30 |

### BUS-BRA (150 cases, 85 groups)

| scorer | AUROC vs small (95% CI, group bootstrap) | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy | severity ρ |
|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.21 (0.20–0.22) | 0.75 (0.74–0.76) | 0.09 (0.09–0.10) | 0.29 | 0.82 | 0.54 | 1.0000 | 0.00 | -0.05 |
| rougeL | 0.09 (0.09–0.10) | 0.66 (0.66–0.67) | 0.09 (0.09–0.10) | 0.29 | 0.78 | 0.69 | 1.0000 | 0.00 | -0.02 |
| chrf | 0.30 (0.29–0.31) | 0.36 (0.35–0.38) | 0.09 (0.09–0.10) | 0.50 | 0.88 | 0.74 | 1.0000 | 0.02 | -0.27 |
| bertscore[roberta-large] | 0.09 (0.09–0.10) | 0.42 (0.41–0.43) | 0.09 (0.09–0.10) | 0.29 | 0.97 | 0.95 | 1.0000 | 0.84 | -0.25 |
| ratescore | 0.52 (0.51–0.53) | 0.66 (0.65–0.67) | 0.20 (0.18–0.22) | 0.60 | 0.92 | 0.87 | 1.0000 | 0.50 | -0.15 |
| finding_f1 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 | 1.00 | 1.00 | 1.0000 | 0.00 | -0.30 |

### BUSI (150 cases, 133 groups)

| scorer | AUROC vs small (95% CI, group bootstrap) | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy | severity ρ |
|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.64 (0.61–0.67) | 0.82 (0.81–0.83) | 0.28 (0.22–0.33) | 0.79 | 0.80 | 0.48 | 1.0000 | 0.01 | -0.09 |
| rougeL | 0.30 (0.25–0.36) | 0.75 (0.73–0.77) | 0.28 (0.22–0.33) | 0.58 | 0.85 | 0.65 | 1.0000 | 0.04 | -0.23 |
| chrf | 0.64 (0.61–0.67) | 0.55 (0.51–0.58) | 0.28 (0.22–0.33) | 0.79 | 0.88 | 0.71 | 1.0000 | 0.05 | -0.37 |
| bertscore[roberta-large] | 0.28 (0.22–0.33) | 0.52 (0.48–0.56) | 0.28 (0.22–0.33) | 0.58 | 0.97 | 0.95 | 1.0000 | 0.86 | -0.51 |
| ratescore | 0.61 (0.58–0.64) | 0.68 (0.65–0.71) | 0.60 (0.57–0.63) | 0.79 | 0.91 | 0.86 | 1.0000 | 0.50 | -0.81 |
| finding_f1 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 | 1.00 | 1.00 | 1.0000 | 0.11 | -0.51 |

### UDIAT (66 cases, 64 groups)

| scorer | AUROC vs small (95% CI, group bootstrap) | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy | severity ρ |
|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.50 (0.50–0.50) | 0.78 (0.78–0.78) | 0.11 (0.11–0.12) | 0.75 | 0.83 | 0.52 | 1.0000 | 0.00 | -0.17 |
| rougeL | 0.11 (0.11–0.12) | 0.67 (0.67–0.67) | 0.11 (0.11–0.12) | 0.50 | 0.84 | 0.65 | 1.0000 | 0.00 | -0.15 |
| chrf | 0.50 (0.49–0.51) | 0.44 (0.44–0.44) | 0.11 (0.11–0.12) | 0.75 | 0.89 | 0.74 | 1.0000 | 0.03 | -0.31 |
| bertscore[roberta-large] | 0.11 (0.11–0.12) | 0.52 (0.50–0.53) | 0.11 (0.11–0.12) | 0.50 | 0.97 | 0.95 | 1.0000 | 0.85 | -0.55 |
| ratescore | 0.53 (0.52–0.54) | 0.63 (0.60–0.66) | 0.51 (0.50–0.52) | 0.75 | 0.91 | 0.86 | 1.0000 | 0.50 | -0.72 |
| finding_f1 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 | 1.00 | 1.00 | 1.0000 | 0.00 | -0.47 |

### BUS-UCLM (177 cases, 9 groups)

| scorer | AUROC vs small (95% CI, group bootstrap) | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy | severity ρ |
|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.85 (0.81–0.90) | 0.92 (0.90–0.95) | 0.71 (0.62–0.80) | 0.90 | 0.76 | 0.42 | 1.0000 | 0.02 | -0.40 |
| rougeL | 0.72 (0.63–0.80) | 0.89 (0.87–0.93) | 0.71 (0.62–0.80) | 0.83 | 0.81 | 0.66 | 1.0000 | 0.15 | -0.51 |
| chrf | 0.85 (0.81–0.90) | 0.82 (0.77–0.87) | 0.71 (0.62–0.80) | 0.92 | 0.87 | 0.68 | 1.0000 | 0.11 | -0.62 |
| bertscore[roberta-large] | 0.71 (0.62–0.80) | 0.81 (0.76–0.87) | 0.71 (0.62–0.80) | 0.83 | 0.97 | 0.95 | 1.0000 | 0.88 | -0.68 |
| ratescore | 0.83 (0.78–0.88) | 0.86 (0.82–0.91) | 0.83 (0.78–0.88) | 0.90 | 0.96 | 0.86 | 1.0000 | 0.50 | -0.85 |
| finding_f1 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 | 1.00 | 1.00 | 1.0000 | 0.44 | -0.71 |

### TN3K (150 cases, 150 groups)

| scorer | AUROC vs small (95% CI, group bootstrap) | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy | severity ρ |
|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.58 (0.58–0.58) | 0.82 (0.81–0.82) | 0.16 (0.15–0.16) | 1.00 | 0.80 | 0.44 | 1.0000 | 0.00 | -0.35 |
| rougeL | 0.16 (0.15–0.16) | 0.73 (0.72–0.73) | 0.16 (0.15–0.16) | 1.00 | 0.84 | 0.63 | 1.0000 | 0.00 | -0.48 |
| chrf | 0.58 (0.58–0.58) | 0.45 (0.44–0.46) | 0.16 (0.15–0.16) | 1.00 | 0.86 | 0.70 | 1.0000 | 0.03 | -0.27 |
| bertscore[roberta-large] | 0.16 (0.15–0.16) | 0.59 (0.57–0.60) | 0.16 (0.15–0.16) | 1.00 | 0.97 | 0.94 | 1.0000 | 0.86 | -0.37 |
| ratescore | 0.56 (0.55–0.57) | 0.55 (0.53–0.56) | 0.33 (0.31–0.34) | 1.00 | 0.88 | 0.74 | 1.0000 | 0.50 | -0.32 |
| finding_f1 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 | 1.00 | 1.00 | 1.0000 | 0.00 | -0.54 |

### TN5000 (150 cases, 149 groups)

| scorer | AUROC vs small (95% CI, group bootstrap) | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy | severity ρ |
|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.58 (0.58–0.58) | 0.82 (0.82–0.82) | 0.16 (0.15–0.16) | 1.00 | 0.80 | 0.44 | 1.0000 | 0.00 | -0.36 |
| rougeL | 0.16 (0.15–0.16) | 0.73 (0.73–0.74) | 0.16 (0.15–0.16) | 1.00 | 0.84 | 0.63 | 1.0000 | 0.00 | -0.50 |
| chrf | 0.58 (0.58–0.58) | 0.47 (0.46–0.47) | 0.16 (0.15–0.16) | 1.00 | 0.86 | 0.71 | 1.0000 | 0.03 | -0.28 |
| bertscore[roberta-large] | 0.16 (0.15–0.16) | 0.56 (0.54–0.57) | 0.16 (0.15–0.16) | 1.00 | 0.97 | 0.94 | 1.0000 | 0.86 | -0.33 |
| ratescore | 0.58 (0.57–0.59) | 0.56 (0.55–0.58) | 0.35 (0.34–0.36) | 1.00 | 0.88 | 0.76 | 1.0000 | 0.50 | -0.35 |
| finding_f1 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 | 1.00 | 1.00 | 1.0000 | 0.00 | -0.59 |

### DDTI (150 cases, 114 groups)

| scorer | AUROC vs small (95% CI, group bootstrap) | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy | severity ρ |
|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.45 (0.43–0.46) | 0.66 (0.65–0.68) | 0.10 (0.09–0.10) | 0.70 | 0.81 | 0.44 | 1.0000 | 0.00 | -0.30 |
| rougeL | 0.11 (0.10–0.13) | 0.66 (0.65–0.67) | 0.11 (0.10–0.13) | 0.71 | 0.73 | 0.61 | 1.0000 | 0.02 | -0.31 |
| chrf | 0.44 (0.42–0.46) | 0.36 (0.34–0.37) | 0.10 (0.09–0.11) | 0.70 | 0.87 | 0.69 | 1.0000 | 0.02 | -0.34 |
| bertscore[roberta-large] | 0.13 (0.11–0.15) | 0.52 (0.50–0.54) | 0.10 (0.09–0.11) | 0.71 | 0.97 | 0.95 | 1.0000 | 0.84 | -0.60 |
| ratescore | 0.48 (0.46–0.50) | 0.55 (0.53–0.57) | 0.24 (0.21–0.26) | 0.75 | 0.87 | 0.76 | 1.0000 | 0.50 | -0.39 |
| finding_f1 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 | 1.00 | 1.00 | 1.0000 | 0.01 | -0.26 |

### HC18 (150 cases, 150 groups)

| scorer | AUROC vs small (95% CI, group bootstrap) | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy | severity ρ |
|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.33 (0.33–0.33) | 0.50 (0.50–0.50) | 0.00 (0.00–0.00) | 0.33 | 0.58 | 0.20 | 1.0000 | 0.05 | — |
| rougeL | 0.17 (0.17–0.17) | 0.50 (0.50–0.50) | 0.00 (0.00–0.00) | 0.17 | 0.72 | 0.68 | 1.0000 | 0.00 | — |
| chrf | 0.34 (0.33–0.34) | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | 0.33 | 0.85 | 0.45 | 1.0000 | 0.05 | -0.15 |
| bertscore[roberta-large] | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | 0.00 | 0.97 | 0.94 | 1.0000 | 0.87 | -0.36 |
| ratescore | 0.42 (0.40–0.44) | 0.10 (0.07–0.13) | 0.04 (0.02–0.05) | 0.50 | 0.89 | 0.61 | 1.0000 | 0.50 | -0.34 |
| finding_f1 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 | 1.00 | 1.00 | 1.0000 | 0.00 | -0.99 |

### FetalHead (153 cases, 54 groups)

| scorer | AUROC vs small (95% CI, group bootstrap) | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy | severity ρ |
|---|---|---|---|---|---|---|---|---|---|
| bleu | 0.37 (0.37–0.37) | 0.56 (0.55–0.57) | 0.01 (0.00–0.02) | 0.33 | 0.79 | 0.35 | 1.0000 | 0.01 | 0.00 |
| rougeL | 0.17 (0.17–0.17) | 0.50 (0.50–0.50) | 0.01 (0.00–0.02) | 0.17 | 0.72 | 0.79 | 1.0000 | 0.00 | 0.00 |
| chrf | 0.55 (0.53–0.56) | 0.22 (0.20–0.24) | 0.07 (0.05–0.09) | 0.52 | 0.93 | 0.70 | 1.0000 | 0.04 | -0.36 |
| bertscore[roberta-large] | 0.13 (0.13–0.13) | 0.22 (0.20–0.24) | 0.11 (0.10–0.12) | 0.00 | 0.97 | 0.95 | 1.0000 | 0.84 | -0.27 |
| ratescore | 0.49 (0.47–0.50) | 0.39 (0.37–0.42) | 0.11 (0.09–0.14) | 0.48 | 0.92 | 0.63 | 1.0000 | 0.50 | -0.10 |
| finding_f1 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 | 1.00 | 1.00 | 1.0000 | 0.00 | -0.82 |


## Test tables: Layer 2 judge, prompt_v2 (main; 25 cases per dataset, group bootstrap)

### BrEaST (25 cases, 25 groups)

| scorer | AUROC vs small (95% CI, group bootstrap) | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy | severity ρ |
|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 0.60 (0.46–0.74) | 0.91 (0.87–0.95) | 0.62 (0.48–0.76) | 0.77 | 0.87 | 0.84 | 1.0000 | — | -0.22 |
| sentence_precision | 0.62 (0.49–0.75) | 0.91 (0.87–0.95) | 0.53 (0.39–0.67) | 0.77 | 0.87 | 0.78 | 1.0000 | — | -0.17 |
| sentence_recall | 0.56 (0.44–0.69) | 0.78 (0.71–0.85) | 0.65 (0.54–0.75) | 0.77 | 0.87 | 0.93 | 1.0000 | — | -0.26 |
| judge_score | 0.81 (0.67–0.94) | 1.00 (1.00–1.00) | 0.44 (0.30–0.60) | 0.64 | 0.76 | 0.34 | 1.0000 | — | 0.05 |

### BUS-BRA (25 cases, 23 groups)

| scorer | AUROC vs small (95% CI, group bootstrap) | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy | severity ρ |
|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 0.69 (0.54–0.83) | 0.92 (0.87–0.96) | 0.92 (0.87–0.96) | 0.73 | 0.89 | 1.00 | 1.0000 | — | -0.44 |
| sentence_precision | 0.70 (0.54–0.83) | 0.92 (0.87–0.96) | 0.92 (0.87–0.96) | 0.73 | 0.87 | 1.00 | 1.0000 | — | -0.25 |
| sentence_recall | 0.59 (0.48–0.68) | 0.75 (0.68–0.81) | 0.75 (0.68–0.81) | 0.81 | 0.91 | 1.00 | 1.0000 | — | -0.57 |
| judge_score | 0.76 (0.58–0.92) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.77 | 0.70 | 1.00 | 1.0000 | — | -0.49 |

### BUSI (25 cases, 24 groups)

| scorer | AUROC vs small (95% CI, group bootstrap) | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy | severity ρ |
|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 0.71 (0.56–0.84) | 0.92 (0.87–0.96) | 0.89 (0.79–0.95) | 0.96 | 0.85 | 0.96 | 1.0000 | — | -0.41 |
| sentence_precision | 0.74 (0.62–0.85) | 0.92 (0.87–0.96) | 0.89 (0.79–0.95) | 0.92 | 0.83 | 0.96 | 1.0000 | — | -0.37 |
| sentence_recall | 0.61 (0.50–0.72) | 0.73 (0.66–0.80) | 0.71 (0.63–0.78) | 0.96 | 0.89 | 0.99 | 1.0000 | — | -0.61 |
| judge_score | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.96 (0.88–1.00) | 1.00 | 0.98 | 0.96 | 1.0000 | — | -0.49 |

### UDIAT (25 cases, 24 groups)

| scorer | AUROC vs small (95% CI, group bootstrap) | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy | severity ρ |
|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 0.58 (0.44–0.73) | 0.94 (0.89–0.98) | 0.85 (0.78–0.92) | 0.82 | 0.79 | 0.92 | 1.0000 | — | -0.41 |
| sentence_precision | 0.56 (0.45–0.69) | 0.90 (0.85–0.95) | 0.88 (0.82–0.94) | 0.75 | 0.79 | 0.97 | 1.0000 | — | -0.26 |
| sentence_recall | 0.57 (0.45–0.70) | 0.84 (0.78–0.90) | 0.72 (0.63–0.80) | 0.82 | 0.79 | 0.89 | 1.0000 | — | -0.49 |
| judge_score | 0.64 (0.48–0.80) | 1.00 (1.00–1.00) | 0.90 (0.81–0.97) | 0.64 | 0.52 | 0.81 | 1.0000 | — | -0.33 |

### BUS-UCLM (25 cases, 9 groups)

| scorer | AUROC vs small (95% CI, group bootstrap) | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy | severity ρ |
|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 0.95 (0.89–1.00) | 0.99 (0.97–1.00) | 0.99 (0.97–1.00) | 0.99 | 0.93 | 1.00 | 1.0000 | — | -0.82 |
| sentence_precision | 0.93 (0.85–0.99) | 0.99 (0.97–1.00) | 0.99 (0.97–1.00) | 0.95 | 0.92 | 1.00 | 1.0000 | — | -0.80 |
| sentence_recall | 0.92 (0.87–0.98) | 0.95 (0.91–0.99) | 0.95 (0.91–0.99) | 0.99 | 0.96 | 1.00 | 1.0000 | — | -0.82 |
| judge_score | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 | 0.99 | 1.00 | 1.0000 | — | 0.09 |

### TN3K (25 cases, 25 groups)

| scorer | AUROC vs small (95% CI, group bootstrap) | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy | severity ρ |
|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 0.99 (0.97–1.00) | 0.99 (0.97–1.00) | 0.93 (0.89–0.97) | 1.00 | 1.00 | 0.88 | 1.0000 | — | -0.34 |
| sentence_precision | 0.99 (0.97–1.00) | 0.99 (0.97–1.00) | 0.99 (0.97–1.00) | 1.00 | 1.00 | 0.88 | 1.0000 | — | -0.62 |
| sentence_recall | 0.80 (0.76–0.84) | 0.80 (0.76–0.84) | 0.74 (0.68–0.80) | 1.00 | 1.00 | 0.88 | 1.0000 | — | -0.35 |
| judge_score | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 | 1.00 | 0.93 | 1.0000 | — | -0.62 |

### TN5000 (25 cases, 25 groups)

| scorer | AUROC vs small (95% CI, group bootstrap) | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy | severity ρ |
|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.86 (0.82–0.91) | 1.00 | 1.00 | 0.79 | 1.0000 | — | -0.47 |
| sentence_precision | 0.99 (0.97–1.00) | 0.99 (0.97–1.00) | 0.99 (0.97–1.00) | 1.00 | 1.00 | 0.79 | 1.0000 | — | -0.69 |
| sentence_recall | 0.82 (0.78–0.86) | 0.82 (0.78–0.86) | 0.68 (0.60–0.76) | 1.00 | 1.00 | 0.79 | 1.0000 | — | -0.49 |
| judge_score | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 | 1.00 | 0.87 | 1.0000 | — | -0.65 |

### DDTI (25 cases, 23 groups)

| scorer | AUROC vs small (95% CI, group bootstrap) | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy | severity ρ |
|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 0.71 (0.58–0.82) | 0.88 (0.83–0.93) | 0.61 (0.47–0.75) | 0.89 | 0.88 | 0.69 | 1.0000 | — | -0.37 |
| sentence_precision | 0.72 (0.59–0.82) | 0.88 (0.83–0.93) | 0.58 (0.40–0.74) | 0.89 | 0.88 | 0.66 | 1.0000 | — | -0.29 |
| sentence_recall | 0.63 (0.52–0.72) | 0.80 (0.75–0.85) | 0.77 (0.71–0.83) | 0.89 | 0.88 | 0.96 | 1.0000 | — | -0.42 |
| judge_score | 0.88 (0.74–1.00) | 1.00 (1.00–1.00) | 0.78 (0.64–0.92) | 1.00 | 0.89 | 0.75 | 1.0000 | — | -0.24 |

### HC18 (25 cases, 25 groups)

| scorer | AUROC vs small (95% CI, group bootstrap) | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy | severity ρ |
|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 0.86 (0.78–0.94) | 1.00 (1.00–1.00) | 0.56 (0.36–0.76) | 0.92 | 0.91 | 0.56 | 1.0000 | — | -0.29 |
| sentence_precision | 0.86 (0.78–0.94) | 1.00 (1.00–1.00) | 0.56 (0.36–0.76) | 0.92 | 0.86 | 0.56 | 1.0000 | — | — |
| sentence_recall | 0.52 (0.50–0.56) | 0.52 (0.50–0.56) | 0.28 (0.18–0.38) | 0.58 | 1.00 | 0.56 | 1.0000 | — | -0.29 |
| judge_score | 0.92 (0.84–0.98) | 1.00 (1.00–1.00) | 0.56 (0.36–0.76) | 1.00 | 0.92 | 0.56 | 1.0000 | — | -0.76 |

### FetalHead (25 cases, 19 groups)

| scorer | AUROC vs small (95% CI, group bootstrap) | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy | severity ρ |
|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 0.92 (0.87–0.96) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.67 | 0.89 | 1.00 | 1.0000 | — | -0.11 |
| sentence_precision | 0.83 (0.74–0.92) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.67 | 0.83 | 1.00 | 1.0000 | — | -0.02 |
| sentence_recall | 0.75 (0.75–0.75) | 0.76 (0.75–0.79) | 0.76 (0.75–0.79) | 0.50 | 1.00 | 1.00 | 1.0000 | — | -0.11 |
| judge_score | 0.81 (0.70–0.91) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 | 0.90 | 1.00 | 1.0000 | — | -0.09 |


## Test tables: Layer 2 judge, prompt_v1 (first 12 of those cases per dataset)

### BrEaST (12 cases, 12 groups)

| scorer | AUROC vs small (95% CI, group bootstrap) | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy | severity ρ |
|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 0.50 (0.29–0.71) | 0.98 (0.94–1.00) | 0.96 (0.88–1.00) | 0.60 | 0.85 | 0.99 | 1.0000 | — | -0.11 |
| sentence_precision | 0.56 (0.38–0.75) | 0.96 (0.90–1.00) | 0.92 (0.79–1.00) | 0.70 | 0.85 | 0.98 | 1.0000 | — | -0.15 |
| sentence_recall | 0.52 (0.35–0.71) | 0.79 (0.71–0.88) | 0.79 (0.71–0.88) | 0.60 | 0.85 | 1.00 | 1.0000 | — | -0.15 |
| judge_score | 0.50 (0.29–0.71) | 0.88 (0.81–0.94) | 0.88 (0.81–0.94) | 0.60 | 0.57 | 1.00 | 1.0000 | — | -0.16 |

### BUS-BRA (12 cases, 12 groups)

| scorer | AUROC vs small (95% CI, group bootstrap) | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy | severity ρ |
|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 0.94 (0.85–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.93 | 0.97 | 1.00 | 1.0000 | — | -0.69 |
| sentence_precision | 0.94 (0.83–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.93 | 0.96 | 1.00 | 1.0000 | — | -0.43 |
| sentence_recall | 0.75 (0.65–0.85) | 0.77 (0.69–0.85) | 0.77 (0.69–0.85) | 0.93 | 0.98 | 1.00 | 1.0000 | — | -0.66 |
| judge_score | 0.94 (0.81–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.93 | 0.92 | 1.00 | 1.0000 | — | -0.79 |

### BUSI (12 cases, 12 groups)

| scorer | AUROC vs small (95% CI, group bootstrap) | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy | severity ρ |
|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 0.94 (0.81–1.00) | 1.00 (1.00–1.00) | 0.94 (0.81–1.00) | 1.00 | 0.97 | 0.97 | 1.0000 | — | -0.65 |
| sentence_precision | 0.94 (0.81–1.00) | 0.98 (0.94–1.00) | 0.92 (0.75–1.00) | 1.00 | 0.97 | 0.96 | 1.0000 | — | -0.61 |
| sentence_recall | 0.81 (0.71–0.92) | 0.85 (0.77–0.94) | 0.85 (0.77–0.94) | 1.00 | 0.97 | 1.00 | 1.0000 | — | -0.76 |
| judge_score | 0.92 (0.85–0.98) | 0.92 (0.85–0.98) | 0.92 (0.85–0.98) | 1.00 | 0.99 | 1.00 | 1.0000 | — | -0.52 |

### UDIAT (12 cases, 12 groups)

| scorer | AUROC vs small (95% CI, group bootstrap) | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy | severity ρ |
|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 0.77 (0.62–0.90) | 1.00 (1.00–1.00) | 0.96 (0.88–1.00) | 0.83 | 0.81 | 0.94 | 0.8000 | — | -0.39 |
| sentence_precision | 0.67 (0.52–0.81) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.75 | 0.78 | 0.98 | 1.0000 | — | -0.35 |
| sentence_recall | 0.73 (0.60–0.83) | 0.90 (0.81–0.96) | 0.81 (0.71–0.90) | 0.83 | 0.86 | 0.92 | 0.6667 | — | -0.42 |
| judge_score | 0.81 (0.67–0.94) | 1.00 (1.00–1.00) | 0.98 (0.94–1.00) | 1.00 | 0.82 | 0.95 | 1.0000 | — | -0.50 |

### BUS-UCLM (12 cases, 6 groups)

| scorer | AUROC vs small (95% CI, group bootstrap) | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy | severity ρ |
|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 | 1.00 | 1.00 | 1.0000 | — | -0.83 |
| sentence_precision | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 | 1.00 | 1.00 | 1.0000 | — | -0.83 |
| sentence_recall | 0.96 (0.93–1.00) | 0.96 (0.93–1.00) | 0.96 (0.93–1.00) | 1.00 | 1.00 | 1.00 | 1.0000 | — | -0.83 |
| judge_score | 0.96 (0.93–1.00) | 0.96 (0.93–1.00) | 0.96 (0.93–1.00) | 1.00 | 1.00 | 1.00 | 1.0000 | — | -0.72 |

### TN3K (12 cases, 12 groups)

| scorer | AUROC vs small (95% CI, group bootstrap) | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy | severity ρ |
|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 | 1.00 | 0.82 | 1.0000 | — | -0.39 |
| sentence_precision | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 | 1.00 | 0.86 | 1.0000 | — | -0.39 |
| sentence_recall | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.79 (0.67–0.92) | 1.00 | 1.00 | 0.79 | 1.0000 | — | -0.39 |
| judge_score | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.98 (0.94–1.00) | 1.00 | 1.00 | 0.83 | 1.0000 | — | -0.37 |

### TN5000 (12 cases, 12 groups)

| scorer | AUROC vs small (95% CI, group bootstrap) | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy | severity ρ |
|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 | 1.00 | 0.82 | 1.0000 | — | -0.76 |
| sentence_precision | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 | 1.00 | 0.86 | 1.0000 | — | -0.76 |
| sentence_recall | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.83 (0.71–0.96) | 1.00 | 1.00 | 0.79 | 1.0000 | — | -0.76 |
| judge_score | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.92 (0.79–1.00) | 1.00 | 1.00 | 0.84 | 1.0000 | — | -0.70 |

### DDTI (12 cases, 12 groups)

| scorer | AUROC vs small (95% CI, group bootstrap) | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy | severity ρ |
|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 0.77 (0.60–0.92) | 1.00 (1.00–1.00) | 0.67 (0.44–0.90) | 0.75 | 0.86 | 0.67 | 1.0000 | — | -0.02 |
| sentence_precision | 0.79 (0.67–0.92) | 1.00 (1.00–1.00) | 0.58 (0.33–0.83) | 0.75 | 0.86 | 0.63 | 1.0000 | — | 0.12 |
| sentence_recall | 0.73 (0.58–0.88) | 0.94 (0.88–1.00) | 0.88 (0.79–0.96) | 0.75 | 0.86 | 0.92 | 1.0000 | — | -0.02 |
| judge_score | 0.92 (0.79–1.00) | 1.00 (1.00–1.00) | 0.81 (0.58–1.00) | 0.88 | 0.85 | 0.78 | 1.0000 | — | -0.51 |

### HC18 (12 cases, 12 groups)

| scorer | AUROC vs small (95% CI, group bootstrap) | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy | severity ρ |
|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.96 (0.88–1.00) | 1.00 | 0.89 | 0.81 | 1.0000 | — | 0.55 |
| sentence_precision | 0.83 (0.71–0.96) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 | 0.83 | 1.00 | 1.0000 | — | — |
| sentence_recall | 0.92 (0.79–1.00) | 0.92 (0.79–1.00) | 0.62 (0.46–0.79) | 0.75 | 1.00 | 0.71 | 1.0000 | — | 0.55 |
| judge_score | 0.96 (0.88–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 | 0.90 | 1.00 | 1.0000 | — | -0.55 |

### FetalHead (12 cases, 10 groups)

| scorer | AUROC vs small (95% CI, group bootstrap) | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy | severity ρ |
|---|---|---|---|---|---|---|---|---|---|
| sentence_f1 | 0.94 (0.89–1.00) | 1.00 (1.00–1.00) | 0.96 (0.89–1.00) | 1.00 | 0.92 | 0.92 | 1.0000 | — | -0.07 |
| sentence_precision | 0.88 (0.79–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 | 0.88 | 1.00 | 1.0000 | — | — |
| sentence_recall | 0.81 (0.75–0.88) | 0.81 (0.75–0.88) | 0.69 (0.55–0.82) | 0.50 | 1.00 | 0.88 | 1.0000 | — | -0.07 |
| judge_score | 0.83 (0.70–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 | 0.92 | 1.00 | 1.0000 | — | -0.03 |


## Test tables: Layer 3 with true masks (own location benchmark , case-level bootstrap)

### BrEaST (100 cases)

| scorer | AUROC (95% CI) | box-only | text position (box right) | text position + box moved | size | harmless mean | identical mean | severity ρ |
|---|---|---|---|---|---|---|---|---|
| bleu | 0.39 (0.39–0.39) | 0.25 | 0.50 | 0.50 | 0.50 | 0.84 | 1.0000 | 0.30 |
| bertscore[roberta-large] | 0.39 (0.39–0.39) | 0.25 | 0.50 | 0.50 | 0.50 | 0.99 | 1.0000 | 0.35 |
| oracle_label_check | 0.78 (0.78–0.79) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.30 |
| mask_verified_facts | 0.78 (0.78–0.79) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.31 |
| semacc | 0.78 (0.78–0.79) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.32 |
| location_check | 0.50 (0.50–0.50) | 1.00 | 0.00 | 1.00 | 0.00 | 0.89 | 1.0000 | -0.31 |
| grounded_check | 0.59 (0.56–0.62) | 1.00 | 0.19 | 1.00 | 0.18 | 0.89 | 1.0000 | -0.30 |
| box_support | 0.70 (0.69–0.71) | 0.89 | 0.50 | 0.97 | 0.50 | 0.94 | 0.9500 | -0.29 |
| box_support_gtbox | 0.67 (0.67–0.68) | 0.82 | 0.50 | 1.00 | 0.50 | 1.00 | 1.0000 | -0.46 |

### BUS-BRA (100 cases)

| scorer | AUROC (95% CI) | box-only | text position (box right) | text position + box moved | size | harmless mean | identical mean | severity ρ |
|---|---|---|---|---|---|---|---|---|
| bleu | 0.39 (0.39–0.39) | 0.25 | 0.50 | 0.50 | 0.50 | 0.86 | 1.0000 | 0.28 |
| bertscore[roberta-large] | 0.39 (0.39–0.39) | 0.25 | 0.50 | 0.50 | 0.50 | 0.99 | 1.0000 | 0.26 |
| oracle_label_check | 0.78 (0.77–0.78) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.29 |
| mask_verified_facts | 0.78 (0.77–0.78) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.29 |
| semacc | 0.76 (0.75–0.77) | 0.50 | 1.00 | 1.00 | 0.97 | 1.00 | 1.0000 | 0.29 |
| location_check | 0.50 (0.50–0.50) | 1.00 | 0.00 | 1.00 | 0.00 | 0.90 | 1.0000 | -0.33 |
| grounded_check | 0.75 (0.72–0.79) | 1.00 | 0.64 | 1.00 | 0.50 | 0.90 | 1.0000 | -0.32 |
| box_support | 0.69 (0.69–0.70) | 0.88 | 0.50 | 1.00 | 0.50 | 0.98 | 0.9900 | -0.36 |
| box_support_gtbox | 0.66 (0.65–0.67) | 0.80 | 0.50 | 1.00 | 0.50 | 1.00 | 1.0000 | -0.47 |

### BUSI (100 cases)

| scorer | AUROC (95% CI) | box-only | text position (box right) | text position + box moved | size | harmless mean | identical mean | severity ρ |
|---|---|---|---|---|---|---|---|---|
| bleu | 0.40 (0.39–0.40) | 0.25 | 0.50 | 0.50 | 0.50 | 0.85 | 1.0000 | 0.34 |
| bertscore[roberta-large] | 0.40 (0.39–0.40) | 0.25 | 0.50 | 0.50 | 0.50 | 0.99 | 1.0000 | 0.25 |
| oracle_label_check | 0.79 (0.79–0.80) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.34 |
| mask_verified_facts | 0.79 (0.79–0.80) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.34 |
| semacc | 0.79 (0.78–0.80) | 0.50 | 1.00 | 1.00 | 0.99 | 1.00 | 1.0000 | 0.34 |
| location_check | 0.50 (0.50–0.50) | 1.00 | 0.00 | 1.00 | 0.00 | 0.90 | 1.0000 | -0.26 |
| grounded_check | 0.98 (0.96–0.99) | 1.00 | 1.00 | 1.00 | 0.96 | 0.90 | 1.0000 | -0.26 |
| box_support | 0.70 (0.69–0.70) | 0.87 | 0.50 | 0.99 | 0.50 | 0.99 | 0.9900 | -0.34 |
| box_support_gtbox | 0.67 (0.67–0.68) | 0.82 | 0.50 | 1.00 | 0.50 | 1.00 | 1.0000 | -0.41 |

### UDIAT (66 cases)

| scorer | AUROC (95% CI) | box-only | text position (box right) | text position + box moved | size | harmless mean | identical mean | severity ρ |
|---|---|---|---|---|---|---|---|---|
| bleu | 0.40 (0.40–0.40) | 0.25 | 0.50 | 0.50 | 0.50 | 0.86 | 1.0000 | 0.35 |
| bertscore[roberta-large] | 0.40 (0.40–0.40) | 0.25 | 0.50 | 0.50 | 0.50 | 0.99 | 1.0000 | 0.31 |
| oracle_label_check | 0.80 (0.79–0.81) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.35 |
| mask_verified_facts | 0.80 (0.79–0.81) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.35 |
| semacc | 0.80 (0.79–0.80) | 0.50 | 1.00 | 1.00 | 0.99 | 1.00 | 1.0000 | 0.35 |
| location_check | 0.50 (0.50–0.50) | 1.00 | 0.00 | 1.00 | 0.00 | 0.89 | 1.0000 | -0.25 |
| grounded_check | 0.93 (0.91–0.96) | 1.00 | 0.92 | 1.00 | 0.86 | 0.89 | 1.0000 | -0.24 |
| box_support | 0.71 (0.70–0.72) | 0.90 | 0.50 | 1.00 | 0.50 | 1.00 | 1.0000 | -0.28 |
| box_support_gtbox | 0.68 (0.67–0.68) | 0.82 | 0.50 | 1.00 | 0.50 | 1.00 | 1.0000 | -0.40 |

### BUS-UCLM (60 cases)

| scorer | AUROC (95% CI) | box-only | text position (box right) | text position + box moved | size | harmless mean | identical mean | severity ρ |
|---|---|---|---|---|---|---|---|---|
| bleu | 0.40 (0.39–0.40) | 0.25 | 0.50 | 0.50 | 0.50 | 0.85 | 1.0000 | 0.31 |
| bertscore[roberta-large] | 0.40 (0.39–0.40) | 0.25 | 0.50 | 0.50 | 0.50 | 0.99 | 1.0000 | 0.31 |
| oracle_label_check | 0.79 (0.78–0.80) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.33 |
| mask_verified_facts | 0.79 (0.78–0.80) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.33 |
| semacc | 0.79 (0.78–0.80) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.34 |
| location_check | 0.50 (0.50–0.50) | 1.00 | 0.00 | 1.00 | 0.00 | 0.90 | 1.0000 | -0.27 |
| grounded_check | 1.00 (1.00–1.00) | 1.00 | 1.00 | 1.00 | 1.00 | 0.90 | 1.0000 | -0.27 |
| box_support | 0.71 (0.70–0.72) | 0.91 | 0.50 | 1.00 | 0.50 | 1.00 | 1.0000 | -0.31 |
| box_support_gtbox | 0.69 (0.68–0.69) | 0.85 | 0.50 | 1.00 | 0.50 | 1.00 | 1.0000 | -0.41 |

### TN3K (100 cases)

| scorer | AUROC (95% CI) | box-only | text position (box right) | text position + box moved | size | harmless mean | identical mean | severity ρ |
|---|---|---|---|---|---|---|---|---|
| bleu | 0.39 (0.39–0.40) | 0.25 | 0.50 | 0.50 | 0.50 | 0.83 | 1.0000 | 0.32 |
| bertscore[roberta-large] | 0.39 (0.39–0.40) | 0.25 | 0.50 | 0.50 | 0.50 | 0.98 | 1.0000 | 0.23 |
| oracle_label_check | 0.78 (0.78–0.79) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.32 |
| mask_verified_facts | 0.78 (0.78–0.79) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.32 |
| semacc | 0.77 (0.76–0.78) | 0.50 | 1.00 | 1.00 | 0.97 | 1.00 | 1.0000 | 0.31 |
| location_check | 0.50 (0.50–0.51) | 1.00 | 0.00 | 1.00 | 0.00 | 0.89 | 1.0000 | -0.30 |
| grounded_check | 0.98 (0.96–0.99) | 1.00 | 1.00 | 1.00 | 0.95 | 0.89 | 1.0000 | -0.29 |
| box_support | 0.69 (0.68–0.69) | 0.86 | 0.50 | 1.00 | 0.50 | 1.00 | 1.0000 | -0.38 |
| box_support_gtbox | 0.67 (0.66–0.67) | 0.81 | 0.50 | 1.00 | 0.50 | 1.00 | 1.0000 | -0.43 |

### TN5000 (100 cases)

| scorer | AUROC (95% CI) | box-only | text position (box right) | text position + box moved | size | harmless mean | identical mean | severity ρ |
|---|---|---|---|---|---|---|---|---|
| bleu | 0.39 (0.38–0.39) | 0.25 | 0.50 | 0.50 | 0.50 | 0.83 | 1.0000 | 0.30 |
| bertscore[roberta-large] | 0.39 (0.38–0.39) | 0.25 | 0.50 | 0.50 | 0.50 | 0.98 | 1.0000 | 0.26 |
| oracle_label_check | 0.78 (0.77–0.78) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.29 |
| mask_verified_facts | 0.78 (0.77–0.78) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.29 |
| semacc | 0.78 (0.77–0.78) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.30 |
| location_check | 0.50 (0.50–0.50) | 1.00 | 0.00 | 1.00 | 0.00 | 0.90 | 1.0000 | -0.34 |
| grounded_check | 1.00 (1.00–1.00) | 1.00 | 1.00 | 1.00 | 1.00 | 0.90 | 1.0000 | -0.34 |
| box_support | 0.68 (0.67–0.68) | 0.83 | 0.50 | 1.00 | 0.50 | 1.00 | 1.0000 | -0.51 |
| box_support_gtbox | 0.68 (0.67–0.68) | 0.83 | 0.50 | 1.00 | 0.50 | 1.00 | 1.0000 | -0.51 |

### DDTI (100 cases)

| scorer | AUROC (95% CI) | box-only | text position (box right) | text position + box moved | size | harmless mean | identical mean | severity ρ |
|---|---|---|---|---|---|---|---|---|
| bleu | 0.40 (0.39–0.40) | 0.25 | 0.50 | 0.50 | 0.50 | 0.84 | 1.0000 | 0.33 |
| bertscore[roberta-large] | 0.40 (0.39–0.40) | 0.25 | 0.50 | 0.50 | 0.50 | 0.99 | 1.0000 | 0.27 |
| oracle_label_check | 0.79 (0.78–0.80) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.32 |
| mask_verified_facts | 0.79 (0.78–0.80) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.33 |
| semacc | 0.79 (0.78–0.80) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.34 |
| location_check | 0.50 (0.50–0.50) | 1.00 | 0.00 | 1.00 | 0.00 | 0.89 | 1.0000 | -0.27 |
| grounded_check | 0.77 (0.73–0.81) | 1.00 | 0.60 | 1.00 | 0.54 | 0.89 | 1.0000 | -0.25 |
| box_support | 0.70 (0.70–0.71) | 0.89 | 0.50 | 1.00 | 0.50 | 1.00 | 1.0000 | -0.33 |
| box_support_gtbox | 0.68 (0.68–0.69) | 0.84 | 0.50 | 1.00 | 0.50 | 1.00 | 1.0000 | -0.41 |

### HC18 (100 cases)

| scorer | AUROC (95% CI) | box-only | text position (box right) | text position + box moved | size | harmless mean | identical mean | severity ρ |
|---|---|---|---|---|---|---|---|---|
| bleu | 0.39 (0.39–0.39) | 0.25 | — | — | 0.50 | 0.75 | 1.0000 | 0.00 |
| bertscore[roberta-large] | 0.39 (0.39–0.39) | 0.25 | — | — | 0.50 | 0.99 | 1.0000 | -0.11 |
| oracle_label_check | 0.79 (0.79–0.79) | 0.50 | — | — | 1.00 | 1.00 | 1.0000 | -0.30 |
| mask_verified_facts | 0.79 (0.79–0.79) | 0.50 | — | — | 1.00 | 1.00 | 0.9993 | -0.28 |
| semacc | 0.61 (0.60–0.62) | 0.50 | — | — | 0.69 | 1.00 | 1.0000 | -0.45 |
| location_check | 0.43 (0.43–0.43) | 1.00 | — | — | 0.00 | 0.90 | 1.0000 | -0.21 |
| grounded_check | 1.00 (1.00–1.00) | 1.00 | — | — | 1.00 | 0.90 | 1.0000 | -0.89 |
| box_support | 0.64 (0.64–0.64) | 0.83 | — | — | 0.50 | 0.99 | 0.9900 | -0.41 |
| box_support_gtbox | 0.63 (0.62–0.63) | 0.79 | — | — | 0.50 | 1.00 | 1.0000 | -0.43 |

### FetalHead (100 cases)

| scorer | AUROC (95% CI) | box-only | text position (box right) | text position + box moved | size | harmless mean | identical mean | severity ρ |
|---|---|---|---|---|---|---|---|---|
| bleu | 0.39 (0.39–0.39) | 0.25 | — | — | 0.50 | 0.88 | 1.0000 | 0.00 |
| bertscore[roberta-large] | 0.39 (0.39–0.39) | 0.25 | — | — | 0.50 | 0.99 | 1.0000 | -0.11 |
| oracle_label_check | 0.79 (0.79–0.79) | 0.50 | — | — | 1.00 | 1.00 | 1.0000 | -0.30 |
| mask_verified_facts | 0.79 (0.79–0.79) | 0.50 | — | — | 1.00 | 1.00 | 1.0000 | -0.30 |
| semacc | 0.57 (0.57–0.57) | 0.50 | — | — | 0.62 | 1.00 | 1.0000 | -0.54 |
| location_check | 0.43 (0.43–0.43) | 1.00 | — | — | 0.00 | 0.89 | 1.0000 | -0.21 |
| grounded_check | 0.88 (0.87–0.88) | 1.00 | — | — | 0.78 | 0.89 | 1.0000 | -0.61 |
| box_support | 0.64 (0.64–0.64) | 0.83 | — | — | 0.50 | 1.00 | 1.0000 | -0.42 |
| box_support_gtbox | 0.62 (0.61–0.62) | 0.77 | — | — | 0.50 | 1.00 | 1.0000 | -0.45 |
