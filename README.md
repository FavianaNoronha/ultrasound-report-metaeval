# Do Report Scorers Catch Clinical Errors? A Meta-Evaluation of Metrics for AI-Generated Ultrasound Reports

AI models now write ultrasound reports, and the scores used to grade those reports mostly count matching words. This project tests the
scorers themselves, not the report writers. On breast, thyroid and fetal-head ultrasound (10 public datasets) we build a reference report
from dataset labels and masks, then make candidates with **one planted clinical error** (wrong BI-RADS, wrong side, wrong size, an invented
or missed finding, each with a provisional severity), **harmless rewordings** of the same report, and identical copies. A good scorer ranks
the error below the harmless rewording. We test four layers of scorer: word overlap and embeddings (BLEU, ROUGE-L, chrF, BERTScore,
RaTEScore), a structured fact check, an AI judge, and an image check against masks. Steps 2-38 are done (see `ROADMAP.md`): the
benchmark and locked test (2-10), real writers and real text (11-17), robustness tests (18-22), a wrap-up block (24-30: box reliability,
error-type coverage, an LLM fact extractor, a natural-error test on real model reports, a label-free segmentation check, a severity
breakdown) and a later block (31-38: a cross-dataset segmenter, a stricter extractor, pre-registered fact-vs-wording and adversarial tests,
metamorphic and limit-of-detection checks, RadGraph-F1, and responsible-AI checks on the image check).

We found no ultrasound work that tests the scorers with planted errors, severity and harmless rewordings (search not exhaustive).

## Headline findings (details and numbers: `usmeta/RESULTS_SUMMARY.md`)

- **Word-overlap and embedding scorers do not track planted clinical errors.** They react to how much text changed, not to whether a fact changed, and no threshold catches errors without flagging harmless rewordings. Even at matched edit size (Step 21e) they mostly prefer the error, and their score drop follows our provisional severity only weakly (Step 30). In a pre-registered 2x2 factorial (Step 33) their score is driven by wording, not by the error (wording share 0.17-0.60 against fact share 0.02-0.04), none reaches AUROC 0.80 even for a size error of x2 (Step 35), and RadGraph-F1 behaves the same way (Step 37).
- **An AI judge (Gemma-2-9B) separates errors from small rewordings** but is weak against larger harmless rewordings on breast and DDTI, depends on the prompt (18-26% of pairs move by more than 0.1), and its penalty score is floored at 0 on long free-text reports. In the same factorial the judge is fact-driven (0.68 against 0.01), and a simple wording attack does not raise its score on average (Step 36: pre-registered hypothesis not supported). GREEN could not be run on a 16 GB machine (Step 37).
- **A structured fact check is an upper bound on templated text** (`finding_f1` 1.00). An LLM extractor (Qwen2.5-7B, Step 27) gets 0.99-1.00 on the templated benchmark and is stable under prompt rewording, but is only 56% right on breast and thyroid free text in a 30-report hand check.
- **The image check only works if the lesion is found.** With the true box it gives position AUROC 0.97; with label-free boxes it collapses to chance (0.39-0.54, Step 21a); it survives imprecise boxes as long as the box centre stays on the lesion (Step 24); a label-free U-Net restores it (0.89 pooled, breast 0.94, thyroid 0.80, Step 29). For head circumference the tolerance rule tuned on breast and thyroid cannot see errors; oracle-geometry numbers are circular. Leave-one-dataset-out on breast gives 0.95 on unseen datasets (Step 31); abstaining on low confidence removes most mask failures and mild corruptions cost at most 0.05 AUROC (Step 38).
- **Natural errors from a real writer (Step 28) are inconclusive.** No scorer clearly separated reports with a wrong key fact from correct ones (AUROC 0.18-0.59), but the labels come from an extractor that was only 56% right on breast and thyroid reports, fetal head was not checkable and thyroid had five wrong reports.
- **Limits that apply to everything:** templated references, provisional severity (never clinician-confirmed), no clinician review, possible training exposure of the models, five datasets without patient ids, small judge samples.

## Design

```
dataset labels + masks  ->  true (reference) reports, built from templates
                        ->  edited candidates: planted errors | harmless rewordings | identical copies
                        ->  scorers (Layer 0 text metrics, 1 fact check, 2 AI judge, 3 image check)
                        ->  AUROC per dataset: does the scorer rank "error" below "harmless"?
```

Splits are locked (dev / val / test, grouped by patient, exam or near-duplicate cluster). Choices were made on dev/val; final numbers are
from the test split. Frozen versions are listed in `usmeta/FROZEN.md` (tag `freeze-v1`).

## Where to start

- **`usmeta/RESULTS_SUMMARY.md`**: plain-language findings that hold, findings that do not, what is unverified, and the limits. Read this first.
- **`ROADMAP.md`**: what is done (Steps 2-30), what was not run on purpose, what is open, which files are stale, and which files in git history may not be redistributable.
- **`usmeta/results/partA/INDEX.md`**: every step with its results folder (`results.md`, `run_info.json`, data); reruns are kept.
- **`usmeta/docs/LIMITATIONS.md`**: read before quoting any number (templated references, provisional severity, no clinician, possible training exposure).
- `usmeta/results_layers_all_final.md`: the combined test-split table by layer and dataset, with n and confidence intervals.
- `usmeta/CHANGELOG.md`: retractions and fixes. `LICENSE-NOTES.md`: what the licence covers and what it does not.

## Reproduce

Python 3.9+ on a Mac or Linux box; the heavy steps (local judge, report writers, MedSAM) were run on a 16 GB Apple-silicon Mac.

```bash
pip install -r requirements.txt          # core: tables, tests, Layer 0/1 scoring
cd usmeta
PYTHONPATH=. python3 -m pytest -q tests  # full suite (needs no dataset and no GPU; local-data tests skip if the data is absent)
```

To rebuild from the data, put the datasets under `~/Downloads` (or set `USMETA_DATA`) using the folder names in `datasets/manifest.json`, then:

```bash
cd usmeta
python3 -m usmeta.unified build          # label records -> usmeta/local_data/ (git-ignored)
python3 -m usmeta.partb select           # Part B, then: predict, analyse  (needs torch + transformers; MedSAM weights download to the HF cache)
python3 -m usmeta.final_table results_layers_all_final.md   # combined table from saved result files
```

Each results folder holds a `run_info.json` with the command, versions and splits used. The Layer 2 judge and the VLM report writers need
`torch`/`transformers` or `mlx-lm`/`mlx-vlm` and downloaded model weights (see `usmeta/docs/third_party.md`).

## Data

**No datasets are included in this repository.** BrEaST, BUS-BRA, BUSI, UDIAT, BUS-UCLM, TN3K, TN5000, DDTI, HC18, the fetal-head plane
dataset and HiSBreast come from their original sources and **keep their own licences** (all still marked "to confirm"; do not redistribute
images). `datasets/manifest.json` lists expected folders, file counts, sizes and tree hashes so you can check your copy. Two small
label files derived from datasets (`baseline_exp/breast.xlsx`, `baseline_exp/tn3k_records.json`) are in the repo, and benchmark / report files built from dataset labels are in git history; see `LICENSE-NOTES.md` and `ROADMAP.md` (not redistributable until licences are confirmed).
Never tracked: `usmeta/local_data/`, model weights, tokens, and any HiSBreast text, translation or exam id (a test guards this).

## Repository layout

| path | what |
|---|---|
| `usmeta/` | the study: code (`usmeta/usmeta/`), tests, benchmarks, results, docs |
| `datasets/` | manifest and manifest builder (no data) |
| `baseline_exp/` | two label files read by `usmeta/usmeta/unified.py` |
| `archive/legacy_scaffold/` | the earlier chest X-ray agent scaffold, kept for history; nothing imports it |
