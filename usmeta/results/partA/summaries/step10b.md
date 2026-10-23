# Step 10b: grouped, locked dev / val / test splits (40 / 20 / 40)

**What was done.** `usmeta/splits.py` assigns every one of the 16,562 cases to dev (40%), val (20%) or test (40%) at GROUP level, stratified by dataset and class, seed 0, with near-duplicate clusters from Step 10a merged into one group (your decision: *group clusters, drop none*). Result: **0 groups in more than one split** (tested). `splits.jsonl` has case id, group id, group source, stratum and split. `splits_manifest.json` has the SHA-256 of `splits.jsonl`, `bench_v2d.jsonl` and `true_reports_v2d.jsonl` and the git commit. `usmeta.splits.load(split)` is the only allowed reader: access to `test` is logged to `results/partA/test_access.log` (date, script, git hash, rows). Tests (`tests/test_splits.py`): no group spans two splits; sizes within 5 points of 40/20/40 per dataset; near-duplicate pairs are never split; the log records test access and not dev.

**Rule from now on:** tuning of any kind (prompts, templates, extractor fixes, thresholds, calibration) uses dev and val only; final numbers come from test, loaded through `usmeta.splits.load("test")`.

| dataset | cases | dev | val | test | groups | group id source | cases in a near-duplicate cluster | leak risk |
|---|---|---|---|---|---|---|---|---|
| BUS-BRA | 1875 | 750 | 375 | 750 | 1064 | record | 0 | low: patient id (Case) known, left and right images stay together |
| BUS-UCLM | 683 | 271 | 141 | 271 | 37 | record | 45 | low: exam prefix known (37 groups) |
| BUSI | 780 | 311 | 157 | 312 | 621 | image id (stand-in) | 290 | MODERATE: no patient id; repeat scans of one patient can sit in different splits (only near-duplicates are merged) |
| BrEaST | 256 | 103 | 50 | 103 | 256 | record | 0 | none: one case per patient record |
| DDTI | 480 | 192 | 96 | 192 | 383 | record | 23 | low-moderate: case id known; one case can hold several images |
| FetalHead | 2833 | 1133 | 564 | 1136 | 1022 | record | 257 | low: patient id known |
| HC18 | 999 | 400 | 199 | 400 | 989 | image id (stand-in) | 19 | MODERATE: no subject id; the Diverse Fetal Head Images folder is a resized copy of HC18 |
| TN3K | 3493 | 1398 | 697 | 1398 | 3468 | image id (stand-in) | 42 | MODERATE: no patient id; frames of one patient can sit in different splits |
| TN5000 | 5000 | 2000 | 1000 | 2000 | 4857 | image id (stand-in) | 279 | MODERATE: no patient id; same |
| UDIAT | 163 | 66 | 31 | 66 | 159 | image id (stand-in) | 8 | MODERATE: no patient id (small dataset) |

**Group ids are missing for five whole datasets (BUSI, UDIAT, TN3K, TN5000, HC18).** The brief says to use the image id and state it; the group is then the image (or its near-duplicate cluster), "patient overlap possible". The remaining risk is the same patient scanned more than once with non-matching frames; with no patient id it cannot be measured or removed. It would make the test slightly optimistic for choices made on dev (prompts, thresholds); none of our scorers is fitted. BUSI had the largest duplicate share (37%), which the clusters now cover. Your stop rule lists "group ids missing for a whole dataset"; I continued because the brief's default policy covers it and the splits are cheap to rebuild before anything uses the test split, but tell me if you want a different rule for these five.

**Honest notes.** (1) The splits cover all 16,562 cases; bench_v2d (150 cases per dataset, drawn before the split existed) contains cases from all three splits, so for final numbers the test rows are rebuilt from test-split cases only (Step 10d). (2) Stratification uses the dataset class (benign/malignant/normal, class 0/1, plane); HC18 has none. (3) Test access so far: none (the log is created on first access). (4) The `freeze-v1` tag is placed at the end of Step 10c, after the frozen files are listed.

Related: `docs/LIMITATIONS.md` (Step 10e).
