# Step 47 preregistration amendment 3 (before freeze-stage1 and before any Set C generation)

Written 2026-11-25. No Set C case has been generated and no Step 47 test score exists. Reason: a 3-day deadline.

1. **Stage 1 shortened.** Stage 1 used only the saved Gemma replies on Step 46 Set B dev/val (no new model calls) and ended after 12 logged trials (`trial_log.csv`), instead of up to 20 trials or 3 days. Every trial is logged, including failures.
2. **Stage 1 winner becomes primary.** Trial T12 ("S1") had 48/48 major/critical errors routed and 24.7% of harmless reports routed on dev, against 45.7% for frozen V3 (which would fail the 30% limit). As allowed by amendment 2 item 6, S1 replaces V3 as the primary variant; this is written into `frozen_variants.json` (with SHA-256) before Set C exists. S1 routes when a rule finds a major difference or any difference, any judge reply cannot be parsed, the three prompt presentations disagree on whether there is a major issue, any reply is unsure, or any reply makes a major claim. H1 and H2 are judged on S1. H2 uses comparator cutoffs recalibrated on dev to S1's dev route budget. V0 to V6 are still reported as secondary.
3. **Dev caveat.** S1 was selected on the same 293 dev/val reports it is described on, so its dev numbers are optimistic; only the Set C result counts.
4. **Known weakness not fixed.** 93 of 771 Gemma dev replies failed the parser twice and their raw text was not saved; in S1 an unparsed reply routes the report. Fixing the parser is left for later work.
5. **Second judge on a subset.** The Llama-3.1-8B judge (H9, descriptive) runs on a fixed 300-report Set C subset (first 300 core report IDs by SHA-256), not all of Set C.
6. Everything else in PREREG.md and amendments 1 and 2 is unchanged, including the >= 400 major/critical error eligibility rule for H1 and the extractor hand check.
