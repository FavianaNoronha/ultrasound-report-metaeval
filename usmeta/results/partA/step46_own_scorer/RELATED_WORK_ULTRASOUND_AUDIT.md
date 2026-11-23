# Related work: breast-ultrasound report auditing

**Reviewed 2026-11-21.** This is a working literature note, not a novelty claim. The publisher full text is subscription-only; this comparison uses the article abstract, its page metadata, and the public supplementary methods/tables.

## Zou et al. (2026)

Mi Zou, Mengsu Xiao, Qingli Zhu, Jing Zhang, Jianchu Li, and Ke Lv, “Multimodal Large Language Models for Breast Ultrasound Report Auditing: Workflow-Error Detection, False-Positive Burden, and Limits of Key-Image Interpretation,” *Journal of Imaging Informatics in Medicine*, published 2026-08-03. [Article](https://link.springer.com/article/10.1007/s10278-026-02163-z) · [Supplementary methods and tables](https://static-content.springer.com/esm/art%3A10.1007%2Fs10278-026-02163-z/MediaObjects/10278_2026_2163_MOESM1_ESM.docx)

### What they did

- Used a retrospective clinical cohort of 818 breast-ultrasound examinations with pathology or follow-up reference standards. This is not our public multi-dataset benchmark; the data are private and available by request.
- Constructed an enriched audit set of 300 reports: 240 reports containing 329 inserted errors and 60 error-free reports. The source reports were in Chinese. The supplement does not describe generating the reports from templates; it describes errors inserted into reports and provides labeled examples.
- Tested GPT-5.5 and Gemini 3.1 Pro Preview with two conditions: report text alone, and report text plus key images cropped from the report. A physician reader was the human benchmark.
- Error categories in Supplementary Table S1: laterality (66), location (53), size/numerical (64), BI-RADS (38), other logical (52), template residue (19), and spelling/punctuation (37). They also classified errors by image dependence: text-sufficient (132), image-supported (140), and image-essential (57).
- The supplement publishes their two audit prompts. The prompt asks the model for a binary error/no-error decision with a short explanation; it is not a structured field-level metric and does not compare a family of existing text scorers.

### Findings that matter for our design

- Adding key images increased report-level sensitivity from 77.5% to 89.6% for GPT-5.5 and from 86.2% to 96.2% for Gemini. Error-level recall increased from 63.2% to 75.4% and from 72.0% to 83.6%.
- The gain was concentrated in image-essential errors: text-only models detected 0/57, while multimodal models detected 45/57 and 48/57. Image input also improved laterality, location, and size/numerical error recall.
- Image input reduced BI-RADS error recall: by 21.1 percentage points for GPT-5.5 and 23.7 points for Gemini. This argues against sending every claim through one undifferentiated vision-language judgment step.
- False alarms were material: Gemini with images flagged 18/60 error-free reports and 12/240 error-enriched reports. The physician reader had 83.0% error-level recall and no false positives in this subset.
- In the full-cohort classification task, key-image input performed below physician-interpreted findings input for malignancy and BI-RADS risk classification. The authors caution against clinical use.
- The dataset and code are not publicly available; analysis code is available from the authors on request.

## Relationship to our Step 46

| Dimension | Zou et al. (2026) | Our Step 46 |
| --- | --- | --- |
| Population | One private clinical breast-ultrasound cohort | Public datasets spanning breast, thyroid, and fetal head |
| Text source | Clinical Chinese reports with inserted errors | Llama-written free text from held-out structured cases; templates and controlled twins are also used elsewhere in the benchmark |
| Main system question | Can two general LLMs audit a report, and do key images help? | Which existing scorers separate planted errors from harmless rewrites under controlled conditions? |
| Comparators | Text-only vs image-plus-text LLM audit; physician reader | Text metrics, extractor/fact checks, judge, CRQS adaptation, and image checks |
| Error design | 329 inserted errors across seven categories in an enriched subset | Controlled fact changes, harmless wording variants, severity and limit-of-detection variants; three organ schemas |
| Main outcomes | Sensitivity/recall, report-level detection, false positives | AUROC, paired group-bootstrap comparisons, fixed false-alarm threshold, detection and limit-of-detection analyses |
| Key-image role | Whole-report audit using report-embedded images | Image check is a separate evaluation component; Step 46’s primary UScore is text/reference-based |

The overlap is real: planted errors, harmless reports, false-alarm measurement, and ultrasound report auditing are present in both. We must not claim that ultrasound report auditing or inserted-error testing is unprecedented. A narrower contribution may remain in a controlled, multi-organ **meta-evaluation of many scorers**, with matched wording changes, edit-size controls, small-error detection, and organ-specific comparison. We should make that claim only after reading the full article and checking related work such as ReEvalMed and CRQS.

## A testable next research direction

Treat this as a prospective Step 47 proposal, separate from the already preregistered Step 46:

> At a fixed, preselected false-alert rate, does an organ-aware, evidence-routed auditor detect more clinically meaningful errors than (a) a text-only UScore/CRQS-style comparison and (b) a general multimodal LLM asked “is there an error?”—and does it avoid the multimodal loss on BI-RADS-like reasoning errors?

One shared engine can serve three anatomy-specific schemas. For each claim, it should first compare report facts with reference facts. It should then route only claims that can be checked from the provided image to a vision verifier; for example, image labels/calipers may support laterality, location, or a displayed measurement, while a single frame cannot establish that a full-exam BI-RADS/TI-RADS assessment is correct. When the relevant evidence is absent or ambiguous, the system should abstain and show why. Keep the field-level evidence and uncertainty visible.

Compare text-only, image-only, and image-plus-text modes on the same cases. Stratify by the paper's image-dependence categories and by error type. Add matched harmless rewrites, edit-size matching, per-organ results, group-level bootstrap intervals, and a fixed false-positive budget. Have clinicians verify the error labels and adjudicate disagreements before calling the system useful. Do not train a new model first: test the routing and abstention hypothesis with existing models, and consider fine-tuning only if an independently annotated development set shows a specific model gap.

This is a promising architecture hypothesis, not yet a demonstrated novelty or clinical benefit.
