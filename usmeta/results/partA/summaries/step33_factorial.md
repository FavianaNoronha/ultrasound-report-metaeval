# Step 33: 2x2 factorial, fact x wording

Limitations: [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md). Pre-registration (committed before any cell (d) score or test number): [PREREG.md](PREREG.md). Code: `usmeta/step33_factorial.py`, `step33_factorial_report.py` (new files; frozen `bench_v2.errors`, `templates_v2.render`, saved test scores and the scorer classes imported unchanged). Test split read once, logged (`usmeta.step33_factorial`).

**Design.** Four cells per reference (breast and thyroid test references): (a) no error, small edit (existing `small` + `matched` harmless), (b) no error, large edit (existing style swaps), (c) error, small edit (existing planted error), (d) **error, large edit (new): the same planted error rendered in the large style** (the frozen large-rewording generator applied to the erroneous report; the regex extractor must show the planted value, else the candidate is dropped). Unit = block (reference, error, large style) with four scores; the two-way variance decomposition splits the score variance into fact, wording, interaction and residual (within-cell spread across references and errors).

## Decision line (pre-registered: "fact-driven" if eta-squared(fact) > eta-squared(wording), pooled breast + thyroid)

**Fact-driven: finding_f1 (upper bound), judge_score, judge sentence_f1. Wording-driven: BLEU, ROUGE-L, chrF, BERTScore, RaTEScore.** BLEU fact 0.02 vs wording 0.60; ROUGE-L fact 0.02 vs wording 0.41; chrF fact 0.04 vs wording 0.27; BERTScore fact 0.02 vs wording 0.41; RaTEScore fact 0.04 vs wording 0.17; finding_f1 (upper bound) fact 0.26 vs wording 0.00; judge_score fact 0.68 vs wording 0.01; judge sentence_f1 fact 0.55 vs wording 0.01.

**What the AUROCs add.** At matched large wording the word scorers do separate an error from a correct text (AUROC (d vs b): BLEU 0.97, ROUGE-L 0.89, chrF 0.97, BERTScore 0.99, RaTEScore 0.77), because an error adds its own changes on top of the rewrite; at matched small wording they cannot (AUROC (c vs a): BLEU 0.69, ROUGE-L 0.53, chrF 0.51, BERTScore 0.44, RaTEScore 0.62). The clinically relevant reversal, an error with a small edit outranking a correct text in a large rewrite, happens in BLEU 76%, ROUGE-L 76%, chrF 76%, BERTScore 76%, RaTEScore 60% of (c, b) pairs and in judge_score 4%, judge sentence_f1 5% for the judge (capped subset, 71 groups).

Built: 17,444 (d) candidates kept of 17,452 attempted (8 dropped: error not shown by the regex extractor (size_pct) x8); 216 planted-error rows could not be regenerated from the frozen builder (histology errors) and are not in the factorial; blocks kept: breast 10,248, thyroid 7,196. The judge rows use the capped subset (239 blocks, at most 12 cases per dataset and 3 planted errors per case, all four cells judged).

## Variance decomposition (share of the total sum of squares; 95% bootstrap CI over reference groups)

| scorer | organ | blocks / groups | fact | wording | interaction | residual | fact - wording (CI) | verdict |
|---|---|---|---|---|---|---|---|---|
| BLEU | pooled | 17,444 / 830 | 0.02 (0.02–0.03) | 0.60 (0.58–0.62) | 0.00 | 0.38 | -0.57 (-0.59–-0.55) | wording-driven |
| BLEU | breast | 10,248 / 413 | 0.02 (0.02–0.03) | 0.58 (0.55–0.61) | 0.00 | 0.39 | -0.56 (-0.59–-0.52) | wording-driven |
| BLEU | thyroid | 7,196 / 417 | 0.02 (0.02–0.03) | 0.63 (0.62–0.64) | 0.00 | 0.35 | -0.60 (-0.61–-0.59) | wording-driven |
| ROUGE-L | pooled | 17,444 / 830 | 0.02 (0.02–0.03) | 0.41 (0.40–0.43) | 0.00 | 0.56 | -0.39 (-0.41–-0.37) | wording-driven |
| ROUGE-L | breast | 10,248 / 413 | 0.03 (0.02–0.03) | 0.42 (0.40–0.45) | 0.00 | 0.55 | -0.39 (-0.43–-0.36) | wording-driven |
| ROUGE-L | thyroid | 7,196 / 417 | 0.02 (0.02–0.03) | 0.41 (0.40–0.41) | 0.00 | 0.57 | -0.38 (-0.39–-0.38) | wording-driven |
| chrF | pooled | 17,444 / 830 | 0.04 (0.04–0.05) | 0.27 (0.25–0.28) | 0.00 | 0.69 | -0.23 (-0.24–-0.20) | wording-driven |
| chrF | breast | 10,248 / 413 | 0.04 (0.04–0.05) | 0.24 (0.22–0.26) | 0.00 | 0.71 | -0.20 (-0.23–-0.17) | wording-driven |
| chrF | thyroid | 7,196 / 417 | 0.04 (0.04–0.05) | 0.31 (0.30–0.32) | 0.00 | 0.65 | -0.27 (-0.28–-0.25) | wording-driven |
| BERTScore | pooled | 17,444 / 830 | 0.02 (0.02–0.02) | 0.41 (0.39–0.43) | 0.00 | 0.56 | -0.39 (-0.40–-0.37) | wording-driven |
| BERTScore | breast | 10,248 / 413 | 0.02 (0.02–0.03) | 0.36 (0.34–0.38) | 0.01 | 0.61 | -0.34 (-0.36–-0.32) | wording-driven |
| BERTScore | thyroid | 7,196 / 417 | 0.02 (0.02–0.02) | 0.49 (0.49–0.50) | 0.00 | 0.48 | -0.47 (-0.48–-0.46) | wording-driven |
| RaTEScore | pooled | 17,444 / 830 | 0.04 (0.03–0.04) | 0.17 (0.15–0.19) | 0.00 | 0.79 | -0.13 (-0.15–-0.11) | wording-driven |
| RaTEScore | breast | 10,248 / 413 | 0.05 (0.04–0.06) | 0.11 (0.09–0.12) | 0.00 | 0.84 | -0.06 (-0.08–-0.03) | wording-driven |
| RaTEScore | thyroid | 7,196 / 417 | 0.02 (0.02–0.03) | 0.32 (0.30–0.35) | 0.00 | 0.66 | -0.30 (-0.32–-0.27) | wording-driven |
| finding_f1 (upper bound) | pooled | 17,444 / 830 | 0.26 (0.25–0.27) | 0.00 (0.00–0.00) | 0.00 | 0.74 | 0.26 (0.25–0.27) | fact-driven |
| finding_f1 (upper bound) | breast | 10,248 / 413 | 0.23 (0.22–0.24) | 0.00 (0.00–0.00) | 0.00 | 0.77 | 0.23 (0.22–0.24) | fact-driven |
| finding_f1 (upper bound) | thyroid | 7,196 / 417 | 0.31 (0.30–0.32) | 0.00 (0.00–0.00) | 0.00 | 0.69 | 0.31 (0.30–0.32) | fact-driven |
| judge_score | pooled | 239 / 71 | 0.68 (0.63–0.73) | 0.01 (0.00–0.01) | 0.00 | 0.31 | 0.68 (0.62–0.73) | fact-driven |
| judge_score | breast | 120 / 41 | 0.65 (0.56–0.74) | 0.00 (0.00–0.01) | 0.00 | 0.35 | 0.65 (0.55–0.74) | fact-driven |
| judge_score | thyroid | 119 / 30 | 0.72 (0.67–0.77) | 0.02 (0.01–0.03) | 0.00 | 0.26 | 0.70 (0.64–0.75) | fact-driven |
| judge sentence_f1 | pooled | 239 / 71 | 0.55 (0.49–0.62) | 0.01 (0.01–0.02) | 0.00 | 0.43 | 0.54 (0.48–0.60) | fact-driven |
| judge sentence_f1 | breast | 120 / 41 | 0.51 (0.42–0.63) | 0.00 (0.00–0.00) | 0.00 | 0.49 | 0.51 (0.42–0.63) | fact-driven |
| judge sentence_f1 | thyroid | 119 / 30 | 0.60 (0.54–0.66) | 0.06 (0.04–0.07) | 0.00 | 0.34 | 0.54 (0.47–0.62) | fact-driven |

† = under 30 groups: too small to compare (judge rows). Interaction means the effect of an error depends on the wording (for example an error is hidden by a large rewrite).

## AUROC of error vs harmless at matched wording, and reversal rates (95% CI by group bootstrap, per-reference means)

| scorer | organ | AUROC (c vs a): error vs correct, small edits | AUROC (d vs b): error vs correct, large edits | reversal as specified: share of (d, a) pairs with d < a | clinically relevant reversal: share of (c, b) pairs with error+small ABOVE correct+large | share of (d, a) pairs with d above a |
|---|---|---|---|---|---|---|
| BLEU | pooled | 0.69 (0.66–0.71) | 0.97 (0.97–0.97) | 1.00 (1.00–1.00) | 0.76 (0.70–0.82) | 0.00 (0.00–0.00) |
| BLEU | breast | 0.69 (0.64–0.73) | 0.95 (0.95–0.96) | 1.00 (1.00–1.00) | 0.69 (0.61–0.78) | 0.00 (0.00–0.00) |
| BLEU | thyroid | 0.68 (0.67–0.69) | 0.99 (0.99–0.99) | 1.00 (1.00–1.00) | 0.86 (0.86–0.87) | 0.00 (0.00–0.00) |
| ROUGE-L | pooled | 0.53 (0.49–0.56) | 0.89 (0.88–0.90) | 0.99 (0.99–0.99) | 0.76 (0.70–0.82) | 0.01 (0.01–0.01) |
| ROUGE-L | breast | 0.55 (0.50–0.60) | 0.91 (0.90–0.92) | 1.00 (1.00–1.00) | 0.69 (0.61–0.78) | 0.00 (0.00–0.00) |
| ROUGE-L | thyroid | 0.49 (0.49–0.50) | 0.86 (0.86–0.87) | 0.98 (0.98–0.98) | 0.86 (0.85–0.86) | 0.02 (0.02–0.02) |
| chrF | pooled | 0.51 (0.47–0.55) | 0.97 (0.97–0.98) | 1.00 (1.00–1.00) | 0.76 (0.70–0.82) | 0.00 (0.00–0.00) |
| chrF | breast | 0.54 (0.47–0.60) | 0.96 (0.95–0.96) | 1.00 (1.00–1.00) | 0.69 (0.61–0.78) | 0.00 (0.00–0.00) |
| chrF | thyroid | 0.47 (0.46–0.48) | 1.00 (0.99–1.00) | 1.00 (1.00–1.00) | 0.86 (0.85–0.86) | 0.00 (0.00–0.00) |
| BERTScore | pooled | 0.44 (0.39–0.48) | 0.99 (0.99–1.00) | 1.00 (1.00–1.00) | 0.76 (0.70–0.82) | 0.00 (0.00–0.00) |
| BERTScore | breast | 0.46 (0.39–0.52) | 0.99 (0.99–1.00) | 1.00 (1.00–1.00) | 0.69 (0.61–0.78) | 0.00 (0.00–0.00) |
| BERTScore | thyroid | 0.40 (0.39–0.41) | 1.00 (0.99–1.00) | 1.00 (1.00–1.00) | 0.86 (0.85–0.86) | 0.00 (0.00–0.00) |
| RaTEScore | pooled | 0.62 (0.59–0.65) | 0.77 (0.75–0.79) | 0.88 (0.87–0.89) | 0.60 (0.54–0.65) | 0.12 (0.11–0.13) |
| RaTEScore | breast | 0.67 (0.63–0.70) | 0.81 (0.78–0.84) | 0.86 (0.85–0.88) | 0.53 (0.46–0.61) | 0.14 (0.12–0.15) |
| RaTEScore | thyroid | 0.55 (0.55–0.56) | 0.71 (0.70–0.71) | 0.90 (0.89–0.91) | 0.69 (0.68–0.70) | 0.10 (0.09–0.11) |
| finding_f1 (upper bound) | pooled | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) |
| finding_f1 (upper bound) | breast | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) |
| finding_f1 (upper bound) | thyroid | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) |
| judge_score | pooled | 0.98 (0.96–0.99) | 0.95 (0.92–0.98) | 0.96 (0.93–0.98) | 0.04 (0.01–0.07) | 0.01 (0.00–0.03) |
| judge_score | breast | 0.97 (0.94–0.99) | 0.94 (0.88–0.98) | 0.94 (0.89–0.97) | 0.05 (0.01–0.10) | 0.02 (0.01–0.05) |
| judge_score | thyroid | 1.00 (0.99–1.00) | 0.97 (0.93–1.00) | 0.98 (0.95–1.00) | 0.02 (0.00–0.05) | 0.00 (0.00–0.00) |
| judge sentence_f1 | pooled | 0.94 (0.91–0.96) | 0.94 (0.92–0.97) | 0.94 (0.91–0.97) | 0.05 (0.02–0.08) | 0.03 (0.01–0.05) |
| judge sentence_f1 | breast | 0.90 (0.86–0.94) | 0.97 (0.94–0.99) | 0.93 (0.88–0.96) | 0.04 (0.01–0.09) | 0.04 (0.02–0.08) |
| judge sentence_f1 | thyroid | 0.98 (0.95–1.00) | 0.91 (0.85–0.95) | 0.97 (0.93–1.00) | 0.05 (0.00–0.12) | 0.00 (0.00–0.00) |

The reversal share as specified (d below a) is expected to be high for **any** scorer that reacts to either factor, because (d) carries both an error and a large rewrite; it does not separate fact from wording. The clinically relevant reversal is the share of pairs where an error with a small edit outranks a harmless large rewrite (a wrong report scored better than a correct one in another wording); the last column is the share where the doubly changed text still scores above the correct small-edit text.

## Deviations from the pre-registration

- None in the design or decision rule. Implementation notes: histology errors cannot be regenerated from the frozen builder and are excluded (counted above); the judge subset is chosen with seed 0 among judged cases whose (a), (b), (c) were judged, so it may be smaller than 12 per dataset.

## Caveats

- **Templated text only.** (d) is the same error in the terse or long template; real paraphrases of an erroneous report are not tested. The regex extractor that verifies (d) reads the same template (it verifies the planted fact is present, not that the text reads naturally).
- **Block structure:** blocks share references and errors, so the bootstrap resamples reference groups, not blocks; the eta-squared shares also include the spread across error types and references in the residual.
- **Judge rows** use at most 12 cases per dataset (< 30 groups for several cells); the judge was run once with prompt_v2, greedy.
- `finding_f1` (regex) is an upper bound on templated text and is shown for reference.
