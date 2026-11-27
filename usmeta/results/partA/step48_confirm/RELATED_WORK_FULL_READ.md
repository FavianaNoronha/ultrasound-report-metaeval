# Full read of the 2025-26 report-evaluation papers (2026-11-27)

All read in full text (VERT, CRIMSON, Beyond Scalar Scores, RadOT-Eval, BUSTR) except reference lists; ReEvalMed and RadEval read earlier.

| Paper | Data | What they found that matters to us | Their limitation we address |
|---|---|---|---|
| ReEvalMed (Li 2025) | CXR, 400 pairs, clinician-reviewed rewrites | metrics either catch errors or tolerate rewording, not both | CXR only, no stats, no operating point |
| RadEval (Xu 2025) | CXR 208 studies, radiologist error counts | GREEN best (tau 0.18); location/severity errors not tracked by any metric | CXR; ultrasound only as GREEN training data |
| VERT (Bologna 2026) | RadEval + RaTE-Eval (9 modalities; US n=76, tau 0.43) | direct score prompt beats GREEN; judges miscount omissions; small open models (Qwen3-4B) fail; reasoning effort does not help; list image-grounded evaluation as future work | report-level correlation only; no planted-error safety test; no ultrasound-specific analysis |
| CRIMSON (Baharoon 2026) | CXR; ReXVal 50, RadJudge 30, RadPref 100 | severity-weighted errors align best with radiologists (Weighted E tau 0.78); measurement errors significant only past clinical thresholds (nodule <6 mm: >2 mm; >=6 mm: >4 mm) | rubric is CXR-specific; authors say other modalities need new severity criteria |
| Beyond Scalar Scores (Lu 2026) | ReEvalMed | "discrimination bias": LLM judges D >= 94% but R often < 60%; two-pass prompting moves errors between D and R, does not remove them; CRIMSON best score metric (D 75 / R 80.5); maximin threshold for scalar metrics; clinician checked 400 synthetic pairs (93% valid) | CXR only; no operating point / miss-rate bound |
| RadOT-Eval (Liu 2026) | ReXVal select, RadEvalX frozen test, ReXErr-v1 stress | structured clinical units + alignment beat GREEN; shortcut control (reference-count only) shows insignificant-error prediction is mostly report complexity; paired win rate of corrupted vs clean 99%; robustness to 10/25% unit dropout | CXR; 100-pair test, wide CIs |
| BUSTR (Mohammed 2026) | breast US: BrEaST, BUS-BRA | public breast US sets have descriptors but no radiologist reports; they build descriptor-derived (template-like) references; evaluate by descriptor recovery | no factuality, size accuracy or reader study |

## Methods from these papers we can apply (analysis only, no new model calls unless stated)
1. D/R with maximin threshold (Lu; ReEvalMed): report discrimination and robustness for every scorer, scalar ones at their maximin threshold.
2. Shortcut controls (RadOT-Eval): length-only and number-of-facts-only baselines; check S2 harmless routes are not explained by report length or complexity.
3. Paired win rate (RadOT-Eval): for each planted twin vs its clean reports of the same case, share where the scorer rates the twin worse.
4. Extractor-failure robustness (RadOT-Eval unit dropout): randomly drop 10% / 25% of extracted fields, re-score, report the fall in catch rate.
5. Error-type breakdown (VERT, RadEval): catch rate by planted error type (wrong value, wrong category, missing finding, wrong number), since judges miss omissions.
6. Judge-alone vs rules+judge D/R (Lu's discrimination bias): show the judge alone has the bias and the rules-first routing removes most of it.
7. Clinician validation of the benchmark, not of every report (Lu: 400-pair review): a radiologist checks a sample of planted errors (is it clinically significant as labelled?) and harmless rewordings (is it truly harmless?). Feasible size: 50-100 pairs.
8. Clinically grounded size thresholds (CRIMSON): replace the fixed 5% / 1 mm limit-of-detection framing with organ guideline thresholds (e.g. TI-RADS size cut-offs, HC centile shift) for deciding when a size error matters. Changes the scorer: Step 49, not Step 48.
9. Image-grounded check (VERT future work; BUSTR masks): our U-Net check is the gap nobody has filled. Step 49.
10. Small fine-tuned judge (Lu, CRIMSON, VERT): train a 4-8B judge on our synthetic pairs to cut harmless routing. Later.

---
# Wider search (2026-11-27): papers found and read (via web; some long pages only partly verbatim, marked *)

| Paper | Modality | Relevance |
|---|---|---|
| ReXErr (Rao et al., PSB 2025, arXiv 2409.10829) | CXR | GPT-4o injects 12 clinically meaningful error types (chosen with 3 radiologists), 3 errors/report; clinician found 83/100 plausible. No metric tested. Prior art for planted errors. |
| VLScore, "Image-aware Evaluation of Generated Medical Reports" (Dawidowicz et al., NeurIPS 2024) | CXR | IMAGE-AWARE metric (image + both reports embedded with LIMITR; triangle area). ReXVal tau 0.718; perturbation tests (removed pathology, location change). Prior art for image-grounded evaluation: our U-Net check is NOT the first image-aware evaluation; difference: explicit segmentation-based position/size check, ultrasound. |
| GREEN (Ostmeier et al., EMNLP Findings 2024) | CXR (+ US in training notes) | GREEN = matched / (matched + significant errors a-f). ReXVal tau 0.63; base model RadLLaMA-2 7B; ~3.75 s/sample on A100; OOD needs fine-tuning. HF checkpoint ID to confirm on stanford-aimi.github.io/green.html. |
| ICARE (Dua et al., 2025) | CXR | two-agent MCQ evaluation; robustness to word deletion; no ultrasound. |
| RadMatch (2026, arXiv 2609.01470)* | CXR | LLM finding extraction + matching, deterministic comparators for measurements/status (closest hybrid to ours); |tau| ~0.58 on RadEvalExpert; no operating point or workload. |
| ReportQA (2026, arXiv 2606.15037) | CXR, CT | QA-based; RadEvalX Pearson 0.45 vs GREEN 0.42; no ultrasound. |
| RadQC-Bench (MICCAI 2026 workshop) | CXR | 10,362 pairs with LLM-planted omission, fabrication, laterality, severity/measurement, typos; VLMs repair <= 43%. Prior art for planted laterality/measurement errors. |
| ThyroidXAgent (arXiv 2608.12590)* | thyroid US | generates thyroid US reports; proposes ThyClinScore (lesion-level) checked only against an LLM judge (r 0.696), not humans. A prior thyroid-US report metric. |
| BreastViT + ChatGPT (BMC MIDM 2026) | breast US | report generation; BLEU/ROUGE/BERTScore + 3-radiologist Likert (ICC 0.88). No metric validation. |
| Breast US report processing benchmark (Cheng et al., Diagnostics 2026) | breast US (Chinese) | 44 LLMs on text tasks incl. error detection and findings-impression inconsistency in 1,173 real reports, physician gold. Closest real-report ultrasound error-detection work; not a scorer meta-evaluation, no planted errors. |
| FetUSAgents (arXiv 2605.25357)* | fetal US | multi-agent report generation; HC/AC from segmentation ellipse + WHO chart consistency check feeding the report. Prior art for image-measurement grounding (generation side). |
| FetalMind (arXiv 2510.12953)*, FETAL-GAUGE (2512.22278), role-adapted biometry reports (ClinicalNLP 2026) | fetal US | generation/VQA; evaluation by BLEU/accuracy; no metric meta-evaluation. |
| LLM thyroid TI-RADS (Front. Endocrinol. 2025) | thyroid text | LLM risk classification from text; not report evaluation. |

## Updated novelty position
- Not found anywhere: a meta-evaluation of report SCORERS on ultrasound reports (planted errors + harmless rewording), pre-registered, with a miss-rate bound and workload. Still our main claim.
- Must cite and NOT claim: planted-error benchmarks (ReXErr, RadQC-Bench, ReEvalMed); image-aware evaluation (VLScore); image-measurement grounding of fetal reports (FetUSAgents); hybrid LLM extraction + deterministic comparators (RadMatch); thyroid-US report metric (ThyClinScore); real breast-US report error detection (Cheng et al.).
- U-Net check claim narrowed to: first explicit segmentation-based position/size check inside an ultrasound report scorer, tested against planted errors (to verify again before writing).
