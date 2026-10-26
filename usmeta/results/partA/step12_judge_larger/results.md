# Step 12: larger judge sample on the locked TEST split (Gemma-2-9B sentence_check, prompt_v2)

Limitations: [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md). Frozen settings: Gemma-2-9B-it 4-bit (MLX, greedy), `prompt_v2` (the stricter prompt; prompt_v1 was not re-run: no time budget), same scoring as Step 7 / 10d. New file `usmeta/judge_big.py`.

**Sample size: the largest that fits in the 3-hour limit.** 59 cases per dataset (590 cases, 2,892 candidate rows), i.e. the 25 cases of Step 10d plus 34 new test cases per dataset (fresh seed, none reused): 1,477 new pairs judged in 6,871 s (plus about 21 minutes of an earlier, interrupted start of the same run; about 2.3 hours of judging in total, 0 unparseable replies). Per case: 1 harmless_small, 1 matched one-word synonym, 1 harmless_large, 2 planted errors of different categories, and identical copies for the first 3 added cases (so 3 + 3 per dataset). The brief's "up to 50 per dataset" for Step 10d is now exceeded (59). The added pairs were scheduled round-robin over datasets so that every dataset has the same number of cases. Confidence intervals resample **groups** (patient / exam / near-duplicate cluster), 1,000 resamples.

**"Too small to compare" rule (n < 30).** Every dataset has 59 cases, so none falls below 30 cases; but **BUS-UCLM has only 9 patient groups on the test split** (59 cases come from 9 patients), so its row is marked too small to compare (cases are not independent). Of the 43 dataset x category cells below, **29 have fewer than 30 planted errors and are marked ⚠**: read them as counts, not as comparisons.

**Wiring gate.** Identical-copy mean = 1.0000 on every dataset for both `sentence_f1` and `judge_score` (prompt_v2).

**Headline (sentence_f1; AUROC of planted error vs harmless; 1.0 perfect, 0.5 chance).**
- **vs the matched one-word synonym: 0.89-1.00 on all ten datasets** (BrEaST 0.89, BUSI 0.89, DDTI 0.90, BUS-BRA 0.96, UDIAT 0.95, BUS-UCLM 0.97, TN3K 0.99, TN5000/HC18/FetalHead 1.00): the judge reliably separates an error from a one-word reword. This is stable against the 25-case numbers (0.88-1.00).
- **vs harmless_small (synonyms, reorder, unit rewrite) it stays weak on breast and DDTI:** BUS-BRA 0.60 (0.50-0.71), UDIAT 0.61, BrEaST 0.67, BUSI 0.67, DDTI 0.71; strong elsewhere (BUS-UCLM 0.91 but few groups, FetalHead 0.94, HC18 0.82, TN3K 0.99, TN5000 1.00). Its mean score on harmless_small is 0.81-0.93 on the breast sets and DDTI: the judge still marks some harmless rewrites as differences.
- **vs harmless_large (style swap):** HC18 0.63 (0.49-0.75), BrEaST 0.61, DDTI 0.69, TN5000 0.90, TN3K 0.92, UDIAT 0.87, BUSI 0.88, BUS-UCLM 0.95, BUS-BRA and FetalHead 0.96-1.00.
- **Larger sample vs Step 10d (25 cases):** point estimates moved by up to 0.09 (BUS-BRA vs small 0.69 -> 0.60; BrEaST 0.60 -> 0.67) and the intervals roughly halved in width (BrEaST 0.46-0.74 -> 0.59-0.75). The qualitative picture did not change; the Step 10d concern ("BrEaST vs small fell from 0.86 to 0.60") was partly noise: at 59 cases it is 0.67 (0.59-0.75), still below the 0.86 seen in the dev-era sample (20 cases, 0.86): the dev-era figure was optimistic.
- **Category naming and detection (planted errors).** The judge lists at least one error for 99-100% of planted errors in every dataset (BrEaST 99%, all others 100%) and names the planted category for 85% (BrEaST, BUS-BRA), 88% (BUSI, UDIAT, TN3K), 91% (DDTI), 96% (BUS-UCLM), 81% (TN5000), 100% (HC18, only one error type) and **50% on FetalHead** (the plane-swap error is detected but named with another category). See the category table for counts.

**What did not change vs earlier steps.** The judge is useful for detecting that something differs and weak at telling harmless rewording from a planted error when the rewording is large; it is prompt-sensitive (Step 7), the references are templated, and the judge can say nothing about real report quality. Layers 0-1 are unaffected.

**Caveats.** Templated reports (synthetic but fact-correct); provisional severity; template sources "to confirm"; one judge model, one prompt (prompt_v2) here; groups missing for BUSI, UDIAT, TN3K, TN5000, HC18 (image-level groups, patient overlap possible); BUS-UCLM 9 groups; the earlier 25-case sample is included in these 59 cases (so the two are not independent samples).

## Tables

| dataset | cases | groups | planted errors | AUROC vs harmless_small (95% CI, group bootstrap) | vs matched one-word synonym | vs harmless_large | harmless_small mean | harmless_large mean | identical mean | same measure, Step 10d (25 cases): vs small |
|---|---|---|---|---|---|---|---|---|---|---|
| BrEaST | 59 | 59 | 117 | 0.67 (0.59–0.75) | 0.89 (0.86–0.92) | 0.61 (0.52–0.69) | 0.90 | 0.85 | 1.0000 | 0.60 (0.46–0.74) |
| BUS-BRA | 59 | 50 | 118 | 0.60 (0.50–0.71) | 0.96 (0.94–0.98) | 0.96 (0.94–0.98) | 0.84 | 1.00 | 1.0000 | 0.69 (0.54–0.83) |
| BUSI | 59 | 57 | 106 | 0.67 (0.57–0.75) | 0.89 (0.86–0.92) | 0.88 (0.83–0.91) | 0.82 | 0.98 | 1.0000 | 0.71 (0.56–0.84) |
| UDIAT | 59 | 57 | 118 | 0.61 (0.52–0.70) | 0.95 (0.93–0.98) | 0.87 (0.83–0.92) | 0.81 | 0.94 | 1.0000 | 0.58 (0.44–0.73) |
| BUS-UCLM **(too small to compare)** | 59 | 9 | 75 | 0.91 (0.87–0.96) | 0.97 (0.96–0.99) | 0.95 (0.91–0.99) | 0.93 | 0.97 | 1.0000 | 0.95 (0.89–1.00) |
| TN3K | 59 | 59 | 118 | 0.99 (0.98–1.00) | 0.99 (0.98–1.00) | 0.92 (0.89–0.95) | 1.00 | 0.87 | 1.0000 | 0.99 (0.97–1.00) |
| TN5000 | 59 | 59 | 118 | 1.00 (0.99–1.00) | 1.00 (0.99–1.00) | 0.90 (0.87–0.93) | 1.00 | 0.82 | 1.0000 | 1.00 (1.00–1.00) |
| DDTI | 59 | 52 | 117 | 0.71 (0.63–0.79) | 0.90 (0.87–0.93) | 0.69 (0.60–0.78) | 0.87 | 0.74 | 1.0000 | 0.71 (0.58–0.82) |
| HC18 | 59 | 59 | 59 | 0.82 (0.76–0.89) | 1.00 (1.00–1.00) | 0.63 (0.49–0.75) | 0.88 | 0.63 | 1.0000 | 0.86 (0.78–0.94) |
| FetalHead | 59 | 37 | 117 | 0.94 (0.91–0.97) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.92 | 1.00 | 1.0000 | 0.92 (0.87–0.96) |

**judge_score (error-list score), same sample:**

| dataset | vs small | vs matched | vs large | critical-only (small) |
|---|---|---|---|---|
| BrEaST | 0.85 (0.77–0.93) | 1.00 (0.99–1.00) | 0.51 (0.42–0.62) | 0.74 |
| BUS-BRA | 0.64 (0.54–0.75) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.61 |
| BUSI | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.98 (0.95–1.00) | 1.00 |
| UDIAT | 0.69 (0.60–0.79) | 1.00 (1.00–1.00) | 0.93 (0.89–0.97) | 0.81 |
| BUS-UCLM | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.97 (0.92–1.00) | 1.00 |
| TN3K | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (0.99–1.00) | 1.00 |
| TN5000 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.99 (0.97–1.00) | 1.00 |
| DDTI | 0.89 (0.82–0.96) | 1.00 (1.00–1.00) | 0.82 (0.73–0.90) | 1.00 |
| HC18 | 0.94 (0.90–0.97) | 1.00 (1.00–1.00) | 0.63 (0.49–0.75) | 1.00 |
| FetalHead | 0.85 (0.77–0.93) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 |

## Per error category: AUROC vs harmless_small (sentence_f1) and the judge naming the planted category / flagging any error

Cells with fewer than 30 planted errors are marked ⚠ (too small to compare).

| dataset | category | planted errors | AUROC vs small | judge names the planted category | judge lists any error |
|---|---|---|---|---|---|
| BrEaST | false finding | 29 ⚠ | 0.66 | 1.00 | 1.00 |
| BrEaST | missed finding | 15 ⚠ | 0.93 | 0.67 | 0.93 |
| BrEaST | wrong location | 5 ⚠ | 0.90 | 1.00 | 1.00 |
| BrEaST | wrong measurement | 24 ⚠ | 0.35 | 1.00 | 1.00 |
| BrEaST | wrong severity/category | 44 | 0.73 | 0.70 | 1.00 |
| BUS-BRA | false finding | 12 ⚠ | 0.50 | 1.00 | 1.00 |
| BUS-BRA | missed finding | 14 ⚠ | 1.00 | 0.36 | 1.00 |
| BUS-BRA | wrong location | 16 ⚠ | 0.62 | 0.94 | 1.00 |
| BUS-BRA | wrong measurement | 34 | 0.50 | 1.00 | 1.00 |
| BUS-BRA | wrong severity/category | 42 | 0.57 | 0.81 | 1.00 |
| BUSI | false finding | 27 ⚠ | 0.85 | 1.00 | 1.00 |
| BUSI | missed finding | 12 ⚠ | 1.00 | 1.00 | 1.00 |
| BUSI | wrong location | 8 ⚠ | 0.69 | 1.00 | 1.00 |
| BUSI | wrong measurement | 35 | 0.34 | 1.00 | 1.00 |
| BUSI | wrong severity/category | 24 ⚠ | 0.60 | 0.46 | 1.00 |
| UDIAT | false finding | 19 ⚠ | 0.37 | 1.00 | 1.00 |
| UDIAT | missed finding | 17 ⚠ | 1.00 | 1.00 | 1.00 |
| UDIAT | wrong location | 14 ⚠ | 0.71 | 1.00 | 1.00 |
| UDIAT | wrong measurement | 31 | 0.39 | 0.87 | 1.00 |
| UDIAT | wrong severity/category | 37 | 0.70 | 0.73 | 1.00 |
| BUS-UCLM | false finding | 46 | 0.98 | 1.00 | 1.00 |
| BUS-UCLM | missed finding | 7 ⚠ | 1.00 | 1.00 | 1.00 |
| BUS-UCLM | wrong location | 3 ⚠ | 0.83 | 1.00 | 1.00 |
| BUS-UCLM | wrong measurement | 11 ⚠ | 0.32 | 1.00 | 1.00 |
| BUS-UCLM | wrong severity/category | 8 ⚠ | 0.81 | 0.62 | 1.00 |
| TN3K | false finding | 17 ⚠ | 1.00 | 1.00 | 1.00 |
| TN3K | missed finding | 17 ⚠ | 1.00 | 0.18 | 1.00 |
| TN3K | wrong location | 13 ⚠ | 1.00 | 1.00 | 1.00 |
| TN3K | wrong measurement | 46 | 0.98 | 1.00 | 1.00 |
| TN3K | wrong severity/category | 25 ⚠ | 1.00 | 1.00 | 1.00 |
| TN5000 | false finding | 27 ⚠ | 1.00 | 1.00 | 1.00 |
| TN5000 | missed finding | 22 ⚠ | 1.00 | 0.00 | 1.00 |
| TN5000 | wrong location | 9 ⚠ | 1.00 | 1.00 | 1.00 |
| TN5000 | wrong measurement | 43 | 0.99 | 1.00 | 1.00 |
| TN5000 | wrong severity/category | 17 ⚠ | 1.00 | 1.00 | 1.00 |
| DDTI | false finding | 13 ⚠ | 0.88 | 1.00 | 1.00 |
| DDTI | missed finding | 19 ⚠ | 0.84 | 0.58 | 1.00 |
| DDTI | wrong location | 6 ⚠ | 0.75 | 1.00 | 1.00 |
| DDTI | wrong measurement | 37 | 0.50 | 1.00 | 1.00 |
| DDTI | wrong severity/category | 42 | 0.77 | 0.95 | 1.00 |
| HC18 | wrong measurement | 59 | 0.82 | 1.00 | 1.00 |
| FetalHead | wrong measurement | 58 | 0.89 | 1.00 | 1.00 |
| FetalHead | wrong severity/category | 59 | 1.00 | 0.00 | 1.00 |