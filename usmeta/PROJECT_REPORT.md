# Project report in plain words (short version)

## The question
AI can now write ultrasound reports. To check them, people use "scores". Most scores just **count matching words**. Do these scores notice a **real medical mistake** (wrong side, wrong size, wrong BI-RADS), or only how many words changed?

## What we did
1. Took 10 public ultrasound datasets (breast, thyroid, fetal head).
2. Wrote a correct "reference" report for each scan from its labels (so we know the truth).
3. Made copies with **one planted mistake**, copies with **harmless rewordings**, and exact copies.
4. Asked each score: "is the mistake worse than the harmless rewording?" (1.0 = always, 0.5 = coin flip).
5. Tested four kinds of scorers: word-matching, a fact checker, an AI judge (Gemma), and a check against the image (masks).
6. Locked the data into dev / val / test, so the final numbers come from scans we never tuned on.
7. Tried real AI report writers (Qwen, MedGemma) and a small set of real doctor-written conclusions (HiSBreast, machine-translated).

## What we found
- **Word-matching scores cannot tell a mistake from a rewording.** No cut-off flags most mistakes without also flagging most harmless rewordings. A lazy answer, "No abnormality.", still scores about 0.85 on BERTScore.
- **They react to how much text changed, not to what changed.** A mistake changes 2–4% of the words, a rewording 5–60%.
- **The AI judge is much better** at telling a mistake from a one-word rewording (0.89–1.00), but it is weaker on bigger rewordings in breast and one thyroid set (0.60–0.71), and it changes with the prompt wording.
- **The fact checker catches every planted mistake (1.00), but that is flattering:** it reads the same template that wrote the reports.
- **Image check with predicted masks works on breast and thyroid** (0.91 vs 0.25–0.62 for word scores), **but only with an easy setup** (the lesion box was handed to it, errors were big). It **fails on fetal head** (a mismatch between how the skull is outlined), and it marks correct reports down (mean 0.68).
- **Today's small open AI writers get the facts wrong a lot**, and the scorers disagree about which writer is better.
- **On real doctor text (small subset)** the direction is the same: BERTScore at chance (0.43), the AI judge best (0.79–0.89).

## What failed or turned out wrong
- Our first headline ("word scores are worse than chance") was **an artefact** of our rewordings being much bigger than our mistakes. Retracted.
- The first good-looking judge number (0.86 on BrEaST) dropped to 0.67 on the locked test set.
- Several bugs found and fixed (BUS-BRA "single breast" wording, a decimal bug in the extractor, copied option lists); reruns are kept.
- Only 101 of 427 HiSBreast exams passed our translation checks.
- Not run: GREEN, a Claude judge, Jev, LLaVA-Med, clinician review.

## Limits (please remember)
Reports are templated, not doctor-written. Severity levels are our guesses. No clinician has reviewed anything. The AI models may have seen these public datasets. Datasets are small and some have no patient IDs. We found no ultrasound work that tests the scorers with planted errors, severity and harmless rewordings (search not exhaustive).

## Right now: Step 18 (in progress)
Question: do scorers understand **guideline cut-offs** (e.g. a thyroid nodule growing past 10 mm changes what a doctor does), or only the size of the edit? No dataset has both a real size in mm and a TI-RADS level, so we use **synthetic sizes with real TI-RADS levels** (labelled as such). Hypotheses were written down before scoring. Dev/val scoring is running; results are not in yet.

Full details: `RESULTS_SUMMARY.md`, `results/partA/INDEX.md`, `docs/LIMITATIONS.md`.
