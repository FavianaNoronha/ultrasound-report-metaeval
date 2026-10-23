# Step 10b: grouped, locked dev / val / test splits (40 / 20 / 40)

**What was done.**  assigns every one of the 16,562 cases to dev (40%), val (20%) or test (40%) at GROUP level, stratified by dataset and class, seed 0, with near-duplicate clusters from Step 10a merged into one group (the decision: *group clusters, drop none*). Result: **0 groups in more than one split** (tested).  has case id, group id, group source, stratum, split.  has SHA-256 of ,  and  and the git commit.  is the only allowed reader: access to  is logged to  (date, script, git hash, rows). Tests: no group spans two splits; sizes within 5 points of 40/20/40 per dataset; near-duplicate pairs never split; the log records test and not dev.

**Rule from now on:** tuning of any kind (prompts, templates, extractor fixes, thresholds, calibration) uses dev and val only; final numbers come from test, loaded through .

| dataset | cases | dev | val | test | groups | group id source | cases merged into a near-duplicate cluster | leak risk |
|---|---|---|---|---|---|---|---|---|
| BUS-BRA | 1875 | 750 | 375 | 750 | 1064 | record | 0 | low: patient id (Case) known, left and right images stay together |
| BUS-UCLM | 683 | 271 | 141 | 271 | 37 | record | 45 | low: exam prefix known (37 groups) |
| BUSI | 780 | 311 | 157 | 312 | 621 | image id (stand-in) | 290 | MODERATE: no patient id; repeat scans of one patient can sit in different splits (only near-duplicates are merged) |
| BrEaST | 256 | 103 | 50 | 103 | 256 | record | 0 | none: one case per patient record |
| DDTI | 480 | 192 | 96 | 192 | 383 | record | 23 | low-moderate: case id known; one case can hold several images |
| FetalHead | 2833 | 1133 | 564 | 1136 | 1022 | record | 257 | low: patient id known |
| HC18 | 999 | 400 | 199 | 400 | 989 | image id (stand-in) | 19 | MODERATE: no subject id (HC18 normally has 1-2 images per fetus); Diverse Fetal Head Images is a resized copy of it |
| TN3K | 3493 | 1398 | 697 | 1398 | 3468 | image id (stand-in) | 42 | MODERATE: no patient id; frames of one patient can sit in different splits |
| TN5000 | 5000 | 2000 | 1000 | 2000 | 4857 | image id (stand-in) | 279 | MODERATE: no patient id; same |
| UDIAT | 163 | 66 | 31 | 66 | 159 | image id (stand-in) | 8 | MODERATE: no patient id (small dataset) |

**Group ids are missing for five whole datasets (BUSI, UDIAT, TN3K, TN5000, HC18).** The brief says to use the image id and state it; the group is then the image (or the near-duplicate cluster), "patient overlap possible". The remaining risk is the same patient scanned more than once with non-matching frames; with no patient id it cannot be measured or removed. It would make the test slightly optimistic for scorers that are tuned on dev (none of ours are fitted, so the effect is mostly on thresholds and prompt choices). BUSI had the largest duplicate share (37%), which the clusters now cover.

**Honest notes.** (1) The splits cover all 16,562 cases; the benchmark files so far (bench_v2d: 150 cases per dataset, drawn before the split existed) contain cases from all three splits, so for final numbers the test rows are taken by filtering or rebuilding from test-split cases only (Step 10d). (2) Stratification uses the dataset class (benign/malignant/normal, class 0/1, plane); fetal HC18 has none. (3) Test access so far: none (the log is created on first access).

Related:  (Step 10e).
