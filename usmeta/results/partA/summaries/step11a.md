# Step 11a: HiSBreast loader and Vietnamese -> English translation (STOPPED here for your hand-check)

Limitations: [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md). **This folder holds only aggregate numbers.** HiSBreast has a blank licence and no de-identification statement, so the Vietnamese text, the English translations, the check table and the exam table stay LOCAL in `usmeta/local_data/hisbreast/` (git-ignored; the GitHub repo is public). Exam ids are salted SHA-256 hashes.

**Loader (`usmeta/hisbreast.py`).** The zip is read in place. Its JSON holds 3,052 records of many exam types (abdomen 1,363, breast 960, thyroid 337, endoscopy, cardiac Doppler, ...); only `Siêu âm tuyến vú hai bên` (bilateral breast ultrasound) is kept: **960 records = 427 exams** (289 exams have more than one image; no empty text; no exam has two different conclusions). The earlier unified-loader table included all exam types and is not used. Conclusions: median 13 words, maximum 35. **310 unique conclusion texts** (many exams share the same sentence). The brief's "972 images" matches the 960 breast records plus a few more in the images folder; the images are not used in these steps (no image was opened, so the burned-in-name check is still open and only needed for Step 5).

**Translation (`usmeta/hisbreast_translate.py`).** Gemma-2-9B-it 4-bit (MLX, greedy), one call per unique text after cleaning (HTML entities and bullet dashes removed, parts joined with " | "), with a glossary of Vietnamese breast-ultrasound terms in the prompt (the glossary is my own Vietnamese knowledge: please check it). First attempt discarded: it kept only the first line of multi-line text and turned "NANG" (cyst) into "mass". Remaining known weakness seen in the first rows: "HÓA MỦ HOÀN TOÀN" (completely suppurated) was once rendered "completely drained". 310 texts translated, 0 empty.

**Automatic flags on the 310 translations** (rule checks, not a quality score): BI-RADS category differs between source and translation 19 (6%); number of " | " parts differs 59; left/right word differs 1; 61 of 310 (20%) carry at least one flag. Of the 40 random items chosen for your check, 6 carry a flag. Flags are a floor: a translation can change meaning without any flag.

**What I need from you before continuing (hand-check):**
1. **40 random translations** (`local_data/hisbreast/translation_check.md`, side-by-side table; mark OK / changes meaning / minor wording). Stop rule: more than 4 of 40 meaning-changing.
2. **The 20 flagged translations that have a BI-RADS or side difference** are the most important to look at (listed in `translations_flagged.json`, same folder); BI-RADS errors would corrupt the planted-error severity.
3. **Paraphrases: 100**, as in the brief (generated after the translations are accepted; none exist yet, so there is nothing to check today).

**Splits.** New file `local_data/hisbreast/hisbreast_splits.jsonl`, by hashed exam id (dev 164 / val 83 / test 180 exams). The frozen `splits.jsonl` is untouched. Note: 46 conclusion texts occur in more than one exam, so identical wording can sit in dev and test; if you prefer, group by unique text instead (changes the split sizes slightly).

Not done yet (waiting for your answer): rule-based field parser, planted mistakes on real text, scorer comparison templated vs real, lazy-report test.
