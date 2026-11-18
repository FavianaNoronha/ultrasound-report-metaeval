# Step 43 pre-registration: stricter free-text fact extractor (v4), checked on 30 fresh reports graded by a person (written 2026-11-18, before v4 was run on any test or check report)

Background: extractor v3 (`step32_extractor_v3.py`) was right on 13 of 30 hand-checked free-text reports (`docs/step32_check_filled.csv`; `step32_extractor_v3/hand_check.md`: breast 7 of 12, thyroid 0 of 12, fetal head 6 of 6), so Step 28 (natural errors) stayed inconclusive. v4 tries a stricter instruction; this file fixes the change list, the fresh check and the pass rule before anything is run on test or check reports.

## What v3 got wrong in the filled check (author's reading of the reviewer's notes; 17 wrong rows)
| v3 error type | rows | what happened |
|---|---|---|
| E1 BI-RADS on a thyroid report written as `tirads` | 9 (C05, C07, C08, C09, C10, C11, C12, C15, C22) | the thyroid schema has no BI-RADS key; v3 put the BI-RADS category into `tirads` |
| E2 a described nodule returned as `{"lesion": "absent"}` / stated category left out | 3 (C04, C20, C27) | all keys null for a report that describes a nodule, so the unchanged mapping marks the thyroid "absent" |
| E3 shape narrowed (a stated range reduced to one term) | 3 (C02, C18, C28) | |
| E4 gland / background echotexture written as the nodule's echo | 4 of the rows above (C07, C10, C22, C28) | |
| E5 stated margin, enhancement, benign pathology or histology left out | 2 (C17, C18) | |
| E6 invented value or changed term (shape 'round' added, hypoechoic -> isoechoic, 'benign lesion' -> normal, a bright area labelled calcification) | 2 (C17, C19) | |
| E7 'multiple' nodules given no count | 2 notes (C05, C08) | schema `count` is an integer, so null is the only valid value |
Several rows have more than one error. **No text of any of the 30 reports is copied into the prompt or the few-shot examples**; the rules below are written in general terms.

## v4 changes (instruction text only; same model Qwen2.5-7B-Instruct 4-bit MLX, greedy, same schema, same three dev-only few-shot examples per organ as v3)
| rule in v4 | targets |
|---|---|
| 2 "record every stated fact, also in a summary or category line; leaving out is an error" | E2, E5 |
| 3 "copy a stated range or combination in the report's own words; do not narrow" | E3, E6 (a value the report does not use) |
| 4 "BI-RADS and TI-RADS are different; thyroid `tirads` only from a category called TI-RADS; a BI-RADS category on a thyroid report leaves `tirads` null" | E1 |
| 5 "echo, composition, margin, shape, foci describe the nodule, not the surrounding gland" | E4 |
| 6 "pathology only from a stated diagnosis (including 'most likely benign'); suspicious or a category is not pathology; histology only a named type" | E5, E6 (benign lesion read as normal) |
| 7 "halo, calcifications, posterior only if mentioned; a bright area the report says may be something else is not calcifications" | E6 |
| 8 "count only a written number; 'multiple' is null" | E7 (kept from v3) |
| 9 "a described mass or nodule has a lesion: fill every stated key, never all null" | E2 |
| 1, 10 "never infer; copy numbers and units as written" | kept from v3 |
The v4 text (SHA-256 `868a89255a628fa799ab4ec74a1018d1e6e118405d3e2fbdae904d278462d1ce`, checked by an assertion in the code) is:

```
You extract facts from an ultrasound report into JSON. Reply with ONE line of JSON only, containing every key listed below, in this order.
RULES:
1. Fill a key only with a fact that the report itself states. If the report does not state it, the value is null. Never infer, guess or complete.
2. Record every stated fact. If the report states a value for a key anywhere (findings, summary, impression or a category line), fill that key. Leaving out a stated fact is an error, exactly as inventing one is.
3. Copy the report's own words when it gives a range or a combination (a shape such as 'oval to irregular', a margin described with several words). Do not narrow it to one term and do not pick a value the report does not use. Use a listed allowed value only when the report's words match it.
4. BI-RADS and TI-RADS are two different scales. birads (breast) is filled only from a BI-RADS category. tirads (thyroid) is filled only from a category the report itself calls TI-RADS or TIRADS. If a thyroid report gives a BI-RADS category, tirads is null (the thyroid keys have no BI-RADS key).
5. echo, composition, margin, shape, foci / calcifications and posterior features describe the nodule or mass itself. Words about the surrounding gland, parenchyma or background tissue (for example a heterogeneous gland) do not belong to the nodule's echo.
6. pathology is benign, malignant or normal only if the report states a diagnosis in those terms (including 'most likely benign'). Suspicious, concerning, a BI-RADS or TI-RADS category or a recommendation to biopsy is not a stated pathology: null. histology is a named histologic type only if the report names one.
7. Fill halo, calcifications and posterior features only if the report mentions an echogenic halo, calcifications or posterior shadowing / enhancement. A bright area that the report says may be something else is not calcifications.
8. count: only a number or number word that is written (a single / one, two, three). 'multiple', 'several' or a plural without a number is null.
9. A report that describes a mass, nodule or lesion (also as a hypoechoic or hyperechoic area) has a lesion: fill every key the report states about it, even when the report gives no count and no size. Never return all keys null for a report that describes a nodule. Breast lesion_present is false only if the report says there is no lesion. Thyroid count is 0 only if the report says there is no nodule.
10. Copy numbers and units exactly as written (do not convert).

KEYS:
{keys}```

v3 text hash for reference: `f50916b534863500323304fa96794547e6b06a38f02796e859412645548caf1d`. If the templated dev / val check below falls under the Step 32 criterion, the text may be revised using dev / val results only; any revision is a committed addendum to this file **before** the check sheet is produced. After the sheet is produced the text is frozen.

## Validation on templated text (as Step 32)
100 dev and 100 val templated reports per organ (the Step 32 sampler, seed 0); field agreement with the known facts; criterion unchanged: >= 0.98 pooled and per organ on both splits (v3: dev 0.9975, val 0.9986). Reported, not a pass rule for the free-text check.

## Fresh check set
- Pool: the 180 Step 28 writer reports (Qwen2.5-VL-3B, 60 per organ), minus every report already in the Step 32 check (excluded by case id from `step32_extractor_v3/check_sheet_key.json` and by report text from `docs/step32_check.csv`) **and**, stricter than asked, every report in the Step 28 check (`docs/step28_check.csv`, by text). Pool left: **41 breast, 35 thyroid, 42 fetal head**.
- Sample: seeded `random.Random(43)`: reports sorted by case id within organ, shuffled, the first **10 breast, 10 thyroid, 10 fetal head**; the 30 are then shuffled into one sheet (ids D01-D30). v4 is run on these 30 only after this file is committed.
- Sheet `docs/step43_check.csv`: id, organ, report_text, extracted_json, all_fields_right, wrong_fields, note. The grader sees the report text and the extractor's JSON output only, **not the version, not any score, not the labels or the reference**. extracted_json is the model's own JSON (before the unchanged code that maps it onto the schema's flat facts). Grading guide: `docs/step43_grading_guide.md` (what "right" means; one example per organ from dev text only).
- "Fully right" = every extracted field matches what the report says and every key the report does not state is null; a key the report states and the JSON leaves null is wrong.
- **Rubric differences from Step 32 (stated openly):** the thyroid schema has no BI-RADS key. Under the Step 32 rubric (rule 1: BI-RADS written as `tirads` = wrong; rule 2: a stated BI-RADS/TI-RADS category left out = wrong) a thyroid report that states BI-RADS had **no right answer** in this schema, so v3's thyroid 0 of 12 partly reflects that conflict as well as the model. In Step 43 the guide says: on a thyroid report that states BI-RADS, `tirads` must be null (BI-RADS is another scale) and the absence of a BI-RADS key is not counted as a missing fact. A stated TI-RADS category on a thyroid report must be in `tirads`. 'multiple' without a number leaves `count` null (not an error). The Step 32 and Step 43 numbers are therefore not strictly comparable.

## Pass rule (fixed)
v4 passes only if at least **17 of the 20 breast + thyroid reports are fully right**. Fetal head (10 reports) is reported separately and does not count towards the rule. **If v4 passes**, Step 28 (natural errors) is re-run with v4 as pre-registered in Step 28 (same selection, same scores, only `llm_finding_f1` and the accuracy measure change), with the Step 32 hand-check caveat unchanged. **If not**, Step 28 stays inconclusive and v3 / v4 labels stay unvalidated on free text. No other rule or threshold is introduced after the sheet is graded.

## Caveats
- **One grader, not blinded to the project** (knows the project and what the extractor is for); not a clinician; AI use by the grader cannot be verified. Rubric differences above.
- 30 reports (20 for the rule): a pass of 17 of 20 has a wide 95% interval (Wilson about 0.64-0.95 for 17/20 = 0.85); a pass is evidence, not proof.
- The same Qwen2.5-VL-3B reports and the same writer prompt as Steps 28 / 32; reports are the writer's, not a clinician's; thyroid reports often state BI-RADS (a breast scale), which is a writer failure (LIMITATIONS 36).
- v4 changes were designed after reading v3's 17 wrong rows, so they target the known error types; a new error type could appear and the fresh set can show it. The few-shot examples are unchanged (dev-only templated text).
- The unchanged mapping `to_flat` can turn a thyroid JSON with no nodule-related key into `lesion: absent`; the check grades the JSON, the mapping is not changed.

Outputs: `validation.json` (templated check), `check_sheet_key.json`, the graded sheet result (`results.md`, `results.json`, `run_info.json` after grading), `cache.jsonl` (the v4 model replies; separate from the Step 27 and Step 32 caches).
