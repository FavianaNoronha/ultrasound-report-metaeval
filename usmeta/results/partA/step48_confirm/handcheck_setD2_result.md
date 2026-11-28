# Set D2 extractor hand check (pre-registered, before any Set D2 score)

- Sample: 30 Set D2 reports (Llama-3.1-8B writer), 5 per organ x {planted error, harmless}, seed 0; 133 extracted fields (handcheck_setD2.json).
- Reviewer: Faviana Noronha (one reviewer), phone checklist, completed 2026-11-28.
- Result: 133 / 133 fields marked correct (0 wrong). One-sided 95% Clopper-Pearson upper bound on the field error rate: 2.2%.
- Limits: one reviewer; checks copying of stated facts only, not clinical correctness; fabricated-finding sentences have no extractor field and are not covered by this check.
