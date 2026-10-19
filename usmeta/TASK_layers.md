# Task: Layers 1, 2, 3 using the scorers from chest X-ray papers

Read CLAUDE.md first. Same rules: no "first ultrasound benchmark" claims, flag contamination,
don't overwrite existing results, commit after each step, short status after each step.

Idea: don't reinvent scorers. Reuse the published X-ray report scorers (their own code/packages),
wrap each one as a grader in usmeta/usmeta/graders.py, and run them on our planted-mistake benchmark
(bench_small.jsonl, and bench_loc.jsonl for Layer 3). Goal is to test whether these X-ray scorers
transfer to ultrasound — they were built for chest X-ray, so poor transfer is a valid finding.

## Code sources (verify each before use; record version + licence in docs/third_party.md)
- RadEval toolkit — https://github.com/jbdel/RadEval (pip: RadEval). Bundles BLEU, ROUGE, BERTScore,
  RadGraph F1, RaTEScore, GREEN (incl. lightweight GREEN Gemma-2B), RadCliQ, SRR-BERT, RadEvalBERTScore.
  Use it rather than separate installs where possible. Check our existing bleu/rouge/bertscore/ratescore
  numbers match RadEval's on 20 pairs (sanity check), but keep our existing results.
- RadFact (from MAIRA-2) — https://github.com/microsoft/RadFact. Sentence-level logical entailment +
  spatial entailment of boxes (a box is spatially entailed if >=50% of its pixels fall inside evidence boxes).
  The paper used Llama3-70B — too big for this 16 GB Mac. Use a local model (Gemma-2-9B 4-bit via MLX, or
  Qwen2.5-7B) and clearly label it "RadFact protocol with <model>, not the original setup".
- Skip F1CheXbert and SRR-BERT as headline metrics: their label spaces are chest-X-ray-only. Run them
  once and report them in an appendix row marked "X-ray label space, not meaningful for ultrasound".

## Layer 1 — fact / entity checking
- Add graders: radgraph_f1 (via RadEval), keep fact_checker + fact_f1.
- RadGraph is trained on chest X-ray reports: also print, for 10 reports per dataset, which entities it
  extracts, so we can show whether it even recognises ultrasound terms (BI-RADS, TI-RADS, echogenicity, HC).
- Run on bench_small.jsonl -> results_layer1.md/json (AUROC, critical AUROC, harmless mean, identical mean,
  severity Spearman, magnitude Spearman, per dataset). Commit.

## Layer 2 — AI judges
- green_2b: GREEN lightweight Gemma-2B via RadEval (fits 16 GB; replaces "GREEN not run").
  Note in results: the refined GREEN training data includes some ultrasound — possible overlap risk; flag it.
- radfact_logical: RadFact logical precision/recall/F1 with the local model above.
- llm_judge (existing, Gemma-2-9B MLX): finally run it on bench_small.jsonl to get the judge AUROC.
- Rule: a judge never grades reports written by its own model family (relevant later for MedGemma/Gemma).
- If runtime is too long, subsample to 50 cases per dataset and say so.
-> results_layer2.md/json. Commit.

## Layer 3 — image / location check
- Do usmeta/TASK_location.md (IoU loader, planted location mistakes, Qwen boxes, BrEaST added).
- Additionally compute the RadFact spatial metrics on bench_loc.jsonl and on the Qwen box outputs:
  grounding precision/recall and spatial precision/recall, plus MAIRA-2-style box IoU / pixel precision /
  pixel recall. Ground-truth boxes come from masks (BrEaST, BUS-BRA, TN3K), VOC boxes (TN5000),
  filled ellipse (HC18).
- Keep the old label-based evidence_check as an "oracle upper bound" row, clearly labelled.
-> results_layer3.md/json (+ the files TASK_location.md asks for). Commit.

## Finally
- One combined table results_layers_all.md: every scorer x every dataset, AUROC + harmless mean,
  grouped by layer, with a column "built for" (generic text / chest X-ray / ours) and a notes column.
- Update README status and the CLAUDE.md task list. Commit.

## Stop and ask me if
- a package needs a gated model, a paid API, or a download over 5 GB,
- RadFact or RadEval won't install on Apple Silicon after two tries (show the error),
- any scorer gives identical-copy mean != 1.0 (that means a wiring bug),
- a run will take longer than ~3 hours.
