# Step 46: UScore versus CRQS

Pre-registered before scores; the held-out Set B reports were written by Llama-3.1-8B-Instruct with automatic gold. On 861 core test reports across 235 groups, CRQS scored AUROC **0.998** (95% CI 0.996-0.999) versus **0.656** (0.612-0.699) for UScore. The paired UScore-minus-CRQS difference is **-0.341** (-0.385 to -0.298), so CRQS clearly outperformed the current UScore on this controlled set. Step 45's learned scorer was 0.843 (0.808-0.875).

UScore misses its monitor rule at the Set A dev-val threshold: 18.1% error catch and 16.3% harmless flagged on Set B. The holistic judge's rule-clear subset had harmless reports only, making its AUROC not estimable. An exploratory rule-only change reaches 0.990 AUROC, but this was not preregistered. H1/H2/H4 do not pass. CRQS and UScore share extractor v5, and these generated reports are not clinical validation.

Full report: [Step 46 results](../step46_own_scorer/results.md). CRQS code/paper audit: [CRQS_SOURCE.md](../step46_own_scorer/CRQS_SOURCE.md).
