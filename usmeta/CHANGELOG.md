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

## extractor v2.1 (2026-10-27): optional `prompt` argument in `schema_v2.extract_llm_v2`
Why: Qwen2.5-7B (used for MedGemma's reports because a Gemma model must not grade Gemma-family output) ignored the "{value, quote}" object format and returned bare values for 57 of 122 reports, so those parsed as "no facts". For a non-Gemma extractor `usmeta/medgemma.py` passes `QWEN_PROMPT` (the frozen prompt plus a format reminder and one example). Default behaviour (Gemma extractor, `prompt=None`) is unchanged; Step 11 results are not affected. The first Qwen2.5-7B extraction (failed format) is kept as `extract_medgemma_v2_first_attempt.jsonl`.

## judge prompt variants v1q / v2q for non-Gemma judges (2026-10-27)
Why: Qwen2.5-7B (MedGemma's reports must not be judged by a Gemma model) copied the candidate's list length for both true/false lists in 85 of 102 (prompt_v1) and 100 of 102 (prompt_v2) test pairs. `v1q` / `v2q` = the frozen `prompt_v1` / `prompt_v2` text unchanged plus one final line stating the exact number of reference and candidate sentences. The Gemma judge (Qwen reports) keeps the frozen prompts. The first Qwen2.5-7B judge run is kept as `judge_medgemma_v{1,2}.jsonl`.

## extractor v2.2 (2026-10-27): `quote_match` option in `schema_v2.extract_llm_v2`
Why: with the Qwen2.5-7B extractor (non-Gemma, for MedGemma's reports) the frozen rule "the quote must appear verbatim in the report" dropped 69 values over 122 reports because that model shortens or paraphrases its quotes; the dev/val proxy was 30/39 = 76.9% (below the 85% stop rule). `quote_match='tokens80'` accepts a quote when at least 80% of its words occur in the report (3 values dropped on the 20 dev/val reports, proxy 35/39 = 89.7%; tuned on those same 20 reports, so optimistic; approved by the owner). Default stays `'exact'`, so all earlier results (Gemma extractor) are unchanged. The exact-rule extraction is kept as `extract_medgemma_v2_exactquote.jsonl`.

## Step 19a–19c (2026-11-02): additions only, nothing frozen changed
New files only: `usmeta/step19_pairs.py`, `step19_pairs_md.py`, `step19_boxsweep.py`; `datasets/MANIFEST_TABLE.md` (+ `!MANIFEST_TABLE.md` in `datasets/.gitignore`). `bench_v2d`, scorers, splits and judge prompts untouched.
- 19a uses SAVED scores only. Deviations from a literal reading of the brief: (i) the judge has no per-dataset val scores (the dev-era 20-case judge sample leaves 201 rows in the new val split), so its cut-off is pooled over all val datasets and labelled; (ii) harmless set = small + matched + large rewordings (as in Step 19 routing); (iii) the val cut-off is the 90th percentile of planted-error scores with flag = score ≤ cut-off; (iv) the held-out transfer table covers the text scorers only.
- 19b: 1,728 new MedSAM masks (6 degraded-box conditions × 288 scans), cached in the git-ignored `local_data/partb_sweep`. The exact-box condition reuses the Step 16 masks and reproduces its numbers. The pooled breast+thyroid mask IoU in 19b is over the 198 scans with true masks (TN5000 has boxes only and is reported as box IoU per dataset).
- 19c: file placed at `datasets/MANIFEST_TABLE.md` (the repo's existing `datasets/` folder), not `usmeta/datasets/`. URLs, licences and citations are "to confirm"; nothing was guessed.
- Step 18 (threshold crossing) was not touched in this step; its test judge run finished (1,136 pairs, 0 unparseable) but its write-up is still pending.

## Step 18 write-up and Step 20 (2026-11-03): additions only
New files: `usmeta/bench_v3_threshold.py`, `step18.py`, `step18_tables.py`, `step18_h3.py`, `step20.py`, `bench_v3_threshold*.jsonl`. `bench_v2d`, frozen scorers and judge prompt_v2 untouched. Step 18 deviations are recorded in `HYPOTHESES.md` (Amendment 1: synthetic sizes, H3 moved to BrEaST; Amendment 2: design details; erratum on replica counts) and `dev_val_notes.md`. Judge on test was capped to the primary pairs (+ dose extras for 32 size sets): 1,136 pairs, 0 unparseable. H4 not run. Step 20: tolerance tuned on dev/val only (τ = 0.3, adjacent position), evaluated once on test.

## Step 21 (2026-11-04): robustness tests, additions only
New files: `usmeta/step21_localisation.py`, `step21_dose.py`, `step21_dose_md.py`, `step21_judge_sens.py`, `step21_human_sheet.py`, `step21_human_score.py`. Frozen code, `bench_v2d`, prompt_v1/v2 and all earlier results untouched. Deviations from the brief: (21b) judge capped to 12 cases per dataset (Step 12 replies reused when the candidate text is identical) and image check restricted to the Step 16 scans present in `bench_test_v2d`, to stay under ~3 h; (21c) sample reduced to 10 cases per dataset (432 pairs per variant, 89 cases) and the repeat variant to 2 cases per dataset (93 pairs), for the same reason; one MLX crash during 21c, resumed from the saved replies; (21a) wrong-region boxes for 30 of 228 scans had to be scaled down because the true box was too large to avoid; (21d) prepared only, not scored (waiting for the owner). Judge variants were not tuned; prompt_v2 stays the reported prompt.

## Step 21f, housekeeping, Step 22 (2026-11-04): additions only
New files: `usmeta/step21_split_audit.py`, `usmeta/step22_paper_support.py`; `usmeta/.gitignore` gained `.llm_cache_*/`. Committed previously untracked MedGemma result files and the root copies of `bench_val_v2d.jsonl` and the Step 10d/12 judge files (needed by Step 19a/21c). `datasets/MANIFEST_TABLE.md`: HiSBreast licence cell now "blank at the source, to confirm". 21e skipped (no spec available). Backup of the git-ignored Step 18 score files: `~/backups/step18_scores_v3_20261102.zip` (outside the repo). History checks recorded in `results/partA/step22_paper_support/housekeeping.md`.

## Step 24 (2026-11-09): box reliability curve, additions only
New files: `usmeta/step24_box_reliability.py`, `usmeta/step24_report.py`; results in `results/partA/step24_box_reliability/`. Frozen code, `bench_v2d`, Step 19b/20/21a code and results untouched; saved masks reused for exact, shrink x0.9/0.75/0.5, enlarge x1.25 and the 21a label-free prompts. 4,332 new MedSAM masks (cached in the git-ignored `local_data/partb_box_reliability`). Deviations: (1) only the levels listed in the brief were run (shrink 6, enlarge 4, shift 4, jitter 3 x 3 seeds), not six per family; (2) the 19b shift (% of box size) is a different rule from the brief's shift (% of box width), so shift was fully re-run; (3) the prediction run took about 18 h wall clock because the machine was heavily loaded, far over the 3 h guide; the user told me to proceed. Added beyond the brief: a centre-offset table and the 21a boxes re-scored with the Step 20 rule.

## Step 21d scored (2026-11-09): additions only
The filled human-rewording sheet (`reference to human.xlsx`, uploaded to the repository) was copied into `results/partA/step21d_human_sheet/sheet.csv` (blank kept as `sheet_blank.csv`). Fact check: 10 of 30 flagged by the rule extractor; after a manual read 9 were marked `OK` (the extractor misreads free wording), H01 stays excluded (drops "irregular", "Combined" becomes "Associated"). Scored with the existing `step21_human_score score` (BLEU, ROUGE-L, chrF, BERTScore, RaTEScore, finding_f1, Gemma judge prompt_v2); `usmeta/step21_human_report.py` writes `results.md`. `results.md` of 21d replaces the "prepared, not scored" text; the earlier lines of RESULTS_SUMMARY / LIMITATIONS that say 21d is not scored are superseded by the addendum below.
