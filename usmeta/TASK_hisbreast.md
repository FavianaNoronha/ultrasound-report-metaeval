# Task: Use HiSBreast as a REAL-report test set (clinician-written text)

Read CLAUDE.md first. Same rules: no "first ultrasound benchmark" claims, don't overwrite existing results or
bench files (write new ones), commit after each step, short status after each step.

## What HiSBreast is (checked)
- Mendeley Data, DOI 10.17632/5c723rpwz2.1 (v1, Feb 2024), collected at Ca Mau province general hospital, Vietnam.
  Contributor Huong Hoang Luong (Can Tho University / FPT University). Licence field is BLANK; no de-identification
  statement (JSON has patient codes). Everything is in Vietnamese.
- File: ~/Downloads/HiSBreast.zip. Folders: json/ (16 files, 2018-2022), images/ (972 png), descriptions/ (972 txt),
  diagnoses/ (972 txt). Each JSON record has: SO_PHIEU_CDHA (exam id), MO_TA (the radiologist's conclusion),
  TEN_CDHA (exam name, e.g. "Siêu âm tuyến vú hai bên" = bilateral breast ultrasound), CHANDOANBENH (clinical
  diagnosis with ICD code), CHANDOAN, HINHANH (base64 image).
- Measured on our side: 972 descriptions, median 14 words (max 36) -> SHORT CONCLUSIONS, not full reports.
  366 say "no abnormality recorded"; 675 mention right, 687 left; 257 mention axillary node (HẠCH NÁCH).
  455 mention BI-RADS: 2:38, 3:92, 4:57, 4A:11, 4C:1, 5:116, 6:184 (6 = already biopsy-proven cancer).
- Images from the same exam share the same text (e.g. _0 and _1 are identical). 

## Caveats that must go in every results file
1. Single hospital, Vietnamese, English translation is OURS (extra error source).
2. Short conclusion lines, not full radiology reports. Say "clinician-written conclusions".
3. CHANDOANBENH is a clinical/ICD diagnosis (often from referral/history), NOT pathology. Never treat it as
   ground-truth malignancy. Many cases are already-known cancers (BI-RADS 6), text may depend on history
   that the image cannot show.
4. No masks -> no IoU/Dice here. This set is for the TEXT side only.
5. Licence blank and no de-identification statement: do NOT redistribute images or text; keep data local, only
   release code + aggregate numbers + our derived planted-error benchmark with no patient codes/images. Look at
   10 images for burned-in names/ids and tell me what you see before using any image.
6. Split by exam id (SO_PHIEU_CDHA), never by image, so shared text can't leak.

## Step 1 — loader (usmeta/usmeta/hisbreast.py)
- Read the zip in place (don't unzip into the repo). Return per exam: id, date file, exam name, Vietnamese
  conclusion (strip <br />), clinical diagnosis, list of image names. Dedupe images by exam.
- Print: exams vs images, conclusion length histogram, how many exams have >1 image, any empty text.
- Keep patient codes out of every output file (hash the exam id).

## Step 2 — translation + structured fields
- Translate conclusions to English with the local model (Gemma-2-9B MLX; MedGemma is gated, don't use).
  Prompt: translate faithfully, keep BI-RADS terms, side words, numbers; do not add anything. Save both languages.
- Check 40 random translations by eye (I will read them): output a side-by-side table in docs/hisbreast_translation_check.md.
- Rule-based parser into fields: side (right / left / both / unspecified), BI-RADS (incl. 4A/4B/4C), finding type
  (mass / multiple masses / cyst / inflammation / abscess / post-surgical / no abnormality), axillary node mentioned
  (yes/no), recommendation (FNA / follow-up / biopsy), "suspicious for cancer" wording. Manually check 50.
- Report parser agreement with those 50 and with the BI-RADS regex count above.

## Step 3 — planted mistakes on REAL text (bench_his.jsonl)
- True report = the clinician's English conclusion (real wording, real variation).
- Planted mistakes, each tagged with an error category (same categories as TASK_groundtruth.md):
  BI-RADS category change (use severity from guideline thresholds: crossing 3->4A is the biopsy line),
  side swap (right <-> left), negation flip ("no abnormality" <-> "mass"), missed axillary node,
  invented axillary node, benign <-> suspicious wording, recommendation removed/changed.
- Harmless rewordings: synonym paraphrase, reordered clauses, bullet <-> sentence form. LLM paraphrases can
  change meaning, so a person checks 100 of them (I will); log which ones changed meaning and drop those.
- Identical copies must score 1.0 on every scorer.
- ~100 exams for the small file, all exams for the full file.

## Step 4 — run the scorers, then the key comparison
- Run bleu, rougeL, chrf, bertscore, ratescore, finding_f1 (TASK_layers.md Layer 1) and the Gemma judge on
  bench_his.jsonl -> results_his.md/json (AUROC, critical AUROC, harmless mean, identical mean, severity Spearman).
- KEY QUESTION: do the scorer rankings and failure patterns we saw on templated reports (bench_v1 / bench_v2)
  also show up on real clinician text? Table: scorer x (templated breast, real HiSBreast). If they match, our
  templated results are more believable; if not, say where and why. Report honestly either way.
- Also test the "no-image lazy report" idea: score the most common conclusion ("no abnormality") as a
  candidate against every true report -> how high does it score?

## Step 5 — optional, only if Steps 1-4 are done
- Qwen2.5-VL on 50 HiSBreast images, asked for a short English conclusion; compare with the clinician's:
  side agreement, BI-RADS agreement, no-abnormality agreement. Remember caveat 3: images alone often can't
  reproduce history-dependent conclusions, so report this as exploratory.
- Mark as "public dataset, possibly seen in training".

## Step 6 — README + CLAUDE.md update, commit.

## Stop and ask me if
- images show patient names/ids or other identifying marks,
- translation spot-check finds >10% of the 40 meaning-changing,
- parser agrees with manual check on <85% of fields,
- anything needs a download or a gated model.
