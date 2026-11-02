# Step 21c — Judge sensitivity (Gemma-2-9B, frozen prompt_v2 as the original)

Same judge, same sample, four variants: **swap** (the candidate text goes into the REFERENCE slot and vice versa), **paraphraseA** and **paraphraseB** (the instruction text reworded, output format identical), and **repeat** (the original prompt run again with a FRESH cache, to test repeatability). Original = the saved Step 10d/12 replies, untouched (prompt_v1/v2 results unchanged). Code: `usmeta/step21_judge_sens.py`. AUROC = planted errors vs harmless rewordings (small + matched + large) of the same case, per case, group bootstrap; the original is recomputed on exactly the cases each variant was run on.

**Sample (deviation, stated):** reduced from the 59 cases per dataset of Step 12 to 10 per dataset (the cases that have all three harmless types and an error judged): 432 pairs per variant, 89 cases (breast 40, thyroid 29, fetal head 20), to stay near the 3 h limit (1,340 judge calls in 2.5 h; one MLX crash, resumed from the saved replies). **Every per-dataset cell has at most 10 cases: too small to compare** (see the table); only breast (40 cases) reaches 30. The `repeat` variant covers 2 cases per dataset (93 pairs, 19 cases).

## Headline (plain words)
- **Greedy decoding is repeatable:** of 93 pairs judged again with a fresh cache, 0% changed in `judge_score` (and none in `sentence_f1`), as in Step 8b.
- **But the verdict depends on how the prompt is written:** reordering reference and candidate changes `judge_score` by more than 0.1 in 21% of pairs, and the two reworded instructions in 18% and 26%; 27–34% change at all. `sentence_f1` changes by more than 0.1 in 17–27%.
- **AUROC moves by up to +0.10 on breast and +0.07 on thyroid, and slightly down on fetal head:** breast 0.85 → 0.93 (swap), 0.93 (A), 0.96 (B); thyroid 0.93 → 1.00 (B; † 27 cases); fetal head -0.02 to -0.03 († 20 cases). On breast and thyroid every variant scores the same or higher than the frozen prompt (swap on thyroid: unchanged); we did NOT tune on this and keep prompt_v2 as the reported prompt.
- **Reading:** the judge's verdict on a given pair is stable under repetition but not under harmless changes to the prompt, so a single prompt's AUROC (for example 0.85 on breast here) can shift by about 0.1. This is the same prompt sensitivity as Step 7 (up to 0.30 on 20 cases) and Step 12.

## Pooled by organ and overall (n = cases; † fewer than 30 cases: too small to compare)
| group | variant | cases | pairs | AUROC original | AUROC variant | change | share of pairs with judge_score changed by > 0.1 | share changed at all | share with sentence_f1 changed by > 0.1 |
|---|---|---|---|---|---|---|---|---|---|
| breast | swap | 40 | 200 | 0.85 | 0.93 | +0.08 | 0.26 | 0.36 | 0.20 |
| breast | paraphraseA | 39 | 199 | 0.85 | 0.93 | +0.08 | 0.18 | 0.21 | 0.29 |
| breast | paraphraseB | 40 | 200 | 0.85 | 0.96 | +0.10 | 0.30 | 0.38 | 0.30 |
| breast † | repeat | 9 | 45 | 0.80 | 0.80 | +0.00 | 0.00 | 0.00 | 0.00 |
| thyroid † | swap | 29 | 147 | 0.93 | 0.93 | +0.00 | 0.20 | 0.24 | 0.17 |
| thyroid † | paraphraseA | 29 | 147 | 0.93 | 0.95 | +0.02 | 0.21 | 0.22 | 0.33 |
| thyroid † | paraphraseB | 27 | 145 | 0.93 | 1.00 | +0.07 | 0.30 | 0.37 | 0.19 |
| thyroid † | repeat | 6 | 30 | 0.89 | 0.89 | +0.00 | 0.00 | 0.00 | 0.00 |
| fetal head † | swap | 20 | 85 | 0.88 | 0.86 | -0.02 | 0.12 | 0.12 | 0.11 |
| fetal head † | paraphraseA | 20 | 85 | 0.88 | 0.85 | -0.03 | 0.15 | 0.15 | 0.12 |
| fetal head † | paraphraseB | 20 | 85 | 0.88 | 0.87 | -0.01 | 0.09 | 0.21 | 0.00 |
| fetal head † | repeat | 4 | 18 | 0.88 | 0.88 | +0.00 | 0.00 | 0.00 | 0.00 |
| ALL | swap | 89 | 432 | 0.88 | 0.92 | +0.03 | 0.21 | 0.27 | 0.17 |
| ALL | paraphraseA | 88 | 431 | 0.89 | 0.92 | +0.03 | 0.18 | 0.20 | 0.27 |
| ALL | paraphraseB | 87 | 430 | 0.88 | 0.95 | +0.07 | 0.26 | 0.34 | 0.20 |
| ALL † | repeat | 19 | 93 | 0.84 | 0.84 | +0.00 | 0.00 | 0.00 | 0.00 |

## Per dataset (every cell has ≤ 10 cases: too small to compare)
| group | variant | cases | pairs | AUROC original | AUROC variant | change | share of pairs with judge_score changed by > 0.1 | share changed at all | share with sentence_f1 changed by > 0.1 |
|---|---|---|---|---|---|---|---|---|---|
| BrEaST † | swap | 10 | 50 | 0.67 | 0.91 | +0.24 | 0.38 | 0.50 | 0.16 |
| BrEaST † | paraphraseA | 10 | 50 | 0.67 | 0.78 | +0.12 | 0.22 | 0.28 | 0.38 |
| BrEaST † | paraphraseB | 10 | 50 | 0.67 | 0.97 | +0.31 | 0.40 | 0.50 | 0.26 |
| BrEaST † | repeat | 2 | 10 | 0.33 | 0.33 | +0.00 | 0.00 | 0.00 | 0.00 |
| BUS-BRA † | swap | 10 | 50 | 0.84 | 1.00 | +0.16 | 0.26 | 0.46 | 0.26 |
| BUS-BRA † | paraphraseA | 10 | 50 | 0.84 | 1.00 | +0.16 | 0.22 | 0.22 | 0.34 |
| BUS-BRA † | paraphraseB | 10 | 50 | 0.84 | 1.00 | +0.16 | 0.38 | 0.38 | 0.20 |
| BUS-BRA † | repeat | 2 | 10 | 0.83 | 0.83 | +0.00 | 0.00 | 0.00 | 0.00 |
| BUSI † | swap | 8 | 40 | 1.00 | 1.00 | +0.00 | 0.10 | 0.20 | 0.15 |
| BUSI † | paraphraseA | 8 | 40 | 1.00 | 1.00 | +0.00 | 0.07 | 0.17 | 0.17 |
| BUSI † | paraphraseB | 8 | 40 | 1.00 | 1.00 | +0.00 | 0.03 | 0.12 | 0.28 |
| BUSI † | repeat | 2 | 10 | 1.00 | 1.00 | +0.00 | 0.00 | 0.00 | 0.00 |
| UDIAT † | swap | 10 | 50 | 0.90 | 0.82 | -0.08 | 0.28 | 0.32 | 0.24 |
| UDIAT † | paraphraseA | 9 | 49 | 0.92 | 0.94 | +0.03 | 0.18 | 0.18 | 0.24 |
| UDIAT † | paraphraseB | 10 | 50 | 0.90 | 0.85 | -0.05 | 0.42 | 0.52 | 0.50 |
| UDIAT † | repeat | 2 | 10 | 0.92 | 0.92 | +0.00 | 0.00 | 0.00 | 0.00 |
| BUS-UCLM † | swap | 2 | 10 | 1.00 | 1.00 | +0.00 | 0.10 | 0.10 | 0.20 |
| BUS-UCLM † | paraphraseA | 2 | 10 | 1.00 | 1.00 | +0.00 | 0.10 | 0.10 | 0.20 |
| BUS-UCLM † | paraphraseB | 2 | 10 | 1.00 | 1.00 | +0.00 | 0.00 | 0.00 | 0.10 |
| BUS-UCLM † | repeat | 1 | 5 | 1.00 | 1.00 | +0.00 | 0.00 | 0.00 | 0.00 |
| TN3K † | swap | 10 | 50 | 1.00 | 0.98 | -0.02 | 0.22 | 0.26 | 0.22 |
| TN3K † | paraphraseA | 10 | 50 | 1.00 | 1.00 | +0.00 | 0.20 | 0.20 | 0.30 |
| TN3K † | paraphraseB | 10 | 50 | 1.00 | 1.00 | +0.00 | 0.34 | 0.40 | 0.10 |
| TN3K † | repeat | 2 | 10 | 1.00 | 1.00 | +0.00 | 0.00 | 0.00 | 0.00 |
| TN5000 † | swap | 9 | 47 | 1.00 | 1.00 | +0.00 | 0.11 | 0.11 | 0.06 |
| TN5000 † | paraphraseA | 9 | 47 | 1.00 | 1.00 | +0.00 | 0.15 | 0.15 | 0.26 |
| TN5000 † | paraphraseB | 9 | 47 | 1.00 | 1.00 | +0.00 | 0.21 | 0.30 | 0.11 |
| TN5000 † | repeat | 2 | 10 | 1.00 | 1.00 | +0.00 | 0.00 | 0.00 | 0.00 |
| DDTI † | swap | 10 | 50 | 0.81 | 0.82 | +0.02 | 0.28 | 0.34 | 0.22 |
| DDTI † | paraphraseA | 10 | 50 | 0.81 | 0.86 | +0.05 | 0.28 | 0.32 | 0.42 |
| DDTI † | paraphraseB | 8 | 48 | 0.76 | 1.00 | +0.24 | 0.35 | 0.40 | 0.35 |
| DDTI † | repeat | 2 | 10 | 0.67 | 0.67 | +0.00 | 0.00 | 0.00 | 0.00 |
| HC18 † | swap | 10 | 37 | 0.83 | 0.83 | +0.00 | 0.16 | 0.16 | 0.11 |
| HC18 † | paraphraseA | 10 | 37 | 0.83 | 0.77 | -0.07 | 0.19 | 0.19 | 0.00 |
| HC18 † | paraphraseB | 10 | 37 | 0.83 | 0.83 | +0.00 | 0.14 | 0.14 | 0.00 |
| HC18 † | repeat | 2 | 8 | 0.83 | 0.83 | +0.00 | 0.00 | 0.00 | 0.00 |
| FetalHead † | swap | 10 | 48 | 0.93 | 0.88 | -0.04 | 0.08 | 0.08 | 0.10 |
| FetalHead † | paraphraseA | 10 | 48 | 0.93 | 0.93 | +0.01 | 0.12 | 0.12 | 0.21 |
| FetalHead † | paraphraseB | 10 | 48 | 0.93 | 0.91 | -0.02 | 0.06 | 0.27 | 0.00 |
| FetalHead † | repeat | 2 | 10 | 0.92 | 0.92 | +0.00 | 0.00 | 0.00 | 0.00 |

## Limits
Reduced sample (see above); the paraphrases were written once, not searched; the same 4-bit Gemma-2-9B for all variants; the original replies come from Steps 10d/12 (same model, same greedy settings, cache of a different run), and in the 93 pairs repeated with a fresh cache no value differs; judge_score is the error-penalty score of the judge's own listed errors; possible training exposure of the judge; one machine. `docs/LIMITATIONS.md` items 3 and 15.
