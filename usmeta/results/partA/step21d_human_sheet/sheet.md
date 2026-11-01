# Human-rewording sheet (Step 21d)

**Instructions.** For each row below, write ONE rewording of `reference_text` **by hand, in your own words**, in the `human_rewording` column of `sheet.csv`.
- Keep **every fact**: side, category / BI-RADS / TI-RADS level, size and units, position, number of lesions, finding present/absent, plane, head circumference.
- Do **not** copy the template phrasing (change sentence structure and wording, not only a word or two).
- Do **not** use an AI tool, translator or paraphraser.
- You may change the order of sentences, the units (mm <-> cm) and the style, but not the meaning. Do not add new findings or advice.
- If you cannot reword a row without changing a fact, leave it blank and write the reason in `note`.
- The script checks your facts with a rule extractor that was written for the template wording, so a freely worded sentence may be flagged even when every fact is kept. If you have checked by hand that nothing changed, write `OK` in `note` for that row; flagged rows without `OK` are left out of the scoring.
When the CSV is filled, run `python3 -m usmeta.step21_human_score` (it flags any rewording where a fact changed, then scores).

The 30 references come from the locked TEST split (10 breast, 10 thyroid, 10 fetal head; one per patient/exam group). They are templated, fact-correct reports built from dataset labels, not clinician text.

| id | organ | reference_text | human_rewording |
|---|---|---|---|
| H01 | breast | An irregular mass (wider than tall) with not circumscribed (spiculated, angular, indistinct) margins and hypoechoic echo pattern is seen in the upper central part of the image, measuring approximately 24 mm. Combined posterior features and no calcifications and an echogenic halo. Assessment: BI-RADS 5. Pathology: malignant. | |
| H02 | breast | An oval mass (wider than tall) with not circumscribed (indistinct) margins and hypoechoic echo pattern is seen in the upper central part of the image, measuring approximately 18 mm. No posterior acoustic features and calcifications (in a mass) and no echogenic halo. Assessment: BI-RADS 4b. Pathology: malignant. | |
| H03 | breast | A mass (taller than wide) is seen in the left breast, upper central part of the image, measuring about 22% of the image width. Assessment: BI-RADS 2. Pathology: benign. Histology: cyst. | |
| H04 | breast | A mass (wider than tall) is seen in the upper central part of the image, measuring about 37% of the image width. Assessment: BI-RADS 3. Pathology: benign. Histology: fibroadenoma. | |
| H05 | breast | A mass (taller than wide) is seen in the middle central part of the image, measuring about 31% of the image width. Pathology: malignant. | |
| H06 | breast | A mass (wider than tall) is seen in the upper central part of the image, measuring about 10% of the image width. Pathology: benign. | |
| H07 | breast | A mass (wider than tall) is seen in the middle right part of the image, measuring about 23% of the image width. Pathology: malignant. Histology: idc. | |
| H08 | breast | A mass (wider than tall) is seen in the middle right part of the image, measuring about 47% of the image width. Pathology: benign. Histology: fa. | |
| H09 | breast | A mass (wider than tall) is seen in the middle left part of the image, measuring about 36% of the image width. 2 lesions are identified. Pathology: benign. | |
| H10 | breast | A mass (wider than tall) is seen in the upper central part of the image, measuring about 11% of the image width. Pathology: benign. | |
| H11 | thyroid | Two nodules is seen in the middle central part of the image, measuring about 23% of the image width. Wider than tall. | |
| H12 | thyroid | A single nodule is seen in the middle central part of the image, measuring about 54% of the image width. Wider than tall. | |
| H13 | thyroid | A single nodule is seen in the middle central part of the image, measuring about 40% of the image width. Wider than tall. | |
| H14 | thyroid | A single nodule is seen in the middle central part of the image, measuring about 33% of the image width. Wider than tall. | |
| H15 | thyroid | A single nodule is seen in the middle central part of the image, measuring about 21% of the image width. Wider than tall. | |
| H16 | thyroid | A single nodule is seen in the middle central part of the image, measuring about 10% of the image width. Taller than wide. | |
| H17 | thyroid | A single nodule is seen in the middle central part of the image, measuring about 36% of the image width. Well defined smooth margins, wider than tall, no echogenic foci. Assessment: TI-RADS 3. | |
| H18 | thyroid | A single nodule is seen in the middle central part of the image, measuring about 20% of the image width. Dense composition, hypoechoic echotexture, well defined margins, wider than tall, no echogenic foci. Assessment: TI-RADS 4c. | |
| H19 | thyroid | A single nodule is seen in the upper central part of the image, measuring about 29% of the image width. Well defined smooth margins, wider than tall, echogenic foci (microcalcifications). Assessment: TI-RADS 4b. | |
| H20 | thyroid | A single nodule is seen in the middle central part of the image, measuring about 36% of the image width. Well defined smooth margins, wider than tall, no echogenic foci. Assessment: TI-RADS 2. | |
| H21 | fetal head | Fetal head. Head circumference 168.9 mm. | |
| H22 | fetal head | Fetal head. Head circumference 308.5 mm. | |
| H23 | fetal head | Fetal head. Head circumference 279.2 mm. | |
| H24 | fetal head | Fetal head. Head circumference 312.5 mm. | |
| H25 | fetal head | Fetal head. Head circumference 173.8 mm. | |
| H26 | fetal head | Fetal head, trans thalamic plane. Head circumference approximately 283 mm. | |
| H27 | fetal head | Fetal head, trans ventricular plane. Head circumference approximately 180 mm. | |
| H28 | fetal head | Fetal head, trans thalamic plane. Head circumference approximately 347 mm. | |
| H29 | fetal head | Fetal head, trans cerebellum plane. Head circumference approximately 173 mm. | |
| H30 | fetal head | Fetal head, trans ventricular plane. Head circumference approximately 161 mm. | |
