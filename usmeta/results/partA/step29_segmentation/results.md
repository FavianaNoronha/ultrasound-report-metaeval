# Step 29: label-free image check by segmentation (replaces Step 23)

Limitations: [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md). Code: `usmeta/step29_seg.py` (U-Net, training), `step29_run.py` (test pass), `step29_report.py` (new files; `partb.py`, `location.py`, `layer3.py`, `step20.py`, `step24_box_reliability.py` imported unchanged). Test split read once (logged: `usmeta.step29_run`). Training on DEV only, early stopping and post-processing chosen on VAL.

**What it is.** A small U-Net (ResNet-18 encoder, **random init**: no pretrained weights were cached and none were downloaded; 256x256 input, flips + contrast / brightness / gamma augmentation, AdamW, BCE + Dice, at most 30 epochs, early stopping on val Dice) learns to find the lesion from the image alone, one model per organ. Its mask goes through the same measurement code as the MedSAM masks (`partb.pred_meas`) and the Step 20 tolerance-aware image check (tau 0.3, adjacent position, frozen on dev/val; the exact Step 16 rule is shown too). An **empty prediction counts as "no lesion found"**. No label, box or true mask is used at test time.

## Decision line

**29a: position AUROC 0.89 (0.84–0.93) pooled over the 228 test scans, so by the rule of the brief (>= 0.80 works, 0.55-0.80 partial, <= 0.55 no) the check works label-free (>= 0.80): breast 0.94 (0.90–0.97) (works label-free (>= 0.80)); thyroid 0.80 (0.69–0.89) (partial (0.55-0.80), on the boundary: its interval spans 0.80).** Compared with the oracle-box MedSAM check (position 0.97) it loses little on breast and about 0.15 on thyroid; the label-free boxes of Step 21a were at 0.31-0.54 and the U-Net is far above them. Size and all-checkable AUROC are lower (pooled 0.88 (0.85–0.91) and 0.90 (0.88–0.92)). It works because the lesion in these datasets is a single, mostly high-contrast object, and the model was trained on the same datasets (see caveats: no patient ids in several, so patient overlap with test cannot be excluded). It is not shown on other scanners, other datasets or lesions that are small or isoechoic.
**29b: head circumference from the U-Net head mask has MAE 2.70 mm on the 400 HC18 test images (median 1.85, 90th percentile 5.53; mask Dice 0.967).** With the exact Step 16 rule the planted-HC-error check reaches AUROC 0.87 (bench errors) and 0.92 (planted +-1 / +-40 mm and x0.5-x2.0), but the **tolerance-aware rule (tau 0.3) cannot see HC errors at all (AUROC 0.52, the same as with the exact labelled HC): a 30% tolerance is wider than almost every planted HC error, so that rule is the wrong tool for head circumference.** The oracle-geometry numbers (HC taken from the label, or from the true annotation) are **circular** by construction (1.00 with the exact rule). FetalHead has no pixel size: **not testable**.

## Training (DEV only; leaky dev images dropped; chosen on VAL)

| model | dev images | dropped (8-bit cluster reaches val / test) | trained on | val images | epochs run | best val Dice (256 px) | post-processing chosen on val |
|---|---|---|---|---|---|---|---|
| breast | 1501 | 15 | 1270 | 629 | 28 | 0.815 | threshold 0.6, raw |
| thyroid | 1590 | 148 | 1438 | 789 | 30 | 0.751 | threshold 0.3, raw |
| hc18 | 400 | 26 | 374 | 199 | 30 | 0.969 | threshold 0.4, largest |

Training images are the dev images with a real mask (breast: BrEaST, BUS-BRA, BUSI, UDIAT, BUS-UCLM; thyroid: TN3K, DDTI). TN5000 has boxes only, so it is **not** in training and its 30 test scans are cross-dataset; epoch time and seeds are in `train_*.json` (seed 0, MPS).

## 29a-1. Segmentation quality on the 228 test scans (against the true mask; TN5000: box IoU)

| group | scans | found (non-empty) | Dice | IoU |
|---|---|---|---|---|
| breast | 138 | 99% | 0.78 (0.74–0.82) (n = 138) | 0.69 (0.65–0.74) |
| thyroid | 90 | 100% | 0.75 (0.69–0.80) (n = 60) | 0.64 (0.58–0.70) |
| pooled | 228 | 99% | 0.77 (0.74–0.81) (n = 198) | 0.68 (0.64–0.71) |

| dataset | scans | found | Dice (mean, 95% CI) | IoU | box IoU (TN5000) |
|---|---|---|---|---|---|
| BrEaST | 30 | 97% | 0.67 (0.56–0.78) | 0.59 (0.48–0.70) | — | (30 scans per dataset: † under 30 groups where marked)
| BUS-BRA | 30 | 100% | 0.87 (0.83–0.91) † | 0.79 (0.72–0.83) † | — | (30 scans per dataset: † under 30 groups where marked)
| BUSI | 30 | 97% | 0.69 (0.57–0.79) | 0.60 (0.49–0.70) | — | (30 scans per dataset: † under 30 groups where marked)
| UDIAT | 30 | 100% | 0.87 (0.83–0.90) | 0.78 (0.73–0.83) | — | (30 scans per dataset: † under 30 groups where marked)
| BUS-UCLM | 18 | 100% | 0.84 (0.75–0.92) † | 0.75 (0.64–0.85) † | — | (30 scans per dataset: † under 30 groups where marked)
| TN3K | 30 | 100% | 0.82 (0.75–0.88) | 0.73 (0.65–0.80) | — | (30 scans per dataset: † under 30 groups where marked)
| DDTI | 30 | 100% | 0.68 (0.60–0.75) † | 0.55 (0.47–0.62) † | — | (30 scans per dataset: † under 30 groups where marked)
| TN5000 | 30 | 100% | — | — | 0.48 (0.36–0.59) | (30 scans per dataset: † under 30 groups where marked)

Detection rate = share of scans where the model returned a non-empty mask (every test scan contains a lesion). A non-empty mask can still be in the wrong place; position agreement with the true mask (same code as the image check): breast 88%, thyroid 74%.

## 29a-2. Image check, side by side (same 228 scans; AUROC of planted error vs harmless rewording; 95% CI by group bootstrap, 1,000, seed 0)

Columns: Step 20 tolerance-aware rule (position / size / all-checkable AUROC and correct-report score = mean score of the identical copies), then the exact Step 16 rule (position / all-checkable). Rows below the U-Net come from saved Step 24 / 21a runs, unchanged.

### breast

| source | position (tol) | size (tol) | all-checkable (tol) | correct-report score (tol) | position (exact) | all-checkable (exact) |
|---|---|---|---|---|---|---|
| **U-Net, label-free (this step)** | 0.94 (0.90–0.97) | 0.90 (0.87–0.93) | 0.93 (0.91–0.95) | 0.94 (0.92–0.97) | 0.93 (0.89–0.96) | 0.92 (0.90–0.94) |
| oracle-box MedSAM (Step 24 exact box) | 0.98 (0.96–1.00) | 0.94 (0.91–0.96) | 0.96 (0.95–0.97) | 0.97 (0.96–0.98) | 0.96 (0.93–0.99) | 0.94 (0.92–0.96) |
| true box x0.5 (Step 24 shrink) | 0.96 (0.93–0.99) | 0.37 (0.35–0.39) | 0.70 (0.69–0.71) | 0.79 (0.78–0.80) | 0.95 (0.91–0.98) | 0.70 (0.69–0.71) |
| true box shifted 50% of width (Step 24) | 0.88 (0.84–0.93) | 0.64 (0.60–0.68) | 0.80 (0.78–0.82) | 0.83 (0.81–0.85) | 0.79 (0.74–0.84) | 0.75 (0.73–0.77) |
| true box jitter 20% (Step 24, seed 0) | 0.96 (0.93–0.98) | 0.79 (0.76–0.83) | 0.88 (0.86–0.90) | 0.91 (0.89–0.93) | 0.92 (0.88–0.96) | 0.86 (0.83–0.88) |
| label-free: centre 50% box (Step 21a) | 0.56 (0.52–0.60) | 0.58 (0.53–0.63) | 0.71 (0.68–0.74) | 0.85 (0.82–0.87) | 0.56 (0.53–0.60) | 0.70 (0.67–0.73) |
| label-free: whole image (Step 21a) | 0.45 (0.40–0.49) | 0.38 (0.35–0.42) | 0.58 (0.56–0.60) | 0.71 (0.67–0.74) | 0.46 (0.43–0.50) | 0.60 (0.57–0.62) |
| label-free: random box (Step 21a) | 0.44 (0.37–0.52) | 0.72 (0.68–0.76) | 0.80 (0.77–0.82) | 0.79 (0.77–0.82) | 0.48 (0.43–0.54) | 0.76 (0.74–0.79) |
| label-free: wrong region (Step 21a) | 0.33 (0.26–0.41) | 0.68 (0.63–0.71) | 0.77 (0.74–0.79) | 0.75 (0.72–0.77) | 0.38 (0.32–0.43) | 0.72 (0.70–0.75) |

### thyroid

| source | position (tol) | size (tol) | all-checkable (tol) | correct-report score (tol) | position (exact) | all-checkable (exact) |
|---|---|---|---|---|---|---|
| **U-Net, label-free (this step)** | 0.80 (0.69–0.89) | 0.84 (0.80–0.89) | 0.86 (0.82–0.89) | 0.89 (0.85–0.92) | 0.79 (0.69–0.88) | 0.85 (0.82–0.89) |
| oracle-box MedSAM (Step 24 exact box) | 0.95 (0.90–0.99) | 0.84 (0.79–0.87) | 0.89 (0.87–0.92) | 0.89 (0.86–0.91) | 0.92 (0.86–0.97) | 0.86 (0.83–0.89) |
| true box x0.5 (Step 24 shrink) | 0.94 (0.88–0.98) | 0.43 (0.40–0.47) | 0.68 (0.66–0.71) | 0.73 (0.70–0.76) | 0.91 (0.85–0.97) | 0.69 (0.67–0.71) |
| true box shifted 50% of width (Step 24) | 0.78 (0.69–0.86) | 0.66 (0.61–0.70) | 0.77 (0.74–0.80) | 0.78 (0.74–0.81) | 0.66 (0.57–0.73) | 0.71 (0.68–0.75) |
| true box jitter 20% (Step 24, seed 0) | 0.92 (0.87–0.95) | 0.74 (0.69–0.79) | 0.81 (0.78–0.84) | 0.81 (0.78–0.84) | 0.86 (0.80–0.92) | 0.77 (0.74–0.81) |
| label-free: centre 50% box (Step 21a) | 0.51 (0.50–0.54) | 0.52 (0.45–0.58) | 0.67 (0.64–0.71) | 0.78 (0.74–0.82) | 0.51 (0.50–0.54) | 0.66 (0.63–0.70) |
| label-free: whole image (Step 21a) | 0.48 (0.42–0.54) | 0.36 (0.33–0.39) | 0.57 (0.55–0.60) | 0.67 (0.64–0.71) | 0.47 (0.42–0.51) | 0.60 (0.57–0.63) |
| label-free: random box (Step 21a) | 0.45 (0.34–0.56) | 0.78 (0.74–0.82) | 0.80 (0.77–0.83) | 0.76 (0.72–0.80) | 0.45 (0.38–0.52) | 0.77 (0.74–0.81) |
| label-free: wrong region (Step 21a) | 0.27 (0.20–0.34) | 0.69 (0.64–0.74) | 0.73 (0.69–0.76) | 0.67 (0.63–0.71) | 0.41 (0.34–0.46) | 0.70 (0.66–0.73) |

### pooled

| source | position (tol) | size (tol) | all-checkable (tol) | correct-report score (tol) | position (exact) | all-checkable (exact) |
|---|---|---|---|---|---|---|
| **U-Net, label-free (this step)** | 0.89 (0.84–0.93) | 0.88 (0.85–0.91) | 0.90 (0.88–0.92) | 0.92 (0.90–0.94) | 0.88 (0.83–0.92) | 0.90 (0.87–0.91) |
| oracle-box MedSAM (Step 24 exact box) | 0.97 (0.95–0.99) | 0.90 (0.87–0.92) | 0.93 (0.92–0.95) | 0.94 (0.92–0.95) | 0.95 (0.92–0.97) | 0.91 (0.89–0.93) |
| true box x0.5 (Step 24 shrink) | 0.95 (0.92–0.98) | 0.39 (0.38–0.41) | 0.69 (0.68–0.71) | 0.76 (0.75–0.78) | 0.93 (0.90–0.97) | 0.70 (0.69–0.71) |
| true box shifted 50% of width (Step 24) | 0.85 (0.80–0.89) | 0.65 (0.62–0.68) | 0.79 (0.77–0.80) | 0.81 (0.79–0.83) | 0.74 (0.70–0.79) | 0.73 (0.71–0.75) |
| true box jitter 20% (Step 24, seed 0) | 0.94 (0.92–0.96) | 0.77 (0.74–0.80) | 0.85 (0.83–0.87) | 0.87 (0.85–0.89) | 0.90 (0.86–0.93) | 0.82 (0.80–0.84) |
| label-free: centre 50% box (Step 21a) | 0.54 (0.52–0.56) | 0.55 (0.52–0.59) | 0.69 (0.67–0.72) | 0.82 (0.80–0.84) | 0.54 (0.52–0.56) | 0.68 (0.66–0.71) |
| label-free: whole image (Step 21a) | 0.46 (0.43–0.50) | 0.37 (0.35–0.40) | 0.58 (0.56–0.59) | 0.69 (0.67–0.72) | 0.47 (0.44–0.49) | 0.60 (0.58–0.61) |
| label-free: random box (Step 21a) | 0.44 (0.38–0.50) | 0.74 (0.71–0.78) | 0.80 (0.78–0.82) | 0.78 (0.76–0.80) | 0.47 (0.43–0.51) | 0.77 (0.75–0.79) |
| label-free: wrong region (Step 21a) | 0.31 (0.26–0.37) | 0.68 (0.65–0.71) | 0.75 (0.73–0.77) | 0.72 (0.69–0.74) | 0.39 (0.35–0.43) | 0.71 (0.69–0.73) |

## 29a-3. U-Net vs oracle-box MedSAM, per dataset (position AUROC, tolerance rule)

| dataset | scans | U-Net | oracle-box MedSAM |
|---|---|---|---|
| BrEaST | 30 | 0.91 (0.82–1.00) † | 1.00 (1.00–1.00) † |
| BUS-BRA | 30 | 1.00 (1.00–1.00) † | 0.94 (0.86–1.00) † |
| BUSI | 30 | 0.84 (0.74–0.95) † | 0.97 (0.92–1.00) † |
| UDIAT | 30 | 1.00 (1.00–1.00) † | 1.00 (1.00–1.00) † |
| BUS-UCLM | 18 | 0.94 (0.75–1.00) † | 1.00 (1.00–1.00) † |
| TN3K | 30 | 0.93 (0.82–1.00) † | 0.99 (0.96–1.00) † |
| DDTI | 30 | 0.77 (0.57–0.93) † | 0.86 (0.74–0.97) † |
| TN5000 | 30 | 0.69 (0.50–0.85) † | 1.00 (1.00–1.00) † |

† = under 30 groups (every dataset cell has at most 30 scans and the groups are fewer): **too small to compare**; only the organ and pooled rows have 30 or more groups.

## 29b-1. HC18: ring annotation to head circumference (no model)

The annotation is a one-pixel ring. It was filled (`binary_fill_holes`), an ellipse was fitted, and the circumference computed with the Ramanujan formula and the pixel size from the CSV, then compared with the provided HC (mm). Three ways of fitting the ellipse; the one used for predicted masks was chosen on dev + val only.

| ellipse fit | split | images | MAE (mm) | median abs (mm) | mean signed error (mm) | max abs (mm) |
|---|---|---|---|---|---|---|
| second moments of the filled mask | dev + val | 599 | 1.334 | 1.032 | +1.334 | 84.21 |
| second moments of the filled mask | test | 400 | 1.643 | 1.030 | +1.643 | 133.41 |
| cv2.fitEllipse on the outer contour of the filled mask | dev + val | 599 | 0.707 | 0.658 | +0.707 | 2.01 |
| cv2.fitEllipse on the outer contour of the filled mask | test | 400 | 0.724 | 0.656 | +0.724 | 1.81 |
| cv2.fitEllipse on the ring pixels | dev + val | 599 | 0.009 | 0.007 | +0.008 | 0.07 |
| cv2.fitEllipse on the ring pixels | test | 400 | 0.009 | 0.007 | +0.008 | 0.05 |

Fitting the ellipse to the ring pixels reproduces the provided HC to 0.009 mm on average (max 0.07 mm over all 999 images): the dataset HC was derived this way. A filled-mask outline reads +0.71 mm too large (half the ring thickness), the second-moment ellipse is worse (MAE 1.33 mm, with outliers up to 133 mm for non-elliptic rings). Predicted masks have no ring, so they use the filled-contour fit with a constant -0.71 mm calibrated on dev + val true masks.

## 29b-2. U-Net head masks, HC on the 400 HC18 test images

| quantity | value |
|---|---|
| images (test split) | 400 (non-empty masks: 400) |
| mask Dice / IoU | 0.967 / 0.942 |
| **HC MAE** (mm) | **2.70** |
| median / 90th percentile absolute error (mm) | 1.85 / 5.53 |
| MAE without the dev-calibrated constant (mm) | 2.94 |
| MAE of the same geometry on the TRUE filled masks (mm) | 0.21 |

Most of the 2.7 mm comes from the segmentation, not the geometry (0.21 mm on true masks). For scale, the planted HC errors in the benchmark are 3-30 mm and x0.5-x2.0, and the +-1 mm errors are below this MAE.

## 29b-3. Planted HC errors vs harmless rewordings (150 HC18 test cases, 1,500 harmless candidates)

Planted errors: the 600 benchmark HC errors (3-30 mm shifts and factors) and up to 11 extra candidates per case built here by changing only the number in the reference: +-1 mm, +-40 mm, x0.5, 0.75, 0.9, 1.1, 1.25, 1.5, 2.0. AUROC = P(error scores lower than a harmless rewording of the same reference), per case, 95% CI by case bootstrap. **"Label oracle" and "true-mask geometry" are circular: the measurement is the reference HC (or a refit of the annotation that defined it).**

| measurement source | rule | benchmark HC errors | planted +-1/40 mm and x0.5-x2.0 | planted shifts (mm) | planted factors | correct-report score |
|---|---|---|---|---|---|---|
| U-Net mask (label-free) | exact (Step 16) | 0.87 (0.84–0.89) | 0.92 (0.91–0.93) | 0.80 (0.78–0.81) | 0.99 (0.98–1.00) | 0.87 (0.85–0.89) |
| U-Net mask (label-free) | tolerance-aware (tau 0.3) | 0.52 (0.52–0.53) | 0.66 (0.65–0.66) | 0.55 (0.54–0.57) | 0.72 (0.71–0.72) | 1.00 (1.00–1.00) |
| true annotation geometry (circular) | exact (Step 16) | 1.00 (1.00–1.00) | 0.99 (0.99–1.00) | 0.98 (0.97–0.99) | 1.00 (1.00–1.00) | 0.99 (0.99–0.99) |
| true annotation geometry (circular) | tolerance-aware (tau 0.3) | 0.52 (0.52–0.53) | 0.66 (0.65–0.66) | 0.56 (0.54–0.57) | 0.71 (0.71–0.71) | 1.00 (1.00–1.00) |
| labelled HC (circular) | exact (Step 16) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) |
| labelled HC (circular) | tolerance-aware (tau 0.3) | 0.52 (0.52–0.53) | 0.66 (0.65–0.66) | 0.56 (0.54–0.57) | 0.71 (0.71–0.71) | 1.00 (1.00–1.00) |

**Reading.** The tolerance-aware rule gives 0.52 for every source, even the labelled HC: with tau = 0.3 an HC of 180 mm is accepted anywhere between 126 and 234 mm, so almost no planted error is seen. (tau was tuned on breast and thyroid size, not on head circumference; no other tau was tried here.) With the exact rule the U-Net check works for large errors and is blind to small ones:

| planted error | AUROC with the U-Net mask (exact rule), mean over cases |
|---|---|
| factor 0.5 | 1.00 (n = 150 cases) |
| factor 0.75 | 0.99 (n = 150 cases) |
| factor 0.9 | 0.98 (n = 150 cases) |
| factor 1.1 | 0.98 (n = 150 cases) |
| factor 1.25 | 1.00 (n = 150 cases) |
| factor 1.5 | 1.00 (n = 150 cases) |
| factor 2 | 1.00 (n = 150 cases) |
| shift_mm -40 | 0.99 (n = 150 cases) |
| shift_mm -1 | 0.71 (n = 150 cases) |
| shift_mm 1 | 0.48 (n = 150 cases) |
| shift_mm 40 | 1.00 (n = 150 cases) |

(each level uses one error vs the case's harmless rewordings, so the cell is an average over cases, not a pooled bootstrap; levels that would make the HC non-positive were skipped. The planted-error check was first run with a text-placement bug (the new number was placed in only 59 of 150 references); it was recomputed from the saved predictions (`step29_run rescore_planted`), with no model run and no second read of the test split.)

## 29b-4. FetalHead

FetalHead (2,833 images) has no pixel size, so head circumference in mm cannot be computed from a mask: **not testable**. Nothing was guessed or estimated for it.

## Caveats

- **Same-dataset test.** Train, val and test are different patients or groups only where the dataset has ids (BrEaST, BUS-BRA, BUS-UCLM, DDTI); BUSI, UDIAT, TN3K, TN5000 and HC18 have none, so near-identical images of one patient can sit on both sides despite the dHash grouping (<= 4 bits merged; dev images in <= 8-bit clusters that reach val or test were dropped, 15 breast, 148 thyroid, 26 HC18). TN5000 (no training images) is the only cross-dataset check.
- **Small, random-init network, one seed, one split.** No pretrained encoder (weights not available offline; none downloaded). Val Dice is the selection signal; the test Dice and image-check numbers come from one run and have not been repeated.
- **Image-check numbers are computed on the 228 scans of Step 21a / 24** (30 per dataset, at most 3 per group), not on all test images, and the reports being checked are our templated candidates. The check scores claims in the text against a measurement from the mask, so thyroid and breast positions are judged on a 3x3 grid.
- **Thyroid truth for TN5000** is a box, so Dice is not defined there (box IoU instead); thyroid Dice rests on 60 scans.
- **29b geometry:** the HC18 mask Dice is high (0.97) because the head is a large, clear object; the tolerance rule is shown but is not usable for HC; the planted +-1 mm errors cannot be detected at 2.7 mm MAE. The label-oracle and true-geometry rows are circular and are listed only to show the ceiling.
- Step 23 (lesion detector) is not run; this step replaces it. No claim of being first; possible training exposure of none of the models here (all trained from scratch on our dev split).
