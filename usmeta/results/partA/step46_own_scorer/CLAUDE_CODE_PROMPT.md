Paste into Claude Code on the Mac, inside ~/medical-imaging-ai/usmeta, AFTER Step 45 Part G has finished and been committed.

Read CLAUDE.md, the Step 45 results.md files, and results/partA/step46_own_scorer/PREREG.md (do not edit it). Commit the PREREG first, before any Step 46 number. Standing rules apply (additions only, tune on dev/val, read each test set once via a logged read, group bootstrap 1,000 seed 0, under 30 groups = too small to compare).

Order:
1. CRQS source: fetch arXiv 2607.18448 and github.com/surykntsingh/PathBench, write CRQS_SOURCE.md with the exact formula, quotes and commit hash. If it is ambiguous, say so and follow PREREG section 3. You may download the paper and the repo; nothing else.
2. Set B: download Llama-3.1-8B-Instruct 4-bit for MLX (ask me only if the download fails; fall back to Mistral-7B-Instruct 4-bit). Build set B as in PREREG section 1. Keep the stress subset.
3. Run extractor v5 and the number checker on set B (and set A dev/val if not cached).
4. Implement UScore (primary rule version + secondary learned version) and CRQS. Fix UScore's threshold on set A dev/val. Run the Gemma judge only on pairs the rules do not flag; keep Gemma loaded once; cap 3 h, then write what you have as incomplete.
5. Evaluate H1-H7 and the CRQS prediction. Write results.md with PASS / DOES NOT PASS exactly as pre-registered.
Commit and push after each numbered item. At the end give me a one-screen summary in plain language.
