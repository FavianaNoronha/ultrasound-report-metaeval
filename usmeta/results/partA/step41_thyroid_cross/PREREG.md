# Step 41 pre-registration: does the label-free U-Net image check transfer between thyroid datasets? (written 2026-11-18, before any training and before any test number)

Mirrors Step 31 (breast leave-one-dataset-out) for thyroid. Code will be `usmeta/step41_thyroid_cross.py` (new; `step29_seg.py` training code, `step29_run.py` scoring and the Step 20 check imported unchanged).

## Design
- Mask-labelled thyroid datasets: **TN3K and DDTI**. TN5000 has boxes only, so it is not a training set (as in Step 29). Two folds, each with one training dataset and one held-out dataset:
  - Fold A: train on **TN3K dev** -> test on the **DDTI** test scans.
  - Fold B: train on **DDTI dev** -> test on the **TN3K** test scans.
- Same U-Net as Step 29 (ResNet-18 encoder, random init, no pretrained weights), same training settings (AdamW lr 1e-3, weight decay 1e-4, cosine schedule, batch 16, 256 px, flips and intensity augmentation, 30 epochs at most, patience 6, seed 0), same leak filter (dev images in <= 8-bit near-duplicate clusters that reach val or test are dropped), same early stopping and post-processing grid (threshold 0.3-0.7, raw vs largest component) chosen on the **VAL images of the training dataset only**. Same time cap as Step 31: `--max-hours 1.0` per fold. No image of the held-out dataset is used for training, early stopping or tuning.
- Before this file, only split counts were looked at: TN3K dev 1,398 (61 in leaky clusters), val 697; DDTI dev 192 (87 in leaky clusters, so about 105 kept, fewer with a usable mask), val 96. No model was trained and no test image, mask or score was read.

## Test scans (no new scans)
The same 60 thyroid test scans as Steps 29 / 38 (30 per dataset; selection = `step24_box_reliability.selection()`, all in the locked test split; TN5000's 30 scans are not used here). 30 distinct groups in TN3K, 26 in DDTI.
- TN3K (30): `TN3K:trainval/1906.jpg`, `TN3K:trainval/1040.jpg`, `TN3K:trainval/2534.jpg`, `TN3K:trainval/0955.jpg`, `TN3K:trainval/2365.jpg`, `TN3K:test/0480.jpg`, `TN3K:trainval/1700.jpg`, `TN3K:trainval/1558.jpg`, `TN3K:trainval/0615.jpg`, `TN3K:trainval/2188.jpg`, `TN3K:trainval/0110.jpg`, `TN3K:trainval/0632.jpg`, `TN3K:trainval/1157.jpg`, `TN3K:trainval/1499.jpg`, `TN3K:trainval/2043.jpg`, `TN3K:trainval/0104.jpg`, `TN3K:trainval/1143.jpg`, `TN3K:trainval/2626.jpg`, `TN3K:trainval/2331.jpg`, `TN3K:trainval/2595.jpg`, `TN3K:trainval/1866.jpg`, `TN3K:trainval/1687.jpg`, `TN3K:trainval/2670.jpg`, `TN3K:trainval/0230.jpg`, `TN3K:trainval/2755.jpg`, `TN3K:trainval/1327.jpg`, `TN3K:trainval/0062.jpg`, `TN3K:test/0323.jpg`, `TN3K:trainval/2406.jpg`, `TN3K:trainval/0899.jpg`
- DDTI (30): `DDTI:8_1`, `DDTI:271_1`, `DDTI:141_1`, `DDTI:130_2`, `DDTI:139_1`, `DDTI:146_2`, `DDTI:206_1`, `DDTI:53_1`, `DDTI:196_1`, `DDTI:160_1`, `DDTI:353_1`, `DDTI:156_1`, `DDTI:156_2`, `DDTI:150_1`, `DDTI:90_2`, `DDTI:326_1`, `DDTI:337_2`, `DDTI:125_1`, `DDTI:105_1`, `DDTI:270_1`, `DDTI:109_1`, `DDTI:353_2`, `DDTI:91_1`, `DDTI:222_1`, `DDTI:341_1`, `DDTI:394_1`, `DDTI:359_1`, `DDTI:80_1`, `DDTI:146_1`, `DDTI:168_1`

Scoring: the Step 20 tolerance-aware image check with the frozen tau and position rule from `step20_tolerance_image_check/tuning_devval.json` (as Steps 24 / 29 / 31), per-scan AUROC of planted position errors vs harmless rewordings, group bootstrap 1,000 resamples, seed 0. Test read once and logged (`splits.load('test', script='usmeta.step41_thyroid_cross')`).

## Comparison point
The in-dataset position AUROC of the Step 29 thyroid model (trained on TN3K + DDTI dev) on the **same scans**, from the saved Step 29 rows (`step29_segmentation/a_rows.json`; published in Step 38: TN3K 0.93, 0.82-1.00; DDTI 0.77, 0.57-0.93). Also reported: Dice (with the true mask), detection rate and the correct-report score (identical copies; tolerance-aware), cross vs in-dataset, plus the size and all-checkable AUROCs for reference.

## Decision rule (fixed)
A fold **transfers** iff (1) its held-out position AUROC is within 0.05 of the in-dataset AUROC on the same scans (|cross - in-dataset| <= 0.05, or cross above it) AND (2) the lower bound of its 95% group-bootstrap interval is >= 0.70. A fold whose held-out cell has **fewer than 30 groups** (groups counted as distinct groups with a defined per-scan position AUROC, as in Steps 31 / 38) is "too small": its numbers and the rule's outcome are reported as indicative but **no decision is made**. A pooled row over the two folds (60 scans) is **descriptive only**, with no decision. No other rule or threshold will be introduced after the numbers are seen.

## Expectations stated in advance (not hypotheses)
With 30 scans per dataset the per-fold cells may fall under 30 groups, in which case no fold can be decided and the result will say so. The in-dataset DDTI interval (0.57-0.93) already has a lower bound below 0.70, so condition (2) is unlikely to hold for the DDTI fold whatever the transfer.

## Caveats
- **DDTI is small** (about 105 dev images after the leak filter): the DDTI-trained fold may be weak because of **training-set size, not domain shift**; this design cannot separate the two (TN3K has about 13 times more dev images). The Step 29 in-dataset model trained on both datasets, so its advantage over each fold partly reflects more training data.
- 30 scans per held-out dataset, one seed, one split, no repeat; random-init encoder; templated candidates; thyroid only; the scanner / centre of the images is not recorded for TN3K or DDTI, so "dataset" stands in for domain.
- The datasets may share image sources or patients that the leak filter (within-dataset clusters only) cannot see.

Outputs: `results.md` (decision lines first, table, caveats, any deviation from this file), `results.json`, `run_info.json`, `train_*.json`, logs.
