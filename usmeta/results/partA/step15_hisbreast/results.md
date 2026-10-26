# Step 15: HiSBreast, real clinician-written conclusions (automatic translation validation, then TASK_hisbreast on the kept exams)

**No HiSBreast text, translation, paraphrase or exam id appears in this folder or in git.** The data, the validation table and the review CSV stay in `usmeta/local_data/hisbreast/` (git-ignored; licence blank, no de-identification statement). This file holds aggregate counts and scores only. Limitations: [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md) ("HiSBreast translations validated by automatic key-fact checks and independent back-translation; no bilingual human review").

## 1. What replaced the hand-check
Key facts are extracted from each text: numbers with units (cm -> mm), BI-RADS codes, side words (phải / trái / hai bên vs right / left / both), negation (không, chưa vs no, not, without, unclear), "no abnormality" phrases, axillary-node mention, plus soft concept flags (mass, cyst, abscess, inflammation, follow-up, biopsy, cancer, benign, post-surgery, fibro). **The Vietnamese keyword dictionary was written by the assistant (not a bilingual human)**: a missing word makes a check fail (the case is dropped); it cannot make a bad translation pass, but it can wrongly drop a good one. Soft flags are logged but never fail a case.
- **Check 1:** Vietnamese original vs the English translation (Gemma-2-9B).
- **Check 2:** English translation vs a second translation by a different, non-Gemma model (Qwen2.5-7B-Instruct 4-bit, already on the Mac; no download).
- **Check 3:** back-translation of Gemma's English into Vietnamese by Qwen2.5-7B vs the original.
- Degenerate generations (Chinese characters or runaway length) got one retry with a stricter prompt; still-degenerate outputs make that check fail ("unusable").

| check | texts failed (of 310 unique) | exams failed (of 427) | main mismatch types (texts) |
|---|---|---|---|
| 1 original vs Gemma English | 38 (12%) | 66 | BI-RADS 19, negation 15, no-abnormality 18, numbers 12, side 6 |
| 2 Gemma English vs Qwen English | 129 (42%) (2 unusable generations) | 219 | BI-RADS 88, side 45, no-abnormality 28, negation 22, numbers 17, axillary 8 |
| 3 original vs back-translation | 179 (58%) (10 unusable) | 247 | BI-RADS 85, axillary 55, no-abnormality 51, side 46, negation 18, numbers 14 |
| **passed all three** | **86 texts** | **101 exams (dev 46, val 14, test 41)** | |
Reading: Gemma's translation agrees with the original on key facts for 88% of texts; checks 2 and 3 fail much more often, and inspection of failures (locally, not committed) shows the second and back-translations by a 7B model are themselves unreliable (invented BI-RADS codes, English words left in Vietnamese, Chinese text) and also that Gemma sometimes invented items (extra BI-RADS code, extra sizes, "no abnormality recorded") for very short inputs: check 1 catches those. **Only 24% of exams (101 of 427) survive the strict rule**, so the kept set is a small, easier-than-average subset (short, explicit texts), not a sample of HiSBreast. Sensitivity set (pass check 1 and at least one of 2 or 3): 279 exams (test 118), reported separately.
**Parser sanity (rule parsers on the Vietnamese original vs on the English, kept exams; not accuracy):** side 100%, BI-RADS 100%, axillary 100%, recommendation 100%, suspicious wording 99%, **finding type only 50%** (all 427 exams: side 98%, BI-RADS 90%, finding 58%, axillary 100%, recommendation 97%, suspicious 98%). The finding-type parser fails the 85% bar in the brief's agreement sense, so the finding-type field is unreliable; it only enters `finding_f1_his` as one of six fields, identically in reference and candidate. English translations state a BI-RADS code in 215 exams, the Vietnamese originals in 171: 44 codes were added by the translation (mostly caught by check 1).
**Review file:** `local_data/hisbreast/uncertain_cases.csv` (60 rows: 30 borderline failures that failed by one hard mismatch, 30 passes with the most soft disagreements; columns: original, both translations, back-translation, mismatch types, empty verdict column). Nobody has to review it; it is for spot checks only.

## 2. Paraphrases (harmless rewordings)
Gemma-2-9B reworded each of the 208 unique kept-or-sensitivity English texts; each paraphrase had to keep the key facts (rule check) and be judged "same clinical meaning" by a non-Gemma judge (Qwen2.5-7B). Of 208: **123 kept, 67 dropped for changed key facts (mostly BI-RADS codes and numbers), 18 dropped by the meaning judge**, 0 identical to the original. Rule-based harmless rewordings (reverse the order of parts, bullet or sentence form, one-word synonym) need no check.

## 3. Benchmark on the kept exams (locked splits by exam id: `hisbreast_splits.jsonl`, dev 40 / val 20 / test 40 by hashed exam id)
True report = the validated English conclusion. Planted errors (only where the text allows): BI-RADS category +-1 step (severity 3 if crossing the biopsy line 3 -> 4A), side swap (3), negation flip (no abnormality <-> mass; 3), missed axillary node (2), invented axillary node (2), benign <-> suspicious (3), recommendation changed (2), size x2 (2; none applicable). Severity is provisional. Strict test set: **41 exams, 38 unique texts**, 20 side swaps, 42 BI-RADS changes, 39 invented axillary nodes, 13 negation flips, 3 other errors. Edit size matters again: real errors change 12-58% of the tokens (side swap 21%, BI-RADS 14%, invented axillary 30%) because the conclusions are about 13 words long, against 2-4% on the templated reports.
Wiring gate: identical copies score 1.0000 on every scorer on the test exams (RaTEScore scores identical short texts without medical entities as 0.5, giving a dev/val identical mean of 0.98).

## 4. Results (strict test exams, n = 41; 95% CI resamples exams; judge: Qwen2.5-7B with prompt_v2q on 266 pairs, 0 unparseable, 0 length mismatches)
AUROC of planted error vs harmless rewording (1.0 perfect, 0.5 chance), real HiSBreast next to the templated results:

| scorer | templated BrEaST: vs small / matched / large (test) | templated BUS-BRA: vs small / matched / large | **real HiSBreast (41 test exams)**: vs all harmless | vs form/reorder (small) | vs 1-word synonym | vs LLM paraphrase |
|---|---|---|---|---|---|---|
| bleu | 0.25 / 0.61 / 0.08 | 0.21 / 0.75 / 0.09 | 0.64 (0.57–0.71) | 0.76 (0.68–0.84) | 0.82 (0.67–0.95) | 0.04 (0.00–0.10) |
| rougeL | 0.10 / 0.58 / 0.08 | 0.09 / 0.66 / 0.09 | 0.76 (0.71–0.81) | 0.84 (0.79–0.89) | 0.89 (0.75–0.98) | 0.24 (0.08–0.42) |
| chrf | 0.38 / 0.25 / 0.08 | 0.30 / 0.36 / 0.09 | 0.72 (0.67–0.78) | 0.88 (0.83–0.93) | 0.42 (0.29–0.54) | 0.11 (0.03–0.21) |
| bertscore[roberta-large] | 0.21 / 0.53 / 0.08 | 0.09 / 0.42 / 0.09 | 0.43 (0.38–0.50) | 0.47 (0.40–0.54) | 0.86 (0.78–0.95) | 0.08 (0.02–0.15) |
| ratescore | 0.45 / 0.64 / 0.13 | 0.52 / 0.66 / 0.20 | 0.66 (0.58–0.73) | 0.69 (0.61–0.78) | 0.61 (0.46–0.77) | 0.50 (0.33–0.67) |
| finding_f1_his | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 0.94 (0.91–0.97) | 0.95 (0.93–0.98) | 0.89 (0.84–0.93) | 0.87 (0.78–0.94) |
| sentence_f1 (Qwen2.5-7B v2q here; Gemma prompt_v2 on templated: see Step 12) | 0.67 / 0.89 / 0.61 | 0.60 / 0.96 / 0.96 | 0.79 (0.74–0.84) | 0.79 (0.74–0.84) | 0.81 (0.76–0.86) | 0.81 (0.74–0.87) |
| judge_score (Qwen2.5-7B v2q here; Gemma prompt_v2 on templated: see Step 12) | 0.85 / 1.00 / 0.51 | 0.64 / 1.00 / 1.00 | 0.82 (0.77–0.88) | 0.81 (0.75–0.87) | 0.90 (0.85–0.95) | 0.89 (0.82–0.94) |
By category, real text (AUROC vs all harmless; the 20 / 29 / 2 cells are too few errors to compare):

| error category (real text) | test exams with an error of this category | bleu | rougeL | chrf | bertscore | ratescore | finding_f1_his | sentence_f1 (judge) |
|---|---|---|---|---|---|---|---|---|
| wrong location | 20 (too few to compare) | 0.60 | 0.85 | 0.80 | 0.27 | 0.73 | 0.98 | 0.99 |
| wrong severity/category | 29 (too few to compare) | 0.56 | 0.73 | 0.52 | 0.20 | 0.43 | 0.99 | 0.88 |
| false finding | 40 | 0.71 | 0.76 | 0.82 | 0.69 | 0.75 | 0.91 | 0.68 |
| missed finding | 2 (too few to compare) | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.75 |
**Lazy report ("No abnormality recorded." scored against every true report):** BLEU 0.04, ROUGE-L 0.10, chrF 0.09, **BERTScore 0.86**, RaTEScore 0.50 (flat), `finding_f1_his` 0.01. 

## 5. Do the templated findings hold on real text?
- **Partly.** (a) **BERTScore stays at chance** (0.43 overall; 0.47 vs form/reorder) and is blind to a changed side or BI-RADS (0.27 and 0.20 by category); it also gives the lazy report 0.86, as on templated text. (b) **Word-overlap scorers (BLEU, ROUGE-L, chrF) do better than on templated text** against form changes and one-word synonyms (0.76-0.89) and are above 0.5 on every error category except wrong severity/category, which is mostly BI-RADS changes (BLEU 0.56, chrF 0.52, RaTEScore 0.43: near chance): the reason is edit size, not understanding: on 13-word conclusions a side swap or code change is a 14-21% edit (templated: 2-4%). (c) **They still fail against an LLM paraphrase**: AUROC 0.04 (BLEU), 0.24 (ROUGE-L), 0.11 (chrF), 0.08 (BERTScore), 0.50 (RaTEScore): a rewording that changes about half of the tokens scores worse than a changed fact, exactly as the large rewordings on templated text. (d) `finding_f1_his` is high (0.94) but is an upper bound again: the parser reads the same fields in reference and candidate (and its finding-type field is unreliable). (e) The Qwen2.5-7B judge reaches 0.79-0.82 overall, 0.99 for side swaps (wrong location), 0.84-0.88 for wrong severity/category (mostly BI-RADS changes), and only 0.68-0.75 for false findings (mostly invented axillary nodes), similar in spirit to the templated judge result (strong on location, weaker on added content). The judge differs from the Gemma judge of Step 12, so numbers are not like for like.
- **So the templated results are believable for BERTScore, for the paraphrase/edit-size effect and for the lazy-report result, and misleading about how hard small word-overlap gaps are, because real clinical conclusions are so short that real errors are large edits.** Small n (41 exams), one hospital, machine-translated and filtered text: do not generalise.

## 6. Not done from TASK_hisbreast
Step 5 (Qwen on HiSBreast images) was not run: it needs me to look at 10 images for burned-in names or IDs first, and the images were not opened here. A manual check of 50 parsed fields was replaced by the cross-language parser agreement above (not a substitute).

**Caveats (keep visible).** Machine translation validated only by automatic checks (no bilingual human); strict filter keeps 24% of exams (selection bias towards short explicit texts); dictionary written by the assistant; checks 2 and 3 use a 7B model and fail often for model reasons; single hospital; clinical or ICD diagnosis is not pathology; no masks (text side only); severity provisional; HiSBreast is public: possible exposure of the models, unverifiable; licence blank: no redistribution.
