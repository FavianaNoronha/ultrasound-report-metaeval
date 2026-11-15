# Step 39: stabilising the Gemma-2-9B judge by averaging over prompt wordings

**H1 (stability): NOT SUPPORTED.** Share of pairs with |ensemble A - ensemble B| > 0.1: **39.2% (34.3%–44.7%)** (311 pairs, 67 groups) against the single-prompt share (P0 vs P3, same pairs) **21.5% (16.5%–26.1%)**. Pre-registered rule: ensemble share < 10% AND its CI upper bound below the single-prompt point estimate (21.5%).
**H2 (no loss of accuracy): SUPPORTED.** ensemble A minus P0 alone, per-case AUROC difference (pooled, 91 cases): vs matched synonym 0.000 (0.000–0.000); vs harmless_small 0.087 (0.028–0.163). Pre-registered rule: lower bound of the difference > -0.02 for both.

Pre-registration: [PREREG.md](PREREG.md) (committed before any new test-split judge call). Limitations: [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md). Code: `usmeta/step39_judge_ensemble.py`, `step39_report.py` (new files; frozen `judge2.PROMPT_V2`, Step 21c paraphrases and saved replies reused). Same model (Gemma-2-9B-it 4-bit, MLX, greedy), same parser. Group bootstrap (1,000, seed 0); cells under 30 groups are marked † (too small to compare).

## Prompts

| id | what | reused from |
|---|---|---|
| P0 | the frozen judge prompt (prompt_v2) | saved Step 10d / 12 replies |
| P1 | Step 21c paraphraseA | saved Step 21c replies |
| P2 | Step 21c paraphraseB **plus a verbatim-copy rule** (amended after the dev/val gate) | new replies (the Step 21c replies belong to the old text) |
| P3 | P0 text with the candidate in the REFERENCE slot and vice versa (Step 21c swap) | saved Step 21c replies |
| P4 | new paraphrase C | new replies |
| P5 | new paraphrase D **plus the verbatim-copy rule** | new replies |

Set A = {P0, P1, P2}, set B = {P3, P4, P5}; ensemble score = mean `judge_score` over a set. Full texts and SHA-256 hashes: PREREG.md.

## H1: stability on the 89 Step 21c cases (432 pairs)

| group | pairs | groups | ensemble share (A vs B > 0.1) | single-prompt share (P0 vs P3 > 0.1) |
|---|---|---|---|---|
| pooled | 311 (121 excluded: a reply missing) | 67 | 39.2% (34.3%–44.7%) | 21.5% (16.5%–26.1%) |
| breast | 150 (50 excluded: a reply missing) | 32 | 40.0% (32.2%–47.5%) | 25.3% (19.3%–31.6%) |
| thyroid | 101 (46 excluded: a reply missing) | 21 † | 42.6% (33.3%–51.6%) | 19.8% (11.4%–29.1%) |
| fetal head | 60 (25 excluded: a reply missing) | 14 † | 31.7% (22.0%–42.6%) | 15.0% (6.8%–23.7%) |

Context: Step 21c measured |judge_score change| > 0.1 in 21% (swap) and 18% / 26% (paraphrases) of pairs against the original prompt; here the single-prompt comparison is P0 vs P3 on the same pairs. Per-organ rows are shown for orientation; fetal head has 20 cases (under 30 groups: too small to compare).

## H2: accuracy, ensemble A vs P0 alone (AUROC of planted errors vs harmless, per case, ties 0.5)

Cases: the 89 Step 21c cases (P0, P1, P2 replies for all of their pairs) plus 0 extra cases from the Step 12 sample (0 per dataset), 91 cases in all. Each case has 1 small + 1 matched + 1 large harmless rewording and its planted errors.

| group | harmless | cases / groups | AUROC P0 | AUROC ensemble A | difference (95% CI) |
|---|---|---|---|---|---|
| pooled | matched synonym | 60 / 60 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.000 (0.000–0.000) |
| pooled | harmless_small | 63 / 63 | 0.87 (0.79–0.94) | 0.96 (0.92–0.99) | 0.087 (0.028–0.163) |
| breast | matched synonym | 29 / 29 † | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.000 (0.000–0.000) |
| breast | harmless_small | 29 / 29 † | 0.82 (0.66–0.94) | 0.98 (0.96–1.00) | 0.164 (0.052–0.302) |
| thyroid | matched synonym | 20 / 20 † | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.000 (0.000–0.000) |
| thyroid | harmless_small | 20 / 20 † | 0.94 (0.84–1.00) | 1.00 (1.00–1.00) | 0.062 (0.000–0.163) |
| fetal head | matched synonym | 11 / 11 † | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.000 (0.000–0.000) |
| fetal head | harmless_small | 14 / 14 † | 0.89 (0.79–1.00) | 0.86 (0.68–1.00) | -0.036 (-0.107–0.000) |

## Dev / val gate (before any new test call)

Identical-copy gate on 17 identical copies from the dev / val judge sample (one per distinct reference): **passed** for all six prompts. The first draft of P2 (= Step 21c paraphraseB) and of P5 scored one of eight identical copies 0.4 (a dev report ending in the abbreviation "Histology: fa."); both were amended with a verbatim-copy rule on dev / val, re-frozen, and the gate re-run (file `devval_gate_v1.json` keeps the first result). Seconds per judge call: 5.4.

| prompt | identical copies, mean judge_score | unparsed identical | unparsed other pairs |
|---|---|---|---|
| P0 | 1.000 | 0 | — |
| P1 | 1.000 | 0 | — |
| P2 | 1.000 | 0 | 0 |
| P3 | 1.000 | 0 | — |
| P4 | 1.000 | 0 | 0 |
| P5 | 1.000 | 0 | 0 |

## Compute and deviations

Compute clock started 2026-11-14 20:32:46 IST (first dev/val judge call) (first dev / val judge call); cap 3 h. See `run_info.json` for the compute used and the n reached.

- The Step 21c replies of paraphraseB cannot be reused for P2 (amended text), so P2 was re-run on all H1 pairs.
- **The compute cap (3 h) stopped the test run after 66 of 91 cases** (about 311 of 432 H1 pairs have all six replies; 121 pairs are excluded for a missing reply, no extension). The excluded pairs are the last cases of a seeded dataset round-robin order, so the kept pairs are balanced across datasets but fewer than planned.
- The first test schedule (all P4 calls first) would have run past the cap with P5 incomplete; after 54 P4 replies it was replaced by a prompt-interleaved order (P2, P4, P5 per pair, case by case). No reply was discarded. This changed order only, not any prompt text or rule.
- Prompt texts were amended during the dev/val gate (P2 and P5 several versions, superseded files kept) until all six prompts gave 1.0 on identical copies, before any test call; H2 used no extra cases beyond the 89.
- The optional second-family judge (Llama-3.1-8B-Instruct) was **not run** (compute cap; it would need a new 4-bit download).

## Caveats

- One model family (Gemma-2-9B), one machine, greedy decoding; the ensemble averages **prompt wordings**, not models, so any model-specific bias is untouched (the optional second-family check was not run).
- Set B contains the order swap (P3), so H1 compares three reworded prompts with the swap plus two paraphrases; the single-prompt reference is P0 vs P3.
- Templated candidates; 89 Step 21c cases for H1 (breast 40, thyroid 29, fetal head 20): per-organ cells are small, only the pooled row has 30 or more groups; H2 adds a few extra cases per dataset.
- The judge penalty score is floored by its error-count rule; an ensemble mean of floored scores is still a mean of the same scale.
