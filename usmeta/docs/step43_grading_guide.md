# Grading guide for `docs/step43_check.csv` (30 reports)

**Your task.** For each row, decide whether `extracted_json` faithfully records what `report_text` **says**. You are not judging whether the report is medically correct or matches any scan: only whether the JSON copies the report's own facts into the listed keys.

**Rules for you:** read the reports yourself; use no AI tools; do not look at any scan image; do not discuss the answers with anyone; do not look up how the rows were produced. Grade each row on its own. Rows are in random order.

**Columns to fill**
- `all_fields_right`: type `yes` or `no` (lowercase, no blanks).
- `wrong_fields`: if `no`, the key names that are wrong, separated by commas (for example `shape, birads`); leave empty if `yes`.
- `note`: optional, a short reason in your own words.

## What "right" means
A row is `yes` only if **every key** in `extracted_json` is correct:
1. **A value is filled** only if the report states it. A value the report does not state (a guess, a typical finding, something inferred from another fact) makes the row `no`.
2. **A key is null** only if the report does not state it. If the report states a fact that fits a key (anywhere: findings, summary, impression, a category line) and the JSON leaves that key null, the row is `no`.
3. **The value says what the report says**, not something narrower or different: a stated range or combination of terms must not be reduced to one of them; a different echo, shape, margin, side or pathology word is wrong. Allowed-value lists in the prompt are guidance: if the report uses other words, copying its own words is fine.
4. **Numbers and units are copied as written.** `{"value": 2.5, "unit": "cm"}` is right for "2.5 cm"; no conversion is expected. A wrong number is wrong.
5. **Describes the nodule or mass itself.** Words about the surrounding gland or tissue (for example the gland being heterogeneous) are not the nodule's echo, margin or composition.
6. **Category lines.** `birads` (breast) is the category after "BI-RADS". `tirads` (thyroid) is the category after "TI-RADS" or "TIRADS" only. **The thyroid keys have no BI-RADS key.** On a thyroid report that states a BI-RADS category: `tirads` must be null (BI-RADS is a different scale), and the missing BI-RADS key is **not** counted as a missing fact. A thyroid report that states TI-RADS must have it in `tirads`.
7. **Pathology** is benign / malignant / normal only if the report states a diagnosis in those terms (including "most likely benign"). Suspicious wording, a category or a recommendation to biopsy is not a pathology. `histology` is a named histologic type, only if the report names one.
8. **Counts.** `count` is an integer. If the report says "multiple" or "several" with no number, `count` null is right. A written number or number word must be that number.
9. **Presence.** If the report describes a mass, nodule or lesion, the JSON must not be all-null: the facts the report states about it must be there. If the report says there is no lesion / nodule, the JSON should say so (breast `lesion_present` false; thyroid `count` 0).
10. **Empty output.** `{}` or all-null keys are right only if the report states none of the keys' facts (for example a fetal-head report that gives no head circumference and no plane).

If you are unsure, apply the rules as written; do not give the benefit of the doubt in either direction. Mark `no` if any key fails.

## Keys per organ
- **breast:** lesion_present, count, side, position, orientation, size, shape, margin, echo, posterior, halo, calcifications, birads, pathology, histology.
- **thyroid:** count, position, orientation, size, composition, echo, margin, foci, tirads.
- **fetal head:** plane, hc (head circumference with its unit).

## Examples (DEV templated text, not one of the 30 reports; the "wrong" versions are constructed for illustration)
**Breast (right).** Report: "An oval mass (wider than tall) with not circumscribed (indistinct) margins and hypoechoic echo pattern is seen in the middle central part of the image, measuring approximately 9 mm. No posterior acoustic features and no calcifications and no echogenic halo. Assessment: BI-RADS 4b. Pathology: benign."
JSON: `{"lesion_present": true, "count": 1, "side": null, "position": "middle-central", "orientation": "wider than tall", "size": {"value": 9, "unit": "mm"}, "shape": "oval", "margin": "not circumscribed (indistinct)", "echo": "hypoechoic", "posterior": "no", "halo": "no", "calcifications": "no", "birads": "4b", "pathology": "benign", "histology": null}`
Right: every stated fact is recorded, `side` and `histology` are null because the report does not state them. **Wrong versions:** `"birads": "4"` (category narrowed); `"pathology": null` (a stated pathology left out); `"histology": "fibroadenoma"` (not stated); `"echo": "isoechoic"` (changed).

**Thyroid (right).** Report: "Two nodules is seen in the upper left part of the image, measuring about 22% of the image width. Solid composition, isoechoic echotexture, well defined margins, wider than tall, echogenic foci (microcalcifications). Assessment: TI-RADS 4b."
JSON: `{"count": 2, "position": "upper-left", "orientation": "wider than tall", "size": {"value": 22, "unit": "%"}, "composition": "solid", "echo": "isoechoic", "margin": "well defined", "foci": "microcalcifications", "tirads": "4b"}`
Right. **Wrong versions:** `"tirads": null` (a stated TI-RADS category left out); `"composition": "cystic"` (changed); `"echo": null` (a stated echo left out). If the last line of the same report had read "Assessment: BI-RADS 4b", then `"tirads": "4b"` would be wrong and `"tirads": null` right.

**Fetal head (right).** Report: "Fetal head, trans thalamic plane. Head circumference approximately 323 mm."
JSON: `{"plane": "trans thalamic", "hc": {"value": 323, "unit": "mm"}}`
Right. **Wrong versions:** `"plane": "trans cerebellum"` (changed); `"hc": null` (a stated head circumference left out). If a report stated neither plane nor head circumference, `{"plane": null, "hc": null}` would be right.
