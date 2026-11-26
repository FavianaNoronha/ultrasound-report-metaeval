# Step 48 (PRE-REGISTRATION): improve S1 on Set C, then confirm once on fresh text (Set D)

Written 2026-11-26, after Step 47 results and before any Step 48 trial or Set D text exists. Deadline: 2026-11-29.

## Why
Step 47 Set C: S1 missed 0 of 293 major/critical errors and routed 19.5% of harmless reports, but only 293 such errors survived (pre-registered minimum 400), so H1 was not eligible. 116 of 263 routed harmless reports were routed only because a Gemma reply could not be parsed; the judge's quotes were rarely exact; the workload depended on the judge (Llama 60.7% routed). Set C is now spent: it becomes Step 48 development data.

## Data
- Development: Step 47 Set C (all 1,770 core reports, Mistral writer) plus Step 46 Set B dev/val. Every Stage 1 trial uses only these.
- Fresh test, Set D: the test-split scans of Step 46 Set B and Step 47 Set C (about 1,000 cases), rewritten by a writer never used before: `mlx-community/Phi-3.5-mini-instruct-4bit`, seed 48, same planted-error types and harmless rewordings, same gold and filter rules as Step 47. Set D reuses scans that earlier steps used, with new text; we say so. No scorer component was fitted on these scans' text other than the Step 47 routing choices.
- Eligibility: at least 400 planted major/critical errors after filtering and at least 30 groups per organ; otherwise H1 to H4 are reported as not eligible.

## Fixed now
- Baseline: S1 exactly as frozen in Step 47 (`frozen_variants.json` 17ff9879…), Gemma judge.
- Candidate changes for Stage 1 (alone or combined):
  P. Parser fix: failed judge calls are re-asked once with the raw reply saved; a lenient parser accepts JSON inside code fences, single quotes, trailing commas and extra text. A reply still unreadable routes, as in S1.
  L. Llama-3.1-8B-Instruct-4bit as the judge instead of Gemma, or both (route if either routes, or only if both route).
  U. Image check: the Step 45 G / Step 29 U-Net predicts the lesion region on the report's own scan; a report routes when its stated position or size disagrees with the prediction by more than a margin chosen on development data. Fetal head circumference uses the HC18-style ellipse only if a working model exists; otherwise U is breast and thyroid only.
- Stage 1: at most 12 logged trials or until 2026-11-28 12:00 IST, whichever first. Selection metric: catch of major/critical errors on Set C at harmless routed <= 30%, ties broken by lower harmless routed share, then fewer model calls. Every trial goes in `trial_log.csv`, none deleted.
- Freeze: the winner (or S1 if nothing beats it on development data), its thresholds and the Set D plan size go in `frozen_variants.json` with a SHA-256, committed before Set D generation.

## Hypotheses (primary = frozen winner, called S2; S1 also reported)
- H1: miss rate of major/critical errors with one-sided 95% Clopper-Pearson upper bound <= 2%, AND harmless routed <= 30%.
- H2: at S2's development route budget, S2 catches more planted errors than each word scorer (BLEU, ROUGE-L, chrF, BERTScore, RaTEScore), group-bootstrap CI excluding 0. CRQS and Step 45 learned are reported, not required (Step 47 showed a tie with CRQS).
- H3: S2 harmless routed share is lower than S1's on Set D, paired group-bootstrap CI excluding 0.
- H4 (descriptive): judge dependence: S2 with Gemma vs Llama on a fixed 300-report Set D subset.
- H5 (descriptive): share of routes per reason; share of unreadable judge replies before and after P.
- H6 (descriptive): if U is in S2, its extra catches and extra false alarms by organ.
- Extractor hand check on 30 Set D reports, one reviewer, before any Set D score.

## Reporting
Group bootstrap 1,000 seed 0; groups under 30 marked too small. Model-written text only; no clinician validation. Commits carry no AI co-author line.
