# Step 10f: contamination notes for report-writing models (Qwen2.5-VL-3B run; MedGemma and LLaVA-Med not run yet)

Linked limitations: [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md). **These are probes and notes, not proof either way. Contamination cannot be ruled out.**

## What the model card says about training data
- **Qwen/Qwen2.5-VL-3B-Instruct** (read on 2026-10-24 from the Hugging Face README via `huggingface_hub`): the README describes the architecture, capabilities and usage; **it does not list the training datasets** (keyword search for training/data/medical found only architecture and usage text). The training data are described in the Qwen2.5-VL technical report, which I have not read here: **to confirm** before writing anything about exposure.
- **MedGemma (google/medgemma-4b-it)**: not run (Hugging Face access not granted). Its card is expected to list public medical image datasets used for training: **to confirm when access is granted**; nothing is claimed here.
- **LLaVA-Med**: not run. **To confirm** from its paper / card when run.

## Which of our datasets are public
All ten benchmark datasets are public downloads and could have been scraped or included in some form: BrEaST (public archive), BUS-BRA, BUSI, UDIAT dataset B (access on request, to confirm), BUS-UCLM, TN3K, TN5000, DDTI, HC18 (public challenge; the "Diverse Fetal Head Images" folder is a resized copy of HC18), fetal-head planes. Licences are "to confirm". Whether any model saw them is **unverifiable**. BrEaST is the newest and smallest public set and stays the "cleanest" check, but that is a guess, not a measurement.

## Memorisation probe (Qwen2.5-VL-3B; 20 scans per dataset from the DEV split; `usmeta/memprobe.py`; raw answers in `memprobe_qwen.jsonl`)
(a) Text only, no image: name the dataset file and ask for its label. (b) With the image: ask which public dataset it comes from.
| dataset | probe | result | baseline |
|---|---|---|---|
| BUS-BRA | benign / malignant from the file name | 12 of 20 correct | 0.60 majority class (12 of 20): **no better than always saying the majority** |
| BrEaST | same | 10 of 20 | 0.50: chance |
| BUSI | same | 17 of 20 | 0.50, **but BUSI file names contain the class ("benign (17).png")**, so this is reading the file name, not memory |
| HC18 | head circumference (mm) from the file name | 0 of 20 within 5 mm; median error 142 mm (answers around 50 mm; true values 205-300 mm) | no signal |
| all six datasets | "which public dataset is this image from?" | **0 of 120 named correctly**; the model answers "CUPID" for almost every scan | none |
Reading: no evidence of memorised labels or dataset identities in this 3B model for these prompts. A probe with 20 images and short answers cannot show absence of exposure; it only shows that this simple retrieval does not work.

## What this does and does not change
Part A (scorer tests) does not use the VLM outputs (reference and candidate text are ours), so exposure of the writers affects only the real-report comparison (Stage 3: Qwen reports, flip test). Pretrained scorers (BERTScore, RaTEScore, Gemma judge/extractor) cannot be decontaminated by us.
