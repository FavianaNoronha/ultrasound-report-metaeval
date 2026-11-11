# Step 32: stricter free-text extractor (extractor v3) and the Step 28 metrics re-run

**PROVISIONAL until the owner fills `docs/step32_check.csv`** (30 reports, hand check of the v3 extractions). Nothing in this file is hand-verified for v3. Limitations: [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md). Code: `usmeta/step32_extractor_v3.py`, `step32_report.py` (new files; `step27_extractor.py`, `step28_natural_errors.py` imported unchanged; the v3 calls are cached separately). Prompt version **v3** is logged in `CHANGELOG.md`.

## What changed (extractor v3)

Only the instruction text. Same model (Qwen2.5-7B-Instruct, 4-bit, greedy), same dev-only few-shot examples, same JSON schema and the same JSON-to-facts mapping and comparer as Step 27. New instruction (full text in `usmeta/step32_extractor_v3.py`): fill a key only with a fact **explicitly stated**, null otherwise; never infer pathology (a BI-RADS / TI-RADS category, "suspicious", "biopsy recommended" are not a stated pathology), halo, calcifications, posterior features, count ("multiple" is null) or composition (echogenicity words are echo, never composition); presence rules for breast (`lesion_present` true / false / null) and thyroid (count 0 only if "no nodule" is stated).

## Re-validation on the templated dev and val sets (criterion: field agreement >= 0.98)

| set | reports | field agreement pooled | breast | thyroid | fetal head | all fields right per report (breast / thyroid / fetal head) | parse failures |
|---|---|---|---|---|---|---|---|
| dev | 300 | 0.9975 | 0.9981 | 0.9960 | 1.0000 | 0.97 / 0.96 / 1.00 | 0 |
| val | 300 | 0.9986 | 0.9981 | 0.9990 | 1.0000 | 0.97 / 0.99 / 1.00 | 0 |

**Criterion PASSED** (every organ x set >= 0.98). For reference, v2 on the same 300-report dev sample: mean per-field agreement breast 0.9975, thyroid 0.9990, fetal head 1.0000; all fields right per report 0.96 / 0.99 / 1.00. Known facts = the rule extractor on the templated text; the val set is a fresh draw of 100 reports per organ (seed 0, val split). The remaining dev/val misses are listed in `validation.json` (for example thyroid "echogenic foci" read as an echo pattern, and a side read from "upper left part of the image").

## The owner's Step 28 hand check, replayed with v3 (diagnostic only; not a v3 hand check)

For each of the 8 extractions the owner marked wrong for v2, the field(s) named in the owner's note, with the v2 value, the v3 value, and what the owner said. "Fixed" means the v3 value is the one the note implies is correct (null for an invented field); this is read from the note, not re-verified.

| id | organ | field | v2 value | v3 value | owner note (v2) |
|---|---|---|---|---|---|
| C07 | thyroid | lesion | present | present | lesion marked present, but report describes a normal thyroid with no abnormality/lesion |
| C07 | thyroid | count | None | None | lesion marked present, but report describes a normal thyroid with no abnormality/lesion |
| C08 | thyroid | count | 3 | None | count 3 not in report (only says multiple nodules); comp set to hypoechoic, but that is echogenicity, report g |
| C08 | thyroid | comp | hypoechoic | None | count 3 not in report (only says multiple nodules); comp set to hypoechoic, but that is echogenicity, report g |
| C14 | breast | path | malignant | None | path malignant not stated; report only says potential malignancy, biopsy recommended |
| C15 | thyroid | lesion | absent | present | lesion marked absent, but report describes multiple hypoechoic areas (cysts or solid nodules) |
| C23 | thyroid | count | 3 | None | count 3 not in report (only says multiple nodules); comp set to hypoechoic, but that is echogenicity, report g |
| C23 | thyroid | comp | hypoechoic | None | count 3 not in report (only says multiple nodules); comp set to hypoechoic, but that is echogenicity, report g |
| C24 | breast | halo | no | None | halo no not mentioned in report |
| C25 | breast | path | malignant | None | path malignant not stated (suspicious mass, biopsy recommended); halo no not mentioned; margin circumscribed c |
| C25 | breast | halo | no | None | path malignant not stated (suspicious mass, biopsy recommended); halo no not mentioned; margin circumscribed c |
| C25 | breast | margin | circumscribed | circumscribed | path malignant not stated (suspicious mass, biopsy recommended); halo no not mentioned; margin circumscribed c |
| C30 | thyroid | comp | hypoechoic | None | comp set to hypoechoic, but that is echogenicity, report gives no composition |

Of the 10 breast / thyroid extractions the owner marked right for v2, 7 change under v3 (fields changed: C01 echo: hypoechoic -> None, tirads: 4 -> None, lesion: present -> absent; C02 echo: hypoechoic -> heterogeneous; C04 count: None -> 1; C10 comp: heterogeneous -> None; C12 margin: well-defined -> None; C19 count: None -> 1, margin: well defined -> well-defined; C26 echo: hypoechoic -> heterogeneous, comp: heterogeneous -> None, count: None -> 1). Any change among these needs the new hand check to say whether v3 lost a stated fact or removed a wrong one.

## Step 28 metrics re-run on the same 180 reports (60 per organ), v2 vs v3

Same reports, same word / embedding / judge scores (saved Step 28 scores); only the extractor changes, and with it `llm_finding_f1` **and the labels** (fact F1, stated / wrong key facts), because Step 28 reads the truth comparison through the extractor. AUROC for separating reports with at least one wrong key fact from fully correct ones (95% CI by image bootstrap): v2 pooled 40 wrong of 97 checkable, v3 pooled 36 wrong of 102 checkable.

| scorer | AUROC wrong vs correct, v2 (pooled) | v3 (pooled) | v2 breast | v3 breast | Spearman with fact F1, v2 pooled | v3 pooled |
|---|---|---|---|---|---|---|
| BLEU | 0.41 (0.30–0.53) | 0.42 (0.29–0.55) | 0.50 (0.36–0.64) | 0.50 (0.36–0.65) | 0.66 (0.53–0.77) | 0.70 (0.57–0.79) |
| ROUGE-L | 0.40 (0.28–0.54) | 0.43 (0.29–0.57) | 0.44 (0.29–0.59) | 0.46 (0.30–0.62) | 0.70 (0.58–0.80) | 0.72 (0.60–0.81) |
| chrF | 0.33 (0.21–0.46) | 0.29 (0.15–0.43) | 0.34 (0.20–0.49) | 0.31 (0.15–0.47) | 0.67 (0.55–0.78) | 0.70 (0.59–0.80) |
| BERTScore | 0.18 (0.11–0.27) | 0.15 (0.08–0.23) | 0.26 (0.15–0.40) | 0.25 (0.12–0.39) | 0.49 (0.36–0.60) | 0.47 (0.34–0.57) |
| RaTEScore | 0.41 (0.30–0.53) | 0.45 (0.33–0.58) | 0.53 (0.37–0.67) | 0.57 (0.42–0.72) | 0.33 (0.18–0.47) | 0.32 (0.17–0.45) |
| llm_finding_f1 | 0.59 (0.47–0.71) | 0.60 (0.47–0.72) | 0.61 (0.45–0.75) | 0.57 (0.41–0.73) | 1.00 (0.99–1.00) | 1.00 (0.99–1.00) |
| judge sentence_f1 | 0.58 (0.47–0.69) | 0.53 (0.42–0.65) | 0.67 (0.52–0.81) | 0.62 (0.47–0.77) | -0.10 (-0.23–0.05) | -0.17 (-0.31–-0.03) |
| judge_score | 0.50 | 0.50 | 0.50 | 0.50 | -0.19 (-0.26–-0.13) | -0.21 (-0.28–-0.14) |

| organ | metric | v2 | v3 |
|---|---|---|---|
| breast | reports with a wrong key fact / stating no key fact | 58% / 0% | 50% / 3% |
| breast | mean fact F1 | 0.29 | 0.28 |
| breast | checkable / wrong / fully correct | 60 / 35 / 25 | 58 / 30 / 28 |
| thyroid | reports with a wrong key fact / stating no key fact | 8% / 38% | 10% / 27% |
| thyroid | mean fact F1 | 0.17 | 0.23 |
| thyroid | checkable / wrong / fully correct | 37 / 5 / 32 | 44 / 6 / 38 |
| fetal | reports with a wrong key fact / stating no key fact | 0% / 100% | 0% / 100% |
| fetal | mean fact F1 | 0.00 | 0.00 |
| fetal | checkable / wrong / fully correct | 0 / 0 / 0 | 0 / 0 / 0 |
| ALL | reports with a wrong key fact / stating no key fact | 22% / 46% | 20% / 43% |
| ALL | mean fact F1 | 0.15 | 0.17 |
| ALL | checkable / wrong / fully correct | 97 / 40 / 57 | 102 / 36 / 66 |

Per-field stated / correct counts (v3) are in `results.json`. The Gemma `judge_score` is floored at 0.00 on almost every free-text report (as in Step 28), so its row carries no information.

## What can and cannot be concluded

- v3 keeps the templated-text agreement (>= 0.98 on dev and val): the stricter prompt did not cost accuracy on the text it was tuned on.
- Whether v3 is **more accurate on free text** is **not known**: the replay above reads the owner's v2 notes, not a v3 hand check. `docs/step32_check.csv` (30 fresh reports: 12 breast, 12 thyroid, 6 fetal head; none of the 30 reports of the Step 28 check) is waiting for the right / wrong marks; until then every v3 free-text number here is **provisional**, and a result that moves with the extractor is a statement about the extractor and the labels, not about the scorers.
- The Step 28 decision (scorers track similarity and completeness, not mistakes; inconclusive) is not changed by this file; see the pooled AUROC columns above and judge them only after the hand check.

## Caveats

- Same 180 reports, same writer, same scorers: only the extractor changed. Labels depend on the extractor, so v2 and v3 AUROCs are not independent estimates of the scorers.
- Thyroid presence cannot be read from a missing field (count null and no attributes maps to "absent"), a mapping unchanged from Step 27; fetal head has no checkable key fact in these reports.
- One extractor model, one prompt change, greedy decoding. Possible training exposure of Qwen is unverifiable.
