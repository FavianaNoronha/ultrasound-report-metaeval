# Step 18, sub-step 1 — feasibility (2026-10-28): STOPPED, 0 eligible cases

Source: `local_data/*.jsonl` (unified records) and `splits.jsonl` (counts only; no scorer was run, no test result was looked at).

**Primary (TI-RADS size thresholds): 0 eligible cases in dev + val + test (need ≥ 30). No dataset has both a size in mm and a TI-RADS level.**

| dataset | records | pixel size (mm/px) | TI-RADS level | both |
|---|---|---|---|---|
| DDTI | 480 | 0 | 349 (dev 136, val 66, test 147) | **0** |
| TN3K | 3,493 | 0 | 0 | 0 |
| TN5000 | 5,000 | 0 | 0 | 0 |
| BrEaST (breast) | 256 | 256 | 0 (BI-RADS instead) | 0 |
| BUS-BRA, BUSI, UDIAT, BUS-UCLM | 3,501 | 0 | 0 | 0 |
| HC18, FetalHead | 3,832 | 3,832 | 0 | 0 |

- DDTI has TI-RADS levels (2: 42, 3: 19, 4a: 96, 4b: 79, 4c: 68, 5: 45, none: 131) but no pixel size and no labelled size, so a lesion size in mm cannot be stated; our DDTI reports give size as a percent of image width only. The 4a/4b/4c scheme is also the older Kwak-style split, not ACR TR4, so it would need a mapping to ACR TR levels (not done; not invented).
- The only datasets with mm are BrEaST (breast) and the fetal sets. No thyroid set has pixel size.
- Nothing was invented: no synthetic TI-RADS level or pixel size was created.

## Secondary (breast size 20 mm / 50 mm cut-offs, "to confirm") — counts only
BrEaST lesion major axis from the mask × pixel size (mm); reports state size in mm and a BI-RADS level.

| split | n with size | median mm | ≥ 20 mm | ≥ 50 mm | within ±3 mm of 20 or 50 | within ±5 mm of 20 |
|---|---|---|---|---|---|---|
| dev | 101 | 13.6 | 26 | 0 | 13 | 30 |
| val | 50 | 11.6 | 6 | 1 | 7 | 12 |
| test | 101 | 14.4 | 28 | 2 | 18 | 29 |

Only the 20 mm cut-off is usable (50 mm: 3 lesions in all). A 3 mm matched pair at 20 mm needs the case within about 3 mm of 20: 13 + 7 + 18 = 38 over all splits, but only 18 on test and 13 on dev. That is one dataset, one cut-off (breast T1/T2), 18 test cases, so most cells would fall below n = 30. Also BrEaST's size is approximate (pixel-size unit inferred, `docs/LIMITATIONS.md` item 9) and a ±3 mm change is within that uncertainty.

## What would be needed
(a) pixel size or size labels for DDTI (not in the data we hold; the DDTI xml has no size field), or (b) your approval of synthetic labels, which must be called "synthetic level"/"synthetic size", or (c) switching the primary to the breast 20 mm cut-off on BrEaST (n = 13/7/18 matched cases dev/val/test, mostly "too small to compare"), or (d) another dataset with mm sizes plus TI-RADS.
