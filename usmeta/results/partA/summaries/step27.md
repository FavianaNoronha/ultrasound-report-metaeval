# Step 27: LLM fact extractor + deterministic comparer (`llm_finding_f1`)

Limitations: [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md). Prior art: [docs/step27_prior_art.md](../../../docs/step27_prior_art.md). Code: `usmeta/step27_extractor.py`, `step27_run.py`, `step27_report.py` (new files; `schema.py` and every other frozen file untouched). Test-split access is logged in `results/partA/test_access.log` (script `usmeta.step27_run`).

**What it is.** Qwen2.5-7B-Instruct (4-bit MLX, greedy, not the Gemma judge family) reads a report and fills a fixed per-organ JSON (null = not stated); plain code converts mm / cm / % and maps the JSON onto the schema facts; the comparer is the existing `schema.finding_scores` (same credit rules and tolerances), so the only new part is the extractor. 3 few-shot examples per organ, all from DEV cases; every call cached; the prompt was fixed after dev validation and **not changed after seeing the human rewordings or the test run**.

## Headline

- **On the templated benchmark `llm_finding_f1` is almost as good as the regex `finding_f1` and clearly better than the Gemma judge.** Test AUROC of planted error vs harmless rewording (small / matched / large; 590 cases, 503 groups): `llm_finding_f1` 0.99 (0.99–1.00) / 1.00 (1.00–1.00) / 1.00 (1.00–1.00); Gemma `judge_score` 0.89 (0.86–0.91) / 1.00 (1.00–1.00) / 0.88 (0.86–0.91); RaTEScore 0.60 (0.55–0.63) / 0.59 (0.55–0.62) / 0.36 (0.31–0.40). Weakest cell: fetal head vs small (0.97 (0.94–0.99)).
- **Wiring gate passed:** identical copies score exactly 1.0000 (breast 1.0000, thyroid 1.0000, fetal head 1.0000; n = 60); 0 unparseable replies in 2812 test texts.
- **Extractor accuracy (dev, 300 reports, all fields right per report):** breast 0.96, thyroid 0.99, fetal head 1.00. On the test texts it agrees with the rule extractor on 0.998 / 1.000 / 0.991 of fields.
- **Stable under reworded prompts:** 0.2% (altA) and 1.6% (altB) of extracted fields change; the pair score `llm_finding_f1` changes by more than 0.1 in 0.4% and 1.8% of dev pairs (the Gemma judge changed in 18% and 26% of pairs in Step 21c; different samples, see caveats).
- **Human rewordings (29, too small to compare, all cells †):** AUROC error vs human rewording 0.90 (0.80–0.97) for `llm_finding_f1` (regex `finding_f1` 0.94 (0.85–1.00), Gemma `judge_score` 0.84 (0.72–0.95), RaTEScore 0.17 (0.08–0.27)). The extractor reads 76% of the human rewordings to the same facts as the reference; the misses are phrasing it did not normalise ("wider than taller", "in the mass") and two items where it read a different orientation.

## Decision line

**`llm_finding_f1` is a usable scorer for the templated benchmark and it is non-circular in the narrow sense that it does not need our template wording: a different model family from the judge reads the text and fixed code compares the facts. On these data it beats the Gemma judge (pooled AUROC 0.99 vs small and 1.00 vs large harmless, against 0.89 and 0.88 for the judge; both 1.00 vs matched) and is far more stable under prompt rewording (about 0.4-1.8% of pairs move by more than 0.1, against 18-26% for the judge). It does NOT beat the regex `finding_f1` (1.00), and this benchmark cannot show that it is better on real writer output: the test text is templated, the few-shot examples are templated, and the 29 human rewordings are too few to compare. Step 28 is the free-text check.** Do not call it validated on free text from this step alone.

## 1. Wiring and extractor accuracy on DEV

100 dev reports per organ (25 references, 40 planted errors, 35 template rewordings; seed 0; `dev_validation.json`, items in `dev_validation_items.json`). Known facts = the rule extractor on the same templated text (the texts are generated from facts; for references it equals the dataset facts). Parse failures: 0. Per-field accuracy is in `dev_validation.json`; every field is 1.00 where it is stated except the ones below.

| field | known present | correct | spurious (known absent, extractor gave a value) |
|---|---|---|---|
| breast.size_mm | 44 | 41 | 0 |
| breast.path | 98 | 98 | 1 |
| thyroid.echo | 25 | 25 | 1 |

All-fields-correct per report: breast 0.96, thyroid 0.99, fetal head 1.00. The five misses are: breast size 15 mm read as 5 and 11 mm as 1 (digit dropped), one size missing, "No focal lesion is seen." given `pathology: normal` (inferred, not written), and thyroid "echogenic foci" read as an echo pattern. These are the kinds of error the test table below includes.

## 2. Prompt stability (DEV, same 100 reports per organ, two reworded extractor prompts)

| prompt | fields that change vs main prompt (breast / thyroid / fetal head) | reports with any change | `llm_finding_f1` of dev pairs changed by > 0.1 | changed at all | all fields correct (breast / thyroid / fetal head) |
|---|---|---|---|---|---|
| altA | 0.3% / 0.0% / 0.0% | 4% / 0% / 0% | 0.4% (n = 225) | 1.3% | 0.98 / 0.99 / 1.00 |
| altB | 2.4% / 0.7% / 0.0% | 23% / 7% / 0% | 1.8% (n = 225) | 8.9% | 0.80 / 0.94 / 1.00 |

altB (schema listed in reverse order, different wording) is less accurate on breast (0.80 of reports fully right vs 0.96), so "stable" is not the same as "right": the prompt matters for breast. The judge numbers (18% / 26%) come from the Step 21c test sample (89 cases, swap / reworded instructions); these come from 225 dev pairs, so the two are indicative, not like for like.

## 3. Test run: judged subset (59 cases per dataset = Gemma judge sample of Steps 10d + 12; no cap needed)

2841 candidate rows, 590 cases, 2812 unique texts, 2625 model calls in 2.78 h of model time (a second run would resume from the cache). AUROC = P(planted error scores lower than a harmless rewording of the same reference), ties 0.5, 95% CI by group bootstrap (1,000, seed 0); strict = share of pairs with the error strictly lower. Judge and RaTEScore rows use only pairs the judge saw (same set for every row).

### vs harmless small

| scorer | breast | thyroid | fetal head | pooled | pooled strict preference |
|---|---|---|---|---|---|
| llm_finding_f1 (Qwen2.5-7B extractor) | 1.00 (0.99–1.00) | 1.00 (1.00–1.00) | 0.97 (0.94–0.99) | 0.99 (0.99–1.00) | 0.99 |
| finding_f1 (regex extractor, upper bound) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 |
| Gemma judge_score | 0.84 (0.79–0.88) | 0.96 (0.94–0.99) | 0.90 (0.85–0.94) | 0.89 (0.86–0.91) | 0.87 |
| Gemma sentence_f1 | 0.69 (0.64–0.74) | 0.90 (0.86–0.94) | 0.88 (0.84–0.92) | 0.79 (0.77–0.82) | 0.71 |
| RaTEScore | 0.61 (0.55–0.67) | 0.60 (0.54–0.65) | 0.55 (0.46–0.64) | 0.60 (0.55–0.63) | 0.56 |

### vs harmless matched one-word synonym

| scorer | breast | thyroid | fetal head | pooled | pooled strict preference |
|---|---|---|---|---|---|
| llm_finding_f1 (Qwen2.5-7B extractor) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.99 (0.98–1.00) | 1.00 (1.00–1.00) | 1.00 |
| finding_f1 (regex extractor, upper bound) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 |
| Gemma judge_score | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 |
| Gemma sentence_f1 | 0.93 (0.91–0.94) | 0.96 (0.95–0.98) | 1.00 (1.00–1.00) | 0.95 (0.94–0.96) | 0.90 |
| RaTEScore | 0.69 (0.65–0.74) | 0.59 (0.55–0.64) | 0.30 (0.21–0.39) | 0.59 (0.55–0.62) | 0.54 |

### vs harmless large (style swap)

| scorer | breast | thyroid | fetal head | pooled | pooled strict preference |
|---|---|---|---|---|---|
| llm_finding_f1 (Qwen2.5-7B extractor) | 1.00 (0.99–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 |
| finding_f1 (regex extractor, upper bound) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 |
| Gemma judge_score | 0.88 (0.84–0.91) | 0.94 (0.90–0.96) | 0.81 (0.72–0.88) | 0.88 (0.86–0.91) | 0.87 |
| Gemma sentence_f1 | 0.85 (0.82–0.88) | 0.84 (0.80–0.88) | 0.81 (0.72–0.88) | 0.84 (0.81–0.87) | 0.78 |
| RaTEScore | 0.46 (0.39–0.53) | 0.32 (0.28–0.37) | 0.16 (0.10–0.22) | 0.36 (0.31–0.40) | 0.36 |

Cases / groups: breast 295 / 236, thyroid 177 / 171, fetal head 117-118 / 95-96 (small and large), pooled 589-590 / 502-503; all cells have at least 30 groups. The `llm_finding_f1` misses in fetal head vs small come from one harmless rewording, "Cranial circumference" for "Head circumference" (13 candidates: the extractor returns no head circumference, so the fact is lost and the score drops to 0.67).

## 4. The 29 human rewordings (Step 21d), reported separately

| scorer | breast (9) | thyroid (10) | fetal head (10) | pooled (29) |
|---|---|---|---|---|
| llm_finding_f1 | 0.73 (0.49–0.94) † | 0.96 (0.88–1.00) † | 1.00 (1.00–1.00) † | 0.90 (0.80–0.97) † |
| regex finding_f1 | 0.81 (0.52–1.00) † | 1.00 (1.00–1.00) † | 1.00 (1.00–1.00) † | 0.94 (0.85–1.00) † |
| Gemma judge_score | 0.92 (0.80–1.00) † | 0.89 (0.74–1.00) † | 0.70 (0.40–1.00) † | 0.84 (0.72–0.95) † |
| RaTEScore | 0.37 (0.14–0.60) † | 0.12 (0.03–0.23) † | 0.05 (0.00–0.15) † | 0.17 (0.08–0.27) † |

All cells have 9-10 items: **too small to compare**. Identical copies on this set: 1.0000. Mean `llm_finding_f1` of a human rewording against its reference: 0.970 (a perfect reader would give 1.000). Items below 1.0: H02 ("wider than taller", "in the mass"), H03 and H05 (orientation read the other way), H04 and H06 (a shape added), H07 (position "middle"), H16 ("taller than wider"): all in `human_results.json`.

## Caveats and deviations

- **Templated text.** The test candidates are our own templates and rewordings; the few-shot examples are templated too. This measures how well the extractor reads templated and rewritten templated text, not free clinical prose. Step 28 tests free text from a real writer.
- **"Known facts" = the rule extractor** on the same text (plus the dataset facts for references). A wrong rule extraction would hide an LLM error or blame it unfairly; Step 6 / 11b found the rule extractor accurate on these templates.
- **Judge columns** use only judged pairs (59 cases per dataset); the non-judge scorers in the same rows use the same pairs. The earlier full-set numbers of Steps 5-6 are unchanged.
- **Human rewordings:** 29 items, 9-10 per organ; no prompt change was made after seeing them (rule of the brief). H01 excluded as in Step 21d.
- **Stability sample** is dev pairs (225), the judge sample is test (89 cases); the two shares are not directly comparable.
- **One extractor model and one machine** (Qwen2.5-7B-Instruct 4-bit, MLX, greedy, 16 GB Mac); a first run of the dev job at low priority was abandoned and rerun at normal priority (results come from the cache, same prompt). The test pass took about 2.8 h of model time, inside the 3 h cap.
- No "first" claim: see the prior-art note. Possible training exposure of Qwen to public ultrasound reports is unverifiable.
