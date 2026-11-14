# Step 32 hand check of extractor v3 (30 free-text Qwen reports)

Sheet: `docs/step32_check_filled.csv`. One non-clinician reviewer; rubric in row 1 (judge the extraction against the report text only; BI-RADS written as `tirads` on thyroid = wrong; a stated BI-RADS/TI-RADS category left out = wrong; a narrowed shape = wrong). AI use by the reviewer was not verified.

**13 of 30 right (43%, 95% Wilson CI 0.27-0.61).**

| organ | right / n | 95% CI |
|---|---|---|
| breast | 7 / 12 | 0.32-0.81 |
| fetal | 6 / 6 | 0.61-1.0 |
| thyroid | 0 / 12 | 0.0-0.24 |
| breast + thyroid | 7 / 24 | 0.15-0.49 |

The 17 wrong rows by cause (author reading of the notes): birads as tirads 9 (C05, C07, C08, C09, C10, C11, C12, C15, C22), stated category left out 3 (C04, C20, C27), shape narrowed 3 (C02, C18, C28), other omitted or changed field 2 (C17, C19).

Borderline: C06 (counted right). Counting it wrong gives 12 right, 18 wrong.

**Verdict:** extractor v3 keeps templated agreement (Step 32) but is NOT validated on free text. The v3 labels in the Step 28 re-run therefore stay unreliable, and Step 28 stays inconclusive. The rubric is stricter than the Step 28 check (22 of 30 right; 10 of 18 on breast and thyroid), so the two numbers are not comparable. Fetal-head rows are empty extractions on reports that state nothing and are easy.
