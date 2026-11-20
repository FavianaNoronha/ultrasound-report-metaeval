# Step 45: improving scorers without human grading

Pre-registered before results. The free-text evaluation uses Qwen2.5-7B-Instruct reports with automatic gold, on a smaller set than planned. These are writer-made reports, not clinician-written text or clinical validation. Detailed results: [Part A](../step45_improve_scorers/freetext/results.md), [B](../step45_improve_scorers/extractor/results.md), [C](../step45_improve_scorers/partC/results.md), [D](../step45_improve_scorers/partD/results.md), [E](../step45_improve_scorers/partE/results.md), [F](../step45_improve_scorers/partF/results.md), [G](../step45_improve_scorers/partG/results.md).

## Results

- **A, free-text set:** generated with automatic gold; the set is smaller than the preregistered target.
- **B, extractor v5: PASS.** Full-report match: breast 98.1%, thyroid 98.7%, fetal head 100%; v4 ties in two organs.
- **C, number checker: PASS.** AUROC 1.00 at 5% size change and 1 mm head-circumference change, with 0% harmless reports flagged; near-ceiling by construction.
- **D, claim-by-claim Gemma judge: DOES NOT PASS.** At the val-fixed threshold, catch is 8.9% (95% CI 4.0–14.4) versus the 71.3% bar; variant agreement is 100%. The sampled run completed after resuming from saved replies; 349 of 350 test pairs parsed, with one c1 response still unparsed after retry.
- **E, learned scorer: PASS.** Set A AUROC 0.895 versus 0.750 for the best single scorer; the gain comes from regex difference features.
- **F, hybrid: PASS on the complete test set.** Catch is 100% (185/185) with 5.0% harmless flagged (95% CI 3.0–7.3), versus 71.4% catch for the judge alone; paired catch gain +28.6 points (95% CI 22.4–35.5). The rules alone catch all planted errors and flag 0.9% of harmless reports.
- **G, pretrained U-Net / MedSAM: DOES NOT PASS.** Pretrained U-Net position AUROC is 0.905 (95% CI 0.877–0.930), below 0.92; its paired difference from random-init is +0.013 (95% CI −0.007 to +0.034). MedSAM prompted by the U-Net box scores 0.895.

Parts D and F initially reached their compute caps, then resumed from saved replies to complete the planned calls; this exceeded the original per-run caps. D retains one unparsed response. G's one test evaluation was not repeated.
