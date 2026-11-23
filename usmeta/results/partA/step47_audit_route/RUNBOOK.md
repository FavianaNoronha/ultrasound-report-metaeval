# Step 47 runbook

Run these commands from the repository root. They use the saved Step 46 Set B dev/val data for calibration. The Set C test plan is blocked until its thresholds are frozen and hash-checked.

## Development calibration

```sh
PYTHONPATH=usmeta .venv/bin/python -m usmeta.step47_audit_route calls --set devval --max-hours 1
```

Resume that command until it prints `calls complete`. Calls are saved as they finish. Then freeze the audit-route budget and equal-budget comparator cutoffs:

```sh
PYTHONPATH=usmeta .venv/bin/python -m usmeta.step47_audit_route freeze-devval
```

This may take a while because it computes BLEU, ROUGE-L, chrF, BERTScore, RaTEScore, and the frozen Step 45 learned score on Set B dev/val. It writes `devval_scores.json`, comparator caches, and the hashed `thresholds.json`.

## Fresh Set C

Keep the Mac on power for the model download and long generation / judge run. Download the pinned Mistral model before planning; planning records the resolved revision and SHA-256 for every weight file.

```sh
PYTHONPATH=usmeta .venv/bin/python -c 'from huggingface_hub import snapshot_download; snapshot_download("mlx-community/Mistral-7B-Instruct-v0.3-4bit")'
PYTHONPATH=usmeta .venv/bin/python -m usmeta.step47_freetext plan
PYTHONPATH=usmeta .venv/bin/python -m usmeta.step47_freetext generate --max-hours 2
```

Resume `generate` until it completes the core reports. Then build the gold-filtered set and LOD plan, generate the LOD reports, rebuild the final set, and extract facts:

```sh
PYTHONPATH=usmeta .venv/bin/python -m usmeta.step47_freetext gold
PYTHONPATH=usmeta .venv/bin/python -m usmeta.step47_freetext generate --only lod --max-hours 1
PYTHONPATH=usmeta .venv/bin/python -m usmeta.step47_freetext gold
PYTHONPATH=usmeta .venv/bin/python -m usmeta.step47_freetext extract
```

The script refuses to run `gold` before core generation is complete and refuses extraction until both core and LOD generation are complete.

## Judge, baselines, and report

Extract and audit the 30 descriptive Set R reports, then audit Set C. Resume either `calls` command until it prints `calls complete`.

```sh
PYTHONPATH=usmeta .venv/bin/python -m usmeta.step47_audit_route extract-setr
PYTHONPATH=usmeta .venv/bin/python -m usmeta.step47_audit_route calls --set setr --max-hours 1
PYTHONPATH=usmeta .venv/bin/python -m usmeta.step47_audit_route calls --set test --max-hours 1
PYTHONPATH=usmeta .venv/bin/python -m usmeta.step47_audit_route score-test
```

`score-test` checks that all required extractions and judge calls exist, applies the frozen thresholds, and writes `scored_test.json`, `metrics.json`, `scored_setr.json`, and cached comparator scores. Set R labels only measure one reviewer's judgment that extractor v4 copied facts from the report text; they do not measure image correctness.
