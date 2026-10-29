# Step 20 — tolerance-aware image check: plan (written 2026-10-29, BEFORE any test evaluation; optional step)

**Question.** The Step 16 check compares a report's size / position claims to the facts measured from MedSAM's predicted mask with a strict rule, so a correct report loses points when MedSAM is a little off (mean 0.68, only 0–20% of correct breast/thyroid reports scored 1.0). Does a check that tolerates MedSAM's own measurement error keep catching planted errors while giving correct reports fewer false alarms?

**Check (new file `usmeta/step20.py`; `layer3.py` stays frozen).** Same claims and same measurements as `layer3.mask_verified` (lesion, count, image position, orientation, size / head circumference), same prompts (boxes from the TRUE mask; exact box only). Two tolerances:
- size: relative error d = |claim − measured| / measured; credit = max(0, 1 − max(0, d − τ) / 0.5). τ = 0 is the Step 16 rule.
- position (e.g. "upper-central"): credit 1 if equal; with `adjacent` also 1 if only one component differs by one step (one third of the image); otherwise 0. Planted position errors flip a component by two steps, so they stay wrong.
Score = mean credit over the report's checkable claims (1.0 if none), as in Step 16.

**Tuning on dev/val only.** MedSAM is run on dev/val scans (exact box, ≤30 scans per dataset, ≤3 per group, seed 1, cases that are in `bench_v2d`). Grid: τ ∈ {0, 0.1, 0.2, 0.3, 0.4, 0.5} × position ∈ {exact, adjacent}. Objective, on breast + thyroid pooled (fetal head excluded because its failure is an annotation mismatch, not noise): J = ½ (AUROC of all mask-checkable planted errors vs harmless rewordings + mean score of identical copies). The (τ, position) with the highest J is frozen. Ties → the smaller τ.

**Evaluation once on test.** The Step 16 test masks (exact box, 288 scans), the frozen (τ, position). Report next to the exact-match check (τ = 0, exact): identical-copy mean, share of correct reports scoring 1.0, AUROC (all checkable, position, size) per dataset and pooled, group-bootstrap CIs, n, † n < 30. Fetal head reported separately and expected not to improve.

**Held / failed.** Held if on test breast + thyroid pooled: identical mean rises by ≥ 0.05 and AUROC (all checkable) falls by ≤ 0.03 (point estimates, CI reported). Failed if the identical mean does not rise or AUROC falls by more than 0.03. Otherwise "partly".

**Caveats stated now.** Boxes come from the true masks (easy case); the tolerance is tuned on a small dev/val sample; planted size errors are large (×0.5 to ×2), so a tolerance of up to 0.3 may look free here but would hide the small, threshold-relevant errors of Step 18; MedSAM may have seen these datasets.
