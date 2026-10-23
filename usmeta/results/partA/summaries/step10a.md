# Step 10a: duplicate and leakage check (perceptual hash)

**Method.** 64-bit difference hash (dHash, 9x8 grey, PIL + numpy only) of every image of the 10 benchmark datasets (16,562 images) plus the "Diverse Fetal Head Images" folder as a reference set (999 images), 17,561 in total; all pairs compared (Hamming distance). **Duplicate = distance <= 4 of 64 bits; possible = 5-8.** No image was unreadable; no near-uniform image was skipped. Pairs: `duplicates.jsonl` (file names only). A pixel check (48x48 grey, correlation) was run on the <= 4 pairs to separate real duplicates from hash coincidences.

**Cross-dataset (the leakage question).**
- **No benchmark dataset shares a near-duplicate (<= 4 bits) with another benchmark dataset.** BUSI vs BUS-BRA vs BUS-UCLM vs UDIAT vs BrEaST: 0 duplicate pairs. TN3K vs TN5000 vs DDTI: 0. HC18 vs fetal-head planes: 0.
- "Possible" pairs (5-8 bits, not confirmed by eye): e.g. TN3K-TN5000 24, DDTI-TN5000 30, DDTI-TN3K 14, FetalHead-HC18 90, BUS-BRA-TN3K 7. These are mostly similar-looking ultrasound frames; none is dropped.
- **HC18 vs "Diverse Fetal Head Images": 1,021 pairs at <= 4 bits, and all 999 HC18 images have a partner.** The Diverse folder holds the same `000_HC.png ... ` files resized to 959x661, i.e. it is a derived copy of HC18, not independent data. Anything trained or tuned on one is exposed to the other. It is not in our benchmark; it is listed so nobody uses it as an "independent" fetal test set.

**Within-dataset near-duplicates (images with a partner at <= 4 bits; pixel-verified pairs in brackets: correlation >= 0.98).**
| dataset | images | in a <= 4 pair | % of dataset | pairs (verified) | same group id |
|---|---|---|---|---|---|
| BUSI | 780 | 290 | **37.2%** | 189 (124) | no group ids in this dataset |
| FetalHead | 2,833 | 257 | **9.1%** | 141 (107) | 116 of 141 pairs share the patient id (consecutive frames of one patient) |
| BUS-UCLM | 683 | 45 | **6.6%** | 28 (17) | 24 of 28 share the exam prefix |
| TN5000 | 5,000 | 279 | **5.6%** | 150 (140) | no group ids |
| UDIAT | 163 | 8 | 4.9% | 4 (4) | no group ids |
| DDTI | 480 | 23 | 4.8% | 19 (16) | 6 of 19 share a case |
| TN3K | 3,493 | 42 | 1.2% | 25 (7) | no group ids |
| HC18 | 999 | 19 (inside HC18) | 1.9% | 11 (8) | no subject ids |
| BrEaST, BUS-BRA | 256 / 1,875 | 0 | 0% | 0 | case / patient ids |

Clusters (connected near-duplicates inside a dataset): BUSI 131 clusters / 290 images (largest 4), FetalHead 123 / 257 (5), TN5000 136 / 279 (3), BUS-UCLM 21 / 45 (4), TN3K 17 / 42 (8), DDTI 10 / 23 (5), HC18 9 / 19 (3), UDIAT 4 / 8 (2).
If we kept one image per cluster, the benchmark would lose BUSI 159 (20.4% of BUSI), FetalHead 134 (4.7%), TN5000 143 (2.9%), BUS-UCLM 24 (3.5%), TN3K 25 (0.7%), DDTI 13 (2.7%), HC18 10 (1.0%), UDIAT 4 (2.5%).

**STOP condition reached (the brief says to stop and ask when a dataset has more than 5% duplicates):** BUSI 37.2%, FetalHead 9.1%, BUS-UCLM 6.6%, TN5000 5.6% (UDIAT 4.9% and DDTI 4.8% are just under). Nothing has been dropped or split yet. `dropped_cases.jsonl` is empty so far (no cross-dataset duplicates to drop).

**Why this matters for the benchmark.** The templated reports of two near-duplicate images are nearly identical, so putting one in dev and one in test would leak. BUSI, TN3K, TN5000, HC18 and UDIAT have no patient/exam id, so image-level splitting could put the same patient on both sides. The plan options are in the status message: group each cluster (same group id, so a cluster is never split) or drop all but one image per cluster.

**Caveats.** dHash on dark, low-detail ultrasound images can match different scans (correlation shows 20-40% of BUSI/TN3K pairs are weaker matches); the check cannot find the same patient in different poses; the BUSI/UDIAT/BrEaST copies on this Mac are the ones hashed. Related limitations: `docs/LIMITATIONS.md` (to be written in 10e).
