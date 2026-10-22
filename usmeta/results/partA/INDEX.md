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
