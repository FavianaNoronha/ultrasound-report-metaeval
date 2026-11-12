# Step 37: RadGraph-F1 and GREEN added to the Step 33, 34 and 35 analyses

Limitations: [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md). Code: `usmeta/step37_rg_worker.py` (runs in a separate venv), `step37_new_scorers.py`, `step37_report.py` (new files; Steps 33 / 34 / 35 modules and saved results are read, not changed). Same group bootstrap (1,000, seed 0), same under-30-groups marks and decision rules. The test split was **not read again**: every score is for texts already in the earlier steps (their logged test reads). HiSBreast text stays in `usmeta/local_data` and the git-ignored annotation cache; only aggregated rates are written here.

## What ran

- **RadGraph-F1: ran on everything.** Official `radgraph` package 0.1.18 with the RadGraph-XL model (`StanfordAIMI/RRG_scorers`, ~416 MB download approved by the owner), CPU, installed in the separate venv `~/.venvs/radgraph` (transformers pinned to 4.46.3: version 5 removed an API the package uses). The 'partial' reward level is the RadGraph-F1 used here (simple and complete are saved in the local score files). Scored: all Step 33 blocks (17,444 blocks; 27,694 pairs), all Step 35 candidates (13,566 pairs), all Step 34 items (3,444 pairs: templated, HiSBreast, writer reports). Total about 10 min of scoring on CPU (3,370 + 10,263 + 23,461 unique texts).
- **GREEN:** Not run: no GREEN score exists for any item. The official checkpoint was set up as approved, but on this 16 GB Mac it could not score even two pairs within 36 minutes, so the capped-subset analyses were not started and no other model was substituted.

GREEN set-up and timing test (all approved by the owner):
- **Package:** the PyPI index served no installable `green-score` release to `uv` (project page exists, no versions resolved), so it was installed from `github.com/Stanford-AIMI/GREEN` (0.0.13) into a separate Python 3.11 venv (`~/.venvs/green`; `pyarrow` 17 and `datasets` 3.2.0 pinned because the pinned `numpy<2` conflicts with newer ones).
- **Model:** `StanfordAIMI/GREEN-radllama2-7b`, 13 GB downloaded to the Hugging Face cache (about 10 min). The package loads it in float16 and, without CUDA, only on the CPU (no Apple-GPU path in its code; `cpu=True`).
- **Timing test:** loading took 40 s; scoring **two pairs** (batch of 2, greedy, as the package does) was still running after **36 minutes** at about 360% CPU, (resident memory was only about 0.3 GB at the last check, so the weights appear to be paged in from disk), and was stopped. At that rate even a 20-pair subset would take many hours, far over the 90-minute cap for GREEN, and the 239-block subset of Step 33 (about 950 pairs) is out of reach.
- **Not done on purpose:** no 4-bit conversion or other model was used (not authorised); no GREEN number appears in any table. The 13 GB checkpoint and the venv remain on disk (`~/.cache/huggingface/hub`, `~/.venvs/green`) and can be deleted; a machine with a CUDA GPU (or at least 32 GB of memory) could run it with the same package.

## Decision lines

**RadGraph-F1 does not beat the judge, and it does not change the Step 33 / 35 conclusions; it joins the word scorers.** Factorial (pre-registered rule, eta-squared fact > wording): RadGraph-F1 is **wording-driven** (fact 0.00 vs wording 0.17 on all 17,444 blocks; on the judge's 239 blocks fact 0.05 vs wording 0.12), whereas the judge is fact-driven (judge_score fact 0.68 vs wording 0.01). Limit of detection: RadGraph-F1 never reaches AUROC 0.80 at any size error up to x2 or any HC shift up to 20 mm (its AUROC vs matched synonyms is 0.2-0.3: it scores a size error above a one-word synonym because RadGraph reads entities and relations, not numbers), whereas judge_score reaches it at the smallest level (5% / 1 mm). Metamorphic: RadGraph-F1 violates the invariances (unit invariance on 100% of templated items, synonym invariance on 90%) and fails the "number swap must lower the score" check on 80% of templated items. **A scorer built for chest X-ray entities and relations does not see an ultrasound measurement.**

**GREEN: not run (see above), so the question whether it beats the judge is unanswered; nothing here supports or refutes it.**

## Step 33 factorial: share of the score variance, fact vs wording (breast + thyroid pooled; verdict by the pre-registered rule)

| scorer | blocks / groups | fact | wording | interaction | residual | verdict | AUROC c vs a (small edits) | AUROC d vs b (large edits) | error+small above correct+large |
|---|---|---|---|---|---|---|---|---|---|
| BLEU | 17,444 / 830 | 0.02 | 0.60 | 0.00 | 0.38 | wording-driven | 0.69 | 0.97 | 76% |
| ROUGE-L | 17,444 / 830 | 0.02 | 0.41 | 0.00 | 0.56 | wording-driven | 0.53 | 0.89 | 76% |
| chrF | 17,444 / 830 | 0.04 | 0.27 | 0.00 | 0.69 | wording-driven | 0.51 | 0.97 | 76% |
| BERTScore | 17,444 / 830 | 0.02 | 0.41 | 0.00 | 0.56 | wording-driven | 0.44 | 0.99 | 76% |
| RaTEScore | 17,444 / 830 | 0.04 | 0.17 | 0.00 | 0.79 | wording-driven | 0.62 | 0.77 | 60% |
| judge_score (capped subset) | 239 / 71 | 0.68 | 0.01 | 0.00 | 0.31 | fact-driven | 0.98 | 0.95 | 4% |
| judge sentence_f1 (capped subset) | 239 / 71 | 0.55 | 0.01 | 0.00 | 0.43 | fact-driven | 0.94 | 0.94 | 5% |
| finding_f1 (regex, upper bound) | 17,444 / 830 | 0.26 | 0.00 | 0.00 | 0.74 | fact-driven | 1.00 | 1.00 | 0% |
| **RadGraph-F1 (partial), all blocks** | 17,444 / 830 | 0.00 | 0.17 | 0.01 | 0.82 | **wording-driven** | 0.49 | 0.65 | 59% |
| **RadGraph-F1 (partial), judge-subset blocks** | 239 / 71 | 0.05 | 0.12 | 0.01 | 0.82 | **wording-driven** | 0.64 | 0.74 | 40% |

Per organ (RadGraph-F1, all blocks): breast fact 0.02 vs wording 0.16 (wording-driven); thyroid fact 0.01 vs wording 0.31 (wording-driven). On the judge's subset the breast cell is fact-driven (fact 0.29 vs 0.04, 41 groups) and thyroid is wording-driven; the subset is small (71 groups pooled), so the full-block result is the one to read. † = under 30 groups.

## Step 35 limit of detection: smallest error with AUROC >= 0.80 vs matched synonyms

| scorer | breast, size (mm) | breast, size (% width) | thyroid, size (% width) | fetal head, HC (mm) |
|---|---|---|---|---|
| BLEU | not reached (> 100%) | not reached (> 100%) | not reached (> 100%) | not reached (> 20) |
| ROUGE-L | not reached (> 100%) | not reached (> 100%) | not reached (> 100%) | not reached (> 20) |
| chrF | not reached (> 100%) | not reached (> 100%) | not reached (> 100%) | not reached (> 20) |
| BERTScore | not reached (> 100%) | not reached (> 100%) | not reached (> 100%) | not reached (> 20) |
| RaTEScore | not reached (> 100%) | not reached (> 100%) | not reached (> 100%) | not reached (> 20) |
| judge_score (capped subset) | 5% | 5% | 5% | 1 mm |
| judge sentence_f1 (capped subset) | not reached (> 100%) | 100% | 25% | 1 mm |
| finding_f1 (regex, upper bound) | 5% | 5% | 5% | 1 mm |
| image check, oracle-box MedSAM | 25% | 25% | 25% | not reached (> 20) |
| image check, label-free U-Net | 50% | 50% | 50% | — |
| **RadGraph-F1 (partial)** | not reached (> 100%) | not reached (> 100%) | not reached (> 100%) | not reached (> 20) |

RadGraph-F1 AUROC by level (point estimates; levels as in Step 35): breast, size (mm): 0.27, 0.30, 0.30, 0.29, 0.30, 0.29, 0.32; breast, size (% width): 0.23, 0.24, 0.22, 0.23, 0.23, 0.23, 0.24; thyroid, size (% width): 0.20, 0.20, 0.20, 0.20, 0.20, 0.21, 0.23; fetal head, HC (mm): 0.32, 0.29, 0.30, 0.31, 0.32. Judge cells in the Step 35 table rest on a capped subset (many under 30 groups); RadGraph-F1 uses every Step 35 candidate.

## Step 34 metamorphic: violation rate (templated items; the full item sets are in the second table)

R1-R3 violation = score change > 0.05; R4 / R5 violation = the error is not scored strictly below a harmless synonym swap; R6 = a larger error raises the score. † = fewer than 30 applicable items.

| scorer | R1 unit | R2 order | R3 synonym | R4 number swap | R5 negation flip | R6 monotone |
|---|---|---|---|---|---|---|
| BLEU | 100% | 98% | 84% | 26% | 24% | 0% |
| ROUGE-L | 96% | 100% | 28% | 100% | 100% | 2% |
| chrF | 88% | 24% | 59% | 82% | 100% | 22% |
| BERTScore | 0% | 26% | 0% | 81% | 38% | 46% |
| RaTEScore | 79% | 1% | 80% | 62% | 86% | 43% |
| judge_score (capped subset) | 86% † | 33% † | 5% † | 0% † | 0% † | 0% † |
| judge sentence_f1 (capped subset) | — | — | — | — | — | — |
| llm_finding_f1 (v3; Step 34 subset) | 0% † | 0% † | 0% † | 0% † | 37% † | 0% † |
| finding_f1 (regex, upper bound) | 0% | 0% | 28% | 0% | 49% | 0% |
| **RadGraph-F1 (partial), all items** | 100% | 76% | 90% | 80% | 58% | 20% |
| **RadGraph-F1 (partial), judge-subset items** | 100% † | 71% † | 95% † | 95% † | 58% † | 19% † |

### All items and writer reports (RadGraph-F1 next to the others)

| scorer | set | R1 | R2 | R3 | R4 | R5 | R6 |
|---|---|---|---|---|---|---|---|
| BLEU | ALL | 65% | 63% | 51% | 38% | 42% | 1% |
| BLEU | writer | 0% | 0% | 0% | 89% | 69% | 3% |
| chrF | ALL | 57% | 16% | 36% | 78% | 81% | 27% |
| chrF | writer | 0% | 0% | 0% | 62% | 61% | 49% |
| BERTScore | ALL | 0% | 16% | 0% | 80% | 49% | 55% |
| BERTScore | writer | 0% | 0% | 0% | 75% | 63% | 94% |
| RaTEScore | ALL | 51% | 3% | 52% | 58% | 62% | 52% |
| RaTEScore | writer | 0% | 5% | 8% | 41% | 36% | 87% |
| judge_score (subset) | ALL | 60% † | 23% | 8% | 12% † | 45% | 0% † |
| judge_score (subset) | writer | 0% † | 11% † | 6% † | 100% † | 100% † | 0% † |
| **RadGraph-F1 (all items)** | ALL | 65% | 51% | 55% | 83% | 65% | 17% |
| **RadGraph-F1 (all items)** | hisbreast | — | 36% † | 100% † | — | 18% † | — |
| **RadGraph-F1 (all items)** | writer | 0% | 11% | 0% | 100% | 79% | 6% |

HiSBreast cells are almost all too small to compare (R1, R4 and R6 apply to none of the 41 texts).

## Caveats

- **RadGraph-F1 is a chest-X-ray entity and relation scorer** (RadGraph-XL was trained on radiology reports of several modalities, not our templated ultrasound wording); a low score here is a statement about this use, not about RadGraph on chest X-ray. The partial reward level was chosen up front as the RadGraph-F1; simple and complete levels are saved locally but not analysed.
- Same limits as Steps 33 / 34 / 35: templated text, matched synonyms as the harmless side (word-level scorers follow edit size), crude rule-based transformations on free text, the judge on capped subsets.
- The venv versions (radgraph 0.1.18, transformers 4.46.3, torch 2.15, CPU) are recorded in `run_info.json`; RadGraph-XL was not retrained or tuned.
