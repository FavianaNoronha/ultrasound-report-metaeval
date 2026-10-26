# Step 11b: free-text extractor v2 (fixes for the decimal bug and copied option lists)

Limitations: [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md). **Still a proxy:** agreement with independent regex readings of the same report, not with hand labels.

**What changed (`usmeta/schema_v2.py`, post-processing only; `schema.py` v1 untouched; prompt unchanged so cached model replies were reused).** (1) A number is re-read from the model's own quote when the quote holds a number with a unit; this fixes "10.6 mm" being returned as 106. (2) A value that is an option list ("solid|cystic") is dropped and counted. (3) JSON booleans for lesion map to present / absent. Unit tests (`tests/test_schema_v2.py`, 5 tests): decimal dropped by the model corrected from the quote, cm to mm, head circumference 25.88 cm to 258.8 mm, option list dropped and counted, boolean lesion and missing quote. CHANGELOG.md has the "extractor v2" entry.

**The 8 hand-checked reports** (the 8 I read in Step 11): the two bad ones are fixed (BUS-BRA bus_0486: size 106 -> 11 mm; TN5000 003205 and TN3K 0532: "solid|cystic" and "solid|cystic|mixed" -> field left unstated); the other 6 are unchanged.

**Proxy agreement on dev/val reports (fields where an independent regex gives a value and the schema has the field):**
| set | extractor | agree / comparisons | side | BI-RADS | size | lesion present/absent | option-list values left |
|---|---|---|---|---|---|---|---|
| first 40 reports (10 per dataset) | v1 | 37 / 41 = 90.2% | 10/10 | 9/9 | 8/9 | 10/13 | 5 |
| same 40 reports | v2 | 38 / 41 = 92.7% | 10/10 | 9/9 | 9/9 | 10/13 | 0 (5 dropped, 1 number corrected) |
| **40 NEW dev/val reports** (10 per dataset, not seen before) | v2 | **46 / 47 = 97.9%** | 10/10 | 10/10 | 11/11 | 15/16 | 0 (3 dropped, 2 numbers corrected) |
Pooled v2 over 80 reports: 84 / 88 = 95.5%.

**Reading, and what it does not show.** Side, BI-RADS and size agree 30/30, 29/29 and 20/20 on v2 (new + old sets); the remaining disagreements are all in lesion presence (25 / 29), where the regex itself is a rough heuristic ("no abnormal", "normal appearance") and I did not hand-verify which side is right. Comparisons per field are 9-16, so the intervals are wide; the new 40 were the first 40 reports sampled after the fixes, and v1's old set was reused for the before/after, so the improvement from 90.2% to 97.9% mixes two samples (on the same 40 reports the gain is 37 to 38). Position phrases (e.g. "upper outer quadrant") are still kept as written and cannot match the template's image-thirds vocabulary; dropping a copied option list loses information that a human might read as "mixed". This is a proxy: it checks that the extractor reads numbers, sides and BI-RADS the way a regex does, not that every attribute is right.
