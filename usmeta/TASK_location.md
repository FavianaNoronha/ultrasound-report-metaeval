# Task: Location check (IoU) + BrEaST in the real-report run

Read CLAUDE.md first. Same rules apply: never claim "first ultrasound benchmark", flag possible
training-data contamination, don't overwrite existing results, commit after each step.

## Why
Our professor suggested IoU (intersection over union) metrics used in chest X-ray grounded reporting
(prior art: MAIRA-2 / RadFact, arXiv 2412.01031). Our Layer 3 "evidence check" is currently an oracle
that reads dataset labels (scores 1.00, upper bound only). This task makes it a real location check.

## Data (all on this Mac)
| Dataset | Images | Location ground truth |
|---|---|---|
| BrEaST | ~/Downloads/BrEaST-Lesions_USG-images_and_masks/caseNNN.png (256) | caseNNN_tumor.png (252; 4 normal cases have none), caseNNN_otherK.png (14 extra masks); labels + Pixel_size in ../baseline_exp/breast.xlsx |
| BUS-BRA | ~/Downloads/archive-5/BUSBRA/BUSBRA/Images (1875) | .../Masks (1875); labels bus_data.csv |
| TN3K | ~/Downloads/TN3K.rar (reuse wherever you extracted it for the Qwen run) | *-mask/ folders inside the rar |
| TN5000 | ~/Downloads/TN5000_forReview/JPEGImages | Annotations/*.xml (VOC boxes, no masks) |
| HC18 | ~/Downloads/archive-7/training_set/NNN_HC.png | NNN_HC_Annotation.png (ellipse outline; fill it to get a region) + head circumference mm and pixel size in training_set_pixel_size_and_HC.csv |

## Step 1 — usmeta/usmeta/location.py
- Loader that returns, per case: image path, GT mask (or None), GT box(es) [x1,y1,x2,y2 in original pixels].
  Masks -> boxes via bounding rect of each connected component. TN5000 = boxes only. HC18 = filled ellipse.
- box_iou(a,b), mask_iou(a,b), best-match IoU for multiple lesions (Hungarian or greedy, document which).
- HC18: also estimate head circumference from a box/ellipse (Ramanujan) and return abs error in mm.
- BrEaST: lesion longest diameter in mm from mask + Pixel_size (needed later for size errors).
- Unit tests in tests/ (IoU of identical = 1, disjoint = 0, known overlap case).
- Print a sanity table: cases loaded per dataset, % with GT region. Commit.

## Step 2 — Planted location errors (benchmark extension, new file bench_loc.jsonl)
Candidates are now "text + box". For ~100 cases per dataset build:
- harmless: same text, box jittered so IoU >= 0.85; same text paraphrased + jittered box.
- box-only errors: box shifted to IoU ~0.5 (sev1), ~0.2 (sev2), 0 / wrong side or wrong lesion (sev3).
- text location errors where the template has a location field (BUS-BRA side, TN3K/TN5000 position grid),
  with the box kept correct, and with the box moved consistently.
- size errors: HC18 head size and BrEaST lesion size changed in the text (reuse existing magnitude levels).
Score with: existing text scorers (bleu, rougeL, chrf, bertscore, ratescore, fact_checker) and a new
`location_check` (box IoU vs GT) and `grounded_check` = fact_checker x IoU (document the formula).
Report AUROC, harmless mean, identical mean, severity Spearman as before -> results_stage4_location.md/json.
IMPORTANT honesty note in the results: text-only scorers cannot see boxes, so missing box-only errors is
by construction — present that as a sanity check, not a finding. The interesting rows are text-location
errors and the grounded scorer.

## Step 3 — Add BrEaST to the real-report run + ask for boxes
- Add BrEaST (50 scans, same sampling seed logic) to generate.py with Qwen2.5-VL-3B.
- Re-run Qwen on 50 scans per dataset (all 5) asking for the report AND a JSON box for each lesion/head.
  Qwen2.5-VL returns absolute coords on its resized input — rescale to original image size, and log raw output.
- For each generated report: box IoU vs GT, % of reports with IoU >= 0.5, HC18 size error mm.
- Key analysis: on real reports, do text-scorer scores correlate with box IoU? (Spearman per dataset.)
  i.e. do text scorers reward reports from a model that looked in the wrong place?
- Flip test: mirrored image -> box should mirror too; report how often it does.
- Mark every dataset "public — may have been seen in training"; BrEaST is public (TCIA).
-> results_stage4_qwen_location.md/json, reports_qwen_v2.jsonl (keep the old reports_qwen.jsonl).

## Step 4 — Update README status + CLAUDE.md task list. Commit.

## Stop and ask me if
- a dataset's masks/boxes don't match image filenames for >5% of cases,
- Qwen box output can't be parsed for >30% of scans (show 3 raw examples),
- anything needs a download or a gated model.
