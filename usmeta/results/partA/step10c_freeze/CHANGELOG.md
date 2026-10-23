# CHANGELOG (usmeta, Part A)

Rule: after `freeze-v1`, any change to a frozen item is a new version listed here with what changed and why; old versions and their results are kept.

## freeze-v1 (2026-10-24)
Frozen: templates_v2, schema + extractors, benchmark builders (bench_v2 / v2b / loc), scorers and settings, judge prompts v1 and v2, splits (dev 40 / val 20 / test 40, grouped), threshold rule. See `FROZEN.md`.

## Before the freeze (all kept in `results/partA/INDEX.md`)
- Step 4 headline retracted as an artefact: "Layer 0 below chance" mostly reflected edit size (harmless rewordings change 5-10x more text than a planted error). See step5 and step5 rerun2.
- Step 5 rerun2: added the matched one-word synonym group (`synonym1`), bench_v2c.
- Step 5 rerun3: BUS-BRA `Side = single` was written as "single breast"; fixed in bench_v2d / true_reports_v2d (other datasets unchanged).
- Step 6: `schema._norm_llm` and the position prompt wording changed after a first LLM-extractor run scored 82.9% (below the 85% stop rule); validated on a fresh sample (98.5%).
- Step 7 rerun2: judge prompt v1 -> v2 (stricter) so identical copies score 1.0; AUROC moved by up to 0.30 (prompt sensitivity).
- Step 8: thyroid count capped at 3 in `mask_verified`; `box_support_gtbox` added next to `box_support`.
- Step 10a: no cross-dataset duplicates; within-dataset near-duplicate clusters grouped (none dropped).
