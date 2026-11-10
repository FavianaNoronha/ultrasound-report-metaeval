# Step 28: natural-error validity test (Qwen2.5-VL-3B reports, test split)

Limitations: [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md). Code: `usmeta/step28_natural_errors.py`, `step28_report.py` (new files; `generate.py` writer prompt, `schema.py`, `graders.py`, `judge2*.py` imported unchanged). Test-split access is logged in `results/partA/test_access.log` (script `usmeta.step28_natural_errors`). Extractor and cache: Step 27 (Qwen2.5-7B, same prompt).

**Question.** On the mistakes a real writer makes (not planted ones), do the scorers track the real factual errors, or only how similar the text looks?

## Decision line

**On these reports the scorers track surface similarity and completeness, not real mistakes (indicative: the extractor that labels the mistakes was 56% right on breast and thyroid reports in the hand check, so the labels are noisy; see the hand-check section).** Separating reports with at least one wrong key fact from fully correct ones (AUROC, 1.0 = perfect, 0.5 = chance; 97 checkable reports, 40 with a wrong key fact): BLEU 0.41 (0.30–0.53), ROUGE-L 0.40 (0.28–0.54), chrF 0.33 (0.21–0.46), BERTScore 0.18 (0.11–0.27), RaTEScore 0.41 (0.30–0.53), `llm_finding_f1` 0.59 (0.47–0.71), Gemma `sentence_f1` 0.58 (0.47–0.69). None is clearly above chance and BERTScore and chrF are below it (a report with a wrong key fact scores higher). Gemma `judge_score` cannot be assessed: it is 0.00 for 171 of 179 reports (the penalties exceed 1.0 for almost every free-text report), so it has no spread. The positive rank correlations with fact F1 (word scorers 0.33–0.54 in breast, intervals around 0 in thyroid) come from completeness and length (a report that states more of the reference facts shares more words), not from correctness. `llm_finding_f1` correlates 0.97–1.00 with fact F1 because both use the same extractor (built in, not an independent check), yet it does not separate wrong from correct reports either, because it rewards stating a fact as much as getting it right.

## What was measured

- **Writer and sample.** Qwen2.5-VL-3B with the frozen writer prompt (`generate.PROMPT`, greedy, `torch.manual_seed(0)`). **180 test images, 60 per organ (the brief asked for 100; reduced to stay inside the 3 h cap, since the writer needs about 35 s per image)**: breast 12 each from BrEaST, BUS-BRA, BUSI, UDIAT, BUS-UCLM; thyroid 20 each from TN3K, TN5000, DDTI; fetal head 30 each from HC18, FetalHead. One image per patient/group. 74 reports were reused from Steps 11/14 (same writer, same prompt, original images), 106 were generated now.
- **Truth.** The label facts of the reference (`true_reports_v2d` facts). **Factual accuracy** = fact-level F1 (`schema.finding_scores`, same credit rules) between the Step 27 extracted facts of the report and the label facts. **Key facts** (those in the labels): presence, side (breast with a side label), size, category (BI-RADS, TI-RADS, pathology) and, for fetal head, head circumference and plane. A key fact is *stated* if the report gives a checkable value, *wrong* if it is stated and disagrees (size: relative error above 25%, i.e. fact credit below 0.5). A report is *wrong* if at least one stated key fact is wrong and *fully correct* if at least one key fact is stated and none is wrong; reports that state no key fact are left out of the AUROC (not counted as correct).
- **Scores.** Every report against the REFERENCE text: BLEU, ROUGE-L, chrF, BERTScore (roberta-large), RaTEScore, `llm_finding_f1` (Step 27 extractor on both texts, unchanged comparer), Gemma judge (prompt_v2). The writer text is cleaned of markdown first (`qwen_real.clean_md`, as in Step 11).
- **Statistics.** Spearman and Kendall between each scorer and fact F1; AUROC wrong vs fully correct (ties 0.5); 95% CI by bootstrap over images (1,000, seed 0; one image per group, so images are groups).

## What the writer got right and wrong (key facts, per organ)

| key fact | in labels | stated by the report | correct of stated |
|---|---|---|---|
| breast.birads | 24 | 24 | 3 (12%) |
| breast.path | 60 | 28 | 16 (57%) |
| breast.presence | 60 | 60 | 50 (83%) |
| breast.side | 12 | 12 | 10 (83%) |
| breast.size | 48 | 11 | 3 (27%) |
| fetal.hc | 60 | 0 | 0 |
| fetal.plane | 30 | 0 | 0 |
| thyroid.presence | 60 | 37 | 35 (95%) |
| thyroid.size | 59 | 0 | 0 |
| thyroid.tirads | 16 | 10 | 7 (70%) |

Fetal head: the writer states neither head circumference nor plane in any of the 60 reports, so no fetal-head report is checkable and **fetal head cannot be assessed here** (its fact F1 is 0.00 for all 60). Thyroid: 37 of 60 reports state a checkable key fact (mostly presence), only 5 are wrong, so every thyroid wrong-vs-correct cell is **too small to compare** (†). Breast: BI-RADS is right in 3 of 24 stated, size in 3 of 11 stated; 35 of 60 breast reports have a wrong key fact.

## Scorer vs factual accuracy and vs wrong key facts

| scorer | organ | images | Spearman with fact F1 | Kendall | AUROC wrong vs fully correct (n) |
|---|---|---|---|---|---|
| BLEU | breast | 60 | 0.33 (0.03–0.60) | 0.25 (0.04–0.46) | 0.50 (0.36–0.64) (60) |
| BLEU | thyroid | 60 | 0.15 (-0.14–0.41) | 0.11 (-0.11–0.32) | 0.55 (0.32–0.77) † (37) |
| BLEU | fetal head | 60 | — | — | — |
| BLEU | pooled | 180 | 0.66 (0.53–0.77) | 0.52 (0.43–0.60) | 0.41 (0.30–0.53) (97) |
| ROUGE-L | breast | 60 | 0.48 (0.19–0.71) | 0.37 (0.16–0.56) | 0.44 (0.29–0.59) (60) |
| ROUGE-L | thyroid | 60 | 0.19 (-0.09–0.46) | 0.15 (-0.06–0.36) | 0.63 (0.34–0.87) † (37) |
| ROUGE-L | fetal head | 60 | — | — | — |
| ROUGE-L | pooled | 180 | 0.70 (0.58–0.80) | 0.56 (0.47–0.64) | 0.40 (0.28–0.54) (97) |
| chrF | breast | 60 | 0.54 (0.26–0.77) | 0.44 (0.22–0.62) | 0.34 (0.20–0.49) (60) |
| chrF | thyroid | 60 | 0.16 (-0.11–0.40) | 0.13 (-0.08–0.32) | 0.30 (0.09–0.56) † (37) |
| chrF | fetal head | 60 | — | — | — |
| chrF | pooled | 180 | 0.67 (0.55–0.78) | 0.55 (0.45–0.64) | 0.33 (0.21–0.46) (97) |
| BERTScore | breast | 60 | 0.51 (0.27–0.72) | 0.38 (0.21–0.54) | 0.26 (0.15–0.40) (60) |
| BERTScore | thyroid | 60 | 0.15 (-0.14–0.39) | 0.10 (-0.12–0.29) | 0.35 (0.05–0.67) † (37) |
| BERTScore | fetal head | 60 | — | — | — |
| BERTScore | pooled | 180 | 0.49 (0.36–0.60) | 0.37 (0.27–0.45) | 0.18 (0.11–0.27) (97) |
| RaTEScore | breast | 60 | 0.44 (0.13–0.67) | 0.34 (0.11–0.54) | 0.53 (0.37–0.67) (60) |
| RaTEScore | thyroid | 60 | 0.01 (-0.24–0.24) | 0.00 (-0.17–0.18) | 0.53 (0.11–0.89) † (37) |
| RaTEScore | fetal head | 60 | — | — | — |
| RaTEScore | pooled | 180 | 0.33 (0.18–0.47) | 0.26 (0.14–0.36) | 0.41 (0.30–0.53) (97) |
| llm_finding_f1 * | breast | 60 | 0.97 (0.91–1.00) | 0.95 (0.86–1.00) | 0.61 (0.45–0.75) (60) |
| llm_finding_f1 * | thyroid | 60 | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) † (37) |
| llm_finding_f1 * | fetal head | 60 | — | — | — |
| llm_finding_f1 * | pooled | 180 | 1.00 (0.99–1.00) | 0.99 (0.97–1.00) | 0.59 (0.47–0.71) (97) |
| Gemma judge_score ** | breast | 60 | — | — | 0.50 (60) |
| Gemma judge_score ** | thyroid | 59 | — | — | 0.50 † (37) |
| Gemma judge_score ** | fetal head | 60 | — | — | — |
| Gemma judge_score ** | pooled | 179 | -0.19 (-0.26–-0.13) | -0.17 (-0.23–-0.11) | 0.50 (97) |
| Gemma sentence_f1 | breast | 60 | 0.37 (0.14–0.60) | 0.29 (0.11–0.48) | 0.67 (0.52–0.81) (60) |
| Gemma sentence_f1 | thyroid | 59 | 0.15 (-0.18–0.39) | 0.11 (-0.15–0.31) | 0.43 (0.11–0.79) † (37) |
| Gemma sentence_f1 | fetal head | 60 | — | — | — |
| Gemma sentence_f1 | pooled | 179 | -0.10 (-0.23–0.05) | -0.07 (-0.17–0.05) | 0.58 (0.47–0.69) (97) |

`*` shares the extractor with the accuracy measure, so its correlation with fact F1 is partly built in. `**` 171 of 179 values are 0.00 (floor), so its correlations are not meaningful. † fewer than 30 reports in the wrong class (thyroid 5) or no checkable report (fetal head): too small to compare. The pooled rows mix organs with very different fact F1 and text length (fetal head is 0.00 fact F1 with very short reports), so the pooled Spearman is partly an organ effect; read the per-organ rows.

Share of reports with a wrong key fact / stating no key fact: breast 58% / 0%, thyroid 8% / 38%, fetal head 0% / 100%. Mean fact F1: breast 0.29, thyroid 0.17, fetal head 0.00.

## Extractor check on these free-text reports

Parse failures: 0 of 180. Agreement of the Qwen7B extractor with the independent regex reading used in Step 11 (`qwen_real.regex_reading`), where both state a value:

| field | both stated | agree | regex or LLM silent |
|---|---|---|---|
| breast.birads | 59 | 100% | 1 |
| breast.lesion | 50 | 96% | 10 |
| breast.side | 48 | 100% | 12 |
| breast.size_mm | 53 | 98% | 7 |
| thyroid.lesion | 31 | 81% | 29 |
| thyroid.size_mm | 7 | 100% | 53 |

## Hand check of the extractor on these reports (done by the owner)

`docs/step28_check.csv`: 30 random reports (seed 0) with the extracted facts, marked right / wrong by hand. **22 of 30 right (73%, 95% Wilson interval 56-86%).** By organ: breast 4 of 7, thyroid 6 of 11, fetal head 12 of 12. The 12 fetal-head extractions are right only because they are empty (the writer states nothing checkable); **on the 18 breast and thyroid reports it is 56% right (34-75%)**, so the extractor is much less reliable on free text than on templated text (dev: 0.96-1.00).

The 8 wrong extractions, in the owner's words (`hand_check.json`): a normal thyroid read as lesion present (C07), multiple hypoechoic areas read as lesion absent (C15), "multiple nodules" read as count 3 (C08, C23), "hypoechoic" put in composition (C08, C23, C30), pathology "malignant" inferred from "potential malignancy / biopsy recommended" (C14, C25), a halo "no" that is not in the report (C24, C25), and a lobulated / irregular margin read as "circumscribed" (C25). They are mostly **invented or over-read fields**, not misread numbers. Several of the same kind of error sit in the key facts used for "wrong key fact" (presence, pathology, category), so some reports are labelled correct or wrong by the extractor rather than by the writer.

What this does to the result: the wrong-vs-correct labels are noisy, which pushes every scorer's AUROC towards 0.5 (including `llm_finding_f1`, which shares the extractor) and widens the real uncertainty beyond the bootstrap intervals shown. It cannot explain scorers below chance on its own, but the decision line should be read as **indicative on breast; thyroid and fetal head do not carry it**. The regex cross-check on four simple fields agrees with the extractor (BI-RADS 100% of 59, side 100% of 48, size 98% of 53, breast presence 96% of 50) but thyroid presence only 81% of 31, matching the hand check.

## Caveats

- **Reduced to 60 images per organ** (brief: 100), because of the 3 h cap; fetal head has no checkable report and thyroid only 37 (5 wrong), so the wrong-vs-correct result rests on breast (60 images: 35 wrong, 25 correct) and is pooled with the small thyroid cell.
- **Truth comes from the labels, accuracy from an LLM extractor.** Extraction mistakes enter both fact F1 and the "wrong key fact" flag, and `llm_finding_f1` shares them. The hand check (30 reports) bounds this: 73% right overall, 56% on breast and thyroid.
- **Key facts are those the labels have.** BUSI and several datasets have no side or BI-RADS label, thyroid labels give size only as a % of image width (the writer never states it), so the key-fact set differs by dataset.
- **One writer, small open model (3B, fp16 on MPS), one prompt, one machine.** Possible training exposure to public ultrasound sets, unverifiable. The writer text is long markdown against one-sentence references, so all word-overlap scores are very low (mean BLEU 0.007) and mostly reflect length and format.
- **Judge:** prompt_v2 as frozen (not tuned). `judge_score` is floored at 0 by its penalty rule (0.6 / 0.3 / 0.1 per error) on long reports with several errors; this is a property of the frozen scorer, reported as is.
- 60 groups per organ; the 74 reused reports come from Steps 11/14 and were not regenerated.
