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

## extractor v2 (2026-10-26): `usmeta/schema_v2.py` (post-processing only; `schema.py` v1 stays frozen)
Why: Step 11 showed two failures of the free-text LLM extractor. (1) The model returned 106 for "10.6 mm" (dropped decimal) -> numbers are now re-read from the model's own quote when the quote holds a number with a unit (mm / cm / %). (2) Option lists copied from the prompt ("solid|cystic") were kept as values -> dropped and counted. (3) JSON booleans for `lesion` map to present / absent. The prompt is unchanged, so cached model replies are reused. Old results with v1 are kept (`step11_qwen_real_reports`). Evaluation: `results/partA/step11b_extractor_v2/`.
