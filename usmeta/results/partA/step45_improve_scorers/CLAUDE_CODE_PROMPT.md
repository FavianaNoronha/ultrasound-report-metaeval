Paste this into Claude Code on your Mac, inside ~/medical-imaging-ai/usmeta.

Read CLAUDE.md, RESULTS_SUMMARY.md, docs/LIMITATIONS.md and results/partA/step45_improve_scorers/PREREG.md (already written; do not edit it). Follow the standing rules in CLAUDE.md: additions only, tune on dev/val, read test once via usmeta.splits.load("test"), group bootstrap 1,000 seed 0, cells under 30 groups are "too small to compare", never rewrite history.

Do Step 45 in this order, committing after each part (commit the PREREG first, before any test number exists):
1. Part A: build the free-text set (writer Qwen2.5-7B-Instruct, saved prompts, deterministic gold check). Report how many reports were dropped.
2. Part B and C: extractor v5 and the number checker (CPU is fine). Tune on dev/val, then evaluate on set A test once.
3. Part E and F: small learned scorer and the hybrid, using saved judge scores (no new model calls).
4. Part D: claim-by-claim Gemma-2-9B judge (cache every reply under .llm_cache).
5. Part G: pretrained-encoder U-Net and MedSAM-with-U-Net-box on the same 498 scans as Step 40.
For each part write results.md with the PREREG pass rule, the numbers, and "DOES / DOES NOT PASS". Add the INDEX.md row, CHANGELOG entry, RESULTS_SUMMARY addendum and a numbered LIMITATIONS item. Tell me the headline numbers in plain language after each part.
