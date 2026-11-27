# Related work: ReEvalMed (Li et al., arXiv 2510.00280v1, 30 Sep 2025)

Read in full (15 pages) on 2026-11-26.

## What they did
- Meta-evaluation of report metrics for chest X-ray (MIMIC-CXR: 50 reports; ReXVal: 20 reports).
- Clinically grounded criteria co-developed with clinicians: location, severity, description, negation, modality, size/distance, comparison/progression, internal contradiction, uncertainty, terminology; plus metric capabilities: discrimination, robustness (grammatical noise, stylistic variation), monotonicity.
- DeepSeek-R1 7B rewrote each ground-truth report changing one aspect, giving clinically significant or insignificant errors (omission, fabrication, inaccuracy). 400 GT-rewrite pairs, reviewed by clinicians with written explanations.
- Discriminative Score = mean metric score on significant-error pairs (lower is better); Robustness Score = mean on insignificant pairs (higher is better); monotonicity on 5 severity groups of 4 reports each.
- Metrics: BLEU, ROUGE-L, METEOR, BERTScore, AlignScore, RaTEScore, CheXbert-F1, RadGraph-F1, GREEN.
- Findings: no metric is good at both; BERTScore is robust but does not penalize significant errors; GREEN discriminates best but over-penalizes harmless variation; all metrics fail when a single localized significant error follows a larger harmless rewrite, and on internal contradictions.
- Stated limitations: chest X-ray only, manual verification limits scale, interpretability not assessed. No significance tests by design.

## Overlap with our project
The core design is the same idea: planted clinically significant errors against harmless rewrites, scoring metrics on discrimination and robustness, with a severity ladder. We must not claim this design as new, and must cite ReEvalMed as the closest prior work.

## What differs (claims we can still make, carefully)
1. Ultrasound (breast, thyroid, fetal head) from 10 public datasets, not chest X-ray.
2. Scale and statistics: thousands of report pairs, group bootstrap CIs, pre-registration, edit-size-matched controls and a fact-by-wording factorial.
3. A limit-of-detection test (5% size, 1 mm head circumference).
4. An operational routing scorer (S1) judged by a safety target (miss rate of major errors with a Clopper-Pearson bound) and workload, plus judge-dependence and quote-validity tests.
5. CRQS (pathology) adapted and tested.

## Where ReEvalMed is stronger
- Clinician-reviewed pairs with explanations; ours have no clinician validation.
- Broader aspects: uncertainty, internal contradiction, comparison/progression, modality and terminology are not planted in our benchmark.

## Consistent findings
BERTScore tolerant of rewording but weak at catching significant errors (ours: worst catch rate at the same workload). LLM-based metrics catch more but are less stable (ours: judge flips, workload depends on the judge).

---
# Related work: RadEval (Xu et al., arXiv 2509.18030v1, 22 Sep 2025)

Read in full (12 pages) on 2026-11-26.

- Unified open-source toolkit: BLEU, ROUGE, BERTScore, F1CheXbert, F1RadGraph, RaTEScore, SRR-BERT, TemporalEntityF1, RadCliQ, GREEN (extended to several modalities incl. ultrasound via a Gemma-2B fine-tune on ~50k pairs), plus RadEvalBERTScore (ModernBERT, SimCSE).
- Meta-evaluation: expert set of 208 chest X-ray studies (148 findings, 60 impressions), 3 AI-written candidates each, radiologist counts of significant/insignificant errors. Kendall tau-b against error counts, block bootstrap CIs.
- Results: GREEN best (tau -0.183), then SRR-BERT, RadCliQ; ROUGE, RadGraph, BLEU not significant; CheXbert wrong sign. No metric tracks insignificant errors. Per-category: only omissions and (grammar) are clearly tracked; wrong location, wrong severity, spurious comparison not significant.
- Not implemented: LLM-API metrics (CheXprompt, FineRadScore, RadFact).
- Limits: chest X-ray, English, US. Ultrasound appears only as GREEN training data, not as an evaluated benchmark.

## Overlap / difference
- Closest in spirit to our metric comparison (same family of scorers, bootstrap CIs, error-count agreement). Real radiologist labels, which we lack.
- Different: correlation with human error counts on real model outputs, not controlled planted-error twins; no routing/safety target; no ultrasound evaluation; no pre-registration; no limit-of-detection test.
- Use: cite as the toolkit and human-label benchmark; consider running RadEval's GREEN as an extra comparator if time allows (not pre-registered, so report as exploratory).
- Reinforces our finding that BLEU/ROUGE/BERTScore are weak on location/severity errors.

---
# Batch of five more papers (read first 3 pages of each on 2026-11-26; abstract, intro, method start only. Full read still to do before we cite details.)

1. VERT (Bologna, Corbeil, Wilkens, Abacha; arXiv 2604.03376v2, 14 Oct 2026): "Towards Better Aligned LLM Judges for Radiology Report Evaluation across Modalities and Anatomies". Systematic study of LLM judges on RadEval (CXR, 148 studies) and RaTE-Eval (9 modalities, 22 anatomies, paragraph-level expert scores 0-5). Compares RadFact, GREEN, FineRadScore, CRIMSON; proposes VERT (direct-score prompt). GREEN most robust of existing; VERT up to +26% Kendall over GREEN; ensembling +9.9%, fine-tuning Qwen3-30B +25% with 37x lower latency; error-injection analysis shows judges miscount omissions. Correlation with expert scores, not a planted-error twin design; no routing/safety target.
2. CRIMSON (Baharoon et al.; arXiv 2603.06183v2, 16 Mar 2026): context-aware (age, indication), severity-weighted LLM metric for CXR; error taxonomy (false, missing, 8 attribute errors); validated on ReXVal (Kendall 0.61-0.71) plus new RadJudge pass/fail cases and RadPref (100+ pairs, 3 cardiothoracic radiologists). Closest to our severity-weighting idea (we use field weights from rules; theirs from an LLM and clinical guideline).
3. Beyond Scalar Scores (Lu et al.; arXiv 2606.18797v1, 17 Jun 2026): tests 8 LLM judges and 11 score metrics on ReEvalMed; finds "discrimination bias": LLMs catch errors but over-penalise harmless rephrasings; trains Qwen3-8B / MedGemma-4B on 4k synthetic pairs (12 ReEvalMed aspects), 78.5% discrimination / 70.5% robustness. Matches our finding that LLM judges route too many harmless reports (Gemma 21.8%, Llama 60.7%). Two-pass prompting trades discrimination for robustness, similar to our order-swap/prompt-reword disagreement.
4. RadOT-Eval (Liu et al., Vanderbilt; arXiv 2606.08769v1, 7 Jun 2026): extract attribute-structured clinical units (Llama-3.3-70B), align by optimal transport, monotone risk readout; Spearman 0.715/0.548/0.399 on RadEvalX; ReXErr-v1 synthetic corruption test AUROC 0.768. Closest to our extract-then-compare design; CXR only; no safety bound, no pre-registration.
5. BUSTR (Mohammed, Attin, Gewali, Shareef, UNLV; arXiv 2511.20956v2, 20 Jul 2026): breast ultrasound report generation from structured descriptors, masks and radiomics; datasets BrEaST and BUS-BRA; descriptor-derived (template-like) reference reports because paired radiologist reports are scarce. Evaluated with NLG and descriptor-recovery metrics, no metric meta-evaluation. Relevance: confirms that public breast US sets lack paired reports, supports our template-built references; potential source of model outputs to test on.

Still unidentified: "Zou et al. 2026" (two uploads were the wrong paper).

## Effect on our novelty claim
- Planted/harmless-pair design: ReEvalMed + Lu et al. + RadOT-Eval (ReXErr). Not new.
- LLM-judge over-penalisation of harmless rewording: Lu et al. Not new; our contribution is measuring it as workload in an audit-and-route setting, on ultrasound.
- Extract-then-compare structured scoring: RadOT-Eval, CRIMSON, CLEAR. Not new; ours differs by deterministic rule checks (units, size, HC) plus routing.
- Still ours (to be re-checked after full reads): ultrasound multi-organ, pre-registered, limit-of-detection tests, miss-rate bound with workload, judge-dependence and quote-validity analysis.
- Comparator candidates (exploratory only, not pre-registered): GREEN, CRIMSON, VERT prompt. Ultrasound coverage in RaTE-Eval via VERT is the only prior LLM-judge evaluation touching ultrasound; check page details.
