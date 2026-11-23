# Rerun audit

Reviewed 2026-11-21 after the request to rerun work that did not run cleanly.

## Resume: computationally incomplete Step 46 work

- Llama Set B core true/twin reports and the dev/val transfer sample are generated. The limit-of-detection plan has 472 items; the first generation run hit its 5.5-hour cap after 322. The missing 150 were resumed from the existing generation cache on 2026-11-21; all 472 are now generated.
- The v5 extractor was interrupted before it wrote `extraction_v5.json`. Its append-only raw-response cache contained 600 completed calls; extraction restarted after LOD generation and reuses those cached outputs.
- Re-run the gold/filter assembly after missing LOD items are generated, then finish extraction, judging, scoring, and the report. Keep the original Step 46 preregistration and thresholds fixed.

## Completed results: preserve, do not repeat on the same locked test

- Step 45 D initially hit a cap, then resumed and completed 349/350 paired test cases after a retry; the remaining unparsable response is excluded and the preregistered verdict is **DOES NOT PASS**. Repeating the same test does not fix its low detection rate.
- Step 45 F initially hit a cap, then resumed and completed all 629 planned test pairs; it **passes on Set A writer-made text**, with the limitations stated in its report.
- Step 45 G completed its held-out test once and **does not pass** the preregistered AUROC rule. Re-training/re-scoring against the same test would compromise the locked evaluation; a new-seed/model study needs a new preregistration and untouched holdout.
- Step 43 extractor v4 completed its fresh-report check and **does not pass**. Repeating the same 20 reports would not provide independent validation.
- Step 42 GREEN (4-bit) ran the 40 units selected by its preregistered dev-timing rule. Its small sample is an acknowledged limitation, not an accidental truncation; adding units after seeing the first test results would violate that rule.

## Inconclusive or intentionally superseded work

- Step 28 remains inconclusive because the labels relied on a free-text extractor that failed independent checks. A meaningful rerun needs clinician-verified reference labels or another independently validated annotation process.
- Step 23 was replaced by Step 29 segmentation. Step 26 was held and its general idea was later examined in Step 39. The old Step 34 hybrid preregistration was superseded by later designs; Step 45 F and Step 46 cover the hybrid direction more directly.
- Full-precision GREEN could not run on the 16 GB Mac; the preregistered 4-bit Colab version is the available result. Other intentionally unrun items are listed in the main `ROADMAP.md`.

The only action being resumed from this audit is Step 46's missing LOD generation and its downstream extraction/evaluation. The completed negative results remain reported as results, not converted into reruns.

## Final reconciliation (2026-11-23)

- Completed v5 extraction for all 1,771 kept core, LOD, stress and human reports. The earlier extraction table had omitted 376 test-only LOD reports; the extraction builder now includes them.
- Fixed split filtering for LOD candidates, restricted H6 to the 29 true human rewrites with unique IDs, and prevented duplicate judge calls within a run.
- Fixed Set A threshold tuning to load `step45_improve_scorers/freetext/set_A.json` explicitly. The saved threshold is 0.4, chosen on 281 harmless / 120 error Set A dev-val rows (4.6% harmless flagged there).
- The final test comparison scores 861 core reports in 235 groups. The 376 LOD rows are scored separately. Set B test monitor results are 18.1% error catch and 16.3% harmless flagged. The rule-clear Gemma subset contains 632 harmless reports and no errors, so its AUROC is not estimable.
- Scoring and report generation completed from saved artifacts; the Step 46 test split was not read again. Duplicate legacy judge rows were reduced to 875 unique relevant rows before reporting.
