# End-to-end review of 21 related papers (2026-11-27)

## Coverage (honest)
| # | Paper | Read |
|---|---|---|
| 1 | PathReportEval / CRQS (2607.18448) | full (earlier) |
| 2 | ReEvalMed (2510.00280) | full |
| 3 | RadEval (2509.18030) | full |
| 4 | VERT (2604.03376) | full main text + appendix prompts and modality tables |
| 5 | CRIMSON (2603.06183) | full |
| 6 | Beyond Scalar Scores (2606.18797) | full main text; appendices skimmed by heading only |
| 7 | RadOT-Eval (2606.08769) | full main text; appendices not read |
| 8 | BUSTR (2511.20956) | full main text incl. results, discussion, limitations |
| 9 | ReXErr (2409.10829) | full incl. appendices |
| 10 | GREEN (2405.03595) | full incl. appendices (figures as captions) |
| 11 | VLScore (2410.17357) | full |
| 12 | ICARE (2508.02808) | full incl. appendix |
| 13 | RadMatch (2609.01470) | main text; appendices (prompts, costs) NOT read |
| 14 | ReportQA (2606.15037) | main text + appendices A-E; some knowledge-tree figures not read |
| 15 | RadQC-Bench (MICCAI 2026 wksp) | full |
| 16 | BreastViT + ChatGPT (BMC MIDM 2026) | full |
| 17 | Breast US LLM benchmark (Diagnostics 2026) | methods + results; Discussion/Limitations NOT available (page truncated, PDF unreadable) |
| 18 | LLM TI-RADS (Front Endocrinol 2025) | full |
| 19 | FetUSAgents (2605.25357) | full |
| 20 | FetalMind (2510.12953) | full |
| 21 | FETAL-GAUGE (2512.22278) | full |
| 22 | Role-adapted biometry reports (ClinicalNLP 2026) | full |
| -- | ThyroidXAgent (2608.12590) | NOT READ (arXiv rate limit twice); only a third-party summary seen. Do not cite details until read. |
| -- | UltraReporter (Sci Rep 2026) | NOT READ (page error) |
Papers 9-22 were read through a web reader that paraphrases; numbers were cross-checked where two sources existed.

## Comparison matrix
| Paper | Modality | Evaluates scorers? | Human labels | Planted errors | Harmless-rewording test | Operating point / workload | Image used | Stats |
|---|---|---|---|---|---|---|---|---|
| ReEvalMed | CXR | yes | clinician-reviewed pairs | yes (LLM rewrite) | yes (robustness) | no | no | none |
| RadEval | CXR | yes | radiologist error counts | no | no | no | no | block bootstrap |
| VERT | CXR + 9 modalities (US n=76) | yes (LLM judges) | expert scores/counts | yes (GPT-4.1 omission/false finding) | no | no | no | paired bootstrap |
| CRIMSON | CXR | new metric | radiologists (ReXVal, RadPref) | curated pass/fail cases | partly (paraphrase category) | no | no | CIs |
| Beyond Scalar | CXR (ReEvalMed) | yes | clinician check of 400 synthetic pairs | yes | yes (D/R) | maximin threshold | no | bootstrap |
| RadOT-Eval | CXR | new metric | radiologist counts | ReXErr stress | no | AUROC, sens@spec | no | bootstrap, frozen external test |
| GREEN | CXR (+US in training) | new metric | ReXVal, preferences | no | no | no | no | CI on tau |
| VLScore | CXR | new metric | ReXVal | manual edits (removal, location, severity) | normal-report pairs | no | YES (embedding) | none |
| ICARE | CXR | new metric | clinician question/preference studies | word deletion | no | no | no | seed SD |
| RadMatch | CXR | new metric | radiologist counts | no | no | triage P/R only | no | clustered bootstrap |
| ReportQA | CXR, CT | new metric | RadEvalX | negative questions | no | no | no | none |
| ReXErr | CXR | dataset | 1 clinician, 83/100 plausible | yes | no | no | no | none |
| RadQC-Bench | CXR | VLM repair | 100-output human check | yes (5 types incl. typo control) | unaltered controls | no | yes (VLM input) | none |
| BUSTR | breast US (BrEaST, BUS-BRA) | no (generator) | none | no | no | no | yes (generator) | fold t-tests |
| BreastViT | breast US | no (generator) | 3 radiologists Likert | no | no | no | yes | Friedman, ICC |
| Breast US LLM bench | breast US (real Chinese reports) | LLMs on error detection | 2 seniors + adjudication | real QC errors | no | no | no | paired bootstrap |
| TI-RADS LLM | thyroid text | LLM classification | sonologists, histology | no | no | no | no | AUC CIs |
| FetUSAgents | fetal US | no (system) | 2 sonographers + LLM judge | no | no | no | yes (HC from mask) | none |
| FetalMind | fetal US | no (generator) | experts (realism) | swap edits for training | no | no | yes | none |
| FETAL-GAUGE | fetal US | VLM VQA | labels | no | no | no | yes | none |
| Role-adapted biometry | fetal biometry | no (system) | none | no | no | no | no | unit tests |
| **Ours (Step 47/48)** | **breast, thyroid, fetal US** | **yes** | **none yet (planned 50-100)** | **yes (schema + off-schema)** | **yes** | **yes (miss-rate bound + workload)** | **planned (U-Net, Step 49)** | **pre-registered, group bootstrap, CP bounds** |

## What the full reads changed or confirmed
1. GREEN checkpoint confirmed by RadOT-Eval: StanfordAIMI/GREEN-RadLlama2-7b via the green_score wrapper. GREEN's own paper reports internal inconsistencies (RadGraph tau 0.47 vs 0.57) -> quote table values only.
2. BUSTR uses BrEaST and BUS-BRA (two of our breast sources) and states that descriptor-recovery metrics "do not capture unsupported statements outside the predefined descriptor set" -> direct support for our off-schema (fabricated finding) test.
3. RadMatch: single-call LLM baselines matched the structured pipeline in correlation -> we must report a single-call judge baseline (we have the Step 46 holistic judge; report it beside S2).
4. ReXErr: 17% of synthetic errors implausible to a clinician; RadQC-Bench uses a change log plus automatic validation -> our gold filter is the validation; a clinician plausibility check of a sample of planted errors (incl. fabrications) is the missing piece.
5. Role-adapted biometry: deterministic decision layer caught the only LLM factual error (macrosomia report mentioning growth restriction) -> same lesson as our rules-first design; also negation-aware checks and boundary unit tests.
6. FetUSAgents: HC from segmentation ellipse used to ground reports; LLM judge given a reference written by the same model family (self-preference risk) -> Step 49 U-Net HC check is feasible and has prior art on the generation side; we use different judge and writer families (Gemma/Llama judges, Mistral/Phi writers).
7. Breast US LLM benchmark: on real report error detection, senior physicians 0.75 vs best LLM groups ~0.41-0.43 accuracy -> LLM judges alone are weak at error detection in ultrasound reports, consistent with routing to humans rather than replacing them.
8. VLScore needs an image-text model trained on the modality (LIMITR, CXR) and a domain constant -> none exists for ultrasound, which is why a segmentation-based check is the practical image route for us.
9. RadQC-Bench typo control class and unaltered controls; ReportQA negative questions -> our normal-statement controls play this role; a typo control could be added in Step 49.
10. Nobody among the 21 reports a pre-registered operating point with a miss-rate bound and workload; RadOT-Eval and RadMatch come closest (sens@spec, triage P/R).
