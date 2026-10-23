# Task: Step 10 - freeze, dedupe, held-out test split, honesty labels

Run this BEFORE Step 8b (borrowed ideas) and before any new tuning. Read CLAUDE.md, usmeta/TASK_layers_v3.md and
usmeta/results/partA/INDEX.md first. Same rules: no "first ultrasound benchmark" claims, don't overwrite old
results, save every step to usmeta/results/partA/step10_<name>/ (data, results.md, run_info.json, run.log),
update INDEX.md and summaries/, commit after each sub-step, push if a remote exists.

## Why
Our Layer 1 and Layer 3 results are circular on templated text (extractor/checker use the same facts that built
the reference). Prompts and the synonym fix were chosen after looking at the same cases they are scored on.
There has been no duplicate/leak check and no held-out split. This step fixes what can be fixed and labels the
rest honestly.

## 10a: duplicate and leakage check (do first)
- Within each dataset and across all datasets: perceptual hash every image (dHash or pHash via PIL/numpy; avoid
  heavy new dependencies) and list near-duplicate pairs (Hamming distance <= 4 of 64 bits; also report <= 8 as
  "possible"). Also compare by filename/patient/exam ids where they exist.
- Specifically check: HC18 vs "Diverse Fetal Head Images" (if present) and vs fetal head planes; BUSI vs BUS-BRA vs
  BUS-UCLM vs UDIAT vs BrEaST; TN3K vs TN5000 vs DDTI.
- Output dedupe_report.md (counts per dataset pair, examples as file names only) and duplicates.jsonl.
- Policy: exact/near duplicates across datasets: keep one copy (prefer the dataset with the richest labels), drop
  the others from the benchmark, and record every drop in dropped_cases.jsonl with the reason. Never drop silently.
- Same patient/exam in more than one case: group them (see 10b).
STOP AND ASK if more than 5% of any dataset is duplicated or if dedupe would remove a whole dataset.

## 10b: grouped, locked splits
- Group id per case: patient id / exam id if the dataset has one (BUS-UCLM filename prefix, fetal plane filename
  id, HC18 subject if derivable, DDTI case id, BrEaST case id); otherwise use the image id and say so in
  results.md ("group = image, patient overlap possible").
- Three splits at GROUP level, stratified by organ/dataset and class where possible, fixed seed:
  dev 40% (for prompts, templates, thresholds, extractor fixes), val 20% (for threshold selection and calibration),
  test 40% (LOCKED: used once for final numbers).
- Write splits.jsonl (case id, group id, split) and splits_manifest.json with SHA-256 of splits.jsonl,
  bench_v2d.jsonl and true_reports_v2d.jsonl, plus the git commit hash.
- Test-split guard: add a helper `usmeta.splits.load(split)` that logs every access to `test` into
  results/partA/test_access.log (date, script, git hash). All analysis scripts must use the helper.
- Tag the commit `freeze-v1`.

## 10c: freeze
- Freeze templates, schema, extractor, scorers' settings, judge prompts (both existing Gemma prompts, labelled
  "prompt_v1" and "prompt_v2 (stricter)"), thresholds rule. Write FROZEN.md listing each with file hash.
- From now on, any change after freeze must be a new version (v2 etc.) with a note in CHANGELOG.md saying what
  changed and why, and the old version's results are kept.
- Rule: tuning of any kind uses dev and val only.

## 10d: re-run the headline results on the locked test split
- Layer 0 scorers (matched-synonym group, harmless_small, harmless_large), finding_f1, Gemma sentence_check
  with both prompts, Layer 3 true-mask checks. Judge on up to 50 cases per dataset on test (say the number; 20
  is too few). If runtime is too long, say so and use the largest subsample that fits.
- Thresholds (for D/R or flag rates) are picked on val and applied to test.
- Report per dataset, bootstrapped 95% CI (resample at group level). Same columns as Step 5/9, plus a column
  "split = test".
- Keep the old dev-based numbers in a separate table labelled "dev, tuned".
- Save as step10_test_results/. Add a short diff: which conclusions changed vs the dev numbers.

## 10e: honesty labels (write into results docs, README and CLAUDE.md)
Create docs/LIMITATIONS.md and make every results.md link to it. It must state:
1. Reference reports are templated from labels/masks (synthetic but fact-correct); real clinician text only
   for HiSBreast (once built).
2. Layer 1 (finding_f1) and Layer 3 (mask_verified_facts, grounded_check on true masks) are "upper bounds under
   templated text" because the extractor/checker uses the facts that built the reference. They are not evidence
   that these scorers work on real reports.
3. Judge prompts were selected on dev data; judge is prompt-sensitive (cite the AUROC changes). Final numbers
   come from the locked test split.
4. All reruns are listed (Step 4 headline retracted: edit-size artifact; Step 5 reruns 2 and 3; Step 7 rerun 2).
5. Qwen, MedGemma and LLaVA-Med outputs: "possible exposure to the public datasets during training;
   unverifiable". UltraG text: GPT-5.5-written from masks, not radiologist text.
6. Severity labels are provisional (guideline-based) pending clinician ranking.
7. Template sources marked "to confirm" are not yet verified.
8. A judge never grades reports from its own model family.
9. No decontamination of external pretrained scorers is possible; we only control our own data and splits.

## 10f: contamination notes for model outputs
- For each report-writing model run (Qwen now; MedGemma, LLaVA-Med later) save contamination_notes.md: model
  card statements about training data (quote with source link, "to confirm" if not verified), which of our
  datasets are public, and a memorisation probe: for 20 images per dataset, ask the model for the dataset's
  label or filename-style metadata without the image context; log any exact matches. Report as a probe, not as
  proof either way.

## Final
- Update INDEX.md with a step10 row per sub-step and a line "From here on, final numbers = locked test split".
- Short status with folder paths, counts dropped by dedupe, split sizes, and the 3 biggest changes vs dev.

## Stop and ask me if
- duplicates are > 5% of any dataset, or dedupe would remove a dataset
- group ids are missing for a whole dataset (tell me which, and the leak risk)
- any scorer's identical-copy mean is not 1.0 on the test split
- a step needs a gated model, paid API, or download over 5 GB
- a run will take longer than ~3 hours
