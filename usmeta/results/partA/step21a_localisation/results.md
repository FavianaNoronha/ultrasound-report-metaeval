# Step 21a — Label-free localisation for the image check (breast + thyroid, the same 228 test scans as Steps 16 / 19b)

**This is label-free prompting, NOT a detector.** Nothing finds the lesion. The prompts need no mask or box label, except that `random` and `wrongregion` boxes reuse the SIZE of the true box (to keep box size comparable), which leaks size information (see below). Everything else is Step 16: MedSAM (`wanglab/medsam-vit-base`, MPS), `mask_verified_facts`, the same reports (`bench_v2d`), planted size errors ×0.5 to ×2. Conditions (seed 0, crc32(case|condition)): `centre50` = centred box covering 50% of the image area; `whole` = whole-image box; `random` = box of the true box's size at a random position; `wrongregion` = box of the true box's size at a random position with NO overlap with the true lesion box (for 30 of 228 scans the true box was too large to avoid, so the box was scaled down until it fitted: listed in `wrongregion_fallbacks.json`). `exact` = the oracle box of Step 16 (cached masks). 912 new masks (23 min; cached in the git-ignored `local_data/partb_localisation`). Code: `usmeta/step21_localisation.py`.

## Headline (breast + thyroid pooled, n = 228 scans)
| prompt | mask IoU (n=198) | AUROC all checkable | position | size | correct report scores | correct reports < 0.5 | correct reports < 0.8 |
|---|---|---|---|---|---|---|---|
| exact box (oracle, Step 16) | 0.66 (0.64–0.69) | 0.91 (0.89–0.93) | 0.95 (0.92–0.97) | 0.86 (0.82–0.89) | 0.852 | 0.02 | 0.25 |
| centre box, 50% of image | 0.25 (0.21–0.28) | 0.68 (0.66–0.71) | 0.54 (0.52–0.57) | 0.53 (0.49–0.58) | 0.655 | 0.22 | 0.70 |
| whole-image box | 0.10 (0.08–0.11) | 0.60 (0.58–0.61) | 0.47 (0.44–0.49) | 0.41 (0.39–0.44) | 0.543 | 0.43 | 0.86 |
| random box, true-box size | 0.09 (0.07–0.12) | 0.77 (0.75–0.79) | 0.47 (0.43–0.51) | 0.67 (0.63–0.71) | 0.646 | 0.17 | 0.79 |
| wrong-region box (no overlap with lesion box) | 0.00 (0.00–0.00) | 0.71 (0.69–0.73) | 0.39 (0.35–0.43) | 0.58 (0.55–0.62) | 0.581 | 0.25 | 0.97 |

RaTEScore on the same cases (no image): all checkable 0.62 (0.61–0.63), position 0.28 (0.27–0.30), size 0.52 (0.49–0.54).

- **Position needs a localisation and does not survive without one:** position AUROC 0.54 (0.52–0.57) (centre box), 0.47 (0.44–0.49) (whole image), 0.47 (0.43–0.51) (random box), 0.39 (0.35–0.43) (wrong region), i.e. chance or below, against 0.95 (0.92–0.97) with the oracle box.
- **The size result is partly a leak.** Size AUROC with the random and wrong-region boxes (0.67 (0.63–0.71), 0.58 (0.55–0.62)) is above chance only because those boxes carry the true box's size; with boxes that carry no size information it is 0.53 (0.49–0.58) (centre) and 0.41 (0.39–0.44) (whole image, below chance).
- **The all-checkable AUROC of 0.60–0.77 is NOT evidence of localisation.** It is driven by claims that need no localisation: errors that say "no lesion" are caught at AUROC 1.00 in every condition (any non-empty mask contradicts them), and count / orientation claims keep AUROC 0.84–0.97 / 0.60–0.83. The random-box number (0.77) is above RaTEScore (0.62) only for that reason.
- **False alarms rise sharply:** a correct report scores 0.852 with the oracle box and 0.655, 0.543, 0.646, 0.581 without it; the share of correct reports flagged below 0.5 goes from 0.02 to 0.22 (centre), 0.43 (whole), 0.17 (random), 0.25 (wrong region); below 0.8 it is 0.25 → 0.97–0.86.
- **Reading:** the image check's advantage over text (Step 16) depends on being told where the lesion is. Without a localisation, position claims are at chance and correct reports are marked down heavily; a lesion detector (not tested here) is the missing piece.

## AUROC by claim type (pooled, all conditions)
| claim type | exact | centre50 | whole | random | wrongregion |
|---|---|---|---|---|---|
| lesion presence | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) |
| count | 1.00 (0.99–1.00) | 0.94 (0.91–0.98) | 0.84 (0.79–0.88) | 0.97 (0.94–0.99) | 0.94 (0.91–0.97) |
| orientation | 0.90 (0.87–0.94) | 0.67 (0.61–0.74) | 0.60 (0.54–0.67) | 0.83 (0.78–0.88) | 0.82 (0.77–0.87) |
| position | 0.95 (0.92–0.97) | 0.54 (0.52–0.57) | 0.47 (0.44–0.49) | 0.47 (0.43–0.51) | 0.39 (0.35–0.43) |
| size | 0.86 (0.82–0.89) | 0.53 (0.49–0.58) | 0.41 (0.39–0.44) | 0.67 (0.63–0.71) | 0.58 (0.55–0.62) |

## Per dataset (test; † n < 30 scans: too small to compare)
| dataset | prompt | n | mask IoU (TN5000: box IoU) | AUROC all checkable | position | size | correct report scores |
|---|---|---|---|---|---|---|---|
| BrEaST | exact | 30 | 0.74 (0.69–0.79) | 0.93 (0.88–0.97) | 0.97 (0.91–1.00) | 0.88 (0.78–0.96) | 0.894 |
| BrEaST | centre50 | 30 | 0.28 (0.20–0.37) | 0.69 (0.63–0.75) | 0.56 (0.50–0.65) | 0.51 (0.41–0.62) | 0.683 |
| BrEaST | whole | 30 | 0.09 (0.05–0.14) | 0.61 (0.56–0.66) | 0.44 (0.35–0.50) | 0.45 (0.36–0.54) | 0.573 |
| BrEaST | random | 30 | 0.13 (0.05–0.22) | 0.77 (0.72–0.83) | 0.50 (0.35–0.65) | 0.68 (0.58–0.79) | 0.682 |
| BrEaST | wrongregion | 30 | 0.00 (0.00–0.00) | 0.70 (0.65–0.75) | 0.35 (0.24–0.50) | 0.56 (0.47–0.67) | 0.587 |
| BUS-BRA | exact | 30 | 0.61 (0.56–0.67) | 0.91 (0.86–0.95) | 0.94 (0.85–1.00) | 0.83 (0.73–0.91) | 0.865 |
| BUS-BRA | centre50 | 30 | 0.23 (0.18–0.30) | 0.61 (0.56–0.67) | 0.53 (0.50–0.60) | 0.53 (0.43–0.67) | 0.570 |
| BUS-BRA | whole | 30 | 0.09 (0.06–0.12) | 0.48 (0.45–0.51) | 0.41 (0.31–0.50) | 0.33 (0.29–0.38) | 0.459 |
| BUS-BRA | random | 30 | 0.12 (0.05–0.20) | 0.75 (0.69–0.81) | 0.44 (0.31–0.58) | 0.59 (0.49–0.70) | 0.652 |
| BUS-BRA | wrongregion | 30 | 0.00 (0.00–0.00) | 0.73 (0.68–0.79) | 0.29 (0.16–0.43) | 0.58 (0.49–0.68) | 0.615 |
| BUSI | exact | 30 | 0.73 (0.68–0.77) | 0.95 (0.91–0.98) | 0.92 (0.84–1.00) | 0.93 (0.84–1.00) | 0.894 |
| BUSI | centre50 | 30 | 0.32 (0.22–0.42) | 0.77 (0.71–0.83) | 0.58 (0.50–0.66) | 0.64 (0.53–0.74) | 0.730 |
| BUSI | whole | 30 | 0.11 (0.07–0.16) | 0.62 (0.58–0.67) | 0.50 (0.42–0.58) | 0.44 (0.36–0.53) | 0.592 |
| BUSI | random | 30 | 0.07 (0.02–0.14) | 0.76 (0.71–0.81) | 0.49 (0.38–0.59) | 0.62 (0.52–0.73) | 0.659 |
| BUSI | wrongregion | 30 | 0.00 (0.00–0.00) | 0.71 (0.67–0.76) | 0.33 (0.21–0.42) | 0.57 (0.48–0.66) | 0.597 |
| UDIAT | exact | 30 | 0.80 (0.77–0.84) | 0.98 (0.96–1.00) | 1.00 (1.00–1.00) | 0.98 (0.95–1.00) | 0.943 |
| UDIAT | centre50 | 30 | 0.22 (0.13–0.32) | 0.70 (0.63–0.76) | 0.59 (0.52–0.67) | 0.52 (0.39–0.64) | 0.665 |
| UDIAT | whole | 30 | 0.07 (0.03–0.13) | 0.64 (0.60–0.69) | 0.50 (0.43–0.57) | 0.47 (0.39–0.55) | 0.549 |
| UDIAT | random | 30 | 0.06 (0.01–0.14) | 0.75 (0.70–0.80) | 0.48 (0.39–0.57) | 0.62 (0.52–0.73) | 0.645 |
| UDIAT | wrongregion | 30 | 0.00 (0.00–0.00) | 0.76 (0.71–0.81) | 0.46 (0.39–0.50) | 0.63 (0.53–0.73) | 0.646 |
| BUS-UCLM † | exact | 18 | 0.66 (0.53–0.77) | 0.95 (0.87–0.99) | 1.00 (1.00–1.00) | 0.91 (0.76–1.00) | 0.871 |
| BUS-UCLM † | centre50 | 18 | 0.28 (0.09–0.50) | 0.75 (0.68–0.81) | 0.50 (0.50–0.50) | 0.59 (0.43–0.71) | 0.748 |
| BUS-UCLM † | whole | 18 | 0.10 (0.05–0.16) | 0.64 (0.60–0.69) | 0.44 (0.25–0.50) | 0.34 (0.26–0.43) | 0.656 |
| BUS-UCLM † | random | 18 | 0.11 (0.03–0.18) | 0.80 (0.74–0.86) | 0.50 (0.33–0.67) | 0.69 (0.57–0.80) | 0.673 |
| BUS-UCLM † | wrongregion | 18 | 0.00 (0.00–0.00) | 0.70 (0.64–0.78) | 0.50 (0.50–0.50) | 0.49 (0.35–0.69) | 0.581 |
| TN3K | exact | 30 | 0.60 (0.53–0.66) | 0.89 (0.84–0.93) | 0.94 (0.85–1.00) | 0.84 (0.74–0.92) | 0.824 |
| TN3K | centre50 | 30 | 0.26 (0.18–0.34) | 0.72 (0.66–0.78) | 0.50 (0.50–0.50) | 0.59 (0.47–0.70) | 0.667 |
| TN3K | whole | 30 | 0.11 (0.07–0.16) | 0.59 (0.54–0.65) | 0.50 (0.41–0.59) | 0.44 (0.35–0.55) | 0.502 |
| TN3K | random | 30 | 0.12 (0.05–0.19) | 0.79 (0.73–0.85) | 0.44 (0.32–0.59) | 0.72 (0.62–0.82) | 0.658 |
| TN3K | wrongregion | 30 | 0.00 (0.00–0.00) | 0.72 (0.67–0.78) | 0.38 (0.29–0.47) | 0.58 (0.48–0.68) | 0.585 |
| DDTI | exact | 30 | 0.49 (0.43–0.54) | 0.82 (0.75–0.88) | 0.84 (0.72–0.97) | 0.69 (0.59–0.80) | 0.715 |
| DDTI | centre50 | 30 | 0.15 (0.11–0.20) | 0.67 (0.59–0.74) | 0.50 (0.50–0.50) | 0.53 (0.40–0.67) | 0.605 |
| DDTI | whole | 30 | 0.10 (0.07–0.13) | 0.59 (0.56–0.62) | 0.44 (0.35–0.50) | 0.36 (0.31–0.40) | 0.515 |
| DDTI | random | 30 | 0.06 (0.02–0.11) | 0.74 (0.66–0.82) | 0.38 (0.25–0.47) | 0.69 (0.58–0.80) | 0.560 |
| DDTI | wrongregion | 30 | 0.00 (0.00–0.00) | 0.63 (0.57–0.70) | 0.38 (0.25–0.50) | 0.53 (0.43–0.66) | 0.463 |
| TN5000 | exact | 30 | 0.58 (0.52–0.64) | 0.88 (0.83–0.93) | 0.97 (0.91–1.00) | 0.82 (0.72–0.89) | 0.822 |
| TN5000 | centre50 | 30 | 0.12 (0.08–0.18) | 0.60 (0.56–0.64) | 0.53 (0.50–0.59) | 0.38 (0.31–0.45) | 0.608 |
| TN5000 | whole | 30 | 0.04 (0.03–0.06) | 0.62 (0.58–0.65) | 0.47 (0.41–0.50) | 0.44 (0.40–0.48) | 0.540 |
| TN5000 | random | 30 | 0.01 (0.00–0.02) | 0.79 (0.73–0.84) | 0.53 (0.46–0.62) | 0.73 (0.63–0.84) | 0.648 |
| TN5000 | wrongregion | 30 | 0.00 (0.00–0.00) | 0.73 (0.67–0.79) | 0.46 (0.40–0.50) | 0.69 (0.58–0.81) | 0.574 |

## Limits
Boxes for `random` / `wrongregion` use the true box size (leak); 30 scans per dataset (BUS-UCLM 18), at most 3 per group; planted size errors are large (×0.5 to ×2); MedSAM may have seen these datasets; the correct-report score cannot reach 1.0 for any predicted-mask check; fetal head is not included (the check does not work there, Step 16). See `docs/LIMITATIONS.md`.
