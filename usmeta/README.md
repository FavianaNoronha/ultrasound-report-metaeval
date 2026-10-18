# usmeta: do report graders catch clinical errors in ultrasound reports?

**Question.** Ultrasound report-generation papers grade reports with BLEU, ROUGE, BERTScore and similar. Do those
scores drop for a clinically important mistake and stay high for harmless rewording? Which graders do?

**What this is.** A meta-evaluation benchmark and harness. It builds (reference, candidate) pairs with *planted errors*
(with severity and magnitude) and *harmless rewordings*, runs any set of graders on them, and reports how well each
grader tells them apart. Organs: breast, thyroid, fetal.

## Pipeline

```
 DATA            REPORTS                         GRADERS (pluggable)              META-EVALUATION
 labels, masks → reference (from labels)    →   L0 bleu rougeL chrf bertscore  →  discrimination AUROC
 BrEaST          candidates:                    L1 fact_checker fact_f1            robustness (harmless mean)
 TN3K, UltraG      planted errors (+severity)   L2 llm_judge (Inspect), ratescore, severity / magnitude Spearman
 HC18              harmless rewordings             green, judge_mock               per organ / severity / perturbation
                   (later: VLM-written reports) L3 evidence_check (oracle → image)
```

## Status of v0 (be honest about this)
| piece | state |
|---|---|
| templates, error injection, severity, magnitude (3 organs) | done, tested |
| bleu, rougeL, chrf, fact_checker, fact_f1, evidence_check | done, tested |
| bertscore (roberta-large) | **run** on a 5,654-pair sample (100 cases/dataset, `bench_small.jsonl`): AUROC 0.01, harmless mean 0.96 (`results_stage2.md`) |
| llm_judge (claude CLI backend `claude_judge:<model>`), Inspect task | backend written + unit-tested with a fake runner; **not run live** (CLI returned "Credit balance is too low"); Inspect end-to-end **not** verified |
| ratescore | **run** on the same 5,654-pair sample (CPU): AUROC 0.15, harmless mean 0.76 |
| green | **not run**: 7B model too large for 16 GB (and `green-score` does not install on Python 3.9) |
| severity levels | **provisional**, author-assigned; need clinician confirmation |
| reports | **templated from labels**, as in BUSTR; no real clinician-written report text exists in these datasets |
| fact_checker / evidence_check | rule-based, built on our own wording, so on templated text they are an **upper bound**, not evidence about free text |
| evidence_check | uses dataset annotations as evidence (oracle). Real image check = replace evidence with facts recovered from the image |

## Run
```
pip install -r requirements.txt
python -m usmeta.run build --breast breast.xlsx --thyroid-records tn3k_records.json \
    --ultrag-thyroid-jsonl thyroid_grounded_full_v1.jsonl --hc18 training_set_pixel_size_and_HC.csv --n 500 --out bench.jsonl
python -m usmeta.run grade  --bench bench.jsonl --graders bleu,rougeL,chrf,fact_checker,evidence_check --out scores.json
python -m usmeta.run report --bench bench.jsonl --scores scores.json --out results
# optional graders: bertscore:roberta-large, ratescore, green, llm_judge (set USMETA_JUDGE, USMETA_JUDGE_MODEL)
# Inspect: inspect eval usmeta/inspect_task.py --model anthropic/<model-id> -T bench=bench.jsonl
```

## Item fields
`organ, dataset, case_id, image, kind (error|harmless|identical), perturbation, magnitude, severity (1 minor, 2 major,
3 critical, provisional), reference, candidate, evidence`.

## Metrics
- **Discrimination AUROC**: P(score(error) < score(harmless rewording of the same case)). 1 perfect, 0.5 chance, 0 inverted. Bootstrapped over cases.
- **Robustness**: mean score of harmless rewordings (ideal 1.0). Identical copy must be 1.0 (sanity).
- **Severity ρ**: Spearman(severity, score) over errors. Strongly negative is good.
- **Magnitude ρ**: within one perturbation, Spearman(error size, score): BI-RADS steps, mm.

## Prior work checked (search window about Oct 2025 to Oct 2026; not exhaustive)
- U2-Bench (arXiv 2505.17779): 7,241 ultrasound cases, 15 regions, 23 LVLMs; report generation scored with BLEU-4, ROUGE, BERTScore; no metric validation.
- UltraG-Bench (arXiv 2609.30928, Sep 2026): 40 datasets; report generation scored with ROUGE-L and SemAcc (presence, category, location, size vs masks); references written by an LLM; no metric validation.
- BUSTR (arXiv 2511.20956): breast report generator trained on label-built reports.
- Chest X-ray metric work: GREEN, RaTEScore, RadGraph-F1, CRIMSON (2603.06183), RadMatch (2609.01470), and ReEvalMed with "Beyond Scalar Scores" (2606.18797), which tests discrimination vs robustness for LLM judges on chest X-ray reports.
- Not found: an ultrasound benchmark that tests the *graders* with planted errors, severity and harmless rewordings.

## Stage 3 status (real reports from vision-language models)
| piece | state |
|---|---|
| report writer `usmeta/generate.py` | Qwen2.5-VL-3B **running** (50 scans x BUS-BRA, TN5000, TN3K, HC18; ~30 s/scan on Apple GPU); MedGemma-4B **not started** (waits for Qwen); LLaVA-Med **not started** |
| BrEaST | **no images, not evaluated** (only the label spreadsheet is available) |
| UltraG thyroid | no images, skipped |
| free-text extractor `usmeta/freetext.py` | local Gemma-2-9B-it 4-bit (MLX); agreement with rule-based extractor 0.976 and 1.0 on two 20-report samples |
| judge/extractor for Qwen reports | local Gemma-family model; for MedGemma reports a Qwen-family model (never the same family as the writer) |
| thyroid grading | diagnosis field **left out** (TN3K/TN5000 class 0/1 meaning unconfirmed); count, location, size only |
| Claude judge | **not run** (claude CLI: "Credit balance is too low") |
| GREEN | **not run**: 7B model too large for 16 GB |
| contamination | BUSI, BUS-BRA, TN3K, TN5000, HC18 are **possibly seen in training**; cannot be ruled out. BUS-BRA is the least-bad option, still flagged |
