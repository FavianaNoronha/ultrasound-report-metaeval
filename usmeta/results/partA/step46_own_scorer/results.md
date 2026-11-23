# Step 46: UScore and CRQS on ultrasound reports

UScore is assembled from the project's existing checks and evaluated on its own benchmark plus model-written text. No clinician has validated it; radiologist-written reports are still needed.

Primary test result: on 861 core reports from 235 groups, CRQS separated planted errors from harmless rewordings better than UScore (AUROC 0.998 vs 0.656; paired UScore-minus-CRQS difference -0.341, 95% CI -0.385 to -0.298).

Writer: `mlx-community/Meta-Llama-3.1-8B-Instruct-4bit` at revision `241a666dad6cb93c8ff213d39a7f34a36bf26db4`. Planned Set B: 360 cases; Set A overlap: 0.
Core test report generation: complete; cached reports: 1912.

## Hypotheses

| Hypothesis | Result |
|---|---|
| H1, separation | DOES NOT PASS; UScore AUROC 0.656 |
| H2, monitor | DOES NOT PASS; catch 0.181; harmless flagged 0.163 |
| H3, extras-filter stress subset | Descriptive; n=179, catch 0.183, harmless flagged 0.256 |
| H4, fact versus wording (template ceiling) | DOES NOT PASS; fact share 0.440, wording share 0.000 |
| H5, limit of detection | 5% size AUROC 0.132; 1 mm head circumference AUROC 1.000 |
| H6, human rewordings | Descriptive; 29 items, AUROC 0.654 |
| H7, provisional severity | PASS; Spearman -0.970 |
| Set B dev/val transfer | Descriptive only; 293 scored; UScore AUROC 0.584; CRQS AUROC 0.996 |

## Scorer comparison

| Scorer | AUROC (95% group-bootstrap CI) | UScore minus scorer (95% paired CI) |
|---|---:|---:|
| UScore | 0.656 (0.612–0.699) | — |
| BLEU | 0.676 (0.643–0.710) | -0.019 (-0.077–0.029) |
| ROUGE-L | 0.698 (0.664–0.733) | -0.042 (-0.092–0.005) |
| chrF | 0.682 (0.648–0.717) | -0.026 (-0.080–0.024) |
| BERTScore | 0.613 (0.571–0.656) | 0.043 (-0.011–0.096) |
| RaTEScore | 0.567 (0.526–0.605) | 0.089 (0.038–0.144) |
| CRQS | 0.998 (0.996–0.999) | -0.341 (-0.385–-0.298) |
| CRQS clipped sensitivity | 0.998 (0.996–0.999) | — |
| Step 45 learned scorer | 0.843 (0.808–0.875) | -0.187 (-0.235–-0.144) |
| Holistic Gemma on rule-clear subset | not estimable (judge scored harmless cases only) | — |

## Exploratory diagnostic (not preregistered)

If rule-clear reports are assigned 1.0 instead of the Gemma score, AUROC is 0.990 (0.983–0.995). This suggests the judge fallback penalizes some harmless rewordings; it is not the preregistered UScore result.

## Notes

Filter counts: `{"devval|breast|true": 29, "devval|breast|twin": 9, "devval|fetal|true": 6, "devval|fetal|twin": 4, "devval|thyroid|true": 12, "devval|thyroid|twin": 7, "test|breast|lod": 62, "test|breast|true": 102, "test|breast|twin": 37, "test|fetal|lod": 13, "test|fetal|true": 18, "test|fetal|twin": 9, "test|thyroid|lod": 21, "test|thyroid|true": 33, "test|thyroid|twin": 20}`
Missing generation: `{}`

| Set / organ | Missing-gold filter dropped | Extras filter dropped | Kept |
|---|---:|---:|---:|
| devval|breast | 21.7% | 14.2% | 68.3% |
| devval|fetal | 1.7% | 6.7% | 91.7% |
| devval|thyroid | 11.7% | 6.7% | 84.2% |
| test|breast | 24.1% | 21.7% | 61.0% |
| test|fetal | 2.1% | 6.9% | 92.3% |
| test|thyroid | 9.7% | 6.0% | 85.7% |

CRQS follows the released PathBench code's signed penalties and reports the unclipped normalized score plus a clipped sensitivity score. The paper's displayed formula and the implementation differ; see `CRQS_SOURCE.md`.
The holistic Gemma judge was called only when the rules found no discrepancy; this left 632 harmless reports and no errors in its scored subset, so its AUROC is not estimable.

Test groups below 30 are too small to compare. The report describes model-written free text, not clinical validation.
