# usmeta: do report graders catch clinical errors in ultrasound reports?

**Question.** Ultrasound report-generation papers grade reports with BLEU, ROUGE, BERTScore and similar. Do those
scores drop for a clinically important mistake and stay high for harmless rewording? Which graders do?

**Where the results are (read these first).** `RESULTS_SUMMARY.md` (plain-language findings, artefacts, unverified items, limits), `results_layers_all_final.md` (every scorer x every dataset, grouped by layer, test split, n and CIs; the old `results_layers_all.md` is the Step 9 version), `docs/LIMITATIONS.md`, and `results/partA/INDEX.md` (one folder per step, Steps 2-30). **The "Status of v0", "Stage 3 status" and "Part A status (2026-10-23)" tables further down are historical snapshots and are out of date; the current status is the table below and `../ROADMAP.md`.**

**What this is.** A meta-evaluation benchmark and harness. It builds (reference, candidate) pairs with *planted errors*
(with severity and magnitude) and *harmless rewordings*, runs any set of graders on them, and reports how well each
grader tells them apart. Organs: breast, thyroid, fetal.

## Current status (2026-11-13, Steps 2-38; details in `RESULTS_SUMMARY.md`)
| steps | what | state |
|---|---|---|
| 2-9 | templated true reports (10 datasets), planted-error benchmark, Layers 0-3, harmless split | done (reruns kept) |
| 10 | dedupe, locked splits, freeze (`freeze-v1`), test-split headline results, honesty labels | done |
| 11, 12, 14, 15 | Qwen and MedGemma reports, larger judge sample, HiSBreast real-text check | done (HiSBreast data stays local) |
| 16, 20, 24, 29 | image check: MedSAM with oracle boxes, tolerance-aware check, box-reliability curve, label-free U-Net | done: position AUROC 0.97 oracle boxes, 0.39-0.54 label-free boxes, 0.89 with the U-Net |
| 17, 19, 22 | final combined table, routing and paired preference, paper-support tables | done |
| 18, 21a-g, 25 | threshold crossing (exploratory), robustness tests, error-type coverage | done |
| 27 | LLM fact extractor `llm_finding_f1` (Qwen2.5-7B) | done: 0.99-1.00 on templated text; free text only 56% right on breast and thyroid (hand check) |
| 28 | natural errors from a real writer (60 images per organ) | done, inconclusive (noisy labels, fetal head not checkable, thyroid 5 wrong reports) |
| 30 | severity breakdown from saved scores | done (severity is our provisional label) |
| 31 | cross-dataset segmenter (breast, leave-one-dataset-out) | done: pooled position AUROC 0.95 on held-out datasets vs 0.94 in-dataset |
| 32 | extractor v3 (stricter free-text prompt) | done; hand-checked (13 of 30 right on free text, not validated; `docs/step32_check_filled.csv`) |
| 33 | edit-size law (BLEU R² 0.62, ROUGE-L 0.71) and 2x2 factorial fact x wording (pre-registered) | done: word scorers wording-driven, judge and finding_f1 fact-driven |
| 34 | metamorphic checks (the earlier hybrid-evaluator pre-registration in `step34_hybrid/` was NOT run) | done |
| 35 | limit of detection | done: word scorers never reach AUROC 0.80; judge at 5% / 1 mm |
| 36 | adversarial wording attack on the judge (pre-registered) | done: hypothesis not supported |
| 37 | RadGraph-F1 added to Steps 33-35; GREEN attempted | RadGraph-F1 done (wording-driven); GREEN not feasible on this 16 GB machine |
| 38 | responsible-AI checks on the image check (per-dataset gaps, abstention, corruptions) | done |
| 23, 26 | lesion detector (replaced by 29); Step 26 | not run (23 replaced, 26 on hold at the owner's instruction) |
| open | clinician review of severity and templates, bilingual HiSBreast review, a real detector, a better free-text extractor, patient-level splits, GREEN / Claude judge / Jev / LLaVA-Med | see `../ROADMAP.md` |

Tests: `PYTHONPATH=. python3 -m pytest -q tests` (73 pass). Steps 24-38 modules: `usmeta/step24_*.py` ... `usmeta/step38_*.py` (each also copied into its results folder); heavy local files (models, caches, HiSBreast scores) are git-ignored.

### Steps 31-38 in short

**Status in one line:** Step 28 (natural errors) is inconclusive; Step 31 is breast only; Step 32 v3 was hand-checked and is not validated on free text (13 of 30 right); GREEN was not run; the hybrid evaluator was not run. We found no ultrasound work that tests the scorers with planted errors, severity and harmless rewordings; search not exhaustive.

- **Step 31, cross-dataset segmenter (breast only).** Leave-one-dataset-out on BrEaST, BUS-BRA, BUSI, UDIAT and BUS-UCLM (138 held-out test scans): pooled position AUROC 0.95 (0.91-0.98) against 0.94 (0.90-0.97) for the in-dataset Step 29 model on the same scans. Per held-out dataset (30 scans each, every cell too small to compare): BrEaST 0.94, BUS-BRA 0.97, BUSI 0.87, UDIAT 1.00, BUS-UCLM 0.94. Thyroid and fetal head were not run.
- **Step 32, stricter extractor v3 (hand-checked; not validated on free text).** The prompt-only change keeps templated field agreement at 0.9975 (dev) and 0.9986 (val). Replaying the Step 28 notes, invented fields (pathology, halo, count, composition) disappear, but 7 of the 10 breast / thyroid extractions marked right for v2 change under v3. On the same 180 reports the pooled wrong-vs-correct AUROC moves by at most 0.05 (llm_finding_f1 0.60). Provisional until a real independent human hand check of `docs/step32_check.csv`; the AI-assisted review (16 right / 14 wrong) is a second rater only. Hand check (14 Nov 2026; one non-clinician reviewer, no AI tool verified either way): 13 of 30 free-text reports right (fetal 6/6, all empties; breast 7/12; thyroid 0/12); 9 of the 17 errors are BI-RADS written as tirads on thyroid reports. v3 is NOT validated on free text; Step 28 stays inconclusive. File: `docs/step32_check_filled.csv`.
- **Step 33, edit-size law and 2x2 factorial (fact x wording, pre-registered).** Edit size explains BLEU (R² 0.62) and ROUGE-L (R² 0.71) but not chrF (0.21), BERTScore (0.45), RaTEScore (0.01) or judge_score (0.35). In the factorial, variance share of fact vs wording is BLEU 0.02 vs 0.60, ROUGE-L 0.02 vs 0.41, chrF 0.04 vs 0.27, BERTScore 0.02 vs 0.41, RaTEScore 0.04 vs 0.17 (wording-driven), and judge_score 0.68 vs 0.01, finding_f1 0.26 vs 0.00 (fact-driven). An error with a small edit outranks a correct large rewrite in 76% of pairs for BLEU, ROUGE-L, chrF and BERTScore, 60% for RaTEScore, 4% for judge_score (judge subset: 71 groups).
- **Step 34, metamorphic checks.** Mean violation of the unit / order / synonym invariances (change > 0.05): BLEU 60%, ROUGE-L 48%, chrF 36%, RaTEScore 35%, judge_score 30% (subset), finding_f1 6%, BERTScore 5%, llm_finding_f1 5%. Failure to score a number swap or negation flip below a harmless synonym swap: ROUGE-L 93%, chrF 79%, BERTScore 64%, RaTEScore 60%, finding_f1 44%, BLEU 40%, llm_finding_f1 39%, judge_score 29%. The 41 HiSBreast texts (local only) give mostly too-small cells. The earlier hybrid-evaluator pre-registration (`step34_hybrid`) was not run.
- **Step 35, limit of detection.** Smallest error with AUROC >= 0.80 against matched synonyms: BLEU, ROUGE-L, chrF, BERTScore and RaTEScore never reach it (size errors up to x2, head-circumference shifts up to 20 mm); judge_score reaches it at 5% (size) and 1 mm (head circumference), on small judge cells; judge sentence_f1 25% (thyroid) to 100% (breast, % size); oracle-box MedSAM image check 25%; label-free U-Net check 50%; regex finding_f1 (upper bound) 5% and 1 mm.
- **Step 36, adversarial wording attack on the judge (pre-registered).** Hypothesis (a wording-only gain of at least 0.2) not supported: the winning transform (reorder) on 100 test wrong reports changed the judge score by -0.13 (-0.18 to -0.09) on average, 5% gained >= 0.2, and 6% overtook their correct counterpart (9% before). On dev / val all five transforms lowered the mean score (-0.10 to -0.21); single reports moved by up to +0.3 to +0.5.
- **Step 37, RadGraph-F1 added; GREEN not run.** RadGraph-F1 is wording-driven (fact 0.00 vs wording 0.17 on 17,444 blocks), never reaches AUROC 0.80, violates unit invariance on 100% and synonym invariance on 90% of templated items, and does not beat the judge. GREEN was not run: the official 13 GB checkpoint did not finish scoring two pairs in 36 minutes on the 16 GB machine; no GREEN number exists and nothing was substituted.
- **Step 38, responsible-AI checks on the image check.** Position AUROC per source dataset (30 scans each, too small to compare): TN5000 0.69, DDTI 0.77, BUSI 0.84, BrEaST 0.91, TN3K 0.93, BUS-UCLM 0.94, BUS-BRA 1.00, UDIAT 1.00; scanner identity exists in the files of BUS-BRA only (4 device codes). Abstaining on low U-Net confidence lowers the position-check error from 4.8% to 3.3% at 80% coverage and 2.2% at 60%, and mask failure (Dice < 0.5) from 12.1% to 3.8% and 1.7%. Noise, blur, JPEG and gamma shifts lower the position AUROC by at most 0.05 (clean 0.89, worst 0.84).

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

## Part A status (ground truth v2, Layers 0-3 on bench_v2d), as of 2026-10-23
Everything below lives in `results/partA/` (see `results/partA/INDEX.md`; combined table: `results_layers_all_final.md`; Step 9 version `results_layers_all.md`).
| piece | state |
|---|---|
| true reports from record facts (`templates_v2.py`, 10 datasets, 3 styles) | done, tested; template sources "to confirm" (`docs/templates_sources.md`) |
| `bench_v2d.jsonl` (planted errors with category + provisional severity, harmless groups small / matched / large) | done; BUS-BRA side="single" bug fixed (rerun3) |
| Layer 0: BLEU, ROUGE-L, chrF, BERTScore, RaTEScore | done: below chance vs style swaps; 0.2-0.9 vs matched one-word synonym; size errors unseen |
| Layer 1: `finding_f1` (schema.py) | done: AUROC 1.00 on all datasets (upper bound: extractor = template, 99.99% field agreement); LLM extractor 98.5% on a fresh templated sample |
| Layer 2: Gemma-2-9B `sentence_check` (RadFact protocol, own prompt) | done on 20 cases per dataset; two prompts, identical copies 1.0 with the stricter one; prompt-sensitive |
| Layer 3: location / size check against TRUE masks | done (Test 1); circular for text built from the same masks; SAM/MedSAM not run |
| GREEN | **not run**: 7B model too large for 16 GB |
| Claude judge, original RadFact | **not run** |
| clinician-confirmed severity | **not done** |
| real VLM reports on bench_v2d, MedGemma, LLaVA-Med | **not done** (MedGemma access pending; BrEaST images now on the Mac) |
Datasets: images are not in git; see `../datasets/README.md` (manifest, hashes, licences "to confirm").

**Read `docs/LIMITATIONS.md` before quoting any number.** Final numbers = the locked test split (`usmeta.splits.load("test")`, access logged in `results/partA/test_access.log`); tuning uses dev and val only; frozen versions in `FROZEN.md` / `CHANGELOG.md` (tag `freeze-v1`).
