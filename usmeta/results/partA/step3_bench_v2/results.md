# Step 3: bench_v2 (planted errors and harmless rewordings)

What was built: `python3 -m usmeta.bench_v2` -> bench_v2.jsonl, **27,193 candidate reports** for 1,610 cases (150 cases per dataset sampled by group with seed 0; all 256 for BrEaST). Reference = the "standard" style true report from Step 2. No AI wrote any candidate; errors are made by changing ONE fact and re-rendering.

| dataset | cases | identical | harmless (primary / secondary) | errors |
|---|---|---|---|---|
| BrEaST | 256 | 256 | 1276 / 1019 | 3933 |
| BUS-BRA | 151 | 151 | 604 / 453 | 1656 |
| BUSI | 150 | 150 | 600 / 474 | 998 |
| UDIAT | 150 | 150 | 600 / 450 | 1315 |
| BUS-UCLM | 152 | 152 | 608 / 551 | 525 |
| TN3K | 150 | 150 | 600 / 450 | 977 |
| TN5000 | 150 | 150 | 600 / 450 | 990 |
| DDTI | 150 | 150 | 597 / 450 | 1651 |
| HC18 | 150 | 150 | 750 / 450 | 600 |
| FetalHead | 151 | 151 | 752 / 453 | 751 |

## Error categories (all datasets)

| category | errors |
|---|---|
| wrong measurement | 4741 |
| wrong severity/category | 4711 |
| false finding | 1692 |
| missed finding | 1338 |
| wrong location | 914 |

## Provisional severity (1 minor, 2 major, 3 critical)

| severity | errors |
|---|---|
| 1 | 4368 |
| 2 | 6075 |
| 3 | 2953 |

Rules (all **provisional, guideline-based, pending clinician ranking**):
- missed or false lesion, benign<->malignant, left/right side swap: 3
- BI-RADS (or TI-RADS) change that crosses the biopsy line (<=3 vs >=4a): 3; two or more steps on the same side: 2; one step on the same side: 1
- size x0.5 or x2: 2; size x1.5: 1; extra lesion, calcifications/foci added or missed, margin or shape change, histology change, plane change: 2
- echo pattern, posterior features, halo flips, orientation flip (1; 2 on DDTI where taller-than-wide is a TI-RADS feature), image-position change: 1
- fetal head circumference shifted by +3 mm: 1; +10 or -10 mm: 2; +30 mm: 3 (our guess, no source)

## Harmless groups

- **primary** (used in the main AUROC): terse style, long style, sentence reorder, synonyms, unit rewrite (mm -> cm) where a size in mm exists
- **secondary** (reported separately, `primary=false`): negation rewording ("no calcifications" -> "calcifications are absent"), hedging prefix, padding (+1 or +3 neutral sentences)

## Splits
dev 30% / test 70%, assigned by group id (BrEaST, BUS-BRA, BUS-UCLM, DDTI, FetalHead have patient/exam groups). BUSI, UDIAT, TN3K, TN5000, HC18 have no group id in the records, so the case id is used as a stand-in (`group_source` field): their splits could share a patient. Tests check that no group appears in both splits.

## Caveats
- Errors are generated only for fields a dataset supports: BUSI/UDIAT/BUS-UCLM/BUS-BRA have no descriptors or mm; TN3K/TN5000 have no diagnosis (class 0/1 unconfirmed) and no descriptors; fetal sets only get measurement/plane errors.
- Error counts per dataset differ a lot (BrEaST has the most error types), so never pool datasets: report per dataset.
- The 150-case sample is a subset; rebuild with a larger `per_dataset` if more power is needed.
- Severity is our guess: do not quote it as clinical ground truth.

---
Limitations: see [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md) (templated reports, upper bounds, prompt-sensitive judge, provisional severity, possible exposure). 
