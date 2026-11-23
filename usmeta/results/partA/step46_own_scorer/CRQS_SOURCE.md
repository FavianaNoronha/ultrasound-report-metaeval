# CRQS source audit

Checked 2026-11-21 against PathReportEval v1 and the authors' PathBench repository.

## Paper definition

Singh et al., “PathReportEval: A Systematic Benchmark for Pathology Report Generation,” arXiv:2607.18448v1, Section 3.4, Eqs. (2)–(8):

- `CFC` is the fraction of reference-present clinical fields correctly recovered.
- `KIR` is the fraction of key fields present in the reference that are correctly recovered.
- `HR` is the fraction of generated fields unsupported by the reference or with a non-equivalent value.
- `CDS` is the fraction of fields present in both reports whose values disagree.
- The paper defines `CRQS_raw = 0.30*CFC + 0.40*KIR + 0.20*(1-HR) + 0.40*(1-CDS)`, then `CRQS = CRQS_raw / 0.70`.

Exact equation text (Eq. 6): `CRQS_raw = w1*CFC + w2*KIR + w3*(1-HR) + w4*(1-CDS)`.
Exact normalization (Eq. 8): `CRQS = CRQS_raw / 0.7`.

The paper states this normalized score is in `[0,1]`. Under the displayed equations the raw score ranges from 0 (CFC=KIR=0, HR=CDS=1) to 1.30 (CFC=KIR=1, HR=CDS=0), so the normalized score ranges from 0 to about 1.86. The 0.70 denominator equals the maximum only of the signed-penalty form (+0.3 CFC +0.4 KIR -0.2 HR -0.4 CDS) used in the released code. The displayed formula also cannot give a negative value, so it cannot produce the negative example in the notes. (Corrected 2026-11-22: an earlier version of this note gave a maximum of 1.00 and a floor of 0.60 for the displayed formula; both were arithmetic errors.)

## Authors' implementation

Repository: `https://github.com/surykntsingh/PathBench`

Commit inspected: `a110a98bc912bdf8daa561138ef0ef41a8235b02` (HEAD on 2026-11-21).

The dataset-specific `compute_metrics.py` implementations use signed penalty weights, yielding `CRQS_raw = 0.30*CFC + 0.40*KIR - 0.20*HR - 0.40*CDS`, followed by division by `0.70`. This is algebraically different from the paper's displayed Eq. (6), because the paper writes the last two terms as `+ weight*(1-rate)`. The code does allow negative scores: for example, if `CFC=KIR=0` and `HR=CDS=1`, raw is `-0.60` and normalized is approximately `-0.857`.

Exact implementation excerpt from `crqs/crqs_histai/src/compute_metrics.py` at the inspected commit:

```python
raw = (
    CRQS_WEIGHTS["CFC"] * cfc
    + CRQS_WEIGHTS["KIR"] * kir
    + CRQS_WEIGHTS["HR"] * hr
    + CRQS_WEIGHTS["CDS"] * cds
)
norm = raw / CRQS_MAX_RAW
```

The corresponding `crqs/crqs_histai/src/config.py` comment gives `CRQS_raw = 0.3*CFC + 0.4*KIR - 0.2*HR - 0.4*CDS`; the configured weights are `0.3`, `0.4`, `-0.2`, `-0.4`, and `CRQS_MAX_RAW` is `0.7`.

The repository's implementation sets empty-denominator rates to `0.0` (CFC, KIR, HR, or CDS as applicable) and returns both raw and normalized values. Therefore, it also does not guarantee a `[0,1]` output. The paper equation, signed-code equation, and stated range are inconsistent. The example negative score is compatible with the code's signed-penalty implementation, not with the displayed paper equation. The specific `-0.07` example from the prior notes was not independently located in the paper HTML during this audit.

## Step 46 implementation decision

Per the preregistration, preserve the authors' code-defined signs and weights for the primary CRQS adaptation, and report the raw score plus normalized score without clipping. Also report a `[0,1]`-clipped sensitivity version. Document that this choice follows the released code rather than the paper's printed Eq. (6); do not silently reconcile the inconsistency or alter weights.

The ultrasound field mapping follows the committed Step 46 preregistration: CFC is matched reference fields; KIR is matched key fields; HR counts candidate fields absent from the reference; CDS is a binary flag for any mismatched key field. These are the preregistered ultrasound definitions and differ from PathBench's full pathology-field HR/CDS denominators. The signed code weights are retained unchanged.

## Sources

- Paper: https://arxiv.org/abs/2607.18448 (v1, submitted 2026-07-20); Section 3.4, Eqs. (2)–(8).
- Paper HTML: https://arxiv.org/html/2607.18448v1
- Repository: https://github.com/surykntsingh/PathBench/tree/a110a98bc912bdf8daa561138ef0ef41a8235b02
- Code formula and weights: `crqs/crqs_histai/src/compute_metrics.py`, `crqs/crqs_histai/src/config.py`; the same pattern is used in dataset-specific CRQS implementations.
