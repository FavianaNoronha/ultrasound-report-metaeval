# Step 11: Qwen2.5-VL-3B real reports through Layers 1-3 (locked TEST split)

**Possible training exposure, unverifiable.** Qwen2.5-VL-3B may have seen BUS-BRA, TN3K, TN5000 and HC18 during training; its model card lists no training data (see `step10f_contamination`), and the memorisation probe found nothing, which is a probe, not proof. Limitations: [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md). Frozen code (`freeze-v1`) was not edited; new files `qwen_real.py`, `qwen_real_analysis.py`.

**What was run.** The 200 Qwen reports (50 per dataset: BUS-BRA, TN3K, TN5000, HC18; **BrEaST has no Qwen report yet**) and the 20 flip-test reports, each against the true (templated) report of the same case from `true_reports_v2d`. Final numbers use only the cases in the **test split: 73 reports (BUS-BRA 21, HC18 14, TN3K 22, TN5000 16) + 10 flipped test reports**; dev/val reports (127) were used only for the extractor check and the box-parsing check. Extractor and judge are **Gemma-2-9B (a different family from the writer)**. The Qwen markdown (headings, bold, list numbers) was stripped before extraction and judging (no content removed). Group-level 95% CI (1,000 resamples; in these test sets every case is its own group), n is 14-22 per dataset, so intervals are wide.

**Extractor check first (the 85% stop rule) -- passed, with a weak yardstick.** Free-text reports have no gold labels, so I compared the Gemma LLM extractor with independent regex readings (side words, BI-RADS regex, mm/cm sizes, "no abnormality" phrases) on 40 dev/val reports (10 per dataset), restricted to fields the schema has for that organ: **37 of 41 comparisons agree = 90.2%** (side 10/10, BI-RADS 9/9, size 8/9, lesion present/absent 10/13); 0 unparseable, 2 values dropped because their quote was not in the text. A first, unfair version counted regex hits on fields the schema does not have (57%): not an extractor error. By hand I read 8 extractions: 2 had errors (a size read as 106 mm for "10.6 mm"; a composite option string "solid|cystic" copied as a value); position phrases like "upper outer quadrant" are kept as written and cannot match our image-thirds vocabulary. On the 83 test reports: 0 unparseable, 7 values dropped (quote missing). The proxy is small (41 comparisons) and not a labelled test; real agreement is unknown.

## Layer 1: structured facts (LLM extractor + `finding_f1`) vs the true facts
Test, mean (95% CI): BUS-BRA precision 0.27 / recall 0.23 / F1 0.24 (0.22-0.27); TN3K 0.29 / 0.20 / 0.23; TN5000 0.23 / 0.20 / 0.21; HC18 0 / 0 / 0.
**These look very low for a mostly structural reason:** the true report states 9 attributes for BUS-BRA (presence, count, image position, orientation, size, side, BI-RADS, pathology, histology), 5 for the thyroid sets and 1 for HC18, while the Qwen report states a different set in different words. Recall of exactly 0.20 on TN3K/TN5000 means "only the presence of a nodule is stated" (1 of 5 reference attributes); HC18 is 0 because Qwen never gives a head circumference. Read the per-attribute table, not the F1.
Per attribute (reference attribute vs what the report states; test):
| dataset | attribute | correct | wrong | not stated | not comparable (other unit / vocabulary) |
|---|---|---|---|---|---|
| BUS-BRA (21) | lesion presence | 21 | 0 | 0 | |
| | side | 16 | 4 | 1 | |
| | BI-RADS | 6 | 15 | 0 | |
| | image position (thirds) | 0 | 0 | 5 | 16 (quadrant wording) |
| | size, count, orientation, pathology, histology | 0 | pathology 1, histology 1 | 20-21 each | size (% of width) vs cm |
| TN3K (22) | lesion presence | 22 | 0 | 0 | |
| | count, orientation, size, position | 0 | 0 | 21-22 | position 1 |
| TN5000 (16) | lesion presence | 16 | 0 | 0 | |
| | count, orientation, size, position | 0 | 0 | 12-16 | position 4 |
| HC18 (14) | head circumference | 0 | 0 | 14 | |
Qwen's BI-RADS agrees with the label in 6 of 21 BUS-BRA reports (29%). Lesion presence counts as "correct" for every thyroid and breast report because the frozen extractor marks a lesion present whenever any lesion attribute is found; it cannot show a miss.

## Layer 2: Gemma `sentence_check` (prompt_v2 main, prompt_v1 for comparison), test
`sentence_f1` v2 / v1 (mean, CI): BUS-BRA 0.27 (0.17-0.36) / 0.57 (0.50-0.64); TN3K 0.18 (0.10-0.27) / 0.47 (0.40-0.53); TN5000 0.22 (0.14-0.29) / 0.50 (0.43-0.56); HC18 0.80 (0.71-0.87) / 0.77 (0.68-0.83). `judge_score` (error list) v2: 0.00 for BUS-BRA, TN3K, TN5000, 0.06 HC18: **the judge lists at least one error in 100% of reports** (mean 6.9 errors per report with prompt_v2, 4.1 with v1). **The two prompts disagree by 0.2-0.3 on the breast and thyroid sets** (v2 stricter: a report sentence must be supported by the reference; v1 more lenient), so no single judge number is safe. HC18's high `sentence_f1` is not skill: the reference has two short sentences and the judge treats generic fetal-head statements as supported.
Error types the judge named (prompt_v2, counts over test reports): BUS-BRA false finding 78, wrong measurement 22, wrong location 21, missed finding 14, wrong severity/category 12; TN3K false finding 70, missed finding 31, wrong measurement 8, wrong location 6, wrong category 5; TN5000 false finding 82, missed finding 30, wrong measurement 9, wrong location 4; HC18 false finding 94, missed finding 14, wrong severity/category 2. So the dominant "mistake" in free text is unsupported extra content ("false finding": findings the reference does not contain), a category that our single-planted-error benchmark under-represents. One v2 reply was unparseable (missing, not zero); 36 of 83 (v2) and 28 of 83 (v1) replies had a wrong-length true/false list.

## Layer 3: Qwen boxes vs the true masks / boxes (test)
Qwen2.5-VL was asked for a JSON box of the lesion ("Locate the breast lesion / thyroid nodule / fetal head ... bounding box in JSON"); coordinates are absolute on the resized input and were rescaled. **103 of 103 outputs parsed** (20 dev scans checked first), so the "30% unparseable" stop rule did not apply. Mean box IoU (best match) with the true box, CI: **BUS-BRA 0.21 (0.15-0.28), 10% of scans IoU >= 0.5; TN3K 0.30 (0.18-0.41), 23%; TN5000 0.12 (0.06-0.20), 0%; HC18 0.77 (0.69-0.83), 93%.** Pixel recall 0.79-0.96 but pixel precision 0.14-0.71 (boxes are large and cover the lesion plus much else); share of boxes with >= 50% inside the true box region: BUS-BRA 0.10, TN3K 0.50, TN5000 0.06, HC18 0.93. So the model finds the fetal head but mostly not the small breast and thyroid lesions.
**Do text scores reward reports from a model that looked in the wrong place?** Spearman of text score vs box IoU per dataset (n = 14-22): BLEU -0.37 (BUS-BRA), +0.31 (TN3K), -0.08 (TN5000), -0.18 (HC18); `finding_f1` -0.09, -0.32, -0.22; `sentence_f1` v2 -0.05, n/a, +0.01, +0.23. No consistent relation and n is small, so no conclusion; at least nothing here shows the text scores track location quality.

## Flip test (10 flipped test scans)
Facts that should not change under a mirror (everything but side and position): the share of extracted attributes that stay identical is 0.43-1.00 per scan (BUS-BRA 0.43 and 0.50, TN3K 0.43 / 1.0 / 1.0, TN5000 0.75 and 0.60, HC18 1.0 on three scans, which state almost nothing). In one BUS-BRA scan the stated side changed with the flip (as a position-aware model would), in the other it did not. Boxes mirrored back and compared with the original-orientation boxes: IoU 0.91, 0.04, 0.05, 0.99, 0.71, 0.15, 0.94, 0.35, 0.86, 0.80, i.e. 6 of 10 agree (IoU >= 0.5). The report wording also changes a lot under a flip (Step 3: BLEU between original and flipped 0.48-0.54). The model is not a stable function of the anatomy on these scans.

## Per error type, summary
- **False finding (unsupported content): most frequent** (judge: 70-94 per dataset).
- **Missed finding:** 14-31 per dataset; thyroid reports often describe a diffuse gland and no nodule at the true location.
- **Wrong location:** side wrong 4 of 20 (BUS-BRA); box IoU < 0.5 on 90% of BUS-BRA, 77% TN3K, 100% TN5000; right for HC18.
- **Wrong measurement:** head circumference never stated; sizes in cm not comparable with the template's % of image width (a limitation of our references, not necessarily of the model).
- **Wrong category:** BI-RADS right in 6 of 21 BUS-BRA reports.

**Caveats (keep visible).** Templated true reports (not clinician text) are compared with free text, so vocabulary and level-of-detail mismatches inflate "not stated"; `finding_f1` was built for templated text; n = 14-22 per dataset; the extractor yardstick is a 41-comparison proxy; Gemma is the extractor and judge (prompt-sensitive); results are per dataset and say nothing about real clinical quality; BrEaST not included; MedGemma and LLaVA-Med not run.
