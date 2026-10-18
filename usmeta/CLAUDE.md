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

## TASKS FOR CLAUDE CODE (in order)
1. `pip install -r requirements.txt bert-score`, then run `bash run_stage2.sh`
   (100 cases per dataset; BERTScore roberta-large, RaTEScore, GREEN). The RaTEScore and GREEN wrappers have never run:
   read the errors and fix them in `usmeta/graders.py`. Add a test for each fix.
2. LLM judge across several models. Add a backend that calls the `claude` CLI (uses my login, no API key), selectable by model,
   and run it with `bash run_stage2.sh judge`. Also verify `usmeta/inspect_task.py` end to end with `inspect eval`
   (never verified; the sandbox blocked a tiktoken download). Compare judges in one results table.
3. Realistic reports: generate reports from real scans with an open vision-language model (MedGemma, Qwen2.5-VL, LLaVA-Med),
   then check what real mistakes look like vs our planted ones.
4. Replace the oracle image check (`evidence_check` uses dataset labels) with a real one: a segmentation model or a VLM.
5. Add BUSI and UDIAT; add BERTScore for thyroid and fetal.
6. Severity levels are our own provisional guesses: prepare a short sample for a clinician to confirm.
7. After each stage, regenerate `results_*.md` and tell me the headline numbers; I will update the team slides.

## Rules
- Do not overwrite `bench_v1.jsonl`, `scores_v1.json` or raw data; write new files beside them.
- Every claim needs a number from a results file. Keep the limitations visible: templated reports, provisional severity, oracle image check.
- Keep answers short and plain; I am learning evaluation as I go, so explain new terms in one line.
