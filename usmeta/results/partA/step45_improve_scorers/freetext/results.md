# Step 45, Part A: free-text set with automatic gold (writer-made; no human grader)

Pre-registration: [../PREREG.md](../PREREG.md) (committed before any Step 45 number). Code: `usmeta/step45_freetext.py`, `step45_partA_report.py`. Writer: Qwen2.5-7B-Instruct 4-bit (MLX), temperature 0.7, per-item seed, three styles (terse, narrative, impression-first); the writer gets only the supplied facts. Prompts saved in `plan.json` and in every record of `gen_cache.jsonl`.

## What was built (and how it differs from the PREREG)

- **Sizes are smaller than the PREREG.** PREREG: 600 dev/val cases and 600 test cases, 3 styles, a planted-error twin each. Built: **270 dev/val cases (90 per organ: 60 dev + 30 val) and 270 test cases (90 per organ)**, 3 styles for the true facts, one planted-error twin in one rotating style, plus **323 kept graded size / head-circumference reports** (up to 40 test cases per field group, 4 levels: size x1.05, x1.10, x1.25, x2.0; head circumference 1, 2, 5, 10 mm, sign alternating) for the limit of detection in Part C. Reason: the writer needs about 4-6 s per report on this 16 GB Mac (2.1 h of generation here; the PREREG size would take about 10 h for Part A alone).
- **Case selection:** seeded (seed 45), balanced over organs, datasets round-robin inside an organ, group-disjoint by the locked splits (dev / val / test); each case has at least one planted-error candidate in the benchmark. The twin uses one of the case's own planted-error candidates (its facts re-extracted from the templated candidate); the twin's field / category / severity are recorded in `cases.json`.
- **Gold** = the flat facts of the templated reference (`schema.extract_rule`). A deterministic lexicon check (synonyms + exact numbers; independent of every extractor under test) keeps a report only if it states **every gold value**. Fields: count, side, position, orientation, size (mm / cm / % of the image width), head circumference, shape, margin (with its qualifiers), echo, posterior features, calcifications, halo, BI-RADS / TI-RADS category, pathology, histology, composition, foci, plane.
- **Added after the first look at the writer's replies (a deviation, listed here and in the PREREG-relative notes):** the writer often added facts that were not in its list (a BI-RADS category when none was given, BI-RADS on thyroid and fetal-head reports, a side for a breast lesion with no side). Such a report is not a harmless rewording, so an **extras check** (also deterministic) drops any report that states an unsupplied category, pathology, side, number with a unit, calcification / halo / echo / shape value, or a conflicting enumerated value. The PREREG only required that every gold value is stated; the extras filter is stricter and removes more reports. Drops are counted below and are not charged to any extractor or scorer.

## Reports generated, dropped and kept

| set | organ | kind | generated | dropped | of which: gold value not stated | of which: extras only | kept |
|---|---|---|---|---|---|---|---|
| devval | breast | true facts (3 styles) | 270 | 111 (41%) | 65 | 46 | 159 |
| devval | breast | planted-error twin | 90 | 44 (49%) | 25 | 19 | 46 |
| devval | thyroid | true facts (3 styles) | 270 | 108 (40%) | 18 | 90 | 162 |
| devval | thyroid | planted-error twin | 90 | 37 (41%) | 5 | 32 | 53 |
| devval | fetal | true facts (3 styles) | 270 | 10 (4%) | 0 | 10 | 260 |
| devval | fetal | planted-error twin | 90 | 4 (4%) | 0 | 4 | 86 |
| test | breast | true facts (3 styles) | 270 | 114 (42%) | 60 | 54 | 156 |
| test | breast | planted-error twin | 90 | 36 (40%) | 22 | 14 | 54 |
| test | breast | graded size / HC twin | 158 | 73 (46%) | 43 | 30 | 85 |
| test | thyroid | true facts (3 styles) | 270 | 120 (44%) | 30 | 90 | 150 |
| test | thyroid | planted-error twin | 90 | 45 (50%) | 9 | 36 | 45 |
| test | thyroid | graded size / HC twin | 158 | 73 (46%) | 17 | 56 | 85 |
| test | fetal | true facts (3 styles) | 270 | 14 (5%) | 3 | 11 | 256 |
| test | fetal | planted-error twin | 90 | 1 (1%) | 0 | 1 | 89 |
| test | fetal | graded size / HC twin | 160 | 7 (4%) | 1 | 6 | 153 |

Overall 797 of 2636 generated reports dropped (30%). Most frequent unsupplied statements (extras): thyroid|wrong_organ_scale_or_diagnosis 312, breast|birads 135, breast|side 82, fetal|wrong_organ_scale_or_diagnosis 33, thyroid|number 23, fetal|number 21. Most frequent supplied values the writer left out: breast|count 180, breast|margin 41, thyroid|count 41, breast|calc 37, breast|path 35, thyroid|tirads 26. The lesion count (the writer often wrote "a mass" without saying "single") is the main omission in breast.

## The set used in Parts B, C, E, F

| set | organ | cases | kept true-fact reports | cases with a kept planted-error twin | cases with both |
|---|---|---|---|---|---|
| devval | breast | 90 | 159 | 46 | 44 |
| devval | thyroid | 90 | 162 | 53 | 49 |
| devval | fetal | 90 | 260 | 86 | 86 |
| test | breast | 90 | 156 | 54 | 52 |
| test | thyroid | 90 | 150 | 45 | 44 |
| test | fetal | 90 | 256 | 89 | 89 |

Planted-error twins kept per organ are 44-89 cases, so every rate on the twins has wide intervals (cells under 30 groups are marked too small to compare in the later parts).

## Three kept test reports (the first kept case of each organ in seeded order; writer output unedited)

- **breast** (terse): reference "No focal lesion is seen. Pathology: normal." -> writer "No lesion or nodule seen. Pathology: normal."
- **thyroid** (narrative): reference "A single nodule is seen in the middle central part of the image, measuring about 17% of the image width. Wider than tall." -> writer "A thyroid nodule is present, number one, located in the middle central part of the image. It is oriented wider than tall, and measures about 17% of the image width."
- **fetal** (terse): reference "Fetal head, trans thalamic plane. Head circumference approximately 157 mm." -> writer "- scan plane: trans thalamic / - head circumference: 157 mm"

## Caveats

- **Writer-made free text is a proxy** for real radiologist or VLM text; it does not replace a clinician-written set. The writer copies the structure of the supplied fact list (many reports are list-like), so it is closer to the templates than real prose is; a pass in a later part is "better on writer-made free text", not "clinically validated".
- **Writer and extractor share a model family** (Qwen2.5-7B-Instruct writes the reports; extractors v4 / v5 are Qwen2.5-7B-Instruct). The extractor may read its own family's text more easily than other writers' text. The judge (Gemma) and the writer are different families, as the standing rule requires.
- The lexicon check is a deterministic approximation of "states the value" (it can accept a mention that is not exactly the stated fact and reject an unusual paraphrase); it was checked on the templated styles of dev cases (thyroid and fetal head 90 of 90; breast fails only on the lesion count, which templated breast text does not state, by design of the check).
- Dropping reports that omit values or add unsupplied facts selects the writer's better outputs; rates in Parts B-F describe those, not all writer outputs.
