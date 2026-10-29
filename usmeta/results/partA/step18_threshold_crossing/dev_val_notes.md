# Step 18, sub-step 3a — dev/val run (design only; written 2026-10-29 BEFORE any scorer was run on the test candidates)

Dev + val replicas: 716 (synthetic size, real TI-RADS level, DDTI). Primary cell = delta 3 mm, digit-matched pairs, pooled TR3–TR5: **194 pairs from 119 patient groups** for the text scorers (Layer 0 and finding_f1), 74 pairs / 51 groups for the judge (judged subset: 50 pair replicas + 50 control replicas, capped for time; 314 judge calls, 0 unparseable, 33 min). Full numbers: `dev_val_report.json`.

**Gates.** Identical copies score 1.0 on every scorer (716 copies for Layers 0/1, mean = min = 1.000; judge 53 copies, mean = min = 1.000).

**What dev/val shows (not a result; test decides):**
- BLEU, ROUGE-L, finding_f1: difference (non-crossing − crossing) exactly 0 (all ties), as predicted by construction for equal-size edits.
- chrF −0.001 and BERTScore −0.000 (negligible); RaTEScore DiD +0.010 (CI 0.001–0.018): a tiny tilt toward penalising the crossing error.
- Judge: sentence_f1 DiD +0.014 (CI −0.011 to 0.035, includes 0); **judge_score DiD +0.064 (CI +0.025 to +0.108)**; 22% of pairs penalise the crossing error more, 70% tie, 8% penalise it less. So the judge's error-penalty score may separate crossing from non-crossing a little, a possible falsifier of H2 (judge_score). The judge's dose-response so far: 3 mm 0.93 (0.87–0.98); the other bins have too few units (20) and sit at 0.5 because only some bins were judged on dev/val.
- Edit size is matched: token edit 0.0324 (crossing) vs 0.0318 (non-crossing), character edit 0.0071 vs 0.0057.

**Decisions fixed before test (no change to H1–H4 or the primary analysis):**
1. Test judge run = every digit-matched valid delta-3 pair replica of the test split + an equal number of controls (up and down errors), one matched synonym each, identical copies for every 4th replica, plus dose-response extras (±1, 2, 5 mm, ±10 and ±30 %, remaining synonyms) for 32 replicas. Estimated 2.2 h, under the 3-hour limit; stopped and reported as is if it exceeds 3 h.
2. Both judge scores are reported; `judge_score` is the judge's error-penalty score, `sentence_f1` the sentence-level support score. H2 is judged separately for each (as pre-registered: "sentence_check" = both columns), and the more favourable one is NOT picked.
3. H4 (prompt_v3 with cutoffs) is run only if the test shows the judge does not separate crossing from non-crossing (H2 held) and it fits in under 2 extra hours.
