# Step 47 (PRE-REGISTRATION): audit-and-route scorer, fixed variants, one run on fresh data

Written 2026-11-23, before any Step 47 number. Step 46 stays reported as is (H1/H2/H4 DOES NOT PASS).

## Why
Step 46 post-hoc check: UScore AUROC 0.656 as scored, 0.990 if reports with no rule difference get 1.0 instead of the holistic judge score (exploratory, 861 items). Cause: judge floor on harmless rewordings. CRQS 0.998 shares the extractor with the gold fields, so on templated cases it is close to circular. Open question: what holds on free text we did not build and on real reports.

## Rules against cherry-picking
1. Variants below are fixed now. No variant is added, tuned or dropped after seeing fresh-data numbers.
2. Any threshold or weight is chosen on dev/val only, then frozen in a file with a hash before fresh data is generated.
3. Fresh data is read once. All variants are reported, failures included. Report the number of variants tried.
4. Primary comparison is ONE variant (V3), named now. Others are secondary and get no pass/fail claim.

## Fresh data (untouched)
- Set C: scans never used in any earlier set (check against all earlier case ids). New writer: Mistral-7B-Instruct 4-bit (different from Qwen and Llama). Same error types and harmless rewordings. Size: at least 300 cases, at least 30 groups per organ or mark "too small to compare".
- Set R: the 30 real Qwen-VL reports with existing human answers (descriptive only).

## Variants
- V0: Step 46 UScore as run (judge fills the clean case). Baseline.
- V1: rules only. No rule difference = 1.0, otherwise 1 - severity penalties.
- V2: V1 + holistic judge only as a flag (never lowers a clean score below 0.8).
- V3 (PRIMARY): audit-and-route. Rules decide. Judge audits and must return exact quotes; code checks each quote appears in the report (invalid quote = ignored). Labels: major, minor, unsure. Report goes to radiologist if: rules find a major difference, OR judge says major with valid quote, OR unsure (judge order-swap disagreement, prompt-reword disagreement, invalid quote, or rule/judge disagreement). Every routed report carries its reason.
- V4: V3 without the unsure route (ablation).
- Comparators: CRQS (signed code form), BLEU, ROUGE-L, chrF, BERTScore, RaTEScore, Step 45 learned scorer.

## Hypotheses (V3 primary)
- H1: among reports auto-passed, share with a planted major or critical error <= 1% (upper CI bound <= 2%), while routed share of harmless reports <= 30%.
- H2: at the same routed share as V3, V3 catches more planted errors than CRQS and each word scorer, paired group-bootstrap CI excluding 0.
- H3: AUROC of V1 on Set C >= 0.90 (does Step 46's exploratory 0.990 survive a new writer).
- H4: limit of detection: 5% size and 1 mm head circumference, AUROC >= 0.80 each.
- H5: every routed report has a non-empty reason, and 100% of quoted evidence is valid (code-checked).
- H6 (descriptive): Set R, V3 against the human answers, count only; no pass/fail.
- H7 (descriptive): CRQS vs V1 on Set C versus on templated test (does the CRQS ceiling drop on new free text).

## Reporting
Group bootstrap 1,000 seed 0, groups under 30 marked too small. State plainly: model-written free text, no clinician validation of labels; radiologist-written reports are still needed.

## Novelty claim allowed only if
H1 or H2 passes on fresh data. If not, the paper's contribution is the controlled meta-evaluation plus the negative findings (judge floor flaw, CRQS ceiling and sign inconsistency), not a new scorer.
