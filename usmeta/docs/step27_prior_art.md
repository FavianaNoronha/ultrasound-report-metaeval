# Step 27 prior-art note (short search, 2026-11-09; not exhaustive)

Question: is "LLM extracts structured facts, deterministic code compares them" new? No. We do not claim it is.

What exists (found in a quick search, not verified beyond the abstracts):
- **GREEN** (arXiv 2405.03595, Findings of EMNLP 2024): an LLM counts and explains clinically significant errors in a candidate radiology report.
- **RadFact** (Microsoft; named in the VERT preprint, arXiv 2604.03376, which compares RadFact, GREEN and FineRadScore): LLM-based fact verification of generated reports. We did not read its method, so we do not describe it beyond this.
- **BURExtract-Llama** (arXiv 2408.11334): fine-tuned Llama3-8B turns breast-ultrasound report text into per-lesion JSON with 16 keys, scored by field F1 against clinician labels. Nearest to our extractor step.
- **Endometriosis ultrasound extraction** (arXiv 2601.09053): local LLMs vs human abstraction, field-level accuracy; reports semantic errors such as negation that prompting did not fix.
- Our own `finding_f1` (Step 6) and `schema.extract_llm` (Gemma, frozen) already use this pattern; Step 27 swaps the extractor model (Qwen, not the judge family).

What we claim, and only this: a measurement of whether an LLM-extraction-plus-fixed-comparison scorer (`llm_finding_f1`) separates planted ultrasound mistakes from harmless rewordings on our templated benchmark, and how stable it is compared with the Gemma judge. We found no ultrasound work that tests this scorer with planted errors and harmless rewordings (search not exhaustive).

Sources: arxiv.org/abs/2405.03595, arxiv.org/pdf/2604.03376, arxiv.org/abs/2408.11334, arxiv.org/abs/2601.09053.
