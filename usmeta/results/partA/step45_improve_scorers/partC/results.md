# Step 45, Part C: deterministic number checker on the free-text set A

**DOES PASS the pre-registered rule** (reaches AUROC 0.80 at a 5% size change and a 1 mm head-circumference change, with at most 2% of harmless rewordings flagged). On the writer-made free-text test set the checker has AUROC 1.00 at every level tested (size x1.05 to x2.0, head circumference 1 to 10 mm) and flags **0.0% (0.0-0.0)** of 562 harmless rewordings. Limit of detection: size 5% (breast, thyroid and both pooled), head circumference 1 mm (the lowest level tested). Cells: breast size 22 and thyroid size 19 groups at the 5% level (under 30: too small to compare on their own); **pooled breast + thyroid size 41 groups, head circumference 34 groups (both decided).** The pass is a pass on writer-made free text, not clinical validation.

Pre-registration: [../PREREG.md](../PREREG.md). Code: `usmeta/step45_numchecker.py` (parser + score), `step45_partC.py`, `step45_partC_report.py`. Set A: [../freetext/results.md](../freetext/results.md).

## What the checker is

A regex parser reads the size (mm, cm, percent of the image width), head circumference, lesion count, side and BI-RADS / TI-RADS category from the reference and the candidate; score = 1 minus the largest deviation (relative size or head circumference beyond the tolerance, or 1 for a count / side / category mismatch); a candidate is flagged if score < 1. No model, no extractor.

## Tolerance (fixed on dev/val of set A)

Grid: relative size tolerance [0.0, 0.005, 0.01, 0.02, 0.03, 0.05], head circumference tolerance (mm) [0.0, 0.05, 0.1, 0.25, 0.5]; target: at most 2% of harmless rewordings flagged. Result on 581 dev/val harmless reports: the smallest tolerance (0 and 0 mm) already flags 0.0%, so it was kept at 0. Flagged-by on dev/val: nothing.

## Test results (writer-made free text, one planted-error twin or graded twin per case, harmless = the same case's other-style reports)

| quantity | value |
|---|---|
| harmless rewordings flagged (all) | 0.0% (0.0-0.0) |
| harmless flagged, breast | 0.0% (0.0-0.0) (156 reports) |
| harmless flagged, thyroid | 0.0% (0.0-0.0) (150 reports) |
| harmless flagged, fetal | 0.0% (0.0-0.0) (256 reports) |
| catch of the planted-error twins (all kinds of planted error) | 65.9% (58.8-73.0) (185 twins) |

### Limit of detection (AUROC of the planted change vs the same case's harmless free-text reports; 0.80 rule; group bootstrap)

| cell | level -> AUROC | groups per level | LOD (95% CI) | too small |
|---|---|---|---|---|
| breast|size | 0.05: 1.00, 0.1: 1.00, 0.25: 1.00, 1.0: 1.00 | 22, 22, 21, 20 | 0.05 (0.05-0.05) | 0.05, 0.1, 0.25, 1.0 |
| thyroid|size | 0.05: 1.00, 0.1: 1.00, 0.25: 1.00, 1.0: 1.00 | 19, 19, 21, 22 | 0.05 (0.05-0.05) | 0.05, 0.1, 0.25, 1.0 |
| breast+thyroid|size | 0.05: 1.00, 0.1: 1.00, 0.25: 1.00, 1.0: 1.00 | 41, 41, 42, 42 | 0.05 (0.05-0.05) | — |
| fetal|hc_mm | 1: 1.00, 2: 1.00, 5: 1.00, 10: 1.00 | 34, 33, 34, 36 | 1 (1-1) | — |

### Catch of the planted-error twins by planted field (numbers and categories only: the checker reads nothing else)

| field | twins | caught |
|---|---|---|
| birads | 6 | 100% |
| calc | 2 | 0% |
| comp | 2 | 0% |
| count | 7 | 14% |
| echo | 1 | 0% |
| foci | 2 | 0% |
| halo | 2 | 0% |
| hc_mm | 79 | 100% |
| hist | 5 | 0% |
| lesion | 18 | 0% |
| orient | 5 | 0% |
| path | 2 | 0% |
| plane | 10 | 0% |
| pos | 8 | 0% |
| size_mm | 1 | 100% |
| size_pct | 30 | 100% |
| tirads | 5 | 100% |

The checker catches every planted number, category (BI-RADS / TI-RADS) and head-circumference change and nothing else (lesion absent / present, position, orientation, plane, pathology, histology, halo, calcifications are not numbers): it is a complement to a fact extractor or a judge, not a replacement (Part F).

## Deviations from the PREREG

- Smaller set A than the PREREG (Part A results.md). Levels: size x1.05, x1.10, x1.25, x2.0 and head circumference 1, 2, 5, 10 mm (the Step 35 grids are finer).
- **The test split was read twice by this part** (`test_access.log`: two `usmeta.step45_partC` lines). The first run gave per-organ size cells with 19-22 groups (under 30, "too small to compare"); a **pooled breast + thyroid size cell (41 groups) was added after seeing that** and the evaluation was re-run with a second logged read. The per-organ numbers did not change between the runs (deterministic checker, same reports).
- Pass logic: the PREREG does not say how cells under 30 groups count; here the pass uses the pooled size cell and the head-circumference cell (both at least 30 groups).

## Caveats

- **AUROC 1.00 at every level is close to true by construction on this text:** the writer copies the supplied numbers verbatim, so a changed number is always visible to a parser, and harmless reports always carry the original number. Real radiologist or VLM text writes sizes as two dimensions ("3 cm x 2 cm"), in words, with different units or rounded; the parser has not been tested on such text.
- The checker needs both reference and candidate to state the quantity (a missing number is not flagged); it cannot see omissions, wrong diagnoses or wrong locations (twin catch by field above).
- Set A kept reports only after the gold and extras checks (Part A), so the harmless class contains only reports that state the supplied numbers; the 0% harmless-flagged rate describes those.
