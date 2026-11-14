# Step 39 pre-registration: stabilising the Gemma-2-9B judge by averaging over prompt wordings

Status: written after the dev / val parsing gate and BEFORE any new test-split judge call; the owner commits this file before the test run. The test split is not read for Step 39 until then. Nothing is chosen on test; every number below is fixed here. Deviations after the commit are listed in `results.md` ("Compute and deviations").

## Prompts (frozen; SHA-256 of the text with its `{ref}` / `{hyp}` placeholders)

| id | what | SHA-256 |
|---|---|---|
| P0 | the frozen judge prompt (prompt_v2, `judge2.PROMPT_V2`); inputs in the normal order | `608412841d3fa25641a6db6afe5e888bc150c4fbda37af113ed6538dd63d3438` |
| P1 | Step 21c paraphraseA (`step21_judge_sens.PARA_A`); normal order | `e7211cd6630ccfbedad74527f8e7ec3d2b20dbe56059f772761faefd27f36be9` |
| P2 | Step 21c paraphraseB with rule 4 reworded to "If the two reports are identical, every value must be true and the errors list must be empty." and a rule 6 added ("A sentence that appears word for word in both reports is always true, however short or unusual it looks."); normal order. NOT the text of the saved Step 21c replies | `15590041106b43df3170131a3608b9f6a38ee0607b48b8006a0a3cc66542a5a0` |
| P3 | the P0 text with the candidate in the REFERENCE slot and the reference in the CANDIDATE slot (the Step 21c swap); the saved Step 21c replies are reused | `608412841d3fa25641a6db6afe5e888bc150c4fbda37af113ed6538dd63d3438` |
| P4 | new paraphrase C; normal order | `916533ecf5af4e8cf1e5d94549f28a7bf5df45a2c72ab54af959fd24ed0cb41e` |
| P5 | new paraphrase D (a sibling of P4 in structure, different wording); normal order | `237b445a2f0ea07689973c1bc681cd86e5e3ba582b903ff3b6b335316666b7f4` |

Same model for all six (Gemma-2-9B-it 4-bit, MLX), greedy decoding, same output parsing (`judge2.parse`, `judge2.scores_from`). **Set A = {P0, P1, P2}; set B = {P3, P4, P5}. Ensemble score = the mean `judge_score` over the three prompts of a set.**

### P0

```
You are a sonographer-radiologist comparing an AI-written ultrasound report (CANDIDATE) with a REFERENCE report.
Compare ONLY what the two reports say. Do not judge whether a finding is medically plausible or complete.
Rules:
- A CANDIDATE sentence is supported (true) if it appears word for word in the REFERENCE, or says the same facts in other words.
- A REFERENCE sentence is covered (true) if it appears word for word in the CANDIDATE, or its facts are stated in other words.
- Ignore wording, order and style when the meaning is unchanged. Units are equivalent (10 mm = 1 cm).
- If the two reports are identical, every value is true and errors is empty.
- List an error only when a fact differs: something added, missing, or changed (a value, location, size or category).

REFERENCE sentences:
{ref}

CANDIDATE sentences:
{hyp}

Reply with JSON only:
{{"candidate_supported": [true or false for each CANDIDATE sentence, in order],
 "reference_covered": [true or false for each REFERENCE sentence, in order],
 "errors": [{{"field": "<what differs>", "severity": "critical|major|minor", "category": "false finding|missed finding|wrong location|wrong severity/category|wrong measurement"}}]}}
```

### P1

```
You are a specialist in ultrasound reporting. You are given a REFERENCE report and a CANDIDATE report, both already split into numbered sentences. Your job is to compare what they say, nothing else, and not to decide whether any finding is clinically plausible or complete.
Guidance:
- A CANDIDATE sentence counts as supported (true) when the REFERENCE contains it verbatim or states the same facts differently.
- A REFERENCE sentence counts as covered (true) when the CANDIDATE contains it verbatim or states its facts differently.
- Differences in wording, sentence order or style do not matter if the meaning is the same. Units are interchangeable (10 mm = 1 cm).
- When the two reports are identical, every value must be true and the errors list must be empty.
- Record an error only when a fact is different: added, missing, or altered (a value, a location, a size or a category).

REFERENCE sentences:
{ref}

CANDIDATE sentences:
{hyp}

Reply with JSON only:
{{"candidate_supported": [true or false for each CANDIDATE sentence, in order],
 "reference_covered": [true or false for each REFERENCE sentence, in order],
 "errors": [{{"field": "<what differs>", "severity": "critical|major|minor", "category": "false finding|missed finding|wrong location|wrong severity/category|wrong measurement"}}]}}
```

### P2

```
Task: act as a sonographer-radiologist and check one ultrasound report (CANDIDATE) against a trusted report (REFERENCE). Only compare the content of the two texts; do not assess medical plausibility or completeness.
Rules:
1. Mark a CANDIDATE sentence true if its content is found in the REFERENCE, either word for word or expressed in other words.
2. Mark a REFERENCE sentence true if its content is found in the CANDIDATE, either word for word or expressed in other words.
3. Ignore differences in phrasing, ordering and style when the meaning stays the same; 10 mm and 1 cm are the same.
4. If the two reports are identical, every value must be true and the errors list must be empty.
5. Add an entry to errors only for a real factual difference (something added, left out, or changed: value, location, size, category).
6. A sentence that appears word for word in both reports is always true, however short or unusual it looks.

REFERENCE sentences:
{ref}

CANDIDATE sentences:
{hyp}

Reply with JSON only:
{{"candidate_supported": [true or false for each CANDIDATE sentence, in order],
 "reference_covered": [true or false for each REFERENCE sentence, in order],
 "errors": [{{"field": "<what differs>", "severity": "critical|major|minor", "category": "false finding|missed finding|wrong location|wrong severity/category|wrong measurement"}}]}}
```

### P3

```
You are a sonographer-radiologist comparing an AI-written ultrasound report (CANDIDATE) with a REFERENCE report.
Compare ONLY what the two reports say. Do not judge whether a finding is medically plausible or complete.
Rules:
- A CANDIDATE sentence is supported (true) if it appears word for word in the REFERENCE, or says the same facts in other words.
- A REFERENCE sentence is covered (true) if it appears word for word in the CANDIDATE, or its facts are stated in other words.
- Ignore wording, order and style when the meaning is unchanged. Units are equivalent (10 mm = 1 cm).
- If the two reports are identical, every value is true and errors is empty.
- List an error only when a fact differs: something added, missing, or changed (a value, location, size or category).

REFERENCE sentences:
{ref}

CANDIDATE sentences:
{hyp}

Reply with JSON only:
{{"candidate_supported": [true or false for each CANDIDATE sentence, in order],
 "reference_covered": [true or false for each REFERENCE sentence, in order],
 "errors": [{{"field": "<what differs>", "severity": "critical|major|minor", "category": "false finding|missed finding|wrong location|wrong severity/category|wrong measurement"}}]}}
```

### P4

```
Compare two ultrasound reports sentence by sentence. The REFERENCE is the correct report and the CANDIDATE is the report to be checked. Judge only whether the statements match; do not judge whether the findings are realistic or complete.
How to decide:
- For each CANDIDATE sentence answer true if the REFERENCE says the same thing (identical words or a rewording), otherwise false.
- For each REFERENCE sentence answer true if the CANDIDATE says the same thing (identical words or a rewording), otherwise false.
- A different word order, a different style, or a different unit for the same measurement (10 mm and 1 cm) is not a difference.
- If the two reports say exactly the same, every answer is true and the error list stays empty.
- Put an item in the error list only when a fact really differs: invented, omitted or changed (a number, a position, a size, a category).

REFERENCE sentences:
{ref}

CANDIDATE sentences:
{hyp}

Reply with JSON only:
{{"candidate_supported": [true or false for each CANDIDATE sentence, in order],
 "reference_covered": [true or false for each REFERENCE sentence, in order],
 "errors": [{{"field": "<what differs>", "severity": "critical|major|minor", "category": "false finding|missed finding|wrong location|wrong severity/category|wrong measurement"}}]}}
```

### P5

```
Go through an ultrasound CANDIDATE report and its REFERENCE report, sentence by sentence. The REFERENCE is the correct report. Decide only whether the two say the same thing; do not decide whether the findings are realistic or complete.
Method:
- Mark each CANDIDATE sentence true when the REFERENCE contains the same statement (the same words or a rewording), otherwise false.
- Mark each REFERENCE sentence true when the CANDIDATE contains the same statement (the same words or a rewording), otherwise false.
- Another word order, another style, or another unit for the same measurement (10 mm and 1 cm) is not a difference.
- If the two reports say exactly the same, every mark is true and the error list stays empty.
- Add an item to the error list only when a fact really differs: invented, omitted or changed (a number, a position, a size, a category).

REFERENCE sentences:
{ref}

CANDIDATE sentences:
{hyp}

Reply with JSON only:
{{"candidate_supported": [true or false for each CANDIDATE sentence, in order],
 "reference_covered": [true or false for each REFERENCE sentence, in order],
 "errors": [{{"field": "<what differs>", "severity": "critical|major|minor", "category": "false finding|missed finding|wrong location|wrong severity/category|wrong measurement"}}]}}
```

(P0 and P3 share this text; P3 swaps the two inputs. The Step 21c paraphraseA text is P1.)

## Hypotheses (verbatim from the brief) and their operational definitions
- **H1 (stability):** the share of pairs with |ensemble_A - ensemble_B| > 0.1 is below 10%, compared with the single-prompt share (P0 vs P3, same pairs) on the same cases. **Supported iff the ensemble share < 10% AND its 95% group-bootstrap CI upper bound is below the single-prompt share's point estimate.**
  - Pairs: the 432 (reference, candidate) pairs of the 89 Step 21c cases (breast 40, thyroid 29, fetal head 20). A pair is used only if all six prompts returned a parsed reply (the number excluded is reported). Group bootstrap: pairs are the units, resampled by patient / exam group (1,000 resamples, seed 0). Per-organ rows are reported for orientation; any cell under 30 groups is marked "too small" and not compared.
- **H2 (no loss of accuracy):** ensemble_A AUROC vs matched synonym and vs harmless_small is not lower than P0 alone by more than 0.02 (pooled, group-bootstrap CI of the difference; lower bound > -0.02).
  - AUROC per case = P(planted error scores lower than the harmless rewording), ties 0.5, over the case's planted errors vs its `matched` rewording and, separately, vs its `small` rewording; per-case difference (ensemble_A - P0); mean over cases with a group-bootstrap CI (1,000, seed 0). **Supported iff the lower bound of the pooled difference is > -0.02 for both comparisons.** Per-organ rows reported, under-30-group cells marked.
  - Cases: the same 89 Step 21c cases. They are a stratified subset of the Step 12 sample (10 per dataset); P0, P1 (saved) and P2 (new) replies exist for all their pairs. **No extra cases are added** (planned `h2_extra_cases_per_dataset = 0`): the compute cap leaves no room for more.

## Compute plan and caps
- Measured on dev / val: about 5.4 seconds per judge call. New test calls: P2 (amended text) on 432 pairs, P4 on 432, P5 on 432 = **1,296 calls, about 2 h**. Reused without a new call: P0 (saved Steps 10d + 12 replies) and P1, P3 (saved Step 21c replies), wherever prompt text and input are identical.
- **Compute clock started 2026-11-14 20:32:46 IST** (first dev / val judge call); **hard cap 3 hours of compute** including the dev / val gate (about 45 minutes used when this was written). If the cap is reached the run stops, the n actually reached is reported, and nothing is extended on test.
- The optional second-family judge (Llama-3.1-8B-Instruct) is **not planned** (it would need a new download and there is no compute left).

## Dev / val gate (record)
- Gate = every prompt must give judge_score 1.0 on every identical copy and parse every reply. Final run: **17 identical copies from the dev / val judge sample, all six prompts mean 1.0, 0 unparsed identical, 0 unparsed on 39 further dev / val pairs for P2, P4, P5**; seconds per call 5.4.
- First gate (8 identical copies): P2 (= Step 21c paraphraseB as it was) and the first draft of P5 each scored 0.4 on one copy (a dev report ending "Histology: fa."). Amendments on dev / val only: (v2) a verbatim-copy rule added to both: still failed; (v3) rule 4 of P2 reworded and the copy rule kept: P2 passed, the P5 draft still failed; (v4) P5 rewritten as a procedure list: failed; (v5) P5 rewritten as a sibling of P4: passed. The failed versions' replies are kept as `devval_P2_v1_superseded.jsonl` ... `devval_P5_v4_superseded.jsonl`. P5 is therefore structurally close to P4 (a limitation for the independence of set B).

## Reporting
- `results.md` states the H1 and H2 verdicts in its first lines, with pooled and per-organ tables, n, CIs and too-small marks; `results.json`, `run_info.json`, an INDEX.md row, a RESULTS_SUMMARY.md addendum, a LIMITATIONS.md item and a CHANGELOG.md entry follow.