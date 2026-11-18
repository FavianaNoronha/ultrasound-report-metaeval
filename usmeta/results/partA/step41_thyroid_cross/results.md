# Step 41: does the label-free U-Net image check transfer between thyroid datasets?

Pre-registration: [PREREG.md](PREREG.md) (committed before any training or test number). Limitations: [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md). Code: `usmeta/step41_thyroid_cross.py`, `step41_report.py` (new files; `step29_seg.py` training, `step29_run.py` scoring and the Step 20 check imported unchanged). Test split read once (logged: `usmeta.step41_thyroid_cross`).

## Decision lines

- **Train on DDTI dev -> test on TN3K (30 scans, 17 groups with a defined position AUROC): position AUROC 0.69 (0.51-0.85) against 0.93 (0.82-1.00) in-dataset (Step 29 model, same scans). Within 0.05 of in-dataset: no; lower bound >= 0.70: no. Decision: too small (fewer than 30 groups): not decided; indicative rule outcome: would not transfer.**
- **Train on TN3K dev -> test on DDTI (30 scans, 15 groups with a defined position AUROC): position AUROC 0.64 (0.48-0.80) against 0.77 (0.57-0.93) in-dataset (Step 29 model, same scans). Within 0.05 of in-dataset: no; lower bound >= 0.70: no. Decision: too small (fewer than 30 groups): not decided; indicative rule outcome: would not transfer.**

Pooled over both folds (60 scans, descriptive only, no decision): position AUROC 0.67 (0.54-0.78) (32 groups) against 0.85 (0.74-0.95) for the in-dataset Step 29 model on the same scans. Rule (fixed in the PREREG): a fold transfers iff position AUROC is within 0.05 of the in-dataset value on the same scans AND its 95% lower bound is >= 0.70; a cell under 30 groups is reported, not decided.

**DDTI is small:** the DDTI-trained fold has about 101 dev images against 1337 for TN3K, so a weak DDTI-trained fold may reflect training-set size and not domain shift; this design cannot tell the two apart.

## Training per fold (DEV of the training dataset; VAL of the same dataset)

| trained on | tested on | dev images (after leak filter and mask check) | val images | epochs | best val Dice (256 px) | post-processing chosen on val | minutes |
|---|---|---|---|---|---|---|---|
| TN3K | DDTI | 1337 (dev 1398, dropped 61) | 697 | 30 | 0.759 | threshold 0.4, raw | 19 |
| DDTI | TN3K | 101 (dev 192, dropped 87) | 92 | 28 | 0.632 | threshold 0.5, raw | 2 |

For reference the Step 29 thyroid model (TN3K + DDTI): 1438 dev images, 789 val images, 30 epochs, best val Dice 0.751. Fold time cap 1 h: no fold reached it.

## Cross-dataset vs in-dataset on the same test scans

| held-out dataset (trained on) | scans | Dice cross | Dice in-dataset (Step 29) | detection cross / in-dataset | position AUROC cross | position AUROC in-dataset | size AUROC cross | size in-dataset | all-checkable cross | all-checkable in-dataset | correct-report score cross | in-dataset |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TN3K (trained on DDTI) | 30 | 0.28 (0.18–0.38) | 0.82 (0.75–0.88) | 93% / 100% | 0.69 (0.51–0.85) † | 0.93 (0.82–1.00) † | 0.73 (0.62–0.82) | 0.90 (0.83–0.96) | 0.74 (0.67–0.81) | 0.92 (0.87–0.96) | 0.68 (0.59–0.78) | 0.94 (0.90–0.98) |
| DDTI (trained on TN3K) | 30 | 0.58 (0.47–0.68) † | 0.68 (0.60–0.75) † | 100% / 100% | 0.64 (0.48–0.80) † | 0.77 (0.57–0.93) † | 0.69 (0.59–0.79) † | 0.82 (0.71–0.91) † | 0.80 (0.73–0.85) † | 0.86 (0.79–0.91) † | 0.86 (0.80–0.91) † | 0.91 (0.85–0.95) † |
| pooled (both folds) | 60 | 0.43 (0.34–0.51) | 0.75 (0.69–0.80) | 97% / 100% | 0.67 (0.54–0.78) | 0.85 (0.74–0.95) | 0.71 (0.64–0.78) | 0.86 (0.80–0.92) | 0.77 (0.73–0.81) | 0.89 (0.84–0.92) | 0.77 (0.70–0.83) | 0.92 (0.89–0.95) |

† = under 30 groups (groups with a defined per-scan value): too small to compare. Dice uses the true mask; detection = share of non-empty predictions. TN3K has 30 groups and DDTI 26 among the 60 scans, so the DDTI cells can never reach 30.

## Exact-rule variant (Step 16 exact match, for reference)

| held-out dataset | position AUROC cross | in-dataset | all-checkable cross | in-dataset |
|---|---|---|---|---|
| TN3K | 0.68 (0.53–0.82) † | 0.91 (0.82–1.00) † | 0.75 (0.67–0.82) | 0.92 (0.87–0.97) |
| DDTI | 0.59 (0.44–0.75) † | 0.75 (0.56–0.91) † | 0.79 (0.72–0.85) † | 0.85 (0.78–0.91) † |
| pooled | 0.64 (0.53–0.74) | 0.83 (0.72–0.94) | 0.77 (0.72–0.82) | 0.89 (0.84–0.93) |

## Deviations from the PREREG

- None known at the time of writing (this line is edited by hand if a deviation occurs).

## Caveats

- 30 scans per held-out dataset (26 groups in DDTI); one seed, one split, no repeat; random-init encoder; templated candidates; thyroid only.
- The in-dataset comparison model (Step 29 thyroid) was trained on both TN3K and DDTI dev images, so it had more and more varied training data than either fold: part of any gap is training-set size, not domain shift.
- Neither dataset records the scanner or centre, so "dataset" stands in for domain; images shared between the datasets, if any, are not caught by the within-dataset leak filter.
