# Step 47: next steps on the Mac (after amendment 2 was committed as 1d5f571)

The pre-registration is PREREG.md + PREREG_AMENDMENT.md + PREREG_AMENDMENT_2.md. Do not change a hypothesis, variant or threshold. Do not read Set C or test data before step 6.

Code patched on 2026-11-24 for amendment 2 (`usmeta/usmeta/step47_audit_route.py`, `step47_freetext.py`, `usmeta/tests/test_step47_amendment2.py`): severity leak (`blind(row)`), V5, V6, paper-exact CRQS comparator, second judge (`--judge llama`), Clopper-Pearson H1 and the 400-error eligibility rule, `export-handcheck`, `log_trial`, audit gating consistency in freeze and completeness checks, and the missing `set_a`/`part_e` references. N_TEST_PER_ORGAN raised 120 -> 250.

1. Run the tests: `PYTHONPATH=usmeta .venv/bin/python -m pytest usmeta/tests/test_step47_amendment2.py`. If an import fails, fix only the import. Never change the logic to make a test pass; report failures.
2. Because severity no longer comes from the planted label, a few dev/val rows now need audit calls that were skipped before. Resume: `PYTHONPATH=usmeta .venv/bin/python -m usmeta.step47_audit_route calls --set devval --max-hours 1` until it prints `calls complete`.
3. Write `usmeta/results/partA/step47_audit_route/CODE_SHA256.txt` (SHA-256 of step47_audit_route.py, step47_freetext.py, prompts.json, PREREG*.md). Faviana commits and pushes code, tests, this file and the dev call caches. Wait for her confirmation.
4. Only then `freeze-devval` (writes thresholds.json with the paper-exact CRQS cutoff included). Stage 1 trial and error: log every trial with `log_trial(...)` into trial_log.csv; stop at 20 trials or 3 days; selection metric per amendment 2 item 6; write frozen_variants.json with its SHA-256; commit and push. No Llama trials on Set B; there is no Mistral dev data, so Stage 1 is Gemma-only.
5. Set C: download Mistral-7B-Instruct-v0.3-4bit, then follow RUNBOOK.md (`plan`, `generate`, `gold`, LOD, `extract`). If `plan` reports fewer fresh cases than 250 per organ, stop and tell Faviana; do not lower the number silently. H1 cannot pass below 400 major/critical errors.
6. `export-handcheck` (50 reports). Faviana or Harshal fill it. Then `calls --set test` for gemma, `calls --set test --judge llama`, `calls --set setr`, `score-test`.
7. Write results.md (H1 to H9, V0 to V6, both judges, CRQS-style and paper-exact, number of Stage 1 trials) and commit. Report failures as failures.
