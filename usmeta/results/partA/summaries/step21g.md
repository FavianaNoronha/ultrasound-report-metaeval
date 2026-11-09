# Step 21g — Leakage sensitivity (test split, saved scores only)

**What was dropped:** test images whose near-duplicate cluster (dHash ≤ 8 bits within one dataset, Step 21f; a LOOSE check, not verified duplicates) also has members in dev or val: 431 test images in total, 128 of them have candidates in `bench_test_v2d` (breast 8, thyroid 84, fetal head 36); per dataset: BUS-BRA 2 of 750, BUSI 12 of 312, BrEaST 1 of 103, DDTI 87 of 192, FetalHead 184 of 1136, HC18 30 of 400, TN3K 38 of 1398, TN5000 77 of 2000. All their candidates are removed from the test comparison; nothing else changes (same scorers, same pairs, same method as Step 19a).

## Headline
- **No headline test AUROC changes by more than 0.05 when the leak-risk images are dropped** (largest change +0.033, thyroid image-check size, Step 16 rule; the next largest are +0.032 (thyroid image-check size, Step 20 rule) and +0.022 (judge sentence_f1, thyroid); every other cell is within ±0.017). The conclusions of Steps 5-12, 19a and 20 do not depend on those images.
- The few cells with a change whose interval excludes zero all move UP after dropping (thyroid: BLEU +0.013, chrF +0.009, judge sentence_f1 +0.022, judge_score +0.017, image size +0.032, image all +0.014), i.e. the near-duplicate images were not inflating the scores; the word scorers stay at 0.33-0.54 (thyroid), 0.42-0.63 (breast), 0.08-0.30 (fetal head).
- **Looks off / limits:** the 8-bit clusters are loose and unverified (Step 21f); they flag 431 test images over all datasets, but the benchmark samples only 128 of them (breast 8, thyroid 84, fetal head 36), and DDTI alone contributes 87 of its 192 test images (a dataset with many near-identical frames). Breast has almost nothing to drop (8 of 646 cases; 0 of the 138 image-check scans), so the breast conclusion is "nothing to test", not "robust to leakage". Thyroid drops 84 of 450 cases (19%). Fetal head 36 of 303. The image-check scans: breast 0 dropped; thyroid 11 of 90 (the 228-scan image-check set has no overlap with the dropped breast images).

## Flag: changes above 0.05

**No cell changes by more than 0.05.**

Method: AUROC per case (error vs small / matched / large harmless candidates, ties 0.5), mean over cases; group bootstrap, 1,000 resamples, seed 0, with the full and the reduced set resampled together so the change has its own interval. Under 30 groups = too small to compare. Judge rows use only the judged subset (Steps 10d + 12).

## Breast

| scorer | cases | groups | dropped | groups kept | full-test AUROC | reduced AUROC | change |
|---|---|---|---|---|---|---|---|
| BLEU | 646 | 413 | 8 | 406 | 0.57 (0.51–0.62) | 0.57 (0.51–0.62) | +0.001 (+0.000 to +0.002) |
| ROUGE-L | 646 | 413 | 8 | 406 | 0.48 (0.41–0.54) | 0.48 (0.42–0.54) | +0.002 (+0.001 to +0.003) |
| chrF | 646 | 413 | 8 | 406 | 0.47 (0.40–0.53) | 0.47 (0.40–0.53) | +0.001 (+0.000 to +0.003) |
| BERTScore | 646 | 413 | 8 | 406 | 0.42 (0.35–0.49) | 0.42 (0.35–0.49) | +0.002 (+0.001 to +0.004) |
| RaTEScore | 646 | 413 | 8 | 406 | 0.62 (0.58–0.67) | 0.63 (0.58–0.67) | +0.001 (+0.000 to +0.002) |
| finding_f1 | 646 | 413 | 8 | 406 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | +0.000 (+0.000 to +0.000) |
| sentence_f1 | 400 | 257 | 3 | 254 | 0.86 (0.83–0.89) | 0.86 (0.83–0.89) | -0.000 (-0.002 to +0.001) |
| judge_score | 400 | 257 | 3 | 254 | 0.93 (0.91–0.95) | 0.93 (0.90–0.95) | -0.001 (-0.001 to +0.000) |
| image position (Step 20 tolerance) | 84 | 76 | 0 | 76 | 0.98 (0.96–1.00) | 0.98 (0.96–1.00) | +0.000 (+0.000 to +0.000) |
| image size (Step 20 tolerance) | 138 | 120 | 0 | 120 | 0.94 (0.91–0.96) | 0.94 (0.91–0.96) | +0.000 (+0.000 to +0.000) |
| image all (Step 20 tolerance) | 138 | 120 | 0 | 120 | 0.96 (0.95–0.97) | 0.96 (0.95–0.97) | +0.000 (+0.000 to +0.000) |
| image position (Step 16 exact-match) | 84 | 76 | 0 | 76 | 0.96 (0.93–0.99) | 0.96 (0.93–0.99) | +0.000 (+0.000 to +0.000) |
| image size (Step 16 exact-match) | 138 | 120 | 0 | 120 | 0.90 (0.87–0.94) | 0.90 (0.87–0.94) | +0.000 (+0.000 to +0.000) |
| image all (Step 16 exact-match) | 138 | 120 | 0 | 120 | 0.94 (0.92–0.96) | 0.94 (0.92–0.96) | +0.000 (+0.000 to +0.000) |

## Thyroid

| scorer | cases | groups | dropped | groups kept | full-test AUROC | reduced AUROC | change |
|---|---|---|---|---|---|---|---|
| BLEU | 450 | 417 | 84 | 351 | 0.53 (0.52–0.53) | 0.54 (0.53–0.55) | +0.013 (+0.009 to +0.017) |
| ROUGE-L | 450 | 417 | 84 | 351 | 0.39 (0.39–0.40) | 0.39 (0.39–0.40) | +0.000 (-0.004 to +0.003) |
| chrF | 450 | 417 | 84 | 351 | 0.38 (0.37–0.38) | 0.38 (0.38–0.39) | +0.009 (+0.005 to +0.012) |
| BERTScore | 450 | 417 | 84 | 351 | 0.33 (0.32–0.33) | 0.33 (0.32–0.33) | -0.002 (-0.005 to +0.002) |
| RaTEScore | 450 | 417 | 84 | 351 | 0.48 (0.48–0.49) | 0.48 (0.48–0.49) | +0.001 (-0.004 to +0.005) |
| finding_f1 | 450 | 417 | 84 | 351 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | +0.000 (+0.000 to +0.000) |
| sentence_f1 | 248 | 239 | 43 | 203 | 0.91 (0.89–0.93) | 0.93 (0.92–0.95) | +0.022 (+0.009 to +0.035) |
| judge_score | 248 | 239 | 43 | 203 | 0.97 (0.96–0.98) | 0.99 (0.98–1.00) | +0.017 (+0.005 to +0.030) |
| image position (Step 20 tolerance) | 50 | 49 | 2 | 47 | 0.95 (0.90–0.99) | 0.95 (0.89–0.99) | -0.002 (-0.007 to +0.000) |
| image size (Step 20 tolerance) | 90 | 86 | 11 | 77 | 0.84 (0.79–0.88) | 0.87 (0.83–0.91) | +0.032 (+0.010 to +0.056) |
| image all (Step 20 tolerance) | 90 | 86 | 11 | 77 | 0.89 (0.87–0.92) | 0.91 (0.88–0.93) | +0.014 (+0.002 to +0.027) |
| image position (Step 16 exact-match) | 50 | 49 | 2 | 47 | 0.92 (0.86–0.97) | 0.92 (0.86–0.97) | -0.003 (-0.010 to +0.000) |
| image size (Step 16 exact-match) | 90 | 86 | 11 | 77 | 0.78 (0.73–0.84) | 0.82 (0.76–0.87) | +0.033 (+0.009 to +0.061) |
| image all (Step 16 exact-match) | 90 | 86 | 11 | 77 | 0.86 (0.83–0.89) | 0.88 (0.85–0.91) | +0.015 (+0.002 to +0.029) |

## Fetal head

| scorer | cases | groups | dropped | groups kept | full-test AUROC | reduced AUROC | change |
|---|---|---|---|---|---|---|---|
| BLEU | 303 | 204 | 36 | 182 | 0.30 (0.30–0.31) | 0.30 (0.30–0.31) | +0.000 (-0.001 to +0.001) |
| ROUGE-L | 303 | 204 | 36 | 182 | 0.22 (0.21–0.22) | 0.22 (0.21–0.22) | +0.000 (+0.000 to +0.001) |
| chrF | 303 | 204 | 36 | 182 | 0.23 (0.21–0.25) | 0.23 (0.21–0.25) | -0.000 (-0.004 to +0.003) |
| BERTScore | 303 | 204 | 36 | 182 | 0.08 (0.06–0.09) | 0.08 (0.06–0.09) | -0.001 (-0.005 to +0.002) |
| RaTEScore | 303 | 204 | 36 | 182 | 0.29 (0.27–0.30) | 0.28 (0.27–0.30) | -0.004 (-0.008 to +0.000) |
| finding_f1 | 303 | 204 | 36 | 182 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | +0.000 (+0.000 to +0.000) |
| sentence_f1 | 142 | 105 | 15 | 96 | 0.92 (0.89–0.94) | 0.92 (0.89–0.94) | -0.003 (-0.010 to +0.005) |
| judge_score | 142 | 105 | 15 | 96 | 0.92 (0.90–0.94) | 0.92 (0.90–0.94) | -0.000 (-0.007 to +0.008) |
