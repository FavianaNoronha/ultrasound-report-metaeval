# Step 9: combined results (every scorer x every dataset, by layer)

The full table is `results_layers_all.md` (copied here as `results_layers_all.md`). Built by `python3 -m usmeta.layers_all` from the saved results of Step 5 rerun3 (Layer 0), Step 6 (Layer 1), Step 7 rerun2 (Layer 2, 20 cases per dataset) and Step 8 (Layer 3, own box benchmark). Per dataset: AUROC vs harmless_small, the matched one-word synonym and harmless_large; critical-only AUROC; harmless_small / harmless_large means; identical mean (must be 1.0); lazy "No abnormality." score; AUROC per error category; and a column "idea borrowed from" (standard metrics, BERTScore, RaTEScore, RadFact protocol, UltraG-Bench SemAcc, MAIRA-2-style box IoU; ours where it is ours).

**Headline across layers (read per dataset, not pooled).**
- Layer 0 (word overlap, BERTScore, RaTEScore): on BrEaST AUROC 0.08-0.13 vs style swaps and 0.24-0.63 vs the matched one-word synonym (best RaTEScore 0.63; chrF 0.24), size errors unseen; lazy "No abnormality." scores 0.84-0.87 on BERTScore.
- Layer 1 (`finding_f1`): 1.00 everywhere, but only because its extractor reads our own template (upper bound).
- Layer 2 (Gemma-2-9B `sentence_check`, 20 cases per dataset): 0.86-0.94 vs small / matched on BrEaST, 0.50-1.00 across datasets depending on the prompt; identical copies 1.0 only with the stricter prompt; wide intervals.
- Layer 3 (true masks): high on size and position errors because the same masks built the references (circular); the real test needs predicted masks (Part B).
- Not run: GREEN, Claude judge, original RadFact, SAM/MedSAM, real VLM reports through Layers 1-3, clinician severity.

**Keep visible:** reports are templated from labels (synthetic but fact-correct); severity is provisional pending clinician; template sources "to confirm" must be verified before any paper claim; results are per dataset only.

---
Limitations: see [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md) (templated reports, upper bounds, prompt-sensitive judge, provisional severity, possible exposure). 
