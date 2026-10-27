# Step 16 — Part B: the image check with PREDICTED masks (non-circular)

**Question.** In Step 8 the image check read size and position from the TRUE masks, and the reference facts were measured from those same masks, so the check could not fail on a true report. Here a segmenter predicts the mask, Layer 3 reads the facts from the predicted mask, and we ask: does it still catch planted size / position errors, and how often does it wrongly punish a correct report?

## Headline (test split, 288 scans, 10 datasets)
> **Read first: this is the easy case.** The box prompts came from the TRUE masks (oracle localisation). The realistic case, a model finding the lesion itself, is NOT tested, because the Qwen and MedGemma boxes are too poor to use as prompts. The planted size errors are large (×0.5 to ×2). The fetal-head failure is a mismatch between the true skull outline and MedSAM's inner-brain outline: a ground-truth/segmenter disagreement, not proof that image checks fail on fetal head.

- **MedSAM from true-mask boxes reaches IoU 0.62 (0.59–0.65), Dice 0.74 (0.72–0.77)** over the 258 scans with true masks (exact prompt). True mask vs true mask = 1.00 (sanity row). By dataset: UDIAT 0.80, BrEaST 0.74, BUSI 0.73, BUS-UCLM 0.66 (n=18, too small to compare), BUS-BRA 0.61, TN3K 0.60, HC18 0.52, DDTI 0.49, FetalHead 0.44. TN5000 has boxes only: box IoU of the predicted mask vs the true box 0.58.
- **10% and 20% prompt errors did not hurt** (pooled IoU 0.65 and 0.64 vs 0.62 for the exact box). We did not test why; do not read it as "worse prompts are better".
- **Breast and thyroid: the predicted-mask check still separates planted errors from harmless rewordings.** AUROC pooled over the eight breast/thyroid datasets (exact box): 0.91 (0.89–0.93) for all mask-checkable error types, 0.95 (0.92–0.97) for position errors (n=134 cases), 0.86 (0.82–0.89) for size errors (n=228). With true masks it was 1.00 by construction. Text scorers on the same cases: BLEU 0.42, ROUGE-L 0.33, chrF 0.33, BERTScore 0.25, RaTEScore 0.62 (all errors).
- **Fetal head: the predicted-mask check is no better than the text scorers.** AUROC 0.46 (HC18) and 0.50 (FetalHead) vs 0.44 / 0.54 for RaTEScore (chance = 0.5). The true head mask is the whole skull outline; MedSAM outlines the brain inside it, so the head circumference comes out too small (median signed error −26 to −32 mm HC18, −58 to −78 mm FetalHead). Pooling all 10 datasets gives 0.82 (0.79–0.85) only because the fetal sets pull it down.
- **A correct report is punished by the check.** The mean score of identical (correct) reports is 0.68 pooled over all 10 datasets (0.71–0.94 per breast/thyroid dataset, ~0.00 on the two fetal-head sets); only 0–20% of correct breast/thyroid reports score a full 1.0. With true masks it is 1.000. This is the expected cost of a non-circular check, not a bug: the identical-copy mean is 1.0 only when the check reads the same masks as the reference.

## What was run
- **Segmenter:** MedSAM, `wanglab/medsam-vit-base` (SAM ViT-B fine-tuned for medical images), Hugging Face port run with `transformers` `SamModel` on the Mac GPU (MPS), box prompt, single mask (`multimask_output=False`), threshold at the model's logit 0. Licence Apache-2.0, 375 MB, downloaded to the HF cache only; recorded in `docs/third_party.md`. SAM2 was not needed. The HF processor keeps the aspect ratio and uses SAM's normalisation, which differs from the original MedSAM script; we did not compare the two.
- **Prompts:** TRUE boxes only, from the largest connected region of the true mask (HC18: filled ellipse; DDTI: rasterised outline; TN5000: the true box), plus two jittered versions: enlarged by 10% / 20% and the centre shifted by ±5% / ±10% of the box size (random signs, seeded by case id). **Qwen2.5-VL and MedGemma boxes were NOT used as prompts**: their IoU with the true boxes was too low in Steps 11 and 14, so they would measure the report writer, not the check.
- **Scans:** test split only (`usmeta.splits.load('test')`, access logged), cases that are in `bench_v2d.jsonl` and have a lesion and a mask, shuffled with seed 0, at most 3 scans per patient/exam group, **30 per dataset instead of ~20** so the per-dataset rows can reach the n ≥ 30 rule; BUS-UCLM has only 18 such scans. 288 scans in all (258 with a true mask + 30 TN5000 with boxes only).
- **Targets:** the segmenter alone is scored against the largest true region (the object the box points at). Layer 3 then reads facts from the full predicted mask with the same code as Step 8 (`layer3.measured_facts`, `layer3.mask_verified`); HC18 head circumference is the Ramanujan perimeter of the ellipse fitted to the predicted mask, compared with the labelled value.
- **Errors scored:** the planted errors and harmless rewordings of `bench_v2d` for the same scans (position, size, lesion, count, orientation). AUROC is per case, 95% CIs resample patient/exam groups (1,000 resamples, seed 0). Hausdorff is reported as HD95 in % of the image diagonal (cheap, size-independent).

# Full tables

### 1. The segmenter alone (predicted mask vs TRUE mask, test split)

Target = the largest connected region of the true mask (the object the box prompt points at). 95% CIs resample patient/exam groups (1,000 resamples, seed 0). † = n < 30: too small to compare.

| dataset | n scans | prompt | IoU | Dice | HD95 (% of image diagonal) | empty masks |
|---|---|---|---|---|---|---|
| BrEaST | 30 | true_vs_true | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.0 (0.0–0.0) | 0 |
| BrEaST | 30 | exact | 0.74 (0.69–0.79) | 0.84 (0.80–0.88) | 3.1 (2.4–3.9) | 0 |
| BrEaST | 30 | j10 | 0.74 (0.69–0.79) | 0.84 (0.80–0.88) | 3.5 (2.7–4.4) | 0 |
| BrEaST | 30 | j20 | 0.72 (0.65–0.78) | 0.82 (0.75–0.87) | 3.7 (2.7–4.9) | 0 |
| BUS-BRA | 30 | true_vs_true | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.0 (0.0–0.0) | 0 |
| BUS-BRA | 30 | exact | 0.61 (0.56–0.66) | 0.75 (0.70–0.79) | 4.7 (3.7–6.0) | 0 |
| BUS-BRA | 30 | j10 | 0.66 (0.61–0.71) | 0.79 (0.75–0.82) | 4.1 (3.2–5.5) | 0 |
| BUS-BRA | 30 | j20 | 0.68 (0.62–0.74) | 0.80 (0.75–0.84) | 4.3 (3.2–5.9) | 0 |
| BUSI | 30 | true_vs_true | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.0 (0.0–0.0) | 0 |
| BUSI | 30 | exact | 0.73 (0.68–0.77) | 0.83 (0.79–0.87) | 4.5 (3.2–5.9) | 0 |
| BUSI | 30 | j10 | 0.74 (0.69–0.79) | 0.85 (0.80–0.88) | 4.4 (3.1–5.9) | 0 |
| BUSI | 30 | j20 | 0.73 (0.66–0.79) | 0.83 (0.76–0.88) | 4.7 (3.2–6.2) | 0 |
| UDIAT | 30 | true_vs_true | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.0 (0.0–0.0) | 0 |
| UDIAT | 30 | exact | 0.80 (0.77–0.84) | 0.89 (0.86–0.91) | 2.1 (1.4–2.9) | 0 |
| UDIAT | 30 | j10 | 0.82 (0.78–0.85) | 0.90 (0.87–0.92) | 1.8 (1.2–2.6) | 0 |
| UDIAT | 30 | j20 | 0.82 (0.79–0.85) | 0.90 (0.88–0.92) | 2.2 (1.5–3.1) | 0 |
| BUS-UCLM † | 18 | true_vs_true | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.0 (0.0–0.0) | 0 |
| BUS-UCLM † | 18 | exact | 0.66 (0.54–0.78) | 0.78 (0.68–0.87) | 3.8 (2.2–5.6) | 0 |
| BUS-UCLM † | 18 | j10 | 0.69 (0.58–0.80) | 0.80 (0.72–0.89) | 3.6 (2.0–5.4) | 0 |
| BUS-UCLM † | 18 | j20 | 0.71 (0.61–0.80) | 0.82 (0.75–0.89) | 3.3 (2.3–4.7) | 0 |
| TN3K | 30 | true_vs_true | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.0 (0.0–0.0) | 0 |
| TN3K | 30 | exact | 0.60 (0.53–0.66) | 0.73 (0.67–0.78) | 5.7 (4.4–7.3) | 0 |
| TN3K | 30 | j10 | 0.64 (0.58–0.71) | 0.77 (0.71–0.82) | 5.1 (3.9–6.5) | 0 |
| TN3K | 30 | j20 | 0.62 (0.56–0.69) | 0.75 (0.70–0.80) | 5.9 (4.6–7.4) | 0 |
| DDTI | 30 | true_vs_true | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.0 (0.0–0.0) | 0 |
| DDTI | 30 | exact | 0.49 (0.43–0.54) | 0.64 (0.59–0.69) | 6.0 (5.2–6.7) | 0 |
| DDTI | 30 | j10 | 0.54 (0.49–0.60) | 0.69 (0.64–0.74) | 5.5 (4.7–6.1) | 0 |
| DDTI | 30 | j20 | 0.51 (0.45–0.57) | 0.66 (0.61–0.71) | 6.3 (5.3–7.5) | 0 |
| HC18 | 30 | true_vs_true | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.0 (0.0–0.0) | 0 |
| HC18 | 30 | exact | 0.52 (0.44–0.59) | 0.65 (0.57–0.72) | 10.7 (9.1–12.4) | 0 |
| HC18 | 30 | j10 | 0.55 (0.46–0.62) | 0.67 (0.59–0.75) | 10.6 (9.0–12.3) | 0 |
| HC18 | 30 | j20 | 0.54 (0.45–0.61) | 0.66 (0.58–0.74) | 11.3 (9.3–13.2) | 0 |
| FetalHead | 30 | true_vs_true | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.0 (0.0–0.0) | 0 |
| FetalHead | 30 | exact | 0.44 (0.35–0.54) | 0.58 (0.48–0.68) | 12.3 (10.8–13.7) | 0 |
| FetalHead | 30 | j10 | 0.47 (0.37–0.59) | 0.61 (0.51–0.72) | 12.5 (10.8–13.9) | 0 |
| FetalHead | 30 | j20 | 0.47 (0.37–0.58) | 0.60 (0.50–0.71) | 13.0 (11.5–14.5) | 0 |
| TN5000 | 30 | exact | box IoU 0.58 (0.52–0.65) (no true mask) | — | — | 0 |
| TN5000 | 30 | j10 | box IoU 0.60 (0.54–0.66) (no true mask) | — | — | 0 |
| TN5000 | 30 | j20 | box IoU 0.61 (0.54–0.67) (no true mask) | — | — | 0 |

**All datasets with true masks pooled** (n scans, group bootstrap):

| prompt | n | IoU | Dice | HD95 (% diag) |
|---|---|---|---|---|
| true_vs_true | 258 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.0 (0.0–0.0) |
| exact | 258 | 0.62 (0.59–0.65) | 0.74 (0.72–0.77) | 6.0 (5.3–6.7) |
| j10 | 258 | 0.65 (0.62–0.68) | 0.77 (0.74–0.79) | 5.8 (5.1–6.5) |
| j20 | 258 | 0.64 (0.61–0.67) | 0.76 (0.73–0.78) | 6.2 (5.5–7.0) |

## 2. Where the segmenter fails (exact box prompt, datasets with true masks pooled)

| group | n | mean IoU | share with IoU < 0.5 |
|---|---|---|---|
| lesion < 2% of the image | 33 | 0.68 | 0.21 |
| lesion 2–10% | 106 | 0.64 | 0.22 |
| lesion ≥ 10% | 119 | 0.58 | 0.29 |
| low contrast (lowest third) | 86 | 0.50 | 0.47 |
| mid contrast | 86 | 0.63 | 0.21 |
| high contrast (top third) | 86 | 0.73 | 0.08 |

**Breast and thyroid lesions only** (fetal-head sets removed, because their target is a whole skull outline):

| group | n | mean IoU | share with IoU < 0.5 |
|---|---|---|---|
| lesion < 2% of the image | 32 | 0.71 | 0.19 |
| lesion 2–10% | 106 | 0.64 | 0.22 |
| lesion ≥ 10% | 60 | 0.67 | 0.15 |
| low contrast (lowest third) | 66 | 0.52 | 0.42 |
| mid contrast | 66 | 0.70 | 0.11 |
| high contrast (top third) | 66 | 0.76 | 0.05 |

Breast and thyroid only: Spearman of IoU with lesion size -0.03, with contrast 0.57.

Spearman of IoU with lesion size -0.19, with contrast 0.48. Contrast = |mean grey inside − mean grey of a ring outside| / 255.

Per dataset, share of scans with IoU < 0.5 (exact prompt): BrEaST 0.07 (n=30), BUS-BRA 0.20 (n=30), BUSI 0.07 (n=30), UDIAT 0.00 (n=30), BUS-UCLM 0.28 (n=18), TN3K 0.33 (n=30), DDTI 0.43 (n=30), HC18 0.43 (n=30), FetalHead 0.47 (n=30)

Ten lowest-IoU scans (exact prompt): HC18:787_HC IoU 0.00, lesion 0.9% of image; FetalHead:Patient00870_Plane3_4_of_5 IoU 0.03, lesion 26.8% of image; FetalHead:Patient01275_Plane3_2_of_7 IoU 0.08, lesion 15.3% of image; FetalHead:Patient01275_Plane3_3_of_7 IoU 0.09, lesion 16.3% of image; FetalHead:Patient01140_Plane3_2_of_3 IoU 0.12, lesion 30.6% of image; FetalHead:Patient00870_Plane3_3_of_5 IoU 0.14, lesion 27.5% of image; DDTI:109_1 IoU 0.15, lesion 2.9% of image; HC18:760_HC IoU 0.16, lesion 28.2% of image; TN3K:trainval/1906.jpg IoU 0.19, lesion 13.1% of image; HC18:744_HC IoU 0.20, lesion 33.0% of image

## 3. Layer 3 read from the PREDICTED mask: measurement error vs the reference facts

Reference facts come from the TRUE masks (HC18: the dataset's labelled head circumference). Size unit: mm (BrEaST; fetal head circumference), percent of image width (all others, no pixel size). Agreement = same third-of-image position / orientation word / lesion count. † n < 30.

| dataset | prompt | size unit | median abs. size error | median signed error (pred − ref) | median rel. size error | position agrees | orientation agrees | count agrees | lesion found |
|---|---|---|---|---|---|---|---|---|---|
| BrEaST | exact | mm | 1.0 | -1.0 | 0.11 | 0.87 (0.73–0.97) | 0.93 (0.83–1.00) | 1.00 (1.00–1.00) | 1.00 |
| BrEaST | j10 | mm | 1.0 | -1.0 | 0.06 | 0.83 (0.70–0.97) | 0.93 (0.83–1.00) | 1.00 (1.00–1.00) | 1.00 |
| BrEaST | j20 | mm | 1.0 | 0.0 | 0.06 | 0.83 (0.70–0.97) | 0.93 (0.83–1.00) | 0.97 (0.90–1.00) | 1.00 |
| BUS-BRA | exact | % width | 9.0 | -9.0 | 0.20 | 0.90 (0.79–1.00) | 0.97 (0.90–1.00) | 1.00 (1.00–1.00) | 1.00 |
| BUS-BRA | j10 | % width | 5.0 | -5.0 | 0.15 | 0.97 (0.90–1.00) | 0.97 (0.90–1.00) | 1.00 (1.00–1.00) | 1.00 |
| BUS-BRA | j20 | % width | 4.0 | -4.0 | 0.11 | 0.97 (0.89–1.00) | 0.97 (0.89–1.00) | 1.00 (1.00–1.00) | 1.00 |
| BUSI | exact | % width | 5.0 | -5.0 | 0.10 | 0.87 (0.73–0.97) | 0.93 (0.83–1.00) | 0.97 (0.90–1.00) | 1.00 |
| BUSI | j10 | % width | 3.0 | -3.0 | 0.07 | 0.90 (0.80–1.00) | 0.93 (0.83–1.00) | 0.97 (0.90–1.00) | 1.00 |
| BUSI | j20 | % width | 2.0 | -1.0 | 0.07 | 0.90 (0.77–1.00) | 0.93 (0.83–1.00) | 0.97 (0.90–1.00) | 1.00 |
| UDIAT | exact | % width | 2.0 | -2.0 | 0.08 | 1.00 (1.00–1.00) | 0.93 (0.83–1.00) | 1.00 (1.00–1.00) | 1.00 |
| UDIAT | j10 | % width | 1.0 | -1.0 | 0.06 | 0.97 (0.90–1.00) | 0.93 (0.83–1.00) | 1.00 (1.00–1.00) | 1.00 |
| UDIAT | j20 | % width | 1.0 | 0.0 | 0.06 | 0.97 (0.90–1.00) | 0.97 (0.90–1.00) | 1.00 (1.00–1.00) | 1.00 |
| BUS-UCLM † | exact | % width | 3.5 | -3.5 | 0.16 | 0.94 (0.83–1.00) | 0.94 (0.83–1.00) | 0.89 (0.78–1.00) | 1.00 |
| BUS-UCLM † | j10 | % width | 3.5 | -3.5 | 0.13 | 0.94 (0.83–1.00) | 0.94 (0.83–1.00) | 0.89 (0.78–1.00) | 1.00 |
| BUS-UCLM † | j20 | % width | 3.0 | -2.0 | 0.10 | 0.94 (0.83–1.00) | 0.94 (0.83–1.00) | 0.89 (0.78–1.00) | 1.00 |
| TN3K | exact | % width | 5.0 | -5.0 | 0.16 | 0.90 (0.80–1.00) | 0.83 (0.70–0.97) | 0.87 (0.73–0.97) | 1.00 |
| TN3K | j10 | % width | 4.0 | -3.5 | 0.11 | 0.90 (0.80–1.00) | 0.93 (0.83–1.00) | 0.87 (0.73–0.97) | 1.00 |
| TN3K | j20 | % width | 2.0 | -2.0 | 0.10 | 0.83 (0.70–0.97) | 0.90 (0.80–1.00) | 0.87 (0.73–0.97) | 1.00 |
| DDTI | exact | % width | 9.0 | -9.0 | 0.27 | 0.83 (0.69–0.97) | 0.90 (0.79–1.00) | 0.57 (0.38–0.73) | 1.00 |
| DDTI | j10 | % width | 4.0 | -4.0 | 0.21 | 0.80 (0.65–0.94) | 0.90 (0.78–1.00) | 0.60 (0.41–0.76) | 1.00 |
| DDTI | j20 | % width | 4.0 | -3.0 | 0.15 | 0.87 (0.72–0.97) | 0.90 (0.77–1.00) | 0.57 (0.38–0.73) | 1.00 |
| HC18 | exact | mm | 32.2 | -32.2 | 0.18 | — | — | — | 1.00 |
| HC18 | j10 | mm | 27.5 | -27.5 | 0.18 | — | — | — | 1.00 |
| HC18 | j20 | mm | 25.9 | -25.9 | 0.19 | — | — | — | 1.00 |
| FetalHead | exact | mm | 78.5 | -78.5 | 0.28 | — | — | — | 1.00 |
| FetalHead | j10 | mm | 77.5 | -77.5 | 0.28 | — | — | — | 1.00 |
| FetalHead | j20 | mm | 58.5 | -58.5 | 0.25 | — | — | — | 1.00 |
| TN5000 | exact | % width | 3.0 | -3.0 | 0.20 | 0.83 (0.70–0.97) | 0.80 (0.67–0.93) | 1.00 (1.00–1.00) | 1.00 |
| TN5000 | j10 | % width | 3.0 | -3.0 | 0.19 | 0.97 (0.90–1.00) | 0.77 (0.60–0.90) | 0.97 (0.90–1.00) | 1.00 |
| TN5000 | j20 | % width | 2.0 | -2.0 | 0.14 | 0.97 (0.90–1.00) | 0.80 (0.63–0.93) | 1.00 (1.00–1.00) | 1.00 |

## 4. mask_verified_facts on planted position / size errors: true masks (circular) vs predicted masks (non-circular) vs text scorers

AUROC = chance that the check scores a planted error below a harmless rewording of the same report (per case, group bootstrap). 0.5 = chance. `mvf_true` is the Step 8 check (upper bound, templated, circular); `mvf_exact / j10 / j20` read the PREDICTED mask from the exact / 10%-jittered / 20%-jittered box. † n < 30 cases with such errors: too small to compare.

### position errors

| dataset | n cases | mvf_true | mvf_exact | mvf_j10 | mvf_j20 | bleu | rougeL | chrf | bertscore[roberta-large] | ratescore |
|---|---|---|---|---|---|---|---|---|---|---|
| BrEaST † | 17 | 1.00 (1.00–1.00) | 0.97 (0.91–1.00) | 0.94 (0.85–1.00) | 0.97 (0.91–1.00) | 0.20 (0.20–0.20) | 0.17 (0.17–0.17) | 0.13 (0.13–0.13) | 0.09 (0.08–0.11) | 0.20 (0.19–0.20) |
| BUS-BRA † | 17 | 1.00 (1.00–1.00) | 0.94 (0.85–1.00) | 0.97 (0.92–1.00) | 1.00 (1.00–1.00) | 0.20 (0.20–0.20) | 0.15 (0.15–0.15) | 0.10 (0.10–0.10) | 0.00 (0.00–0.00) | 0.30 (0.28–0.32) |
| BUSI † | 19 | 1.00 (1.00–1.00) | 0.92 (0.84–1.00) | 0.92 (0.84–1.00) | 0.92 (0.84–1.00) | 0.28 (0.28–0.28) | 0.11 (0.11–0.11) | 0.22 (0.22–0.22) | 0.00 (0.00–0.00) | 0.27 (0.26–0.28) |
| UDIAT † | 23 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.28 (0.28–0.28) | 0.11 (0.11–0.11) | 0.23 (0.22–0.25) | 0.00 (0.00–0.00) | 0.27 (0.26–0.28) |
| BUS-UCLM † | 8 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.28 (0.28–0.28) | 0.11 (0.11–0.11) | 0.23 (0.22–0.24) | 0.00 (0.00–0.00) | 0.27 (0.26–0.28) |
| TN3K † | 17 | 1.00 (1.00–1.00) | 0.94 (0.85–1.00) | 0.94 (0.85–1.00) | 0.91 (0.82–1.00) | 0.30 (0.29–0.30) | 0.15 (0.15–0.15) | 0.12 (0.10–0.14) | 0.05 (0.03–0.07) | 0.31 (0.26–0.37) |
| DDTI † | 16 | 1.00 (1.00–1.00) | 0.84 (0.72–0.97) | 0.81 (0.69–0.93) | 0.91 (0.80–1.00) | 0.31 (0.31–0.32) | 0.17 (0.16–0.18) | 0.11 (0.09–0.13) | 0.05 (0.02–0.07) | 0.34 (0.29–0.41) |
| TN5000 † | 17 | 1.00 (1.00–1.00) | 0.97 (0.91–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.30 (0.30–0.30) | 0.15 (0.15–0.15) | 0.12 (0.11–0.14) | 0.04 (0.02–0.07) | 0.30 (0.25–0.35) |
| **breast + thyroid pooled (no fetal head)** | 134 | 1.00 (1.00–1.00) | 0.95 (0.92–0.97) | 0.95 (0.92–0.97) | 0.96 (0.94–0.98) | 0.27 (0.26–0.27) | 0.14 (0.14–0.14) | 0.16 (0.15–0.17) | 0.03 (0.02–0.04) | 0.28 (0.27–0.30) |
| **all 10 datasets pooled** | 134 | 1.00 (1.00–1.00) | 0.95 (0.92–0.97) | 0.95 (0.92–0.97) | 0.96 (0.94–0.98) | 0.27 (0.26–0.27) | 0.14 (0.14–0.14) | 0.16 (0.15–0.17) | 0.03 (0.02–0.04) | 0.28 (0.27–0.30) |

### size errors

| dataset | n cases | mvf_true | mvf_exact | mvf_j10 | mvf_j20 | bleu | rougeL | chrf | bertscore[roberta-large] | ratescore |
|---|---|---|---|---|---|---|---|---|---|---|
| BrEaST | 30 | 1.00 (1.00–1.00) | 0.88 (0.78–0.96) | 0.91 (0.83–0.98) | 0.93 (0.86–0.99) | 0.20 (0.20–0.20) | 0.17 (0.17–0.17) | 0.00 (0.00–0.00) | 0.04 (0.02–0.05) | 0.60 (0.58–0.61) |
| BUS-BRA | 30 | 1.00 (1.00–1.00) | 0.83 (0.73–0.91) | 0.94 (0.88–0.99) | 0.96 (0.89–1.00) | 0.20 (0.20–0.20) | 0.15 (0.15–0.15) | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | 0.61 (0.60–0.62) |
| BUSI | 30 | 1.00 (1.00–1.00) | 0.93 (0.84–1.00) | 0.91 (0.82–0.98) | 0.92 (0.83–0.99) | 0.28 (0.28–0.28) | 0.11 (0.11–0.11) | 0.11 (0.11–0.11) | 0.00 (0.00–0.00) | 0.69 (0.67–0.71) |
| UDIAT | 30 | 1.00 (1.00–1.00) | 0.98 (0.95–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.28 (0.28–0.28) | 0.11 (0.11–0.11) | 0.10 (0.09–0.11) | 0.00 (0.00–0.00) | 0.70 (0.69–0.71) |
| BUS-UCLM † | 18 | 1.00 (1.00–1.00) | 0.91 (0.76–1.00) | 0.93 (0.85–1.00) | 0.95 (0.88–1.00) | 0.28 (0.28–0.28) | 0.11 (0.11–0.11) | 0.10 (0.09–0.11) | 0.00 (0.00–0.00) | 0.66 (0.63–0.71) |
| TN3K | 30 | 1.00 (1.00–1.00) | 0.84 (0.74–0.92) | 0.88 (0.81–0.96) | 0.89 (0.81–0.96) | 0.30 (0.29–0.30) | 0.15 (0.15–0.15) | 0.10 (0.10–0.10) | 0.08 (0.07–0.09) | 0.30 (0.29–0.32) |
| DDTI | 30 | 1.00 (1.00–1.00) | 0.69 (0.59–0.80) | 0.83 (0.73–0.93) | 0.86 (0.76–0.94) | 0.31 (0.31–0.32) | 0.17 (0.17–0.18) | 0.09 (0.08–0.09) | 0.06 (0.05–0.07) | 0.32 (0.29–0.35) |
| HC18 | 30 | 1.00 (1.00–1.00) | 0.46 (0.43–0.49) | 0.50 (0.45–0.55) | 0.59 (0.54–0.65) | 0.20 (0.20–0.20) | 0.15 (0.15–0.15) | 0.10 (0.10–0.10) | 0.00 (0.00–0.00) | 0.44 (0.42–0.46) |
| FetalHead | 30 | 1.00 (1.00–1.00) | 0.50 (0.48–0.52) | 0.52 (0.50–0.55) | 0.56 (0.51–0.62) | 0.20 (0.20–0.20) | 0.15 (0.15–0.15) | 0.12 (0.12–0.13) | 0.00 (0.00–0.00) | 0.54 (0.51–0.57) |
| TN5000 | 30 | 1.00 (1.00–1.00) | 0.82 (0.72–0.89) | 0.86 (0.77–0.94) | 0.88 (0.79–0.96) | 0.30 (0.30–0.30) | 0.15 (0.15–0.15) | 0.10 (0.10–0.10) | 0.04 (0.02–0.05) | 0.32 (0.29–0.36) |
| **breast + thyroid pooled (no fetal head)** | 228 | 1.00 (1.00–1.00) | 0.86 (0.82–0.89) | 0.91 (0.88–0.94) | 0.92 (0.90–0.95) | 0.27 (0.26–0.27) | 0.14 (0.14–0.15) | 0.07 (0.07–0.08) | 0.03 (0.02–0.03) | 0.52 (0.49–0.54) |
| **all 10 datasets pooled** | 288 | 1.00 (1.00–1.00) | 0.78 (0.74–0.81) | 0.82 (0.79–0.86) | 0.85 (0.82–0.88) | 0.25 (0.25–0.26) | 0.14 (0.14–0.15) | 0.08 (0.08–0.09) | 0.02 (0.02–0.03) | 0.51 (0.49–0.53) |

### all mask-checkable errors

| dataset | n cases | mvf_true | mvf_exact | mvf_j10 | mvf_j20 | bleu | rougeL | chrf | bertscore[roberta-large] | ratescore |
|---|---|---|---|---|---|---|---|---|---|---|
| BrEaST | 30 | 1.00 (1.00–1.00) | 0.93 (0.88–0.97) | 0.94 (0.90–0.98) | 0.94 (0.90–0.98) | 0.43 (0.42–0.44) | 0.38 (0.37–0.38) | 0.27 (0.27–0.27) | 0.31 (0.30–0.32) | 0.64 (0.62–0.65) |
| BUS-BRA | 30 | 1.00 (1.00–1.00) | 0.91 (0.86–0.95) | 0.97 (0.93–0.99) | 0.97 (0.93–1.00) | 0.38 (0.38–0.39) | 0.33 (0.32–0.33) | 0.27 (0.26–0.27) | 0.24 (0.23–0.25) | 0.64 (0.63–0.66) |
| BUSI | 30 | 1.00 (1.00–1.00) | 0.95 (0.91–0.98) | 0.94 (0.90–0.97) | 0.95 (0.91–0.98) | 0.40 (0.40–0.41) | 0.29 (0.28–0.29) | 0.34 (0.34–0.34) | 0.21 (0.20–0.21) | 0.70 (0.67–0.71) |
| UDIAT | 30 | 1.00 (1.00–1.00) | 0.98 (0.96–1.00) | 0.99 (0.98–1.00) | 1.00 (0.99–1.00) | 0.40 (0.40–0.40) | 0.27 (0.27–0.28) | 0.33 (0.33–0.34) | 0.20 (0.19–0.21) | 0.69 (0.67–0.70) |
| BUS-UCLM † | 18 | 1.00 (1.00–1.00) | 0.95 (0.87–0.99) | 0.96 (0.92–0.99) | 0.97 (0.94–1.00) | 0.41 (0.40–0.42) | 0.29 (0.28–0.30) | 0.34 (0.33–0.35) | 0.21 (0.20–0.23) | 0.69 (0.65–0.72) |
| TN3K | 30 | 1.00 (1.00–1.00) | 0.89 (0.84–0.93) | 0.93 (0.88–0.96) | 0.92 (0.88–0.96) | 0.44 (0.43–0.44) | 0.34 (0.33–0.34) | 0.38 (0.37–0.40) | 0.28 (0.27–0.29) | 0.56 (0.55–0.58) |
| DDTI | 30 | 1.00 (1.00–1.00) | 0.82 (0.75–0.88) | 0.88 (0.83–0.94) | 0.90 (0.83–0.95) | 0.46 (0.45–0.46) | 0.36 (0.35–0.37) | 0.35 (0.34–0.37) | 0.27 (0.25–0.29) | 0.52 (0.51–0.54) |
| HC18 | 30 | 1.00 (1.00–1.00) | 0.46 (0.43–0.49) | 0.50 (0.45–0.55) | 0.59 (0.54–0.65) | 0.20 (0.20–0.20) | 0.15 (0.15–0.15) | 0.10 (0.10–0.10) | 0.00 (0.00–0.00) | 0.44 (0.42–0.46) |
| FetalHead | 30 | 1.00 (1.00–1.00) | 0.50 (0.48–0.52) | 0.52 (0.50–0.55) | 0.56 (0.51–0.62) | 0.20 (0.20–0.20) | 0.15 (0.15–0.15) | 0.12 (0.12–0.13) | 0.00 (0.00–0.00) | 0.54 (0.51–0.57) |
| TN5000 | 30 | 1.00 (1.00–1.00) | 0.88 (0.83–0.93) | 0.90 (0.84–0.94) | 0.92 (0.87–0.96) | 0.44 (0.43–0.44) | 0.34 (0.33–0.35) | 0.39 (0.38–0.40) | 0.26 (0.25–0.28) | 0.58 (0.56–0.60) |
| **breast + thyroid pooled (no fetal head)** | 228 | 1.00 (1.00–1.00) | 0.91 (0.89–0.93) | 0.94 (0.92–0.95) | 0.95 (0.93–0.96) | 0.42 (0.42–0.42) | 0.33 (0.32–0.33) | 0.33 (0.33–0.34) | 0.25 (0.24–0.26) | 0.62 (0.61–0.63) |
| **all 10 datasets pooled** | 288 | 1.00 (1.00–1.00) | 0.82 (0.79–0.85) | 0.85 (0.82–0.88) | 0.87 (0.84–0.90) | 0.37 (0.36–0.39) | 0.29 (0.28–0.30) | 0.29 (0.27–0.30) | 0.20 (0.18–0.21) | 0.59 (0.58–0.61) |

### Identical copies and harmless rewordings (mean score)

| scorer | identical mean | harmless mean |
|---|---|---|
| mvf_true | 1.000 | 1.000 |
| mvf_exact | 0.676 | 0.681 |
| mvf_j10 | 0.701 | 0.706 |
| mvf_j20 | 0.730 | 0.733 |
| bleu | 1.000 | 0.725 |
| rougeL | 1.000 | 0.821 |
| chrf | 1.000 | 0.864 |
| bertscore[roberta-large] | 1.000 | 0.969 |
| ratescore | 1.000 | 0.912 |

### Size errors by how big the planted error is (lesion datasets pooled: BrEaST in mm, others in % of image width; ×1.5 = 50% too large, ×0.5 = half, ×2 = double)

| planted size error | n cases | mvf_true | mvf_exact | mvf_j10 | mvf_j20 | bleu | rougeL | chrf | bertscore[roberta-large] | ratescore |
|---|---|---|---|---|---|---|---|---|---|---|
| ×1.5 | 228 | 1.00 (1.00–1.00) | 0.92 (0.90–0.95) | 0.95 (0.92–0.97) | 0.95 (0.92–0.97) | 0.27 (0.26–0.27) | 0.14 (0.14–0.15) | 0.07 (0.07–0.08) | 0.03 (0.02–0.04) | 0.51 (0.48–0.54) |
| ×0.5 | 228 | 1.00 (1.00–1.00) | 0.73 (0.67–0.79) | 0.83 (0.78–0.88) | 0.87 (0.83–0.91) | 0.27 (0.26–0.27) | 0.14 (0.14–0.15) | 0.07 (0.07–0.08) | 0.03 (0.02–0.03) | 0.52 (0.50–0.55) |
| ×2.0 | 228 | 1.00 (1.00–1.00) | 0.92 (0.90–0.95) | 0.95 (0.92–0.97) | 0.95 (0.93–0.97) | 0.27 (0.26–0.27) | 0.14 (0.14–0.15) | 0.07 (0.07–0.08) | 0.03 (0.03–0.04) | 0.52 (0.49–0.54) |

### What a correct (identical) report scores with the predicted-mask check, per dataset

A correct report should score 1.0. Any shortfall is a false alarm caused by the segmenter, not by the report.

| dataset | n reports | mean mvf_exact | share scoring 1.0 (exact) | mean mvf_j10 | mean mvf_j20 |
|---|---|---|---|---|---|
| BrEaST | 30 | 0.89 | 0.20 | 0.90 | 0.90 |
| BUS-BRA | 30 | 0.86 | 0.03 | 0.91 | 0.93 |
| BUSI | 30 | 0.89 | 0.10 | 0.91 | 0.92 |
| UDIAT | 30 | 0.94 | 0.10 | 0.95 | 0.96 |
| BUS-UCLM † | 18 | 0.87 | 0.00 | 0.89 | 0.90 |
| TN3K | 30 | 0.82 | 0.03 | 0.86 | 0.85 |
| DDTI | 30 | 0.71 | 0.00 | 0.75 | 0.79 |
| HC18 | 30 | 0.01 | 0.00 | 0.03 | 0.16 |
| FetalHead | 30 | 0.00 | 0.00 | 0.03 | 0.10 |
| TN5000 | 30 | 0.82 | 0.10 | 0.85 | 0.87 |

## Where the segmenter fails, in plain words
- **Low contrast is the main failure for breast and thyroid lesions:** IoU 0.52 in the lowest third of contrast vs 0.76 in the top third (Spearman of IoU with contrast 0.57, n=198 scans); 42% of low-contrast scans have IoU < 0.5 vs 5% of high-contrast ones.
- **Lesion size is not the problem here:** IoU does not fall for small lesions (lesions < 2% of the image: 0.71, n=32; Spearman with size −0.03). Only 32 scans have lesions that small, so this says little about very small lesions.
- **Whole-skull targets fail systematically:** HC18 and FetalHead true masks include the bright skull ring, MedSAM outlines the interior (overlays of 6 scans checked by eye), so the head circumference is always too small.
- **Multi-part lesions:** DDTI lesion count from the predicted mask agrees with the reference in only 57–60% of scans; position agrees in 80–87%.
- **Datasets with weak segmentation:** DDTI 43%, HC18 43%, FetalHead 47%, TN3K 33% of scans have IoU < 0.5; UDIAT 0%, BrEaST and BUSI 7%.
- **Size read from predicted masks is off by a median 6–27% (lesion sets)**; the planted size errors (×1.5, ×0.5, ×2) are larger than that, which is why they are still caught. A planted size error of 10% would not be caught by this check; we did not plant those for size_pct / size_mm. The fetal-head ±3 / ±10 mm errors are far inside the segmenter's 26–78 mm error, hence ≈ chance there.

## Is the predicted-mask check better than text scorers?
- **Breast and thyroid: yes**, 0.82–0.98 per dataset for all mask-checkable errors with the exact box (DDTI lowest, 0.82; UDIAT highest, 0.98), against 0.20–0.70 for the text scorers. Part of that gap is the edit-size effect found in Steps 4–5 (word-overlap scorers sit below 0.5 because the planted errors change only 2–4% of the tokens of a templated report), so compare each AUROC with 0.5, not the two columns with each other.
- **Fetal head (HC18, FetalHead): no.** The check is at chance (0.46–0.59 across prompts) and gives correct reports ≈ 0.
- **Position errors:** per-dataset n is 8–23 cases (†, too small to compare); the pooled 134 cases give 0.95 (0.92–0.97).
- **Size by error magnitude (breast + thyroid pooled, n=228 cases each, exact box):** ×1.5 → 0.92, ×0.5 → 0.73, ×2.0 → 0.92. We did not test why ×0.5 is hardest.

## Limits (read before quoting any number)
- **Still templated.** The references and planted errors are our own templated text; the planted errors are large (×0.5 to ×2, a different third of the image). Real reports have smaller errors.
- **Boxes come from the true masks.** Localisation is handed to the segmenter, so this measures the boundary and the check, not "find the lesion". A real pipeline needs a detector, and the VLM boxes tried so far were too poor to use.
- **Small samples.** 30 scans per dataset (18 for BUS-UCLM), at most 3 per group; rows with n < 30 are marked † and are too small to compare. Pooled rows mix datasets.
- **Possible training exposure, unverifiable.** MedSAM was trained on a large collection of public medical images; we did not check whether it saw these datasets. Per-dataset IoU may be inflated for public datasets; BrEaST (newest) is the cleanest.
- **The "truth" for IoU is the annotators' outline,** and conventions differ by dataset (skull ring vs interior, thyroid outline style).
- **No pixel size for 7 of 10 datasets:** sizes are % of image width (box proxy for the longest side), not mm.
- **Single run, MPS.** MedSAM is deterministic given the box; the only randomness is scan selection (seed 0) and the jitter signs.
- Predicted masks (3.4 MB) are in the git-ignored `usmeta/local_data/partb/`; regenerate with `python3 -m usmeta.partb select && python3 -m usmeta.partb predict && python3 -m usmeta.partb analyse`.

## Files here
`results.md` (this file), `results_aggregates.json` (all numbers with CIs), `per_case.json` (per scan: IoU, Dice, HD95, area, contrast, measurement errors), `selected.json` (the 288 scans), `partb.py` (the code), `run_info.json`, `run.log`.
