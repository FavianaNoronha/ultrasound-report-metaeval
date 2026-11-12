# Status and roadmap (2026-11-13, Steps 2-38; tag `final-v5`)

Every step has a results folder under `usmeta/results/partA/` (index: `usmeta/results/partA/INDEX.md`). Read `usmeta/RESULTS_SUMMARY.md` first and `usmeta/docs/LIMITATIONS.md` before quoting a number.

## Done
- **Steps 2-10 (benchmark, freeze, locked test).** Templated reference reports and a planted-error benchmark on 10 ultrasound datasets (breast, thyroid, fetal head); harmless rewordings split into small / matched synonym / large; locked dev / val / test splits (grouped); frozen versions (`freeze-v1`); headline results on the locked test split.
- **Layers.** Layer 0 (BLEU, ROUGE-L, chrF, BERTScore, RaTEScore), Layer 1 (`finding_f1`, an upper bound on templated text), Layer 2 (Gemma-2-9B sentence-check judge), Layer 3 (true masks, then MedSAM predicted masks).
- **Steps 11-17 (real writers and real text).** Qwen2.5-VL-3B and MedGemma-1.5-4B reports; larger judge sample (59 cases per dataset); HiSBreast real-text check (101 of 427 machine-translated exams); MedSAM image check with oracle boxes (Step 16); final combined table.
- **Steps 18-22.** Threshold crossing (exploratory), routing table and paired preference (19a-c), tolerance-aware image check (20), robustness tests 21a-g (label-free boxes, size dose-response, judge sensitivity, human rewordings, matched edit size, split audit, leakage sensitivity), paper-support tables (22).
- **Steps 24-30 (wrap-up work).** Box reliability curve (24); error-type coverage with a built omission type (25); LLM fact extractor and `llm_finding_f1` (27); natural-error validity test with the owner's 30-report hand check (28); label-free image check by a small U-Net and HC18 head-circumference geometry (29, replaces Step 23); severity breakdown (30).
- Tests: `cd usmeta && PYTHONPATH=. python3 -m pytest -q tests` (needs no dataset or GPU).


## Steps 31-38 (added after `final-v4`; tag `final-v5` marks this state, earlier tags were not moved)
Details and caveats: `usmeta/results/partA/INDEX.md`; headline findings and addenda: `usmeta/RESULTS_SUMMARY.md`.
- **31** cross-dataset segmenter (breast, leave-one-dataset-out): pooled position AUROC 0.95 held out vs 0.94 in-dataset. **32** extractor v3 (stricter prompt): templated agreement kept (>= 0.98); **provisional until a real independent human hand check of `usmeta/docs/step32_check.csv`**.
- **33** (two steps share this number, see `step34_hybrid/STATUS.md`): `step33_edit_size_law` (BLEU R² 0.62, ROUGE-L 0.71) and `step33_factorial` (pre-registered: word scorers wording-driven, judge and finding_f1 fact-driven). **34** metamorphic checks (`step34_metamorphic`); the earlier hybrid-evaluator pre-registration (`step34_hybrid`) was **not run**. **35** limit of detection. **36** adversarial wording attack on the judge (pre-registered hypothesis not supported).
- **37** RadGraph-F1 added to Steps 33-35 (wording-driven, never reaches AUROC 0.80); GREEN could not be run on this 16 GB machine (13 GB checkpoint downloaded, two pairs did not finish in 36 minutes; the checkpoint and two venvs sit outside the repository). **38** responsible-AI checks on the image check (per-dataset gaps, risk-coverage, corruptions; scanner metadata exists only in BUS-BRA).

## Not run, on purpose
- **Step 23 (lesion detector):** replaced by Step 29 (a segmenter trained on dev, not a detector with a pretrained backbone).
- **Step 26:** on hold at the owner's instruction; nothing was run or guessed. There is no Step 13 folder.
- GREEN (attempted in Step 37: the official 7B did not run on 16 GB; needs a CUDA GPU or about 32 GB), a Claude judge (no credit), the original RadFact, Jev (paid API, needs approval), LLaVA-Med.

## Open (needs input or resources)
- **Clinician review** of the severity ladder (Step 30 shows severity is provisional and confounded with error type and edit size) and of the template sources.
- **Bilingual review** of the HiSBreast translations; HiSBreast images with Qwen (needs a check for burned-in identifiers first).
- **A real lesion detector** (Step 29 is a segmenter; its thyroid position AUROC, 0.80 with interval 0.69-0.89, sits on the decision boundary) with a pretrained backbone, and a repeat over seeds and splits.
- **A better free-text extractor:** on the 30-report hand check the Qwen7B extractor was right in 22 (all 12 fetal-head ones only because they were empty) and in 10 of 18 breast and thyroid reports, so Step 28 (natural errors) is inconclusive for thyroid and fetal head and indicative for breast. More images per organ (100 were planned, 60 run) would also help.
- Patient-level splits for the five datasets without patient ids; pixel size for FetalHead (head circumference is not testable there); a head-circumference tolerance fitted for fetal head (tau 0.3, tuned on breast and thyroid size, cannot see HC errors).
- Hand check of `usmeta/docs/step32_check.csv` (Step 32 stays provisional until then); the hybrid evaluator (pre-registration kept, not run); Step 26 (on hold).
- Repo visibility is set by the owner. Tags mark repository states, not claims of completeness.

## Stale files (kept, not edited)
- `usmeta/PROJECT_SLIDES.pptx`: built before Steps 18-30; its numbers and wording predate the addenda in `usmeta/RESULTS_SUMMARY.md`. Update the slides from the summary, not the other way round.
- `usmeta/PROJECT_REPORT.md`: marked superseded at the top.
- The old status tables in `usmeta/README.md` ("Status of v0", "Stage 3 status", "Part A status as of 2026-10-23") and `usmeta/results_layers_all.md` (Step 9 version; the final table is `usmeta/results_layers_all_final.md`).

## Files in git history that may not be redistributable (history was not rewritten)
Dataset licences are all still "to confirm"; until they are confirmed, treat these as possibly not redistributable if the repository is made public:
- `baseline_exp/breast.xlsx` (the BrEaST clinical / label spreadsheet) and `baseline_exp/tn3k_records.json` (TN3K labels): committed in the first commit and derived from those datasets; still in the tree and in history.
- Benchmark and report files built from dataset labels or images: `usmeta/bench*.jsonl`, `usmeta/true_reports_v2*.jsonl`, `usmeta/reports_qwen*.jsonl`, `usmeta/reports_medgemma*.jsonl`, `usmeta/judge_*.jsonl`, `usmeta/memprobe_*.jsonl`, `usmeta/duplicates.jsonl` (near-duplicate pairs by image hash), `usmeta/splits.jsonl` and case ids in many result files. They are templated or model-written text and hashes, but they carry dataset case ids and label content.
- `reference to human.xlsx`: the owner's human rewordings of our own templated reports (no dataset text).
- No images, model weights, HiSBreast text, translation or exam id are tracked (checked with `git grep` and a scan for Vietnamese text; the HiSBreast files that are tracked are code, keyword dictionaries and synthetic test strings). A repository test guards `usmeta/local_data/`.

The earlier chest X-ray roadmap is in `archive/legacy_scaffold/ROADMAP_old.md`.
