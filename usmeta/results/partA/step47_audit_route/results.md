# Step 47 results: audit-and-route scorer on fresh model-written reports (Set C)

Pre-registration: PREREG.md, PREREG_AMENDMENT.md, PREREG_AMENDMENT_2.md, PREREG_AMENDMENT_3.md; deviations in DEVIATIONS.md. Thresholds (91ea3053…) and the Stage 1 winner S1 (17ff9879…) were frozen and committed before Set C existed. Set C: 653 fresh cases written by Mistral-7B-Instruct-v0.3 (4-bit); 1,770 core reports scored (506 groups). Extractor hand check: 50 reports, 227 fields, 227 correct (one reviewer). All numbers: model-written free text, no clinician validation.

## Eligibility
Only 293 planted major/critical errors survived filtering (pre-registered minimum: 400), because the datasets had only 111 unused fetal and 252 unused thyroid cases. As pre-registered, every pass/fail hypothesis is therefore **NOT ELIGIBLE** and is reported descriptively below. The numbers are not reinterpreted as passes.

## Primary variant S1 (Stage 1 winner)
| | Result | Pre-registered criterion (descriptive only) |
|---|---|---|
| Major/critical errors missed | 0 of 293 (Clopper-Pearson upper 95%: 1.02%) | upper bound <= 2%: met |
| All planted errors routed | 422 of 422 | — |
| Harmless reports routed to a radiologist | 19.5% | <= 30%: met |
| H2 vs CRQS (same routing budget) | difference 0.000 (CI 0.000 to 0.000) | must exceed CRQS: not met (tie) |
| H2 vs word scorers | BERTScore +0.71, BLEU +0.48, ROUGE-L +0.42, chrF +0.39, RaTEScore +0.36, Step 45 learned +0.24; all CIs exclude 0 | met |
| Every routed report has a reason | yes | — |

Route reasons (a report can have several; "unparsed judge reply" is also attached to the 205 rule-major reports where the judge is deliberately not called, so the real count is 333): unparsed judge reply 538, rule difference 523, judge major claim 218, rule-major fields (count 73, head circumference 75, lesion 51, pathology 46, BI-RADS 9, calcification 5, margin 1), order-swap disagreement 29, judge unsure 21, prompt-reword disagreement 17.

## Other variants and hypotheses
- V3 (original primary): 1 of 293 major/critical errors missed (upper 1.61%), harmless routed 38.6% (above 30%). V4 (no unsure route): caught only 44.5% of errors.
- H3, rule-only V1 AUROC: 0.972 (0.964–0.980); breast 0.967, thyroid 0.954, fetal 1.000. Criterion >= 0.90 met; not eligible.
- H4, limit of detection: 5% size change AUROC 0.955 (0.900–1.000), criterion met; 1 mm head circumference only 29 groups, too small to compare.
- H5, quote validity: every routed report has a reason, but only 17.9% of routed reports had all judge quotes exact (1,593 invalid quotes). FAILS as written: the Gemma judge rarely quotes word for word.
- H6, Set R (30 real Qwen-VL reports, extraction-faithfulness labels only): V3 routed all 30. Descriptive.
- H7, CRQS vs rule-only: Set C CRQS AUROC 0.993 vs V1 0.972 (Set B: 0.998 vs 0.990). The CRQS ceiling holds on new-writer text; the gap widened by 0.013.
- H8: V5 (concept merging) and V6 (no zero floor) were identical to V1 (difference 0.000).
- H9, second judge (300-report subset): under S1, Gemma routes 21.8% of harmless reports and Llama-3.1-8B routes 60.7%; both catch every error; the two judges route 35% of reports differently. Under V3: Gemma 40.6%, Llama 91.7%. S1's low workload depends on the judge.
- Paper-exact CRQS gave the same routing as the CRQS-style adaptation on this set.

## What this means
1. Rules plus the fact extractor do most of the work: they and CRQS catch every planted error. The audit judge adds reasons but not detection on this benchmark.
2. S1 is safe on this benchmark (no major error auto-passed) and sends about 1 in 5 harmless reports for review, but the workload depends on which LLM judges (Llama: 3 in 5).
3. LLM judges are unreliable as evidence sources here: their quotes are rarely exact, and 116 of the 263 harmless reports S1 routed (44%) were routed only because a Gemma reply could not be parsed. A better parser is the cheapest way to cut the workload, and must be tested on new data.
4. Word-overlap scorers (BLEU, ROUGE-L, chrF, BERTScore) and RaTEScore are far worse at catching errors at the same workload.

## Limitations
Model-written text only; planted errors only; one reviewer for the hand check; set smaller than pre-registered; S1 chosen on 293 dev reports; no clinician review; CRQS adapted from pathology.
