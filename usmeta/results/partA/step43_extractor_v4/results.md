# Step 43: extractor v4 on 30 fresh free-text reports graded by a person

**DOES NOT PASS the pre-registered rule: 2 of 20 breast + thyroid reports fully right (rule: at least 17 of 20; 95% Wilson CI 0.03-0.3).** Step 28 stays inconclusive; v4 labels are not validated on free text.

| organ | fully right / n | 95% CI |
|---|---|---|
| breast | 1 / 10 | 0.02-0.4 |
| thyroid | 1 / 10 | 0.02-0.4 |
| fetal | 8 / 10 | 0.49-0.94 |

Wrong rows: D01, D02, D03, D04, D05, D07, D08, D09, D10, D11, D12, D15, D16, D17, D18, D19, D21, D26, D28, D29. Wrong fields (grader's `wrong_fields`, by organ): breast margin x6, shape x4, pathology x4, halo x3, echo x2, calcifications x1, thyroid tirads x9, echo x6, composition x5, count x2, birads x1, fetal birads x2. Pre-registration: [PREREG.md](PREREG.md). One grader, not blinded to the project, not a clinician; rubric differs from Step 32 (BI-RADS on thyroid), so the numbers are not strictly comparable to Step 32's 13 of 30.

## Wrong rows by error type (author reading of the grader notes; a row can have several types)

| error type | rows | n |
|---|---|---|
| BI-RADS category written into tirads on a thyroid report | D03, D04, D07, D09, D11, D17, D18, D21 | 8 |
| key outside the organ schema added (birads on fetal head / thyroid) | D05, D12, D16 | 3 |
| thyroid nodule echo omitted | D03, D07, D09, D11, D17, D18 | 6 |
| thyroid composition wrong (hypoechoic written as composition) or omitted | D04, D07, D11, D16, D18 | 5 |
| count 'multiple' written as a number or as the word | D04, D07 | 2 |
| stated TI-RADS left null (D16: "TIRADS 4C" in the impression) | D16 | 1 |
| breast shape narrowed or changed ("somewhat irregular ... lobulated" -> irregular) | D01, D08, D15, D28 | 4 |
| breast margin word not as written (mapped to circumscribed / not circumscribed) | D01, D08, D10, D15, D19, D28 | 6 |
| pathology benign filled from suggestive wording ("suggesting", "consistent with", "likely") | D02, D10, D19, D26 | 4 |
| halo invented | D10, D19, D29 | 3 |
| echo heterogeneous written for a mass first described as hypoechoic | D15, D29 | 2 |
| stated "no calcifications" left null | D02 | 1 |

Sensitivity: counting the two single-judgement-call rows (D21, D26) as right would give 4 of 20 breast + thyroid, still far under 17.

## Reading

- **Instruction rule 4 was not followed on thyroid:** on 8 of the 10 thyroid reports that state a BI-RADS category, v4 still wrote it into `tirads` (and added a `birads` key on a ninth); the model (Qwen2.5-7B-Instruct, 4-bit, greedy) did not obey the rule although templated dev / val agreement stayed at 0.9989 / 0.9986. The thyroid nodule's echo was left null on 6 reports whose text says hypoechoic nodules or areas.
- **Breast:** 9 of 10 reports have at least one wrong field; the most frequent are the margin word not as written (6), shape narrowed or changed (4), pathology benign taken from suggestive wording (4) and a halo the report does not state (3).
- **Fetal head 8 of 10:** both wrong rows (D05, D12) are wrong only because the JSON added a `birads` key that is not in the fetal schema (BI-RADS 0 is in the report text); the other eight are all-null on reports that state no plane or head circumference.
- Step 32 (v3, a different grader rubric and different reports) had breast 7 of 12, thyroid 0 of 12, fetal head 6 of 6; v4 breast 1 of 10, thyroid 1 of 10, fetal head 8 of 10. The two checks are not strictly comparable (rubric, reports, one grader), so this is not evidence that v4 is worse than v3 on breast, but it shows no improvement on thyroid and no pass.

## Caveats

- **One grader, not blinded to the project, not a clinician; AI use by the grader cannot be verified.** Several wrong rows rest on judgement calls: on four breast rows (D02, D10, D19, D26) the grader treated "most consistent with / suggesting a benign lesion" as not a stated pathology, which is stricter than the grading guide (rule 7 accepts "most likely benign"); counting those pathology calls as right still leaves each of D02, D10 and D19 wrong on other fields, and D26 would become right (see the sensitivity line). The margin and shape rows follow guide rule 3 (copy the report's words).
- 30 reports (20 for the rule); the rule is fixed in the PREREG and the verdict does not depend on any single row (the sensitivity count is 4 of 20).
- Same Qwen2.5-VL-3B reports and writer as Steps 28 / 32; the thyroid and fetal-head reports state BI-RADS (a breast scale), a writer failure (LIMITATIONS 36).
- v4 changed instruction text only (same model, schema and dev-only few-shot examples); prompt rules alone did not change the 4-bit 7B model's behaviour on the thyroid BI-RADS case. **Step 28 (natural errors) was not re-run and stays inconclusive.**
