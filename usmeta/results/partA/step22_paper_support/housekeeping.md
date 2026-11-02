# Housekeeping report (2026-11-04; no history was rewritten)

**1. Backup of the git-ignored Step 18 files.** `~/backups/step18_scores_v3_20261102.zip` (1.9 MB, outside the repo): `scores_v3_devval_layer0/1.json`, `scores_v3_test_layer0/1.json`, `bench_v3_threshold*.jsonl`, `judge_v3_*.jsonl`. `usmeta/.gitignore` now also ignores `.llm_cache_*/` (the repeat-run judge cache).

**2. Untracked MedGemma result files committed** (all < 125 KB, model-written text on public images, our extracted facts and judge replies; checked: no images, no HiSBreast strings): `boxes_medgemma.jsonl.jobs.json/.raw.jsonl`, `extract_medgemma_v2*.jsonl`, `judge_medgemma_v1/v1q/v2/v2q.jsonl`, `memprobe_medgemma.jsonl.jobs.json/.raw.jsonl`, `reports_medgemma.jsonl.jobs.json/.raw.jsonl`, `reports_medgemma_bf16_partial6/run2.jsonl`. Also committed because Step 19a/21c read them from the repo root: `bench_val_v2d.jsonl` (11 MB, templated text built from labels), `judge_test_v1/v2(_bench).jsonl`, `judge_big_v2(_bench).jsonl` (identical to the copies already tracked in the Step 10d/12 folders). Left untracked on purpose: `usmeta/qwen_real_work/` (scratch folder of Qwen working files, 836 KB) and the git-ignored caches.

**3. Files that are, or could be, redistributed dataset content or licensed text.**
| file | what it is | tracked | in git history |
|---|---|---|---|
| `baseline_exp/breast.xlsx` | BrEaST clinical / label spreadsheet (derived from the dataset) | yes | yes, since the first commit `9a1670e` |
| `baseline_exp/tn3k_records.json` | TN3K labels (derived) | yes | yes, since `9a1670e` |
| `usmeta/bench_*.jsonl`, `true_reports_v2*.jsonl`, `results/**/*.jsonl` | candidate and reference reports written by our templates from labels/masks (no dataset images or text; label-derived facts such as sizes, BI-RADS, histology) | yes | yes |
| `usmeta/splits.jsonl`, `duplicates.jsonl`, `datasets/manifest.json` | image file names / case ids and hashes of public datasets | yes | yes |
| `reports_qwen*.jsonl`, `reports_medgemma*.jsonl`, `judge_*.jsonl` | model outputs on public images (the models' own licences apply) | yes | yes |
| HiSBreast text, translations, exam ids (`usmeta/local_data/hisbreast/`) | licensed / unlicensed clinician text | **no** (git-ignored; a test guards it) | see below |
| dataset images, masks (`local_data/partb*`) | public dataset images / predicted masks | **no** (git-ignored) | no |
| `usmeta/PROJECT_SLIDES.pptx`, `boxsweep.png` | our own slides / plot (the plot shows aggregates only) | yes | yes |

File names containing "hisbreast" in history are our code, tests and aggregate results only (checked with `git log --all --name-only`): no HiSBreast data file, zip or `uncertain_cases.csv` was ever committed. **Text search of history:** the 1,448 HiSBreast strings and exam ids (the same needles as `tests/test_hisbreast.py`) were searched in every commit (46 revisions) within the HiSBreast-named files, the Step 11a and Step 15 result folders, `usmeta/docs`, and every `*.md` and `*.csv`: **no match**. A search of ALL blobs of ALL commits (including the large jsonl files) was started but did not finish in a practical time (killed after about 15 minutes), so it is **not** complete; the working tree is covered by the test guard (`tests/test_hisbreast.py`).

`baseline_exp/breast.xlsx` and `baseline_exp/tn3k_records.json` are dataset-derived files in history (see `LICENSE-NOTES.md`); their dataset licences are "to confirm". Removing them would need a history rewrite, which was NOT done.

**4. `datasets/MANIFEST_TABLE.md`:** every licence cell reads "to confirm"; the HiSBreast cell now reads "blank at the source, to confirm".
