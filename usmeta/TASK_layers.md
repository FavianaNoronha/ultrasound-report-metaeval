# Task: Layers 1, 2, 3, borrowing ideas from chest X-ray work (v2)

Replaces the previous TASK_layers.md. Read CLAUDE.md first. Same rules apply: no "first ultrasound
benchmark" claims, flag possible contamination, don't overwrite existing results, commit after each
step, and give a short status after each step.

## Change from v1
Do NOT use chest-X-ray-trained scorers as our metrics (no RadGraph, no CheXbert, no SRR-BERT, no GREEN).
They are built around chest X-ray vocabulary and labels. Instead, borrow the IDEAS that X-ray research
developed and build ultrasound versions of them. Only modality-agnostic code (geometry such as box and
mask overlap) may be reused directly. Record any reused code, its version and licence in
docs/third_party.md.

## Concepts borrowed from X-ray
| X-ray idea (source) | What it means | Our ultrasound version |
|---|---|---|
| Findings as structured facts (RadGraph) | A report is a list of findings, each with an entity, attributes and present/absent/uncertain | Our own schema: breast uses BI-RADS lexicon terms (shape, margin, echogenicity, posterior features, calcifications, size, side, BI-RADS); thyroid uses TI-RADS-style terms (composition, echogenicity, shape, margin, echogenic foci, position, size); fetal uses head circumference in mm |
| Error categories (GREEN / ReXVal) | Count mistakes by type, not just give one score | Tag every planted mistake as: false finding, missed finding, wrong location, wrong severity/category, wrong measurement. Report scorer AUROC per category |
| Two-way sentence checking (RadFact, MAIRA-2) | Precision: is each generated sentence supported? Recall: is each true finding mentioned? | Separates "made something up" from "left something out" |
| Grounded sentences (MAIRA-2 / RadFact) | Each finding sentence carries a box; the box must land on the right region (>=50% of its pixels inside the true region) | Our Layer 3, using masks (BrEaST, BUS-BRA, TN3K), boxes (TN5000) and the filled ellipse (HC18) |
| Locate, then describe (grounded report generation) | Model first finds the region, then describes it | Option for the real-report run: Qwen gives a box first, then describes the cropped region, then writes the report |

## Layer 1: structured fact check
- Write usmeta/usmeta/schema.py: the ultrasound finding schema above (entity, attributes, presence).
  For BrEaST, map spreadsheet columns directly to attributes; BrEaST is the richest dataset here.
- Upgrade the extractor so free-text reports are turned into this schema (rule-based for templated
  reports; the local LLM extractor for real reports, with the model quoting the source text).
- New grader `finding_f1`: match findings, then compare attributes. Report precision, recall and F1
  separately, plus per-attribute accuracy.
- Tag every planted mistake in bench_small.jsonl with an error category (see table).
- Run on bench_small.jsonl and write results_layer1.md/json: AUROC overall and per error category,
  critical AUROC, harmless mean, identical mean (must be 1.0), severity and magnitude Spearman, all per
  dataset. Commit.

## Layer 2: AI judge
- Run the existing llm_judge (Gemma-2-9B, MLX) on bench_small.jsonl to get the first judge AUROC.
- New `sentence_check` judge, using the RadFact protocol idea: split both reports into sentences,
  then ask the local model whether each generated sentence is supported by the true report (precision)
  and whether each true sentence is covered (recall). Label it "RadFact-style protocol with <model>,
  not the original RadFact".
- Ask the judge to also output the error category, and compare it to our planted tag (judge
  category accuracy).
- Rule: a judge never grades reports from its own model family.
- If runs are too long, subsample to 50 cases per dataset and say so.
- Write results_layer2.md/json. Commit.

## Layer 3: image / location check
- Do usmeta/TASK_location.md: the IoU loader, planted location mistakes, Qwen boxes and BrEaST.
- Add the RadFact-style spatial check: a sentence is "spatially supported" if >=50% of its box falls
  inside the true region. Report grounding precision/recall, box IoU, pixel precision and pixel recall.
- Try the "locate, then describe" prompt for Qwen on 20 scans per dataset. Compare it with the normal
  prompt on box IoU and finding_f1, and keep both outputs.
- Keep the old label-based evidence_check only as a clearly labelled "oracle upper bound" row.
- Write results_layer3.md/json. Commit.

## Layer 3b: segmentation check (IoU + Dice)
- Turn each model box into a mask with a promptable segmenter: try MedSAM first, then SAM2-small if
  MedSAM won't run on MPS. Check the licence and record it in docs/third_party.md.
- Score the mask against the true mask (BrEaST, BUS-BRA, TN3K, HC18 filled ellipse) with IoU and Dice.
  TN5000 has boxes only, so report box IoU only there.
- Also use the mask to check the report's claims: lesion size (mm, from pixel size) and position
  (left/right, upper/middle/lower). This gives a `mask_verified_facts` score: how many size and
  location claims in the text are backed by the segmented region.
- Sanity row: true mask vs true mask must give IoU = Dice = 1.0.
- Note in results that this follows UltraG-Bench's segmentation metrics (IoU/Dice) and its
  VLM + segmenter agent design. Cite it; don't present it as new.

## Extra scorer to test: UltraG-Bench SemAcc
- UltraG-Bench scores reports with ROUGE-L plus SemAcc, the average of four yes/no checks: presence,
  category, location and size. Implement SemAcc as a grader, following their paper and repo
  (https://github.com/zhuqh19/UltraG-Bench), and run it on bench_small.jsonl like every other scorer.
- Their reports were written by GPT-5.5 from masks, not by radiologists. Note that wherever
  UltraG-derived text is used.

## Finally
- Write results_layers_all.md: every scorer x every dataset, grouped by layer, with AUROC per error
  category and harmless mean, plus a column "idea borrowed from" (e.g. RadFact, GREEN categories, ours).
- Update the README and the CLAUDE.md task list. Commit.

## Stop and ask me if
- a package needs a gated model, a paid API, or a download over 5 GB,
- any scorer gives an identical-copy mean that is not 1.0 (that means a wiring bug),
- the extractor agrees with the dataset labels on less than 85% of fields on templated reports,
- a run will take longer than about 3 hours.
