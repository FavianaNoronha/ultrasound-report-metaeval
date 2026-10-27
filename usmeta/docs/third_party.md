# Third-party models and tools used by usmeta

Licences are quoted from each model's own card on the date shown; check them again before any release. No weights are stored in this repository (they sit in the Hugging Face / torch cache on the machine that runs the code).

| item | what we use it for | licence (as stated) | where checked | size | step |
|---|---|---|---|---|---|
| MedSAM, `wanglab/medsam-vit-base` (SAM ViT-B fine-tuned for medical images; Ma et al., Nature Communications 2024, built on SAM, Kirillov et al. 2023) | Part B: predicted masks from box prompts, so the image check no longer reads the true masks | Apache-2.0 (Hugging Face model card) | huggingface.co/wanglab/medsam-vit-base, 2026-10-27 | 375 MB (`pytorch_model.bin`) | step16_partB |
| Qwen2.5-VL-3B-Instruct, Qwen2.5-7B-Instruct (4-bit MLX) | report writer (VLM); non-Gemma judge / extractor / translator | see the model cards (Qwen licence terms differ by size) | model cards | local cache | steps 11, 12, 14, 15 |
| MedGemma-1.5-4B-it (4-bit MLX conversion made locally) | report writer | Health AI Developer Foundations terms (gated model; accepted on Hugging Face) | model card | local cache | step 14 |
| Gemma-2-9B-it (4-bit MLX) | LLM judge, paraphrases | Gemma terms of use | model card | local cache | steps 7, 12, 15 |
| roberta-large (BERTScore), RaTE-NER-Deberta (RaTEScore) | Layer 0 learned scorers | see model cards | model cards | local cache | step 4 |

Rows other than MedSAM were not re-verified for this file: they are copied from earlier steps and marked "see the model card" on purpose.
