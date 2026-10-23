# FROZEN (freeze-v1)

Frozen 2026-10-24 at git 94de056 (the tag `freeze-v1` is placed on the commit that adds this file). Anything below that changes after this point must be a NEW version (v2, ...) with a note in `CHANGELOG.md` saying what changed and why; the old version and its results are kept. Tuning of any kind uses dev and val only; final numbers come from the locked test split via `usmeta.splits.load("test")`.

| group | file | SHA-256 | what |
|---|---|---|---|
| templates | `usmeta/templates_v2.py` | `4883715ee63cf8fc...` | true-report templates v2 (3 styles, provenance) |
| schema + extractors | `usmeta/schema.py` | `63621bd3664011e9...` | finding schema, rule extractor, local-LLM extractor, finding_f1 |
| benchmark builders | `usmeta/bench_v2.py` | `5bdd888baa1e2304...` | planted errors + severity rules (provisional) |
| benchmark builders | `usmeta/bench_v2b.py` | `d19d6ad2eb18ec7a...` | harmless split + matched one-word synonym group |
| benchmark builders | `usmeta/bench_loc.py` | `bafae38676222cb6...` | box / location extension |
| scorers | `usmeta/graders.py` | `4780818b9d2bc2f5...` | bleu, rougeL, chrf, bertscore (roberta-large), ratescore (use_gpu=False -> mps), local judge classes |
| scorers | `usmeta/layer0.py` | `53981c115df40fa7...` | AUROC / bootstrap machinery |
| scorers | `usmeta/layer0b.py` | `bb233ed672c48c20...` | analysis with small / matched / large harmless |
| scorers | `usmeta/layer1.py` | `f5ff36289acb9dc3...` | finding_f1 scoring |
| scorers | `usmeta/judge2.py` | `f9ef13d5efd9331c...` | sentence_check; PROMPT_V1 and PROMPT_V2 (stricter) live here |
| scorers | `usmeta/judge2_report.py` | `1c2235853bab1644...` | judge analysis |
| scorers | `usmeta/location.py` | `54790ea0609a467a...` | IoU, Dice, Hungarian, mask loaders |
| scorers | `usmeta/layer3.py` | `626635761a1f27c1...` | location_check, grounded_check, mask_verified_facts, semacc, box_support |
| splits | `usmeta/splits.py` | `0835989433a937c6...` | grouped dev/val/test + guarded loader |
| data | `splits.jsonl` | `be1904128ac1e50f...` | case -> group -> split |
| data | `bench_v2d.jsonl` | `d95cbd38be2dd7d2...` | benchmark (dev-era sample, 150 cases per dataset) |
| data | `true_reports_v2d.jsonl` | `e24f3368b5f743d3...` | true reports |
| data | `bench_loc.jsonl` | `98d8602b9f513fe5...` | location benchmark |
| data | `duplicates.jsonl` | `aaa873a57d19ddb1...` | near-duplicate pairs |

## Judge prompts (Gemma-2-9B-it 4-bit via MLX, greedy, max 500 new tokens)

- **prompt_v1 (first Step 7 run)**: SHA-256 `9e67bb78014b4b5d...`
- **prompt_v2 (stricter, identical copies must get 1.0)**: SHA-256 `608412841d3fa256...`

## Settings that are part of the freeze
- Layer 0: sacrebleu defaults (BLEU effective order, chrF), own ROUGE-L, BERTScore roberta-large (layer default, MPS), RaTEScore 0.6.0 (Angelakeke/RaTE-NER-Deberta, FremyCompany/BioLORD-2023-C, MPS).
- Layer 1: finding_f1 credit rules (size: linear to 0 at 50% relative error; head circumference: linear to 0 at 20 mm; categories exact). LLM extractor: gemma-2-9b-it-4bit, quoted evidence required, normalisation map in `schema._norm_llm`.
- Layer 2: judge penalties critical 0.6 / major 0.3 / minor 0.1 (`graders.PENALTY`); sentence_check precision/recall from true/false lists.
- Layer 3: location_check = Hungarian best-match box IoU; grounded_check = finding_f1 x location_check; mask_verified credit >= 0.5 counts as backed; support rule >= 50% of the box inside the true region.
- Bootstrap: 1,000 resamples, seed 0; to be resampled at GROUP level on the test split (Step 10d).
- **Threshold rule (for detection / robustness and flag rates, Step 8b):** the threshold of a scorer is the score cut-off that flags 90% of planted errors on the VAL split (flag = score below the cut-off); it is then applied unchanged to test. Calibration (if any) is fitted on val.

Rebuild this file with `python3 -m usmeta.frozen`.
