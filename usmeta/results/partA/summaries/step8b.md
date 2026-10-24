# Step 8b: borrowed evaluation ideas (thresholds on val, numbers on the locked test split)

Limitations: [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md). Frozen code was not edited (new files `step8b.py`, `step8b_run.py`, `repeat_judge.py`). Thresholds use val only (dev + val for the judge, see below); numbers are on test via `usmeta.splits.load("test")`. Prior work being extended to ultrasound, **not claimed as ours**: ReEvalMed "Beyond Scalar Scores" (arXiv 2606.18797, chest X-ray: discrimination / robustness), "Can Jev Judge Radiology Reports?" (arXiv 2609.27607, chest X-ray: repeatability, calibration), breast ultrasound report auditing (J Digit Imaging 2026, doi 10.1007/s10278-026-02163-z: false-alarm rate, report- vs error-level sensitivity, physician baseline). See `related_work.md`.

## Discrimination, robustness and false alarms at a fixed threshold
**Definitions.** A scorer *flags* a candidate when its score is at or below a cut-off. The cut-off is the one that flags 90% of planted errors on the val split (frozen threshold rule). **D** = % of test planted errors flagged. **R** = % of test harmless candidates NOT flagged (split into harmless_small, the matched one-word synonym, and harmless_large). **False-alarm rate** = % of error-free test candidates (identical copies + all three kinds of harmless) flagged.

**Headline (test, per dataset; full tables below).**
- **Word-overlap and embedding scorers cannot be set to catch errors without flagging nearly everything harmless.** At 90% error recall, BERTScore flags the planted errors (D 0.89-0.92) but R is 0% on BrEaST, BUS-BRA, TN5000 and HC18 (it flags every harmless rewriting too); false-alarm rate 88-92%. BLEU: D 0.93-1.00 with R 0-50% (BrEaST 0%, BUS-BRA 0-33%, TN5000 0-50%); false alarms 62-92%. RaTEScore: cut-off 1.000 on three datasets (it scores many errors at exactly 1.0), D 0.89-1.00, R 0-43%, false alarms 68-100%.
- **`finding_f1` (upper bound under templated text):** D 0.85-1.00, R 100% on all three harmless kinds, false-alarm rate 0%.
- **Gemma judge (`sentence_f1`, prompt_v2):** cut-offs come from the dev-era judge run restricted to dev and val cases (13-34 val errors per dataset: small). **On BUSI, DDTI and UDIAT the 90% cut-off is 1.000 (at least 10% of val errors get a perfect `sentence_f1`), so it flags everything (false alarm 100%, R 0%): a judge that lists an error but leaves `sentence_f1` at 1.0 cannot be thresholded.** Elsewhere: BUS-BRA D 0.84, R vs small 0.64, false alarms 0.12; BUS-UCLM D 0.97, R vs small 0.84; BrEaST D 0.82, R vs small 0.52, R vs large 0.12, false alarms 0.44; TN3K D 0.98, R vs small 1.00, vs large 0.64; TN5000 D 1.00, R vs large 0.36; HC18 D 1.00, R vs small 0.72, vs large 0.56; FetalHead D 1.00, R vs small 0.67.
- **Report-level vs error-level sensitivity (sentence_check, cases with two planted errors):** a report is "caught" far more often than each error: e.g. BrEaST any error flagged in 100% of cases but each error in 82% and both in 62%; FetalHead, TN5000: 100% / 100% / 100%. See table.

## Repeatability (judge)
5 runs, same settings (greedy decoding, prompt_v2), uncached, on 20 test pairs per organ (60 pairs; **the brief asked for 100 cases per organ, which needs about 4 hours, so this is a reduced check**): **0 of 60 pairs changed in any run** (0 verdict flips; median Kendall tau between runs 1.00 for breast, thyroid and fetal). Greedy decoding on one machine is deterministic, so this says the judge is repeatable under these settings, not that it would be under sampling or on another device. It does not measure prompt sensitivity (see Step 7).

## Calibration
Not applicable: the Gemma judge returns no probabilities and `sentence_f1` / `finding_f1` are not probabilities, so ECE, Brier score and isotonic calibration were not computed. (The cut-off rule above is the calibration we use.)

## Cost and speed (Apple M3, 16 GB, local models; no API cost)
| scorer | seconds per 100 report pairs |
|---|---|
| BLEU / ROUGE-L / chrF | under 0.1 (CPU) |
| `finding_f1` (rule extractor) | under 1 (CPU) |
| BERTScore roberta-large (MPS) | 0.9 (101.8 s for 11,582 pairs) |
| RaTEScore (MPS) | 5.8 (668 s for 11,582 pairs) |
| Gemma-2-9B `sentence_check` (MLX, prompt_v2) | about 590 (109 minutes for 1,116 pairs) |
| Gemma-2-9B LLM extractor (free text) | about 2,000 (20-25 s per report) |
API judges: none run, so no token cost.

## Not done here, and why
- **Jev (paid API, TypeSafe AI): not called. Needs your approval first** (cost, which key, how many pairs). If approved the key would be read from an environment variable only and the one-question support format of arXiv 2609.27607 used, labelled "Jev, following the protocol of arXiv 2609.27607".
- **VLScore (arXiv 2410.17357) not added.** Verified from the arXiv page: "Image-aware Evaluation of Generated Medical Reports", Dawidowicz, Hirsch, Tal (NeurIPS 2024), a chest X-ray metric that compares image, reference and generated report embeddings; **no public code was found** (arXiv page and a web search), and its image-text embedding is X-ray-specific, so it cannot run on ultrasound and our no-X-ray-trained-scorers rule applies. Cited as related work only.
- Clinician agreement: placeholder. When clinician severity labels or error counts arrive, add Kendall tau between each scorer and the clinician, and (if ~50 candidates are reviewed blind) the clinician's sensitivity and false-alarm rate next to the best scorer.
- D/R for Layer 3 (true masks) was not computed (circular by construction).

**Caveats.** Templated reports; provisional severity; template sources "to confirm"; per dataset only; the judge cut-offs rest on 13-34 val errors; group ids missing for BUSI, UDIAT, TN3K, TN5000, HC18.

---

## Test tables: Layers 0 and 1 (cut-offs from val)

**BUS-BRA**

| scorer | cut-off (from val) | D: errors flagged | R vs small | R vs matched | R vs large | false-alarm rate (identical + harmless_small / matched / large flagged) |
|---|---|---|---|---|---|---|
| bleu | 0.941 | 95% | 0% | 33% | 0% | 75% |
| rougeL | 0.971 | 100% | 0% | 0% | 0% | 88% |
| chrf | 0.977 | 91% | 0% | 0% | 0% | 88% |
| bertscore[roberta-large] | 0.999 | 90% | 0% | 0% | 0% | 88% |
| ratescore | 1.000 | 89% | 33% | 43% | 0% | 68% |
| finding_f1 | 0.889 | 93% | 100% | 100% | 100% | 0% |

**BUS-UCLM**

| scorer | cut-off (from val) | D: errors flagged | R vs small | R vs matched | R vs large | false-alarm rate (identical + harmless_small / matched / large flagged) |
|---|---|---|---|---|---|---|
| bleu | 0.926 | 89% | 17% | 25% | 0% | 74% |
| rougeL | 0.958 | 93% | 0% | 7% | 0% | 83% |
| chrf | 0.959 | 86% | 17% | 3% | 0% | 78% |
| bertscore[roberta-large] | 0.998 | 81% | 0% | 0% | 0% | 84% |
| ratescore | 0.946 | 86% | 81% | 74% | 48% | 28% |
| finding_f1 | 0.833 | 94% | 100% | 100% | 100% | 0% |

**BUSI**

| scorer | cut-off (from val) | D: errors flagged | R vs small | R vs matched | R vs large | false-alarm rate (identical + harmless_small / matched / large flagged) |
|---|---|---|---|---|---|---|
| bleu | 0.940 | 100% | 41% | 1% | 0% | 73% |
| rougeL | 0.958 | 98% | 0% | 2% | 0% | 85% |
| chrf | 0.959 | 88% | 42% | 1% | 0% | 73% |
| bertscore[roberta-large] | 0.999 | 93% | 0% | 0% | 0% | 85% |
| ratescore | 1.000 | 91% | 38% | 43% | 0% | 66% |
| finding_f1 | 0.833 | 90% | 100% | 100% | 100% | 0% |

**BrEaST**

| scorer | cut-off (from val) | D: errors flagged | R vs small | R vs matched | R vs large | false-alarm rate (identical + harmless_small / matched / large flagged) |
|---|---|---|---|---|---|---|
| bleu | 0.965 | 93% | 0% | 0% | 0% | 92% |
| rougeL | 0.978 | 83% | 0% | 21% | 0% | 81% |
| chrf | 0.986 | 91% | 0% | 0% | 0% | 92% |
| bertscore[roberta-large] | 0.999 | 92% | 0% | 0% | 0% | 92% |
| ratescore | 1.000 | 94% | 7% | 7% | 0% | 93% |
| finding_f1 | 0.923 | 85% | 100% | 100% | 100% | 0% |

**DDTI**

| scorer | cut-off (from val) | D: errors flagged | R vs small | R vs matched | R vs large | false-alarm rate (identical + harmless_small / matched / large flagged) |
|---|---|---|---|---|---|---|
| bleu | 0.961 | 93% | 0% | 2% | 0% | 88% |
| rougeL | 0.973 | 93% | 0% | 9% | 0% | 85% |
| chrf | 0.989 | 91% | 0% | 0% | 0% | 89% |
| bertscore[roberta-large] | 0.999 | 90% | 0% | 6% | 0% | 86% |
| ratescore | 1.000 | 88% | 11% | 12% | 0% | 89% |
| finding_f1 | 0.909 | 98% | 100% | 100% | 100% | 0% |

**FetalHead**

| scorer | cut-off (from val) | D: errors flagged | R vs small | R vs matched | R vs large | false-alarm rate (identical + harmless_small / matched / large flagged) |
|---|---|---|---|---|---|---|
| bleu | 0.791 | 100% | 33% | 50% | 0% | 63% |
| rougeL | 0.900 | 100% | 0% | 0% | 1% | 87% |
| chrf | 0.951 | 93% | 33% | 0% | 0% | 75% |
| bertscore[roberta-large] | 0.997 | 89% | 0% | 0% | 0% | 87% |
| ratescore | 0.981 | 93% | 34% | 0% | 0% | 75% |
| finding_f1 | 0.925 | 100% | 100% | 100% | 100% | 0% |

**HC18**

| scorer | cut-off (from val) | D: errors flagged | R vs small | R vs matched | R vs large | false-alarm rate (identical + harmless_small / matched / large flagged) |
|---|---|---|---|---|---|---|
| bleu | 0.595 | 100% | 33% | 50% | 0% | 62% |
| rougeL | 0.857 | 100% | 0% | 0% | 0% | 88% |
| chrf | 0.889 | 100% | 33% | 0% | 0% | 75% |
| bertscore[roberta-large] | 0.997 | 92% | 0% | 0% | 0% | 88% |
| ratescore | 0.956 | 89% | 34% | 1% | 0% | 75% |
| finding_f1 | 0.850 | 100% | 100% | 100% | 100% | 0% |

**TN3K**

| scorer | cut-off (from val) | D: errors flagged | R vs small | R vs matched | R vs large | false-alarm rate (identical + harmless_small / matched / large flagged) |
|---|---|---|---|---|---|---|
| bleu | 0.899 | 100% | 50% | 34% | 0% | 62% |
| rougeL | 0.957 | 100% | 0% | 1% | 0% | 87% |
| chrf | 0.955 | 93% | 50% | 0% | 0% | 75% |
| bertscore[roberta-large] | 0.998 | 90% | 0% | 0% | 0% | 88% |
| ratescore | 1.000 | 96% | 5% | 2% | 0% | 97% |
| finding_f1 | 0.805 | 90% | 100% | 100% | 100% | 0% |

**TN5000**

| scorer | cut-off (from val) | D: errors flagged | R vs small | R vs matched | R vs large | false-alarm rate (identical + harmless_small / matched / large flagged) |
|---|---|---|---|---|---|---|
| bleu | 0.899 | 100% | 50% | 33% | 0% | 62% |
| rougeL | 0.957 | 100% | 0% | 0% | 0% | 88% |
| chrf | 0.961 | 89% | 50% | 0% | 0% | 75% |
| bertscore[roberta-large] | 0.998 | 89% | 0% | 0% | 0% | 88% |
| ratescore | 1.000 | 100% | 1% | 0% | 0% | 100% |
| finding_f1 | 0.800 | 92% | 100% | 100% | 100% | 0% |

**UDIAT**

| scorer | cut-off (from val) | D: errors flagged | R vs small | R vs matched | R vs large | false-alarm rate (identical + harmless_small / matched / large flagged) |
|---|---|---|---|---|---|---|
| bleu | 0.947 | 100% | 0% | 0% | 0% | 86% |
| rougeL | 0.962 | 100% | 0% | 0% | 0% | 86% |
| chrf | 0.968 | 92% | 0% | 0% | 0% | 86% |
| bertscore[roberta-large] | 0.999 | 93% | 0% | 0% | 0% | 86% |
| ratescore | 1.000 | 90% | 48% | 48% | 0% | 59% |
| finding_f1 | 0.857 | 92% | 100% | 100% | 100% | 0% |


## Test tables: Gemma judge (cut-offs from dev+val rows of the dev-era judge run; applied to the 25-case test sample)

**BUS-BRA**

| scorer | cut-off (from val) | D: errors flagged | R vs small | R vs matched | R vs large | false-alarm rate (identical + harmless_small / matched / large flagged) |
|---|---|---|---|---|---|---|
| sentence_f1 | 0.889 | 84% | 64% | 100% | 100% | 12% |
| judge_score | 0.800 | 100% | 64% | 100% | 100% | 12% |

**BUS-UCLM**

| scorer | cut-off (from val) | D: errors flagged | R vs small | R vs matched | R vs large | false-alarm rate (identical + harmless_small / matched / large flagged) |
|---|---|---|---|---|---|---|
| sentence_f1 | 0.840 | 97% | 84% | 100% | 100% | 5% |
| judge_score | 0.460 | 90% | 100% | 100% | 100% | 0% |

**BUSI**

| scorer | cut-off (from val) | D: errors flagged | R vs small | R vs matched | R vs large | false-alarm rate (identical + harmless_small / matched / large flagged) |
|---|---|---|---|---|---|---|
| sentence_f1 | 1.000 | 100% | 0% | 0% | 0% | 100% |
| judge_score | 0.700 | 87% | 100% | 100% | 96% | 1% |

**BrEaST**

| scorer | cut-off (from val) | D: errors flagged | R vs small | R vs matched | R vs large | false-alarm rate (identical + harmless_small / matched / large flagged) |
|---|---|---|---|---|---|---|
| sentence_f1 | 0.978 | 82% | 52% | 100% | 12% | 44% |
| judge_score | 0.700 | 96% | 80% | 100% | 28% | 29% |

**DDTI**

| scorer | cut-off (from val) | D: errors flagged | R vs small | R vs matched | R vs large | false-alarm rate (identical + harmless_small / matched / large flagged) |
|---|---|---|---|---|---|---|
| sentence_f1 | 1.000 | 100% | 0% | 0% | 0% | 100% |
| judge_score | 0.700 | 94% | 84% | 100% | 68% | 15% |

**FetalHead**

| scorer | cut-off (from val) | D: errors flagged | R vs small | R vs matched | R vs large | false-alarm rate (identical + harmless_small / matched / large flagged) |
|---|---|---|---|---|---|---|
| sentence_f1 | 0.667 | 100% | 67% | 100% | 100% | 10% |
| judge_score | 0.900 | 100% | 67% | 100% | 100% | 10% |

**HC18**

| scorer | cut-off (from val) | D: errors flagged | R vs small | R vs matched | R vs large | false-alarm rate (identical + harmless_small / matched / large flagged) |
|---|---|---|---|---|---|---|
| sentence_f1 | 0.667 | 100% | 72% | 100% | 56% | 23% |
| judge_score | 0.700 | 100% | 72% | 100% | 56% | 23% |

**TN3K**

| scorer | cut-off (from val) | D: errors flagged | R vs small | R vs matched | R vs large | false-alarm rate (identical + harmless_small / matched / large flagged) |
|---|---|---|---|---|---|---|
| sentence_f1 | 0.667 | 98% | 100% | 100% | 64% | 12% |
| judge_score | 0.400 | 90% | 100% | 100% | 100% | 0% |

**TN5000**

| scorer | cut-off (from val) | D: errors flagged | R vs small | R vs matched | R vs large | false-alarm rate (identical + harmless_small / matched / large flagged) |
|---|---|---|---|---|---|---|
| sentence_f1 | 0.667 | 100% | 100% | 100% | 36% | 21% |
| judge_score | 0.400 | 88% | 100% | 100% | 100% | 0% |

**UDIAT**

| scorer | cut-off (from val) | D: errors flagged | R vs small | R vs matched | R vs large | false-alarm rate (identical + harmless_small / matched / large flagged) |
|---|---|---|---|---|---|---|
| sentence_f1 | 1.000 | 100% | 0% | 0% | 0% | 100% |
| judge_score | 0.750 | 92% | 36% | 100% | 68% | 31% |


## Report-level vs error-level sensitivity (sentence_f1, test sample)

| dataset | cases with 2 planted errors | report-level: any error flagged | error-level: each error flagged | report-level: both flagged |
|---|---|---|---|---|
| BrEaST | 24 | 100% | 82% | 62% |
| FetalHead | 24 | 100% | 100% | 100% |
| TN5000 | 25 | 100% | 100% | 100% |
| BUS-BRA | 25 | 100% | 84% | 68% |
| UDIAT | 25 | 100% | 100% | 100% |
| DDTI | 25 | 100% | 100% | 100% |
| TN3K | 25 | 100% | 98% | 96% |
| BUS-UCLM | 6 | 100% | 97% | 83% |
| BUSI | 20 | 100% | 100% | 100% |
