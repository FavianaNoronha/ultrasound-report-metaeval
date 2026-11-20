# Step 46 (PRE-REGISTRATION): our own scorer, and CRQS adapted to ultrasound

Written 2026-11-20, after Step 45 Parts A-F and before any Step 46 number. Standing rules from CLAUDE.md apply: additions only; frozen files untouched; tune on dev/val only; read each test set once (logged); group bootstrap 1,000 resamples, seed 0; cells under 30 groups = "too small to compare"; no "first" claims; a pass is "better on our benchmark / on model-written free text", never clinical validation.

## Why this step (what Steps 2-45 taught us)
- Word and embedding scorers follow wording, not facts (Steps 33-35).
- The holistic Gemma judge follows facts but is prompt-sensitive (Steps 12, 39) and the claim-by-claim version failed (Step 45 D: 4.9% catch).
- Deterministic checks work where they apply: number checker AUROC 1.00 with 0% harmless flagged, but only 65.9% of all planted errors are numeric/category (Step 45 C).
- Extractor v5 passes on writer-made free text (Step 45 B), and the rules-then-judge hybrid caught 100% at 4.1% harmless (Step 45 F, incomplete).
- **Main weakness of Step 45:** set A was written by Qwen2.5-7B and read by a Qwen2.5-7B extractor (same family), and its extras filter removed the thyroid BI-RADS failure. Step 46 therefore tests on a NEW free-text set written by a different model family.

## 1. New test set B (different writer family)
- Writer: Llama-3.1-8B-Instruct 4-bit (MLX). Not Qwen (the extractor) and not Gemma (the judge). If unavailable, Mistral-7B-Instruct 4-bit; record which.
- Same design as Step 45 Part A (facts only to the writer, 3 styles, one planted-error twin, graded size / HC twins, deterministic gold and extras checks), new seeded cases, group-disjoint by the locked splits, none reused from set A. Target 90 test cases per organ (dev/val: reuse set A dev/val for tuning; set B dev/val 30 per organ only to report transfer).
- Report the share of reports dropped by each filter, per organ. **Also keep, as a separate stress subset, the reports the extras filter would drop** (e.g. BI-RADS on thyroid): they are scored and reported separately, not discarded silently.

## 2. Our scorer (working name: UScore)
Built only from parts already frozen in Step 45 plus fixed rules; no new model.
Components on each (reference, candidate) pair:
 a. Number checker (Step 45 C, frozen tolerances).
 b. Extractor v5 field comparison (Step 45 B), mode conflict + omission.
 c. Holistic Gemma-2-9B judge prompt_v2 (frozen), called ONLY when (a) and (b) find nothing.
 d. (Secondary, image available only) U-Net position / size check: the Step 29 model, or the Step 45 G model if G passes.
**Primary score (rule version, no fitting):** start at 1.0; subtract a severity penalty for each discrepancy found by a or b (critical 0.6 / major 0.3 / minor 0.1, using the project's provisional field severities); if a and b find nothing, use the judge score. Output = score + the list of discrepancies (field, reference value, candidate value, source a/b/c). Flag threshold: fixed on set A dev/val so that at most 5.6% of harmless reports are flagged.
**Secondary (learned):** logistic regression on [a, b, c outputs + Step 45 E diff features], trained on templated DEV, tuned on VAL, frozen before any set B number.

## 3. CRQS adapted to ultrasound (PathReportEval, Singh et al., arXiv 2607.18448)
- **First copy the exact CRQS definition from the paper and its code (github.com/surykntsingh/PathBench) into `CRQS_SOURCE.md`, with quotes and the commit hash.** Our earlier reading of the formula looked inconsistent (weights vs normalisation; a negative example despite a stated [0,1] range). If the source cannot be resolved, implement it as written, record the ambiguity, and also report a [0,1]-clipped version. Do not change their weights.
- Field mapping (fixed now): clinical fact coverage = share of reference fields matched; key-information recall = recall on key fields (breast: pathology, BI-RADS, size; thyroid: TI-RADS, size, composition; fetal head: head circumference, plane); hallucination rate = share of candidate fields absent from the reference; clinical discordance = any mismatch on a key field. Extraction: the same extractor v5 as UScore, so the comparison is fair.

## 4. Hypotheses and pass rules (set B test unless stated)
- **H1 (separation):** UScore primary error-vs-harmless AUROC >= 0.90, and above each of BLEU, ROUGE-L, chrF, BERTScore, RaTEScore, the holistic judge, CRQS and the Step 45 E learned scorer, with the CI of each paired difference excluding 0.
- **H2 (monitor):** at the set-A-val threshold, catch >= 80% of planted-error twins with harmless flagged <= 5.6%.
- **H3 (stress subset):** report catch and harmless flagged on the reports the extras filter would drop; no pass rule (descriptive).
- **H4 (wording vs facts, templated, CEILING):** Step 33 factorial on UScore: fact share >= 0.60, wording share <= 0.05. Labelled a ceiling because rules read template wording.
- **H5 (limit of detection):** AUROC >= 0.80 at a 5% size change and 1 mm head circumference on set B graded twins.
- **H6 (human rewordings, 29 items, too small):** descriptive AUROC only.
- **H7 (severity):** Spearman between provisional severity and score drop <= -0.3 on templated test (severity labels are ours, not clinician-set).
- **CRQS prediction (written now):** CRQS beats the word scorers on H1 but is below UScore on H2, because its fixed weights do not separate a small fact change from a harmless omission. Reported whether right or wrong.

## 5. Reporting
One results.md per part with the rule, the number, PASS / DOES NOT PASS; INDEX row, CHANGELOG, RESULTS_SUMMARY addendum, LIMITATIONS item. State plainly: UScore is assembled from our own components and evaluated on our own benchmark plus model-written text; no clinician has validated it; real radiologist reports are still needed.
