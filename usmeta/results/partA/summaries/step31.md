# Step 31: cross-dataset segmenter (breast, leave-one-dataset-out)

Limitations: [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md). Code: `usmeta/step31_cross_dataset.py`, `step31_report.py` (new files; `step29_seg.py` training code, `step29_run.py` scoring, the Step 20 check imported unchanged). Test split read once (logged: `usmeta.step31_cross_dataset`). Dev-only training, val tuning.

**What it is.** For each held-out breast dataset the Step 29 U-Net (same architecture, settings, augmentation, early stopping, leak filter) is trained on the **dev** images of the other four breast datasets only, early stopping and the threshold / largest-component choice are made on the **val** images of the same four, and the Step 20 tolerance-aware image check (tau 0.3, adjacent position; same code as Steps 24 / 29) is run on the held-out dataset's test scans, the same 138 scans as in Step 29 (30 per dataset, BUS-UCLM 18). No image of the held-out dataset was used for training, early stopping or tuning. An empty prediction counts as "no lesion found".

## Decision line

**Pooled over the five held-out datasets (138 scans, each scored by the model that never saw its dataset), position AUROC is 0.95 (0.91-0.98), against 0.94 (0.90-0.97) for the in-dataset Step 29 model on the same scans: by the rule of the brief (>= 0.80 works, 0.55-0.80 partial, <= 0.55 no) the check works label-free (>= 0.80) across datasets.** Per held-out dataset (30 scans each, so every per-dataset cell is under 30 groups: **too small to compare**, shown for orientation): BrEaST 0.94 (in-dataset 0.91); BUS-BRA 0.97 (in-dataset 1.00); BUSI 0.87 (in-dataset 0.84); UDIAT 1.00 (in-dataset 1.00); BUS-UCLM 0.94 (in-dataset 0.94).

## Training per fold (DEV of the other four datasets; VAL of the same four)

| held out | trained on | dev images (after leak filter and mask check) | val images | epochs | best val Dice (256 px) | post-processing chosen on val | minutes |
|---|---|---|---|---|---|---|---|
| BrEaST | BUS-BRA, BUSI, UDIAT, BUS-UCLM | 1169 (dev 1398, dropped 15) | 579 | 30 | 0.812 | threshold 0.4, raw | 17 |
| BUS-BRA | BrEaST, BUSI, UDIAT, BUS-UCLM | 522 (dev 751, dropped 13) | 254 | 29 | 0.709 | threshold 0.5, raw | 7 |
| BUSI | BrEaST, BUS-BRA, UDIAT, BUS-UCLM | 1018 (dev 1190, dropped 6) | 500 | 30 | 0.837 | threshold 0.6, raw | 14 |
| UDIAT | BrEaST, BUS-BRA, BUSI, BUS-UCLM | 1205 (dev 1435, dropped 14) | 598 | 30 | 0.806 | threshold 0.5, raw | 17 |
| BUS-UCLM | BrEaST, BUS-BRA, BUSI, UDIAT | 1166 (dev 1230, dropped 12) | 585 | 30 | 0.817 | threshold 0.5, raw | 17 |

For reference the Step 29 breast model (all five datasets): 1270 dev images, 629 val images, 28 epochs, best val Dice 0.815. Fold time cap 1 h: no fold reached it.

## Cross-dataset vs in-dataset, per held-out dataset (same test scans)

| held-out dataset | scans | Dice cross (95% CI) | Dice in-dataset (Step 29) | detection cross / in-dataset | position AUROC cross | position AUROC in-dataset | size AUROC cross | size in-dataset | all-checkable cross | all-checkable in-dataset | correct-report score cross | in-dataset |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BrEaST | 30 | 0.67 (0.55–0.78) | 0.67 (0.56–0.78) | 100% / 97% | 0.94 (0.85–1.00) † | 0.91 (0.82–1.00) † | 0.78 (0.68–0.87) | 0.83 (0.74–0.91) | 0.86 (0.81–0.91) | 0.88 (0.82–0.93) | 0.91 (0.86–0.95) | 0.90 (0.82–0.96) |
| BUS-BRA | 30 | 0.74 (0.63–0.83) † | 0.87 (0.83–0.91) † | 97% / 100% | 0.97 (0.90–1.00) † | 1.00 (1.00–1.00) † | 0.86 (0.76–0.94) † | 0.95 (0.88–0.99) † | 0.87 (0.79–0.93) † | 0.95 (0.92–0.98) † | 0.87 (0.78–0.94) † | 0.96 (0.92–0.99) † |
| BUSI | 30 | 0.72 (0.62–0.81) | 0.69 (0.57–0.79) | 100% / 97% | 0.87 (0.76–0.95) † | 0.84 (0.74–0.95) † | 0.88 (0.81–0.93) | 0.86 (0.77–0.93) | 0.91 (0.88–0.95) | 0.90 (0.85–0.95) | 0.94 (0.90–0.97) | 0.93 (0.85–0.98) |
| UDIAT | 30 | 0.85 (0.81–0.90) | 0.87 (0.83–0.90) | 100% / 100% | 1.00 (1.00–1.00) † | 1.00 (1.00–1.00) † | 0.89 (0.82–0.95) | 0.94 (0.88–0.98) | 0.94 (0.91–0.97) | 0.96 (0.94–0.99) | 0.98 (0.95–0.99) | 0.98 (0.96–1.00) |
| BUS-UCLM | 18 | 0.81 (0.69–0.91) † | 0.84 (0.75–0.92) † | 94% / 100% | 0.94 (0.75–1.00) † | 0.94 (0.75–1.00) † | 0.91 (0.80–0.99) † | 0.94 (0.86–1.00) † | 0.92 (0.83–0.99) † | 0.95 (0.90–0.99) † | 0.90 (0.78–0.98) † | 0.95 (0.92–0.99) † |
| pooled (5 datasets) | 138 | 0.75 (0.71–0.80) | 0.78 (0.74–0.82) | 99% / 99% | 0.95 (0.91–0.98) | 0.94 (0.90–0.97) | 0.86 (0.82–0.89) | 0.90 (0.87–0.93) | 0.90 (0.87–0.92) | 0.93 (0.91–0.95) | 0.92 (0.89–0.94) | 0.94 (0.92–0.97) |

† = under 30 groups: too small to compare (each dataset has 30 scans or fewer, 18 for BUS-UCLM; only the pooled row reaches 30 groups). Dice and position agreement use the true mask of the scan; detection = share of non-empty predictions (every test scan contains a lesion).

## Exact-rule variant (Step 16 exact match, for reference)

| held-out dataset | position AUROC cross | in-dataset | all-checkable cross | in-dataset | correct-report score (exact) cross | in-dataset |
|---|---|---|---|---|---|---|
| BrEaST | 0.91 (0.82–0.97) † | 0.88 (0.79–0.97) † | 0.87 (0.82–0.92) | 0.87 (0.81–0.93) | 0.83 (0.77–0.89) | 0.83 (0.75–0.89) |
| BUS-BRA | 0.97 (0.90–1.00) † | 1.00 (1.00–1.00) † | 0.86 (0.78–0.92) † | 0.95 (0.91–0.98) † | 0.82 (0.73–0.90) † | 0.92 (0.87–0.95) † |
| BUSI | 0.87 (0.76–0.95) † | 0.82 (0.71–0.92) † | 0.91 (0.87–0.95) | 0.90 (0.85–0.95) | 0.87 (0.82–0.91) | 0.85 (0.77–0.91) |
| UDIAT | 1.00 (1.00–1.00) † | 1.00 (1.00–1.00) † | 0.93 (0.89–0.97) | 0.96 (0.93–0.99) | 0.92 (0.89–0.95) | 0.93 (0.90–0.96) |
| BUS-UCLM | 0.94 (0.75–1.00) † | 0.94 (0.75–1.00) † | 0.90 (0.82–0.98) † | 0.93 (0.87–0.98) † | 0.84 (0.72–0.94) † | 0.89 (0.82–0.96) † |
| pooled | 0.94 (0.90–0.97) | 0.93 (0.89–0.96) | 0.89 (0.87–0.92) | 0.92 (0.90–0.94) | 0.86 (0.83–0.88) | 0.88 (0.85–0.91) |

## Reading

- **Generalisation gap (position AUROC, in-dataset minus held-out):** pooled -0.01; by dataset BrEaST -0.03, BUS-BRA +0.03, BUSI -0.03, UDIAT +0.00, BUS-UCLM +0.00. Dice: BrEaST 0.67 vs 0.67, BUS-BRA 0.74 vs 0.87, BUSI 0.72 vs 0.69, UDIAT 0.85 vs 0.87, BUS-UCLM 0.81 vs 0.84.
- The held-out datasets differ in scanner, patient population and image format (BrEaST, BUS-BRA, BUSI, UDIAT and BUS-UCLM come from different centres), so this is a different and harder test than Step 29, where the same datasets appear in training and test (different groups only where patient ids exist).

## Caveats

- **30 scans per held-out dataset (BUS-UCLM 18) at most 3 per group:** per-dataset cells are too small to compare; only the pooled row has 30 or more groups. One seed, one split, no repeat; random-init encoder (no pretrained weights), as in Step 29.
- **Leave-one-dataset-out removes a dataset, not its patients' look-alikes elsewhere**: other datasets can contain similar scanners or public re-uses of the same images (Step 10a found no cross-dataset duplicates at <= 4 bits; the leak filter only drops dev images whose <= 8-bit clusters reach val or test inside one dataset).
- Breast only; thyroid and fetal head were not run. The image-check numbers are scored on our templated candidates and on the 228-scan selection of Steps 21a / 24 (breast part).
- Fold epochs may differ from Step 29 because of early stopping on the other four datasets' val images; the 30-epoch maximum and 1 h cap were the same or tighter.
