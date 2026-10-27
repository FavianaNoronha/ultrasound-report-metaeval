# Do Report Scorers Catch Clinical Errors? A Meta-Evaluation of Metrics for AI-Generated Ultrasound Reports

AI models now write ultrasound reports, and the scores used to grade those reports mostly count matching words. This project tests the
scorers themselves, not the report writers. On breast, thyroid and fetal-head ultrasound (10 public datasets) we build a reference report
from dataset labels and masks, then make candidates with **one planted clinical error** (wrong BI-RADS, wrong side, wrong size, an invented
or missed finding, each with a provisional severity), **harmless rewordings** of the same report, and identical copies. A good scorer ranks
the error below the harmless rewording. We test four layers of scorer: word overlap and embeddings (BLEU, ROUGE-L, chrF, BERTScore,
RaTEScore), a structured fact check, an AI judge, and an image check against masks.

We found no ultrasound work that tests the scorers with planted errors, severity and harmless rewordings (search not exhaustive).

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
label files derived from datasets (`baseline_exp/breast.xlsx`, `baseline_exp/tn3k_records.json`) are in the repo; see `LICENSE-NOTES.md`.
Never tracked: `usmeta/local_data/`, model weights, tokens, and any HiSBreast text, translation or exam id (a test guards this).

## Repository layout

| path | what |
|---|---|
| `usmeta/` | the study: code (`usmeta/usmeta/`), tests, benchmarks, results, docs |
| `datasets/` | manifest and manifest builder (no data) |
| `baseline_exp/` | two label files read by `usmeta/usmeta/unified.py` |
| `archive/legacy_scaffold/` | the earlier chest X-ray agent scaffold, kept for history; nothing imports it |
