# Status and roadmap (2026-10-27)

## Done (Steps 2-17; see `usmeta/results/partA/INDEX.md`)
- Templated reference reports and a planted-error benchmark on 10 ultrasound datasets; locked dev/val/test splits; frozen versions (`freeze-v1`).
- Layer 0 (BLEU, ROUGE-L, chrF, BERTScore, RaTEScore), Layer 1 (fact F1, upper bound on templated text), Layer 2 (Gemma-2-9B judge), Layer 3 (true masks, then MedSAM predicted masks).
- Real reports from Qwen2.5-VL-3B and MedGemma-1.5-4B; HiSBreast real-text check (101 of 427 machine-translated exams).
- Final combined table and `usmeta/RESULTS_SUMMARY.md`.

## Open (needs input or resources)
- Clinician review of the severity ladder and of the template sources.
- Bilingual review of the HiSBreast translations.
- A lesion detector for Part B (so the segmenter is not given the box); GREEN; LLaVA-Med; a Claude judge (no credit); Jev (paid API, needs approval).
- HiSBreast images with Qwen (needs a check for burned-in identifiers first).
- Repo visibility is set by the owner.

The earlier chest X-ray roadmap is in `archive/legacy_scaffold/ROADMAP_old.md`.
