# Step 47 (PRE-REGISTRATION): audit-and-route scorer, fixed variants, one run on fresh data

Written 2026-11-23, before any Step 47 number. Updated 2026-11-23 (added V5, V6, then the two-stage design, then the second-judge check, then the validation fixes: H1 metric, severity leak, Set C size, Stage 1 stop rule, extractor hand check) still before any Step 47 number. Step 46 stays reported as is (H1/H2/H4 DOES NOT PASS).

## Why
Step 46 post-hoc check: UScore AUROC 0.656 as scored, 0.990 if reports with no rule difference get 1.0 instead of the holistic judge score (exploratory, 861 items). Cause: judge floor on harmless rewordings. CRQS 0.998 shares the extractor with the gold fields, so on templated cases it is close to circular. Open question: what holds on free text we did not build and on real reports.

## Rules against cherry-picking
1. Variants V0 to V6 are fixed now. Further variants may be added only in Stage 1 and frozen before Set C exists. No variant is added, tuned or dropped after seeing fresh-data numbers.
2. Any threshold or weight is chosen on dev/val only, then frozen in a file with a hash before fresh data is generated.
3. Fresh data is read once. All variants are reported, failures included. Report the number of variants tried (7 fixed, plus the Stage 1 trial count).
4. Primary comparison is ONE variant (V3), named now. Others are secondary and get no pass/fail claim.

## Two-stage design (added)
**Stage 1, open exploration on dev/val only.** Any variant may be tried: penalty values, zero floor, concept merging, judge as flag or auditor, adding the U-Net, thresholds, ensembles. Every trial is logged in `trial_log.csv` (id, description, code hash, dev/val AUROC, catch rate at the fixed false-alarm rate, date), failures included, and none is deleted. Extra dev data may be generated with the Set C writer, on scans excluded from Set C. Test data and Set C are not read in Stage 1.
**Stage 2, freeze and run once.** After Stage 1 ends, the best one to three variants by dev/val are written to `frozen_variants.json` with a SHA-256 hash, before Set C is generated. They are run once on Set C together with V0 to V6. The report states the total number of Stage 1 trials and Stage 2 variants.
**Stop rule:** Stage 1 ends at 20 logged trials or 3 calendar days from the first trial, whichever comes first. Selection metric, fixed now: catch rate of major or critical errors at a routed share of harmless reports <= 30%, on dev. Ties broken by fewer model calls per report.
**Primary variant:** V3 as named below. The Stage 1 winner may replace V3 as primary only if that decision is written into `frozen_variants.json` before Set C exists. Otherwise it is secondary.
**Multiplicity:** results for Stage 2 variants other than the named primary carry no pass/fail claim.

## Judge choice and second-judge check (added)
Primary judge: Gemma-2-9B-it 4-bit (MLX), greedy, cached. Reasons: a different model family from every writer (Qwen wrote Set A, Llama wrote Set B, Mistral writes Set C), and it runs locally and repeatably on the 16 GB Mac. No earlier head-to-head judge comparison exists in this project; this section adds one.
Second judge: Meta-Llama-3.1-8B-Instruct 4-bit, same audit prompt, same quote check, same order-swap and prompt-reword consistency checks. Qwen is not used as a judge (it is the extractor and wrote Set A). Mistral is not used as a judge (it writes Set C).
Stage 1: run V3 with each judge on dev/val and log both in `trial_log.csv`.
Stage 2: V3 is run once with each judge on Set C. The Gemma run stays the primary result unless the choice of judge is written into `frozen_variants.json` before Set C exists. Both are reported.
Descriptive outcome (H9): V3 catch rate and routed share of harmless reports with each judge, and the share of reports where the two judges route differently. No pass/fail. If the two judges disagree on H1 or H2, report both and do not pick the better one afterwards.

## Fresh data (untouched)
- Set C: scans never used in any earlier set (check against all earlier case ids). New writer: Mistral-7B-Instruct 4-bit (different from Qwen and Llama). Same error types and harmless rewordings. Size: at least 400 planted errors of major or critical severity (by field weight), plus matched harmless rewordings; at least 30 groups per organ or mark "too small to compare". Reason: an upper 95% bound of 2% on the miss rate needs about 250 such errors with at most 1 miss, about 400 with at most 3 misses (Clopper-Pearson).
- Set R: the 30 real Qwen-VL reports with existing human answers (descriptive only).

## Severity source (fix)
In Step 46 the scorer used the planted severity label when a case had one (`severity_for` in `step46_eval.py`). That is label leakage. In Step 47 every variant takes severity only from field weights (`extract.WEIGHTS`: weight >= 3 critical, 2 major, else minor) and never reads the planted label. The planted label is used only to define outcomes. The Step 46 H7 result (Spearman -0.97) is circular and is marked so in an added note to Step 46 results; its verdict line is not rewritten.

## Variants
- V0: Step 46 UScore as run (judge fills the clean case). Baseline.
- V1: rules only. No rule difference = 1.0, otherwise max(0, 1 - sum of severity penalties 0.6/0.3/0.1).
- V2: V1 + holistic judge only as a flag (never lowers a clean score below 0.8).
- V3 (PRIMARY): audit-and-route. Rules decide. Judge audits and must return exact quotes; code checks each quote appears in the report (invalid quote = ignored). Labels: major, minor, unsure. Report goes to radiologist if: rules find a major difference, OR judge says major with valid quote, OR unsure (judge order-swap disagreement, prompt-reword disagreement, invalid quote, or rule/judge disagreement). Every routed report carries its reason.
- V4: V3 without the unsure route (ablation).
- V5: V1 with differences merged by clinical concept before penalising. Concepts: size = {size_mm, size_pct, size}; head circumference = {hc_mm, hc_abs_mm}; one penalty per concept, at the highest severity among its hits. (The code already merges by field name; V5 merges across names.)
- V6: V1 without the zero floor. Score = 1 / (1 + sum of penalties). Same penalties, monotone, so many-error reports stay ranked instead of all collapsing to 0.0.
- Comparators: CRQS (signed code form), BLEU, ROUGE-L, chrF, BERTScore, RaTEScore, Step 45 learned scorer.

## Hypotheses (V3 primary)
- H1: miss rate = planted major or critical errors that V3 auto-passes / all planted major or critical errors. Pass if the one-sided upper 95% Clopper-Pearson bound is <= 2%, AND the routed share of harmless reports is <= 30%. (Replaces an earlier wording, share of errors among auto-passed reports, which depends on how many errors the set contains.)
- H2: at the same routed share as V3, V3 catches more planted errors than CRQS and each word scorer, paired group-bootstrap CI excluding 0.
- H3: AUROC of V1 on Set C >= 0.90 (does Step 46's exploratory 0.990 survive a new writer).
- H4: limit of detection: 5% size and 1 mm head circumference, AUROC >= 0.80 each.
- H5: every routed report has a non-empty reason, and 100% of quoted evidence is valid (code-checked).
- H6 (descriptive): Set R, V3 against the human answers, count only; no pass/fail.
- H7 (descriptive): CRQS vs V1 on Set C versus on templated test (does the CRQS ceiling drop on new free text).
- H9 (descriptive): second-judge check, defined in the judge section above.
- H8 (descriptive): V5 and V6 each versus V1, paired AUROC difference with CI. No pass/fail.

## Extractor hand check (added)
Before any Set C score is computed, 50 Set C reports (stratified: organ x error/harmless, fixed seed 0) are exported to `handcheck_setC.csv` with the extractor v5 fields beside the report text. Faviana or Harshal mark each field correct or wrong, blind to the scores. Reported: field accuracy with CI, per organ. If field accuracy is below 90%, every Set C result is labelled "extractor not validated on this text". This sheet does not change any variant.

## Reporting
Group bootstrap 1,000 seed 0, groups under 30 marked too small. State plainly: model-written free text, no clinician validation of labels; radiologist-written reports are still needed.

## Novelty claim allowed only if
H1 or H2 passes on fresh data. If not, the paper's contribution is the controlled meta-evaluation plus the negative findings (judge floor flaw, CRQS ceiling and sign inconsistency), not a new scorer.
