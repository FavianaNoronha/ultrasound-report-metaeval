# Part A results index

| step | date | commit | folder | headline |
|---|---|---|---|---|
| step2 | 2026-10-21 | 91fe031 | [step2_templates_v2](step2_templates_v2/) | 16,562 true reports (10 datasets), 3 styles each; all text numbers match facts |
| step3 | 2026-10-21 | 86bbde4 | [step3_bench_v2](step3_bench_v2/) | 27,193 candidates: 13,396 planted errors, 12,187 harmless, 1,610 identical |
| step4 | 2026-10-21 | 6d4e0ae | [step4_layer0](step4_layer0/) | All Layer 0 scorers below chance on BrEaST/BUS-BRA (AUROC 0.09-0.36); size errors AUROC ~0; lazy answer BERTScore 0.85 |
| step5 | 2026-10-22 | 0ae8d5d | [step5_harmless_split_layer0](step5_harmless_split_layer0/) | Style swaps drive AUROC to ~0.1 (vs large); vs small still <=0.5 on BrEaST/BUS-BRA: synonyms/reorder change 17-36% of tokens, errors 2-4% |
| step5 | 2026-10-23 | 57f8ec7 | [step5_harmless_split_layer0_rerun2](step5_harmless_split_layer0_rerun2/) | RERUN2 (adds 1-word synonym group, edit size matched): BLEU/ROUGE-L 0.58-0.92 vs matched synonym, chrF below chance (0.24 BrEaST), BERTScore ~chance; reason: Step 5 small group changed 5-10x more text than errors |
| step5 | 2026-10-23 | 4a019e7 | [step5_harmless_split_layer0_rerun3](step5_harmless_split_layer0_rerun3/) | RERUN3: BUS-BRA side="single" (253 images) was stated as a laterality; fixed in bench_v2d; BUS-BRA AUROC changes <=0.03, other datasets 0.00 |

_Notes:_ step2 and step3 outputs are superseded for BUS-BRA by step5 rerun3 (side='single' bug); use bench_v2d.jsonl / true_reports_v2d.jsonl from Step 6 on. Step 5 rerun2 added the matched one-word synonym group; reason: Step 5 'small' rewordings changed 5-10x more text than planted errors.
| step6 | 2026-10-23 | 9827cb0 | [step6_layer1_finding_f1](step6_layer1_finding_f1/) | finding_f1 AUROC 1.00 on all 10 datasets (upper bound: extractor = template, 99.99% field agreement); LLM extractor 98.5% fresh sample (82.9% before normalisation); legacy fact_checker fails identical-copy gate |
| step7 | 2026-10-23 | 9280de6 | [step7_layer2_sentence_check_gemma](step7_layer2_sentence_check_gemma/) | Gemma-2-9B sentence_check on 20 cases/dataset: AUROC vs matched synonym 0.95-1.00, vs harmless_small 0.68-1.00; category accuracy 0.80; identical-copy gate fails on UDIAT (0.93) |
| step7 | 2026-10-23 | 5468716 | [step7_layer2_sentence_check_gemma_rerun2](step7_layer2_sentence_check_gemma_rerun2/) | RERUN2 stricter prompt: identical copies 1.0 on all datasets (100/100), 0 unparseable; but AUROC vs harmless_small fell up to 0.30 (BUS-BRA 0.91->0.61, BUSI 0.99->0.66): judge is prompt-sensitive |
| step8 | 2026-10-23 | 0b0e161 | [step8_layer3_location_true_masks](step8_layer3_location_true_masks/) | Test 1 (true masks): grounded_check high on all error kinds on TN5000/HC18; mask_verified_facts 1.00 on text size/position errors but circular (same masks built the reference); text scorers 0.50 |
| step9 | 2026-10-23 | 64e4670 | [step9_combined_results](step9_combined_results/) | combined table: 14 scorers x 10 datasets, 4 layers, per-category AUROC, idea-borrowed-from column |
| step10a | 2026-10-24 | 3531221 | [step10a_dedupe](step10a_dedupe/) | no cross-benchmark duplicates; HC18 == Diverse Fetal Head (derived copy); within-dataset near-dups: BUSI 37%, FetalHead 9%, BUS-UCLM 6.6%, TN5000 5.6% -> STOP/ask |
| step10b | 2026-10-24 | 395c3cf | [step10b_splits](step10b_splits/) | splits 40/20/40 by group, 16,562 cases, near-dup clusters merged; test guard + log; 5 datasets have no group ids (image id stand-in) |
