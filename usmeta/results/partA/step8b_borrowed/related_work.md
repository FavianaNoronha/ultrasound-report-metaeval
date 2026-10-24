# Related work for Step 8b (citations as given in the task brief; verify before use in a paper)

- ReEvalMed, "Beyond Scalar Scores", arXiv 2606.18797 (chest X-ray): discrimination / robustness of report metrics. Cited in CLAUDE.md and the brief; **details not independently re-read here**.
- Naidu et al., ReXErr cross-dataset study, medRxiv 2026 (as named in the brief): **not retrieved or verified here; citation details to confirm**.
- "Can Jev Judge Radiology Reports?", arXiv 2609.27607 (chest X-ray): repeatability and calibration of an LLM judge. As named in the brief; not re-read.
- Breast ultrasound report auditing, J Digit Imaging 2026, doi 10.1007/s10278-026-02163-z: false-alarm rate, report- vs error-level sensitivity, physician baseline. As named in the brief; not re-read.
- VLScore: Dawidowicz, Hirsch, Tal, "Image-aware Evaluation of Generated Medical Reports", arXiv 2410.17357, NeurIPS 2024 (title, authors and venue checked on the arXiv page / search on 2026-10-24). Chest X-ray; no public code found.
We found no ultrasound work that tests the scorers with planted errors, severity and harmless rewordings (our search was not exhaustive); we extend these ideas to ultrasound and do not claim them.
