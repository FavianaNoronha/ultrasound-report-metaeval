# Task: Layers 1-3 on bench_v2 (v3, follows Part A Steps 2-4)

Read CLAUDE.md, usmeta/TASK_layers.md (v2), usmeta/TASK_groundtruth.md and usmeta/results/partA/INDEX.md first.
Same rules: no "first ultrasound benchmark" claims (say: we found no ultrasound work that tests the scorers with
planted errors, severity and harmless rewordings; search not exhaustive); no X-ray-trained scorers (no RadGraph,
CheXbert, GREEN); do not overwrite old results; commit after each step; short status after each step with the
results folder path. Every step saves to usmeta/results/partA/stepN_<name>/ (data, results.md, run_info.json with
commit hash/seeds/versions/command, run.log) and updates INDEX.md + summaries/stepN.md. Re-runs go in a new
_rerunN folder. Large files stay out of git (LARGE_FILES.md).

## Step 5: fix the harmless split, then verify Layer 0 (do this first)
Layer 0 AUROC was below chance (0.09-0.36 on BrEaST/BUS-BRA). Likely cause: "harmless" includes style swaps
(terse <-> long-form), which rewrite the whole text, while a planted error changes one word.
- Split harmless into: `harmless_small` (synonyms, sentence reorder, inside ONE style) and `harmless_large`
  (style swap). Keep the old `harmless` label as the union. Write bench_v2b.jsonl (do not overwrite bench_v2).
- Re-run Layer 0 (BLEU, ROUGE-L, chrF, BERTScore, RaTEScore) with AUROC reported separately against
  harmless_small and harmless_large.
- Wiring checks, per scorer and per dataset: identical-copy mean must be 1.0; print it in the table.
- Full per-dataset table for ALL organs (breast: BrEaST, BUS-BRA, BUSI, UDIAT, BUS-UCLM; thyroid: TN3K, TN5000,
  DDTI; fetal: HC18, fetal head planes). Columns: AUROC (bootstrapped CI), critical-only AUROC, harmless_small
  mean, harmless_large mean, identical mean, severity Spearman, magnitude Spearman, plus the "No abnormality."
  lazy-report score. Only report error types a dataset supports; never average across datasets.
- Also report AUROC per error category (false finding, missed finding, wrong location, wrong severity/category,
  wrong measurement). Explain in results.md what "size errors score about 0" means numerically.
Commit.

## Step 6: Layer 1 structured fact check
- usmeta/usmeta/schema.py: ultrasound finding schema (entity, attributes, present/absent/uncertain). Breast =
  BI-RADS lexicon terms; thyroid = TI-RADS terms; fetal = HC mm, plane, structures.
- Grader `finding_f1`: match findings, then compare attributes. Report precision, recall, F1 and per-attribute
  accuracy. Also keep the old fact_checker/fact_f1 for comparison.
- Extractor: rule-based for templated reports; local LLM extractor for free text, quoting source text. Report
  agreement with dataset labels per field (stop and ask if < 85% on templated reports).
- Run on bench_v2b: same table as Step 5, plus per error category. Commit.

## Step 7: Layer 2 AI judge (subsample 50 cases per dataset; say so)
- Run local Gemma-2-9B judge (MLX) on bench_v2b.
- `sentence_check` (RadFact-style protocol with <model>, not the original RadFact): split both reports into
  sentences; precision = each generated sentence supported by the true report; recall = each true sentence
  covered. Also ask for the error category and compare to the planted tag (judge category accuracy).
- Rule: a judge never grades reports from its own model family (Gemma judge must not grade MedGemma reports;
  use a non-Gemma judge for those).
- Same table as Step 5. Note what Gemma-2-9B scored before (0.78 overall, 0.99 critical on the old benchmark).
- Claude judge needs credits: skip unless credits are available. Commit.

## Step 8: Layer 3 image / location check
- Do usmeta/TASK_location.md items not yet done (IoU loader, planted location mistakes).
- Test 1 (core): plant location/size errors in true reports; score with the image check using the TRUE masks.
  Per organ: breast = side, position thirds, size mm (where pixel size exists), rough shape; thyroid = position,
  size, taller-than-wide (TN3K masks, DDTI outlines->masks; TN5000 box IoU only); fetal = HC mm from HC18
  ellipse, structure visible (fetal head planes). Sanity row: true mask vs true mask gives IoU = Dice = 1.0.
- `mask_verified_facts`: how many size/location claims are backed by the mask. Keep the old label-based
  evidence_check as an "oracle upper bound" row.
- Spatial support: sentence supported if >= 50% of its box falls inside the true region; report grounding
  precision/recall, box IoU, pixel precision/recall.
- Add SemAcc (UltraG-Bench: presence, category, location, size yes/no checks). Note UltraG reports are
  GPT-5.5-written from masks, not radiologists. Cite UltraG-Bench; do not present IoU/Dice or the
  VLM+segmenter design as new.
- Do NOT run MedSAM/SAM2 yet (that is Part B, after this brief).
Commit.

## Step 9: combined results
- results_layers_all.md: every scorer x every dataset grouped by layer, AUROC per error category, harmless_small
  and harmless_large means, column "idea borrowed from" (RadFact, GREEN categories, UltraG, ours).
- Update README and CLAUDE.md task list. Commit.

## Keep visible in every results.md
Reports are templated from labels (synthetic but fact-correct); severity is provisional pending clinician;
template sources marked "to confirm" must be verified before any paper claim; results are per dataset only.

## Stop and ask me if
- identical-copy mean is not 1.0 for any scorer
- extractor agrees with labels on < 85% of fields on templated reports
- a dataset's labels contradict its masks or pixel sizes
- a package needs a gated model, a paid API, or a download over 5 GB
- a run will take longer than ~3 hours
