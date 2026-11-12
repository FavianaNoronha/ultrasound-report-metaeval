# usmeta: do the scorers for AI-written ultrasound reports catch real mistakes?

Owner: Faviana Noronha (PGSSP, IIIT-Hyderabad), with Harshal Bhansali.

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

## FINAL (2026-10-27, Steps 2-17) and UPDATE (2026-11-13, Steps 2-38): read `RESULTS_SUMMARY.md` (headline findings + addenda), `../ROADMAP.md`, `docs/LIMITATIONS.md`, `results/partA/INDEX.md`.
Done: Steps 2-17 (benchmark, freeze, locked test, real writers, HiSBreast, MedSAM Part B, final table), 18-22 (threshold crossing, routing and paired preference, tolerance-aware image check, robustness tests 21a-g, paper-support tables), 24 (box reliability curve), 25 (error-type coverage), 27 (LLM extractor `llm_finding_f1`), 28 (natural errors, inconclusive), 29 (label-free U-Net image check, position AUROC 0.89 pooled), 30 (severity breakdown), 31 (cross-dataset segmenter, 0.95 on held-out breast datasets), 32 (extractor v3, PROVISIONAL until a real independent human hand check of `docs/step32_check.csv`), 33 (edit-size law and the pre-registered fact x wording factorial: word scorers wording-driven, judge fact-driven), 34 (metamorphic checks), 35 (limit of detection), 36 (adversarial wording attack: pre-registered hypothesis not supported), 37 (RadGraph-F1 added: wording-driven; GREEN could not be run on a 16 GB Mac), 38 (responsible-AI checks on the image check). Numbering note: the earlier hybrid-evaluator pre-registration (`results/partA/step34_hybrid/PREREG.md`) was NOT run; the folders `step33_edit_size_law` and `step33_factorial` share the number 33.
Not run: Step 23 (replaced by 29), Step 26 (on hold, owner's instruction), the hybrid evaluator, GREEN (infeasible here), Claude judge, original RadFact, Jev, LLaVA-Med.
Open: real independent human hand check of `docs/step32_check.csv`; clinician review of severity and template sources; bilingual HiSBreast review; a real lesion detector (29 is a segmenter); patient-level splits for 5 datasets; FetalHead pixel size; repo visibility (owner sets it).
Standing rules for every new step: additions only (new files, new `INDEX.md` row, `CHANGELOG.md` entry, addendum in `RESULTS_SUMMARY.md`, numbered item in `docs/LIMITATIONS.md`, copy in `results/partA/summaries/`); frozen files (`FROZEN.md`) untouched; tune on dev/val, read the test split once via `usmeta.splits.load("test")` (logged); steps with hypotheses write `PREREG.md` and commit it before any test score; group bootstrap 1,000 resamples, seed 0; cells under 30 groups are "too small to compare"; judge and writer from different model families; no "first" claims; no tokens, HF cache, images or HiSBreast text/translations in git; never rewrite history; dataset licences stay "to confirm"; label VLM results "possible training exposure, unverifiable". Tags: `freeze-v1`, `final-v1` ... `final-v5` (owner decides when to tag; tags are not moved).

### Steps 31-38 in short (numbers copied from `results/partA/step3x/results.md`)

**Status in one line:** Step 28 (natural errors) is inconclusive; Step 31 is breast only; Step 32 is provisional until a real independent human hand check; GREEN was not run; the hybrid evaluator was not run. We found no ultrasound work that tests the scorers with planted errors, severity and harmless rewordings; search not exhaustive.

- **Step 31, cross-dataset segmenter (breast only).** Leave-one-dataset-out on BrEaST, BUS-BRA, BUSI, UDIAT and BUS-UCLM (138 held-out test scans): pooled position AUROC 0.95 (0.91-0.98) against 0.94 (0.90-0.97) for the in-dataset Step 29 model on the same scans. Per held-out dataset (30 scans each, every cell too small to compare): BrEaST 0.94, BUS-BRA 0.97, BUSI 0.87, UDIAT 1.00, BUS-UCLM 0.94. Thyroid and fetal head were not run.
- **Step 32, stricter extractor v3 (provisional).** The prompt-only change keeps templated field agreement at 0.9975 (dev) and 0.9986 (val). Replaying the Step 28 notes, invented fields (pathology, halo, count, composition) disappear, but 7 of the 10 breast / thyroid extractions marked right for v2 change under v3. On the same 180 reports the pooled wrong-vs-correct AUROC moves by at most 0.05 (llm_finding_f1 0.60). Provisional until a real independent human hand check of `docs/step32_check.csv`; the AI-assisted review (16 right / 14 wrong) is a second rater only.
- **Step 33, edit-size law and 2x2 factorial (fact x wording, pre-registered).** Edit size explains BLEU (R² 0.62) and ROUGE-L (R² 0.71) but not chrF (0.21), BERTScore (0.45), RaTEScore (0.01) or judge_score (0.35). In the factorial, variance share of fact vs wording is BLEU 0.02 vs 0.60, ROUGE-L 0.02 vs 0.41, chrF 0.04 vs 0.27, BERTScore 0.02 vs 0.41, RaTEScore 0.04 vs 0.17 (wording-driven), and judge_score 0.68 vs 0.01, finding_f1 0.26 vs 0.00 (fact-driven). An error with a small edit outranks a correct large rewrite in 76% of pairs for BLEU, ROUGE-L, chrF and BERTScore, 60% for RaTEScore, 4% for judge_score (judge subset: 71 groups).
- **Step 34, metamorphic checks.** Mean violation of the unit / order / synonym invariances (change > 0.05): BLEU 60%, ROUGE-L 48%, chrF 36%, RaTEScore 35%, judge_score 30% (subset), finding_f1 6%, BERTScore 5%, llm_finding_f1 5%. Failure to score a number swap or negation flip below a harmless synonym swap: ROUGE-L 93%, chrF 79%, BERTScore 64%, RaTEScore 60%, finding_f1 44%, BLEU 40%, llm_finding_f1 39%, judge_score 29%. The 41 HiSBreast texts (local only) give mostly too-small cells. The earlier hybrid-evaluator pre-registration (`step34_hybrid`) was not run.
- **Step 35, limit of detection.** Smallest error with AUROC >= 0.80 against matched synonyms: BLEU, ROUGE-L, chrF, BERTScore and RaTEScore never reach it (size errors up to x2, head-circumference shifts up to 20 mm); judge_score reaches it at 5% (size) and 1 mm (head circumference), on small judge cells; judge sentence_f1 25% (thyroid) to 100% (breast, % size); oracle-box MedSAM image check 25%; label-free U-Net check 50%; regex finding_f1 (upper bound) 5% and 1 mm.
- **Step 36, adversarial wording attack on the judge (pre-registered).** Hypothesis (a wording-only gain of at least 0.2) not supported: the winning transform (reorder) on 100 test wrong reports changed the judge score by -0.13 (-0.18 to -0.09) on average, 5% gained >= 0.2, and 6% overtook their correct counterpart (9% before). On dev / val all five transforms lowered the mean score (-0.10 to -0.21); single reports moved by up to +0.3 to +0.5.
- **Step 37, RadGraph-F1 added; GREEN not run.** RadGraph-F1 is wording-driven (fact 0.00 vs wording 0.17 on 17,444 blocks), never reaches AUROC 0.80, violates unit invariance on 100% and synonym invariance on 90% of templated items, and does not beat the judge. GREEN was not run: the official 13 GB checkpoint did not finish scoring two pairs in 36 minutes on the 16 GB machine; no GREEN number exists and nothing was substituted.
- **Step 38, responsible-AI checks on the image check.** Position AUROC per source dataset (30 scans each, too small to compare): TN5000 0.69, DDTI 0.77, BUSI 0.84, BrEaST 0.91, TN3K 0.93, BUS-UCLM 0.94, BUS-BRA 1.00, UDIAT 1.00; scanner identity exists in the files of BUS-BRA only (4 device codes). Abstaining on low U-Net confidence lowers the position-check error from 4.8% to 3.3% at 80% coverage and 2.2% at 60%, and mask failure (Dice < 0.5) from 12.1% to 3.8% and 1.7%. Noise, blur, JPEG and gamma shifts lower the position AUROC by at most 0.05 (clean 0.89, worst 0.84).

## PROGRESS (2026-10-23, older) - read before the old task list
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
