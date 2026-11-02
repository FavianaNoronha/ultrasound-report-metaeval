# Step 21f — Split-leakage audit (counts only, no model calls)

Question: does any near-duplicate cluster, or any patient / exam group, sit in more than one of dev / val / test? Source: `splits.jsonl` (Step 10b) and `duplicates.jsonl` (Step 10a, 64-bit dHash). Code: `usmeta/step21_split_audit.py`. Clusters are connected near-duplicates inside one dataset.

## Result
- **At the threshold the splits were built with (≤ 4 bits): 0 clusters span more than one split, and 0 patient / exam groups span splits, in all 10 datasets.** 0 cross-dataset pairs at ≤ 4 bits. The expectation (0) holds; the stop condition is not met.
- **Looser check (≤ 8 bits, NOT used for splitting): 164 clusters span splits** (largest counts: TN5000 56, FetalHead 42, HC18 25, TN3K 12, DDTI 11, BUSI 11). At 8 bits most pairs are different images of similar anatomy rather than duplicates (Step 10a pixel-verified only the ≤ 4-bit pairs, correlation ≥ 0.98), so this is a sensitivity check, not a finding of leakage; but it means very similar images (not duplicates) can sit on both sides of a split in the datasets without patient ids. No images were dropped or moved.
- Images per split: dev 40% / val 20% / test 40% by group in every dataset (table below).

| dataset | images | dev | val | test | groups | groups spanning splits | near-dup clusters (≤ 4 bits) | clusters spanning splits | clusters (≤ 8 bits) | clusters spanning splits |
|---|---|---|---|---|---|---|---|---|---|---|
| BUS-BRA | 1875 | 750 | 375 | 750 | 1064 | 0 | 0 (0 images) | 0 | 5 (10 images) | 3 |
| BUS-UCLM | 683 | 271 | 141 | 271 | 37 | 0 | 21 (45 images) | 0 | 35 (82 images) | 2 |
| BUSI | 780 | 311 | 157 | 312 | 621 | 0 | 131 (290 images) | 0 | 143 (320 images) | 11 |
| BrEaST | 256 | 103 | 50 | 103 | 256 | 0 | 0 (0 images) | 0 | 1 (2 images) | 1 |
| DDTI | 480 | 192 | 96 | 192 | 383 | 0 | 10 (23 images) | 0 | 18 (237 images) | 11 |
| FetalHead | 2833 | 1133 | 564 | 1136 | 1022 | 0 | 123 (257 images) | 0 | 185 (736 images) | 42 |
| HC18 | 999 | 400 | 199 | 400 | 989 | 0 | 9 (19 images) | 0 | 40 (99 images) | 25 |
| TN3K | 3493 | 1398 | 697 | 1398 | 3468 | 0 | 17 (42 images) | 0 | 31 (174 images) | 12 |
| TN5000 | 5000 | 2000 | 1000 | 2000 | 4857 | 0 | 136 (279 images) | 0 | 207 (502 images) | 56 |
| UDIAT | 163 | 66 | 31 | 66 | 159 | 0 | 4 (8 images) | 0 | 6 (12 images) | 1 |

## Limits
dHash is a coarse similarity measure; datasets without patient ids (BUSI, UDIAT, TN3K, TN5000, HC18) can still have the same patient on both sides of a split (`docs/LIMITATIONS.md` item 9); the ≤ 8-bit counts are not pixel-verified.
