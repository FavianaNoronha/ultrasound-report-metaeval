# usmeta: do the scorers for AI-written ultrasound reports catch real mistakes?

Owner: Faviana Noronha (PGSSP, IIIT-Hyderabad), with Sai Pradeep and Harshal Bhansali.

## The project in one paragraph
AI models now write ultrasound reports, and the scores used to grade them mostly count matching words.
We test the scorers themselves. For each case we build a reference report from dataset labels, then make
(a) candidates with ONE planted mistake (with a severity and, where numeric, a magnitude),
(b) harmless rewordings (mild paraphrase, strong rewrite, unit rewrite) and (c) identical copies.
A good scorer scores mistakes lower than harmless rewordings, scores bigger mistakes lower, and gives identical copies 1.0.

## Metrics we report per grader, per organ and per dataset
- Discrimination AUROC: mistake vs harmless rewording, paired per case, bootstrapped over cases (95% CI)
- Critical-only AUROC
- Robustness: mean score on harmless rewordings; identical copies must be 1.0
- Severity Spearman and magnitude Spearman (negative is good: bigger mistake, lower score)

## Positioning (prior-art rule: never claim "first")
Say: "we found no ultrasound work that tests the scorers with planted errors, severity and harmless rewordings".
Our search was not exhaustive. Closest work: U2-Bench (2505.17779), UltraG-Bench (2609.30928), BUSTR (2511.20956),
ReEvalMed "Beyond Scalar Scores" (2606.18797, chest X-ray), GREEN, RaTEScore, CRIMSON (2603.06183), RadMatch, RadEval.

## What exists (all in this folder)
- `usmeta/templates.py` organ templates, perturbations, builders (breast BrEaST, breast BUS-BRA, thyroid, fetal HC18)
- `usmeta/extract.py` rule-based fact extractors (upper bound on our own templated text)
- `usmeta/graders.py` bleu, rougeL, chrf, fact_checker, fact_f1, evidence_check (oracle image check), judge_mock,
  llm_judge, bertscore:<model>, ratescore, green
- `usmeta/meta.py` AUROC, summaries, markdown tables; `usmeta/run.py` CLI: build | grade | report
- `usmeta/records.py` UltraG thyroid and TN5000 record readers; `usmeta/inspect_task.py` Inspect task `usmeta_judge`
- `tests/test_smoke.py` (3 tests pass: `PYTHONPATH=. python3 -m pytest -q tests`)
- `bench_v1.jsonl` (23,780 pairs, 6 datasets), `scores_v1.json`, `results_v1.md`, `run_stage2.sh`

## Datasets in the benchmark (500 cases sampled per dataset except BrEaST)
BrEaST (256 cases), BUS-BRA (left/right images only), TN3K, TN5000, UltraG thyroid (text labels only), HC18.
Next: BUSI, UDIAT. TN3K/TN5000 class 0/1 meaning is NOT confirmed: keep the label "class 0/1".
Raw data is in ~/Downloads (BUSBRA under archive-5, TN5000_forReview, thyroid_grounded_full_v1.jsonl, archive-7 for HC18).

## Results so far (Stage 1, done)
Word overlap (BLEU, ROUGE-L, chrF): AUROC 0.00 on every organ. A wrong diagnosis scores higher than a harmless rewording
(BLEU: BUS-BRA 0.88 vs 0.45, TN5000 0.94 vs 0.38, BrEaST wrong BI-RADS 0.95 vs 0.47, fetal 1 mm and 40 mm both 0.83).
Fact checker and evidence check: AUROC 1.00, but only because the reports are templated (upper bound, not a finding).

## FREEZE (2026-10-24)
Read `docs/LIMITATIONS.md` first. Tag `freeze-v1`: frozen items are listed in `FROZEN.md`; changes need a new version + `CHANGELOG.md`. Splits are locked (`splits.jsonl`): tune on dev/val only, report final numbers on test via `usmeta.splits.load("test")` (logged). Step 10 outputs are in `results/partA/step10*`.

## PROGRESS (2026-10-23) - read before the old task list
Done: stage 2 scorers (BERTScore, RaTEScore; GREEN not run), local Gemma judge, Qwen real reports (200 scans), Part A steps 2-9 (templates_v2, bench_v2d,
Layers 0-3, results_layers_all.md). Use `bench_v2d.jsonl` and `true_reports_v2d.jsonl` (supersede bench_v2/v2b/v2c; BUS-BRA side bug fixed).
Results are saved under `results/partA/stepN_*/` with `INDEX.md`; datasets manifest in `../datasets/`.
Still open: MedGemma/LLaVA-Med reports and ranking comparison, Claude judge (needs credit), Inspect check, SAM/MedSAM predicted masks (Part B),
real-VLM reports graded by Layers 1-3, clinician severity sample, BERTScore on thyroid/fetal done (Layer 0). Keep the caveats visible:
templated reports, provisional severity, template sources "to confirm", per-dataset results only, contamination cannot be ruled out.

## TASKS FOR CLAUDE CODE (original list, partly done: see PROGRESS above)
1. `pip install -r requirements.txt bert-score`, then run `bash run_stage2.sh`
   (100 cases per dataset; BERTScore roberta-large, RaTEScore, GREEN). The RaTEScore and GREEN wrappers have never run:
   read the errors and fix them in `usmeta/graders.py`. Add a test for each fix.
2. LLM judge across several models. Add a backend that calls the `claude` CLI (uses my login, no API key), selectable by model,
   and run it with `bash run_stage2.sh judge`. Also verify `usmeta/inspect_task.py` end to end with `inspect eval`
   (never verified; the sandbox blocked a tiktoken download). Compare judges in one results table.
3. Realistic reports: run ALL THREE open vision-language models as report writers on the same scans, with the same prompt:
   MedGemma (google/medgemma-4b-it), Qwen2.5-VL (Qwen/Qwen2.5-VL-3B-Instruct or 7B), LLaVA-Med.
   Use 50 scans per dataset first (CPU is slow; use a GPU or a smaller model if needed). Save reports to `reports_<model>.jsonl`,
   then extract facts and grade each model's reports with every scorer. Compare models per organ and per dataset, and
   compare real mistakes against our planted ones (do the scorers behave the same way?).
4. Replace the oracle image check (`evidence_check` uses dataset labels) with a real one: a segmentation model or a VLM.
5. Add BUSI and UDIAT; add BERTScore for thyroid and fetal.
6. Severity levels are our own provisional guesses: prepare a short sample for a clinician to confirm.
7. After each stage, regenerate `results_*.md` and tell me the headline numbers; I will update the team slides.

## Contamination rules (do not skip)
- Our reference texts come from our own templates, so judges cannot have memorised them. The scorer test is mostly safe.
- The report-writing models may have seen BUSI, BUS-BRA, TN3K, TN5000, HC18 during training; we cannot verify this.
  Report every model result per dataset, mark public older datasets as "possibly seen", and keep BrEaST (newer, small) as the cleanest check.
- Add a sanity check: flipped or cropped copies of a scan should not change a model's report much if it is not memorising.
- A judge must never grade reports from its own model family. Use a different family as judge than the report writer.
- State in the paper that contamination cannot be ruled out. Do not claim it is absent.

## Rules
- Do not overwrite `bench_v1.jsonl`, `scores_v1.json` or raw data; write new files beside them.
- Every claim needs a number from a results file. Keep the limitations visible: templated reports, provisional severity, oracle image check.
- Keep answers short and plain; I am learning evaluation as I go, so explain new terms in one line.
