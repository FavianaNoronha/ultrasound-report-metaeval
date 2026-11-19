# Step 45 (PRE-REGISTRATION): making the scorers better without human grading

Written 2026-11-19, before any Step 45 number exists. Additions only; frozen files untouched; tune on dev/val; read test once via `usmeta.splits.load("test")`; group bootstrap 1,000 resamples, seed 0; cells under 30 groups = "too small to compare"; judge and writer from different model families.

## Why this step is shaped the way it is (read first)
On our templated benchmark the regex `finding_f1` already flags every planted error and 0% of harmless rewordings (Step 44: its catch is capped only by the audit budget). So **a better fact extractor or number checker cannot show any gain on templated text**: it is already at the ceiling there. The open weakness is **free text** (Step 43: 2/20). Therefore every claim below is tested on a new free-text set whose gold facts are known automatically, with no human grader.

## A. Free-text test set with automatic gold (needed for B, C, F)
- Writer: Qwen2.5-7B-Instruct (not Gemma, not the judge family). For each case in a fixed sample (dev+val: 600 cases for building and tuning; test: 600 cases, group-disjoint), the writer gets only the structured facts (the same fields the template uses) and writes a natural radiologist-style report in 3 styles (terse, narrative, impression-first). Temperature 0.7, seed fixed, prompts saved.
- Gold = the supplied facts. A deterministic, independent check (lexicon of synonyms + exact numbers, NOT the extractor under test) keeps only reports that state every gold value; dropped share is reported. Writer drops/changes are therefore removed, not charged to the extractor.
- Each kept report also gets a planted-error twin (one field changed in the facts, same writer) so catch and false-alarm rates can be measured on free text.
- Caveat to state: writer-made free text is a proxy for real radiologist or VLM text; it does not replace a clinician-written set.

## B. Extractor v5 (item 1)
Per-organ strict schema; breast scale (BI-RADS) allowed only on breast; thyroid TI-RADS only on thyroid; fetal head only HC and plane; JSON-constrained output; regex values override the model for numbers, sides and counts.
- Metric: full-report exact field match and per-field accuracy on set A (test), against v4 on the same reports.
- **Pass: full-report match >= 0.85 for each of breast, thyroid, fetal head (lower 95% bound >= 0.75), and v4 lower on the same reports.**

## C. Deterministic number checker (item 2)
Parses size (mm/cm, percent change), head circumference, count and side; flags a mismatch beyond a tolerance fixed on dev/val.
- Metric: limit of detection as in Step 35 (smallest planted size/HC change with AUROC >= 0.80 against matched rewordings) on set A twins.
- **Pass: reaches 0.80 at 5% size change and 1 mm head circumference (the judge's Step 35 level), with <= 2% of harmless rewordings flagged.**

## D. Claim-by-claim judge (item 3) — needs a GPU/Mac
Gemma-2-9B-it 4-bit (same as Steps 12/39): split the candidate into claims, verify each against the reference, then score; two prompt variants.
- Metric: catch of planted errors and harmless flagged at the val-fixed threshold, on the same judge test subset as Step 44; flag agreement between the two variants.
- **Pass: catch >= 71.3% with harmless flagged <= 5.6% (Step 44 holistic judge) and variant flag agreement >= 90% (Step 44 ensembles: 82-87%).**

## E. Small learned scorer (item 4)
Features: existing scorer outputs (BLEU, ROUGE-L, chrF, BERTScore, RaTEScore) plus diff features (numbers added/removed/changed, negation words, side words). Logistic regression and gradient boosting; trained on dev, tuned on val, group-disjoint. Wording-only perturbations are used as negatives.
- Metric: error-vs-harmless AUROC on set A test (distribution shift away from templates) and on the templated test.
- **Pass: AUROC on set A test at least 0.05 above the best single existing text scorer, CI of the paired difference excluding 0. If it only wins on templated text it is reported as template overfitting.**

## F. Tuned hybrid (item 6; this is the never-run Step 34 hybrid idea)
Flag if (extractor v5 or number checker finds a mismatch) else send to the judge; thresholds on val to hold harmless flagged <= 5.6%.
- **Pass: catch on set A test >= 80% at harmless flagged <= 5.6%, beating the judge alone on the same candidates, CI of the paired difference excluding 0.**

## G. Better image side (item 5) — needs a GPU/Mac
Same U-Net as Step 29 but with ImageNet-pretrained ResNet-18 weights; also MedSAM prompted by the U-Net box.
- Metric: position AUROC on the same 498 usable test scans as Step 40, paired against the random-init model.
- **Pass: pooled position AUROC >= 0.92 (Step 40: 0.89) and the paired difference CI excludes 0. Thyroid reported separately (Step 40: 0.79).**

## Reporting
Every item is reported whether it passes or not. A pass on set A is "better on writer-made free text", not "clinically validated". Step 28 stays inconclusive unless real-writer text is re-scored. No "first" claims. Dataset licences stay "to confirm".
