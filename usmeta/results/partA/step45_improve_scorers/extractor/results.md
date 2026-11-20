# Step 45, Part B: extractor v5 on the free-text set A, against v4 on the same reports

**PASS the pre-registered rule** (full-report match >= 85% with lower 95% bound >= 75% in each organ, and v4 lower on the same reports). The 'v4 lower' clause is read as pooled over the reports: v4 is lower pooled and in breast but **tied, not lower, in thyroid and fetal head; under a stricter per-organ reading the rule would not be fully met.** Full-report exact match on writer-made free text (test): v5 breast 98.1% (95.5-100.0), thyroid 98.7% (96.6-100.0), fetal head 100.0% (100.0-100.0) (rule: >= 85% with lower 95% bound >= 75%: met). v4 on the same reports: breast 91.7% (85.3-96.6), thyroid 98.7% (96.6-100.0), fetal head 100.0% (100.0-100.0); pooled v5 99.1% (98.3-99.8) vs v4 97.3% (95.4-98.8). Paired difference v5 minus v4: breast +6.4 points (95% CI +2.0 to +11.7), thyroid +0.0, fetal head +0.0. A pass here is "better on writer-made free text", not clinical validation, and **the main test set excludes the failure that motivated v5**: the extras filter of Part A removed the thyroid reports that state BI-RADS (exploratory side check below).

Pre-registration: [../PREREG.md](../PREREG.md). Code: `usmeta/step45_extractor_v5.py`, `step45_partB_report.py` (new; step27 extractor, step43 v4 text and the Part A set imported unchanged). Set A: [../freetext/results.md](../freetext/results.md).

## What v5 is

Qwen2.5-7B-Instruct 4-bit, greedy, same dev-only few-shot examples as v3 / v4, a stricter instruction (V5 text in the code), and three deterministic layers on the model's JSON: (1) **per-organ strict schema** (keys outside the organ's schema dropped, so no BI-RADS on thyroid or fetal head and no TI-RADS on breast; values outside the allowed vocabulary become null after a fixed synonym map; positions normalised to upper / middle / lower x left / central / right); (2) **regex values override the model** for size, head circumference, count, side, BI-RADS (breast only) and TI-RADS (thyroid only), so a number the text does not contain cannot appear; (3) an **evidence-in-text** rule: an orientation, shape, echo, posterior, halo, pathology, composition or plane value is kept only if its key word occurs in the report. **"JSON-constrained output" is implemented as validation of the model's output, not as grammar-constrained decoding (mlx_lm offers none here)** — a deviation from the PREREG wording.

## Test results (set A test; reports kept by the gold and extras checks of Part A; one logged test read for v4 and v5)

| organ | reports | groups | v5 full-report match | v4 full-report match | paired v5 - v4 (95% CI) |
|---|---|---|---|---|---|
| breast | 156 | 68 | 98.1% (95.5-100.0) | 91.7% (85.3-96.6) | +6.4 (+2.0 to +11.7) |
| thyroid | 150 | 86 | 98.7% (96.6-100.0) | 98.7% (96.6-100.0) | +0.0 (-1.9 to +2.1) |
| fetal | 256 | 75 | 100.0% (100.0-100.0) | 100.0% (100.0-100.0) | +0.0 (+0.0 to +0.0) |
| pooled | 562 | 229 | 99.1% (98.3-99.8) | 97.3% (95.4-98.8) | |

Per-field accuracy (test, share of reports whose field matches the gold; a field the gold does not have counts as right if the independent lexicon says the report states the extracted value). v5 / v4:

- **breast:** pos 1.000 / 0.987, echo 1.000 / 0.968, path 0.994 / 1.000, hist 0.987 / 0.962
- **thyroid:** pos 1.000 / 0.993, margin 0.987 / 0.993
- **fetal:** all fields 1.000 for both

## Tuning on dev/val (set A dev/val reports; v5 only)

After the first v5 run on dev/val the post-processing was changed (position and count wording, evidence-in-text) and re-applied to the SAVED model outputs (no new model call), then frozen: full-report match on dev/val breast 0.975, thyroid 1.000, fetal head 1.000 (first run before the fixes: 0.899, 0.938, 1.000). The instruction text was not changed after the first dev/val run. The test set was scored once after the freeze.

## Exploratory side check: thyroid reports that state BI-RADS (the Step 43 failure mode)

Set A's extras filter dropped the thyroid reports in which the writer added a BI-RADS category (a breast scale; the supplied facts had none). 79 such test reports state every supplied value and contain no other unsupplied fact. The correct extraction has `tirads` null. Share with `tirads` null: **v5 100%**, **v4 90%** (v4 wrote the BI-RADS category into `tirads` in 10%). The other thyroid fields are all right in 100% of these reports for v5 and 92% for v4. **This check is exploratory and was not pre-registered** (it was added after the main test numbers existed and is not part of the pass rule). On this writer's text even v4 almost never wrote BI-RADS into `tirads` (the Step 43 failure appeared on real Qwen2.5-VL reports, not here), so this set does not reproduce the failure either; v5 gets `tirads` null by construction (TI-RADS is read from the text by regex only), so the number shows that the rule works, not that the model learned anything.

## Deviations from the PREREG

- Smaller set A (Part A results.md); reports that add unsupplied facts are dropped (stricter than the PREREG's gold check).
- JSON-constrained output = output validation, not constrained decoding (above).
- The PREREG pass clause "v4 lower on the same reports" is read two ways above; the verdict line gives both.
- v4 here is the Step 43 v4 instruction with the unchanged Step 27 mapping (no post-processing), run on the same reports with its own cache.

## Caveats

- **Writer and extractor are the same model family** (Qwen2.5-7B-Instruct); the extractor may read its own family's text more easily than other writers' text.
- The writer copies the structure of the supplied fact list, so the reports are easier than real radiologist or VLM text; v4 already scores 0.987 (thyroid) and 1.000 (fetal head) here, so only breast can show a gain.
- The regex layer (numbers, sides, counts, categories) is what removes the v3 / v4 errors; on text that writes sizes as two dimensions or in words it has not been tested (Part C caveat).
- Pass thresholds use the group bootstrap (groups = cases); 68-86 groups per organ.
