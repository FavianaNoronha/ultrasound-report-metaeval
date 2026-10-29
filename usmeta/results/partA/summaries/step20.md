# Step 20 — Tolerance-aware image check (optional): does allowing for MedSAM's own measurement error cut the false alarms?

Plan, written and committed before any evaluation: `PLAN.md`. Tuned on dev/val only (`tuning_devval.md`: 214 breast + thyroid dev/val cases; chosen size tolerance **τ = 0.3 (30% relative)**, position **adjacent** (one third of the image counts as the same place)). Evaluated **once** on the test split with the Step 16 masks (MedSAM prompted by boxes from the TRUE masks, exact box). Code: `usmeta/step20.py` (`layer3.py` unchanged). The exact-match column is the Step 16 rule (τ = 0, position exact).

## Headline (breast + thyroid pooled, test, n = 228 cases)
- **Correct reports score higher:** mean score of an identical (correct) report **0.852 → 0.937**; share of correct reports scoring a full 1.0 **0.07 → 0.59**.
- **Catching planted errors did not get worse; it went up a little:** AUROC (all checkable) 0.91 (0.89–0.93) → 0.93 (0.92–0.95); position errors 0.95 (0.92–0.97) → 0.97 (0.95–0.99); size errors 0.86 (0.82–0.89) → 0.90 (0.87–0.92).
- **Plan outcome: held** (identical mean rose by ≥ 0.05 and AUROC did not fall by more than 0.03).
- **The identical-copy mean is still below 1.0 (0.937).** That is expected for any check that reads a predicted mask (the reference facts came from the true mask); it is a finding, not a bug. With true masks it is 1.000 (Step 8).
- **Fetal head:** the tolerance moves HC18 from 0.46 (0.43–0.49) to 0.67 (0.64–0.70) and FetalHead from 0.50 (0.48–0.52) to 0.67 (0.63–0.71), but only because a 30% band swallows MedSAM's systematic skull-versus-brain bias (the identical mean jumps from ~0.00 to 0.73 and 0.61); the planted head-circumference errors (3, 10, 30 mm) are small in relative terms (about 1–15%), so a 30% band cannot separate them well (AUROC only 0.67). It does not show that image checks work on fetal head.

## Important limit: this tolerance hides small errors
The planted size errors in this benchmark are large (×0.5, ×1.5, ×2), so a 30% band still sees them. A size error of 3 mm on a 10–15 mm nodule is 20–30% (the kind of change that crosses a TI-RADS cut-off, Step 18) and would fall inside the band: **the tolerance-aware check cannot see decision-relevant small size errors.** MedSAM's own median size error on BrEaST malignant lesions is 2 mm (13%, Step 18 H3), so the band is about twice MedSAM's typical error. Do not use this check to judge threshold-level size claims.

## Test results per dataset (n = cases; † n < 30: too small to compare)
| dataset | check | n correct reports | identical mean | share scoring 1.0 | AUROC all checkable | position errors | size errors |
|---|---|---|---|---|---|---|---|
| **breast + thyroid pooled** | exact-match (Step 16 rule) | 228 | 0.852 | 0.07 | 0.91 (0.89–0.93) | 0.95 (0.92–0.97) (n=134) | 0.86 (0.82–0.89) |
| **breast + thyroid pooled** | tolerance-aware (tau=0.3, adjacent) | 228 | 0.937 | 0.59 | 0.93 (0.92–0.95) | 0.97 (0.95–0.99) (n=134) | 0.90 (0.87–0.92) |
| BrEaST | exact-match (Step 16 rule) | 30 | 0.894 | 0.20 | 0.93 (0.88–0.97) | 0.97 (0.91–1.00) (n=17) | 0.88 (0.78–0.96) |
| BrEaST | tolerance-aware (tau=0.3, adjacent) | 30 | 0.966 | 0.73 | 0.96 (0.93–0.98) | 1.00 (1.00–1.00) (n=17) | 0.93 (0.88–0.98) |
| BUS-BRA | exact-match (Step 16 rule) | 30 | 0.865 | 0.03 | 0.91 (0.86–0.95) | 0.94 (0.85–1.00) (n=17) | 0.83 (0.73–0.91) |
| BUS-BRA | tolerance-aware (tau=0.3, adjacent) | 30 | 0.968 | 0.53 | 0.93 (0.90–0.96) | 0.94 (0.85–1.00) (n=17) | 0.87 (0.81–0.93) |
| BUSI | exact-match (Step 16 rule) | 30 | 0.894 | 0.10 | 0.95 (0.91–0.98) | 0.92 (0.84–1.00) (n=19) | 0.93 (0.84–1.00) |
| BUSI | tolerance-aware (tau=0.3, adjacent) | 30 | 0.970 | 0.83 | 0.97 (0.94–0.98) | 0.97 (0.92–1.00) (n=19) | 0.96 (0.91–0.99) |
| UDIAT | exact-match (Step 16 rule) | 30 | 0.943 | 0.10 | 0.98 (0.96–1.00) | 1.00 (1.00–1.00) (n=23) | 0.98 (0.95–1.00) |
| UDIAT | tolerance-aware (tau=0.3, adjacent) | 30 | 0.985 | 0.83 | 0.98 (0.96–1.00) | 1.00 (1.00–1.00) (n=23) | 0.98 (0.95–1.00) |
| BUS-UCLM † | exact-match (Step 16 rule) | 18 | 0.871 | 0.00 | 0.95 (0.87–0.99) | 1.00 (1.00–1.00) (n=8) | 0.91 (0.76–1.00) |
| BUS-UCLM † | tolerance-aware (tau=0.3, adjacent) | 18 | 0.948 | 0.67 | 0.96 (0.93–0.99) | 1.00 (1.00–1.00) (n=8) | 0.94 (0.87–1.00) |
| TN3K | exact-match (Step 16 rule) | 30 | 0.824 | 0.03 | 0.89 (0.84–0.93) | 0.94 (0.85–1.00) (n=17) | 0.84 (0.74–0.92) |
| TN3K | tolerance-aware (tau=0.3, adjacent) | 30 | 0.910 | 0.47 | 0.92 (0.88–0.95) | 0.99 (0.96–1.00) (n=17) | 0.88 (0.82–0.94) |
| DDTI | exact-match (Step 16 rule) | 30 | 0.715 | 0.00 | 0.82 (0.75–0.88) | 0.84 (0.72–0.97) (n=16) | 0.69 (0.59–0.80) |
| DDTI | tolerance-aware (tau=0.3, adjacent) | 30 | 0.826 | 0.20 | 0.85 (0.80–0.90) | 0.86 (0.74–0.98) (n=16) | 0.76 (0.67–0.85) |
| TN5000 | exact-match (Step 16 rule) | 30 | 0.822 | 0.10 | 0.88 (0.83–0.93) | 0.97 (0.91–1.00) (n=17) | 0.82 (0.72–0.89) |
| TN5000 | tolerance-aware (tau=0.3, adjacent) | 30 | 0.926 | 0.50 | 0.91 (0.86–0.94) | 1.00 (1.00–1.00) (n=17) | 0.86 (0.79–0.92) |
| HC18 | exact-match (Step 16 rule) | 30 | 0.006 | 0.00 | 0.46 (0.43–0.49) | — | 0.46 (0.43–0.49) |
| HC18 | tolerance-aware (tau=0.3, adjacent) | 30 | 0.732 | 0.57 | 0.67 (0.64–0.70) | — | 0.67 (0.64–0.70) |
| FetalHead | exact-match (Step 16 rule) | 30 | 0.003 | 0.00 | 0.50 (0.48–0.52) | — | 0.50 (0.48–0.52) |
| FetalHead | tolerance-aware (tau=0.3, adjacent) | 30 | 0.613 | 0.30 | 0.67 (0.63–0.71) | — | 0.67 (0.63–0.71) |

## Dev/val tuning table (breast + thyroid, 214 cases; objective J = ½ (AUROC + identical mean))
| tau | position | identical mean | share 1.0 | AUROC (all checkable) | J |
|---|---|---|---|---|---|
| 0.0 | exact | 0.866 | 0.11 | 0.918 (0.901–0.934) | 0.892 |
| 0.0 | adjacent | 0.881 | 0.11 | 0.918 (0.901–0.935) | 0.899 |
| 0.1 | exact | 0.894 | 0.30 | 0.925 (0.909–0.940) | 0.910 |
| 0.1 | adjacent | 0.908 | 0.31 | 0.926 (0.910–0.941) | 0.917 |
| 0.2 | exact | 0.915 | 0.44 | 0.930 (0.915–0.944) | 0.922 |
| 0.2 | adjacent | 0.929 | 0.47 | 0.930 (0.915–0.945) | 0.930 |
| 0.3 | exact | 0.929 | 0.59 | 0.932 (0.918–0.945) | 0.931 |
| 0.3 | adjacent | 0.943 | 0.64 | 0.933 (0.919–0.946) | 0.938 |
| 0.4 | exact | 0.937 | 0.67 | 0.916 (0.902–0.929) | 0.926 |
| 0.4 | adjacent | 0.951 | 0.71 | 0.917 (0.903–0.930) | 0.934 |
| 0.5 | exact | 0.942 | 0.72 | 0.880 (0.870–0.890) | 0.911 |
| 0.5 | adjacent | 0.956 | 0.77 | 0.880 (0.870–0.890) | 0.918 |

Chosen on dev/val: tau=0.3, position=adjacent, J=0.938

## Limits
Boxes come from the true masks (easy case, as in Step 16); 30 scans per dataset (BUS-UCLM 18), at most 3 per group; the tolerance was tuned on a small dev/val sample (214 cases); planted size errors are large; MedSAM may have seen these datasets (unverifiable); the identical-copy rule (must be 1.0) cannot hold for a predicted-mask check. See `docs/LIMITATIONS.md`.
