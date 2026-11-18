# Step 42 results: GREEN (4-bit) on a Colab T4

Pre-registration (committed before any GREEN score): [PREREG.md](PREREG.md). Code: `usmeta/step42_green_pairs.py`, `usmeta/step42_analyse.py`, `notebooks/step42_green_colab.ipynb`. Numbers: `results.json`. Every number here is **GREEN (4-bit)**, not the official fp16 GREEN.

## Verdict (all cells are under 30 groups, so by the pre-registered rule they are "too small" and are NOT compared with other scorers)

- **Factorial (as Step 33), pooled breast + thyroid, 120 blocks / 20 groups (too small):** fact share 0.47 (0.39–0.56), wording share 0.002 (0.00–0.01). By the pre-registered decision line GREEN (4-bit) is **fact-driven** in this small sample. It does not reach the judge's fact share (0.68, Step 33), but the judge row used a different, larger sample (239 blocks / 71 groups), so this is descriptive only.
- AUROC error vs no error at small wording (c vs a): 0.99 (0.98–1.00); at large wording (d vs b): 0.86 (0.79–0.93). A large harmless rewrite lowers GREEN only a little (mean (a) 1.00, (b) 0.91).
- Reversal (error with small edit scored above a correct large rewrite): 5% (0–13%) of pairs (judge 4%, word scorers 60–76% in Step 33).
- **Limit of detection (as Step 35), 5 groups per cell (too small):** breast size in mm 10%; breast size % width 10%; thyroid size % width 20%; fetal head circumference 5 mm (CI 5–10 mm). GREEN (4-bit) gives AUROC 0.50 at a 5% size error and at 1–2 mm HC shifts, i.e. it does not notice them; the judge reached the smallest tested level in Step 35 (5%, 1 mm; judge cells partly under 30 groups). Bootstrap CIs over 5 groups are not meaningful.

## What was run

- 507 of 4,088 design pairs scored = 40 of 320 units (20 factorial, 20 limit-of-detection: 5 per cell), the first 40 units of the pre-registered order. 0 unparsed. 30 pairs scored exactly 0 (no matched finding), all planted-error candidates (c or d) in the factorial.
- **Size rule followed as written, but the time estimate was off:** dev timing measured 18.6 s per pair (20 dev pairs, includes first-call warm-up), so the rule chose the minimum, 40 units (expected 2.9 h). Test scoring actually ran at about 6.4–7.6 s per pair (about 1 h). `n_chosen.json` was written before any test pair was scored and was not changed afterwards; no extra units were added (that would break the rule).
- Pair file SHA-256 matches the pre-registration (`3807ae94...`). Dev identical-copy check: 2 of 2 scored 1.0.

## Deviations from the pre-registration (all recorded in `colab_env.json`)

- **Software outside GREEN's declared support:** Python 3.13.16 (green-score 0.0.13 declares Python < 3.13), installed with `pip install --no-deps --ignore-requires-python`; transformers 4.57.6 (package asks for 4.40.0; 5.x removed `batch_encode_plus`, which GREEN calls), torch 2.14.1 (asks < 2.6), numpy 2.4.6 (asks < 2). Prompt, generation and parsing code unchanged. No check that these versions give the same scores as the reference setup.
- `step42_analyse.py` writes only `results.json`; this `results.md` was written by hand from it (no `run_info.json`).
- Realised n (40 units) far below design (320), as the pre-registration allowed.

## Caveats (fixed in advance, repeated)

4-bit quantisation (no fp16 check); templated text only; GREEN was built for chest X-ray reports; one greedy run; every cell under 30 groups.
