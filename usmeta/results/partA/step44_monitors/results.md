# Step 44: scorers as monitors (audit budgets, severity weighting, cascade, reason-match, flag agreement)

**Verdicts (pre-registered analyses; PREREG.md committed before any number; saved scores and cached replies only, no model call; thresholds from val, results on test; group bootstrap 1,000, seed 0; † = under 30 groups).**

1. **At the pre-registered val thresholds the judge catches most planted errors; the word and embedding scorers catch a minority, but the budgets are not matched in realised share, so this is not a like-for-like comparison.** On the judge test subset (4,729 candidates, 33.0% planted errors) the judge (5% budget threshold; 10% gives the same threshold) flags 27.0% of candidates (realised; it scores in coarse steps) and catches **71.3 (68.2-74.5)%** of planted errors (severity-weighted 78.2 (75.0-81.1)%), flagging 5.6 (4.5-7.0)% of harmless rewordings and 0.0 (0.0-0.0)% of identical copies. The best word/embedding scorer at the 10% budget (RaTEScore) catches 27.4 (23.2-32.1)% while flagging 16.0 (14.1-17.8)% of the pool and 11.2 (9.6-12.7)% of harmless rewordings. The ceiling finding_f1 catches 57.3 (53.1-61.1)% at a realised 18.9 (17.5-20.4)% flagged with 0% of harmless flagged.
2. **Catch at a fixed budget is capped by prevalence**: with 39.8% planted errors in the full test pool (33.0% in the judge subset), a monitor that flags 1 / 2 / 5 / 10% of candidates can catch at most 2.5 / 5.0 / 12.6 / 25.1% of errors. Read the *realised* flagged share beside each catch rate, not the nominal budget.
3. **Cascade (cheap scorer first, judge on the flagged share): large call savings, but most of the judge's catch is lost**, because small-edit planted errors score high on word scorers and are never sent to the judge: e.g. chrF at s=40% sends 52.6 (50.0-55.2)% to the judge (saves 47% of judge calls) and catches 33.9 (29.8-38.5)% against 71.3 (68.2-74.5)% for the judge alone.
4. **Judge reason-match: the judge's listed error names the planted field in 98.8 (98.1-99.3)% of planted errors (keyword proxy; a control with another field's keywords matches 4.2 (3.1-5.4)%) and the planted category in 84.3 (82.2-86.4)%.**
5. **Step 39b (exploratory): by flag decision, the 3-prompt ensembles do not agree with each other more than the two single prompts do.** Ensemble A vs B agree on 82.0 (77.7-86.0)% of 311 pairs against 87.1 (83.4-90.8)% for P0 vs P3 (on planted errors alone 63.9 (55.4-72.2)% vs 86.6 (80.5-92.4)%), because set A flags fewer errors (45.4 (36.4-54.1)%) than set B (73.1 (65.5-79.7)%). The original Step 39 H1 result (39.2% vs 21.5%, not supported) is unchanged.

Severity levels are **our own provisional labels, not clinician-set** (Step 30). Severity-based monitoring is prior art (DrugBench, arXiv 2606.20663, the id resolves to DrugBench, an AI-control paper on medication harm; its coverage of severity-based monitoring was not read in full, so the prior-art statement follows the brief), so no novelty is claimed. Pool: test 25,887 candidates (1,034 groups), val 16,200; judge subset test 4,729, val judge pool 813 rows in this analysis (pooled across datasets; too small to read per organ). Pre-registration: [PREREG.md](PREREG.md). Code: `usmeta/step44_monitors.py`, `step44_report.py`.

## A + B + C. Catch rate, severity-weighted catch, safety vs usefulness

All values are percentages with 95% group-bootstrap intervals. Flag = score <= the val percentile of that scorer (X-th percentile of val scores over error + harmless + identical candidates). "Harmless" = small, matched, large and other rewordings; "identical" = copies of the reference.

### Full test pool (text scorers; 25,887 candidates)

| scorer | nominal budget | val threshold | realised flagged share | planted errors caught | severity-weighted catch | harmless flagged | identical flagged |
|---|---|---|---|---|---|---|---|
| BLEU | 1% | 0.000 | 1.1 (1.0-1.3) | 2.8 (2.5-3.1) | 4.4 (3.9-4.9) | 0.0 (0.0-0.0) | 0.0 (0.0-0.0) |
| BLEU | 2% | 0.003 | 2.4 (2.2-2.5) | 6.0 (5.6-6.3) | 9.3 (8.8-9.8) | 0.0 (0.0-0.0) | 0.0 (0.0-0.0) |
| BLEU | 5% | 0.219 | 5.4 (5.1-5.7) | 10.6 (9.7-11.6) | 16.6 (15.2-18.1) | 2.2 (1.8-2.5) | 0.0 (0.0-0.0) |
| BLEU | 10% | 0.426 | 9.9 (9.2-10.6) | 10.6 (9.7-11.6) | 16.7 (15.2-18.1) | 10.3 (9.4-11.3) | 0.0 (0.0-0.0) |
| ROUGE-L | 1% | 0.114 | 1.0 (0.9-1.2) | 2.6 (2.3-2.9) | 4.1 (3.5-4.5) | 0.0 (0.0-0.0) | 0.0 (0.0-0.0) |
| ROUGE-L | 2% | 0.143 | 2.2 (2.0-2.3) | 5.5 (5.1-5.9) | 8.6 (8.1-9.2) | 0.0 (0.0-0.0) | 0.0 (0.0-0.0) |
| ROUGE-L | 5% | 0.467 | 5.6 (5.0-6.1) | 10.6 (9.7-11.6) | 16.7 (15.2-18.1) | 2.4 (2.0-2.9) | 0.0 (0.0-0.0) |
| ROUGE-L | 10% | 0.571 | 9.9 (9.6-10.3) | 10.6 (9.7-11.6) | 16.7 (15.2-18.1) | 10.4 (9.7-11.0) | 0.0 (0.0-0.0) |
| chrF | 1% | 0.058 | 1.0 (0.9-1.2) | 2.6 (2.3-2.9) | 4.1 (3.6-4.5) | 0.0 (0.0-0.0) | 0.0 (0.0-0.0) |
| chrF | 2% | 0.077 | 2.1 (2.0-2.3) | 5.4 (5.0-5.7) | 8.4 (7.8-8.9) | 0.0 (0.0-0.0) | 0.0 (0.0-0.0) |
| chrF | 5% | 0.542 | 4.9 (4.6-5.1) | 10.6 (9.7-11.6) | 16.7 (15.2-18.1) | 1.1 (0.9-1.3) | 0.0 (0.0-0.0) |
| chrF | 10% | 0.698 | 9.9 (8.9-10.8) | 10.7 (9.7-11.6) | 16.7 (15.3-18.2) | 10.3 (9.1-11.5) | 0.0 (0.0-0.0) |
| BERTScore | 1% | 0.867 | 1.0 (0.9-1.2) | 2.5 (2.2-2.8) | 3.9 (3.4-4.3) | 0.1 (0.0-0.2) | 0.0 (0.0-0.0) |
| BERTScore | 2% | 0.874 | 2.2 (2.0-2.3) | 5.4 (5.0-5.7) | 8.4 (7.9-8.9) | 0.1 (0.0-0.2) | 0.0 (0.0-0.0) |
| BERTScore | 5% | 0.924 | 5.0 (4.7-5.2) | 10.6 (9.7-11.6) | 16.6 (15.2-18.1) | 1.3 (1.1-1.6) | 0.0 (0.0-0.0) |
| BERTScore | 10% | 0.940 | 9.6 (9.1-10.2) | 10.7 (9.7-11.6) | 16.7 (15.3-18.2) | 9.8 (8.8-10.8) | 0.0 (0.0-0.0) |
| RaTEScore | 1% | 0.357 | 1.0 (0.9-1.2) | 1.4 (1.2-1.7) | 2.2 (1.9-2.6) | 0.9 (0.7-1.0) | 0.0 (0.0-0.0) |
| RaTEScore | 2% | 0.382 | 2.0 (1.8-2.1) | 3.6 (3.2-4.0) | 5.7 (5.1-6.2) | 1.0 (0.8-1.2) | 0.0 (0.0-0.0) |
| RaTEScore | 5% | 0.614 | 4.9 (4.6-5.1) | 8.5 (7.5-9.5) | 13.1 (11.7-14.6) | 2.8 (2.4-3.2) | 0.0 (0.0-0.0) |
| RaTEScore | 10% | 0.740 | 10.0 (9.5-10.5) | 15.2 (14.1-16.3) | 19.9 (18.5-21.4) | 7.2 (6.7-7.7) | 0.0 (0.0-0.0) |

### Ceiling (not a deployable monitor): finding_f1

finding_f1 reads the same fields the templates are built from, so it is an upper bound on templated text, not a real monitor.

| scorer | nominal budget | val threshold | realised flagged share | planted errors caught | severity-weighted catch | harmless flagged | identical flagged |
|---|---|---|---|---|---|---|---|
| finding_f1 (CEILING, upper bound on templated text) | 1% | 0.000 | 4.8 (4.6-5.1) | 12.1 (11.2-13.1) | 19.0 (17.6-20.4) | 0.0 (0.0-0.0) | 0.0 (0.0-0.0) |
| finding_f1 (CEILING, upper bound on templated text) | 2% | 0.000 | 4.8 (4.6-5.1) | 12.1 (11.2-13.1) | 19.0 (17.6-20.4) | 0.0 (0.0-0.0) | 0.0 (0.0-0.0) |
| finding_f1 (CEILING, upper bound on templated text) | 5% | 0.500 | 7.1 (6.9-7.4) | 18.0 (16.9-19.0) | 25.8 (24.4-27.2) | 0.0 (0.0-0.0) | 0.0 (0.0-0.0) |
| finding_f1 (CEILING, upper bound on templated text) | 10% | 0.800 | 14.6 (13.7-15.5) | 36.7 (34.4-39.2) | 41.7 (39.4-44.2) | 0.0 (0.0-0.0) | 0.0 (0.0-0.0) |

### Judge test subset (4,729 candidates): every scorer on the same candidates

Thresholds for the text scorers still come from their full val pool; the judge threshold comes from the val judge sample (pooled, small). Ties make the realised share differ from the nominal budget (the judge, RadGraph-F1 and finding_f1 take few distinct values).

| scorer | nominal budget | val threshold | realised flagged share | planted errors caught | severity-weighted catch | harmless flagged | identical flagged |
|---|---|---|---|---|---|---|---|
| BLEU | 1% | 0.000 | 0.5 (0.3-0.7) | 1.5 (0.9-2.2) | 2.3 (1.3-3.4) | 0.0 (0.0-0.0) | 0.0 (0.0-0.0) |
| BLEU | 2% | 0.003 | 1.6 (1.2-2.0) | 4.8 (3.8-5.9) | 7.3 (5.8-8.9) | 0.0 (0.0-0.0) | 0.0 (0.0-0.0) |
| BLEU | 5% | 0.219 | 7.9 (6.9-8.9) | 19.5 (14.9-24.9) | 29.5 (23.3-36.4) | 2.3 (1.7-3.1) | 0.0 (0.0-0.0) |
| BLEU | 10% | 0.426 | 14.0 (12.1-16.0) | 19.6 (15.1-25.0) | 29.7 (23.5-36.6) | 12.1 (10.6-13.5) | 0.0 (0.0-0.0) |
| ROUGE-L | 1% | 0.114 | 0.5 (0.3-0.7) | 1.4 (0.8-2.1) | 2.1 (1.2-3.1) | 0.0 (0.0-0.0) | 0.0 (0.0-0.0) |
| ROUGE-L | 2% | 0.143 | 1.6 (1.2-1.9) | 4.7 (3.7-5.8) | 7.2 (5.7-8.8) | 0.0 (0.0-0.0) | 0.0 (0.0-0.0) |
| ROUGE-L | 5% | 0.467 | 6.7 (5.5-7.8) | 19.6 (15.1-25.0) | 29.7 (23.5-36.6) | 0.3 (0.1-0.6) | 0.0 (0.0-0.0) |
| ROUGE-L | 10% | 0.571 | 12.3 (11.6-13.1) | 19.6 (15.1-25.0) | 29.7 (23.5-36.6) | 9.4 (7.6-11.2) | 0.0 (0.0-0.0) |
| chrF | 1% | 0.058 | 0.5 (0.3-0.8) | 1.6 (1.0-2.3) | 2.4 (1.5-3.5) | 0.0 (0.0-0.0) | 0.0 (0.0-0.0) |
| chrF | 2% | 0.077 | 1.5 (1.1-1.9) | 4.4 (3.4-5.5) | 6.7 (5.1-8.3) | 0.0 (0.0-0.0) | 0.0 (0.0-0.0) |
| chrF | 5% | 0.542 | 7.1 (6.0-8.2) | 19.6 (15.1-25.0) | 29.7 (23.5-36.6) | 1.0 (0.6-1.4) | 0.0 (0.0-0.0) |
| chrF | 10% | 0.698 | 17.2 (13.6-20.6) | 19.8 (15.2-25.1) | 29.8 (23.5-36.8) | 17.1 (13.5-20.5) | 0.0 (0.0-0.0) |
| BERTScore | 1% | 0.867 | 0.5 (0.3-0.7) | 1.4 (0.8-2.1) | 2.1 (1.2-3.3) | 0.0 (0.0-0.0) | 0.0 (0.0-0.0) |
| BERTScore | 2% | 0.874 | 1.5 (1.1-1.9) | 4.5 (3.4-5.6) | 6.8 (5.2-8.5) | 0.0 (0.0-0.0) | 0.0 (0.0-0.0) |
| BERTScore | 5% | 0.924 | 7.0 (5.9-8.1) | 19.5 (14.9-24.9) | 29.5 (23.3-36.4) | 0.8 (0.5-1.2) | 0.0 (0.0-0.0) |
| BERTScore | 10% | 0.940 | 9.1 (8.0-10.1) | 19.8 (15.2-25.1) | 29.8 (23.5-36.8) | 4.1 (3.3-4.9) | 0.0 (0.0-0.0) |
| RaTEScore | 1% | 0.357 | 1.0 (0.8-1.4) | 1.9 (1.2-2.5) | 2.8 (1.9-3.8) | 0.7 (0.4-1.1) | 0.0 (0.0-0.0) |
| RaTEScore | 2% | 0.382 | 1.6 (1.3-2.0) | 3.5 (2.6-4.5) | 5.3 (4.0-6.8) | 0.7 (0.4-1.1) | 0.0 (0.0-0.0) |
| RaTEScore | 5% | 0.614 | 6.4 (5.3-7.6) | 15.1 (10.3-21.0) | 22.8 (15.9-30.6) | 2.3 (1.7-3.1) | 0.0 (0.0-0.0) |
| RaTEScore | 10% | 0.740 | 16.0 (14.1-17.8) | 27.4 (23.2-32.1) | 34.7 (28.8-40.9) | 11.2 (9.6-12.7) | 0.0 (0.0-0.0) |
| Gemma-2-9B judge | 1% | 0.000 | 6.5 (5.4-7.6) | 14.0 (12.3-15.9) | 18.8 (16.2-21.4) | 2.9 (2.2-3.8) | 0.0 (0.0-0.0) |
| Gemma-2-9B judge | 2% | 0.000 | 6.5 (5.4-7.6) | 14.0 (12.3-15.9) | 18.8 (16.2-21.4) | 2.9 (2.2-3.8) | 0.0 (0.0-0.0) |
| Gemma-2-9B judge | 5% | 0.400 | 27.0 (24.7-29.3) | 71.3 (68.2-74.5) | 78.2 (75.0-81.1) | 5.6 (4.5-7.0) | 0.0 (0.0-0.0) |
| Gemma-2-9B judge | 10% | 0.400 | 27.0 (24.7-29.3) | 71.3 (68.2-74.5) | 78.2 (75.0-81.1) | 5.6 (4.5-7.0) | 0.0 (0.0-0.0) |
| RadGraph-F1 (partial coverage) | 1% | 0.000 | 22.1 (20.0-24.6) | 32.7 (28.3-37.1) | 42.3 (36.5-47.9) | 18.0 (14.6-22.2) | 0.0 (0.0-0.0) |
| RadGraph-F1 (partial coverage) | 2% | 0.000 | 22.1 (20.0-24.6) | 32.7 (28.3-37.1) | 42.3 (36.5-47.9) | 18.0 (14.6-22.2) | 0.0 (0.0-0.0) |
| RadGraph-F1 (partial coverage) | 5% | 0.000 | 22.1 (20.0-24.6) | 32.7 (28.3-37.1) | 42.3 (36.5-47.9) | 18.0 (14.6-22.2) | 0.0 (0.0-0.0) |
| RadGraph-F1 (partial coverage) | 10% | 0.000 | 22.1 (20.0-24.6) | 32.7 (28.3-37.1) | 42.3 (36.5-47.9) | 18.0 (14.6-22.2) | 0.0 (0.0-0.0) |
| finding_f1 (CEILING, upper bound on templated text) | 1% | 0.000 | 7.0 (5.8-8.1) | 21.1 (16.5-26.4) | 31.9 (25.7-38.7) | 0.0 (0.0-0.0) | 0.0 (0.0-0.0) |
| finding_f1 (CEILING, upper bound on templated text) | 2% | 0.000 | 7.0 (5.8-8.1) | 21.1 (16.5-26.4) | 31.9 (25.7-38.7) | 0.0 (0.0-0.0) | 0.0 (0.0-0.0) |
| finding_f1 (CEILING, upper bound on templated text) | 5% | 0.500 | 9.5 (8.6-10.4) | 28.8 (24.7-33.9) | 40.1 (34.8-46.2) | 0.0 (0.0-0.0) | 0.0 (0.0-0.0) |
| finding_f1 (CEILING, upper bound on templated text) | 10% | 0.800 | 18.9 (17.5-20.4) | 57.3 (53.1-61.1) | 62.9 (58.4-67.2) | 0.0 (0.0-0.0) | 0.0 (0.0-0.0) |

**Not available as budgeted monitors (no val scores, so no val threshold; nothing taken from test):** `llm_finding_f1` (saved for the same 2,568 test pairs, no val pair). **RadGraph-F1** has saved scores only for a non-random part of the benchmark (Steps 33-35 designs): partial coverage, shown above and in the table below; its val threshold is 0.000 at every budget (more than 10% of val RadGraph rows score 0), so all budgets coincide.

### RadGraph-F1 on every test row that has a saved score (partial coverage, not comparable with the full-pool tables)

| scorer | nominal budget | val threshold | realised flagged share | planted errors caught | severity-weighted catch | harmless flagged | identical flagged |
|---|---|---|---|---|---|---|---|
| RadGraph-F1 (partial coverage) | 1% | 0.000 | 18.0 (16.7-19.5) | 18.7 (17.4-20.1) | 24.3 (22.8-25.9) | 18.2 (16.0-20.7) | 2.3 (1.1-3.8) |
| RadGraph-F1 (partial coverage) | 2% | 0.000 | 18.0 (16.7-19.5) | 18.7 (17.4-20.1) | 24.3 (22.8-25.9) | 18.2 (16.0-20.7) | 2.3 (1.1-3.8) |
| RadGraph-F1 (partial coverage) | 5% | 0.000 | 18.0 (16.7-19.5) | 18.7 (17.4-20.1) | 24.3 (22.8-25.9) | 18.2 (16.0-20.7) | 2.3 (1.1-3.8) |
| RadGraph-F1 (partial coverage) | 10% | 0.000 | 18.0 (16.7-19.5) | 18.7 (17.4-20.1) | 24.3 (22.8-25.9) | 18.2 (16.0-20.7) | 2.3 (1.1-3.8) |

### B. By severity

**Catch rate by severity at the 10% budget** (1 minor, 2 major, 3 critical; our own labels)

| scorer | severity 1 | severity 2 | severity 3 | weighted |
|---|---|---|---|---|
| BLEU | 0.0 (0.0-0.0) | 0.0 (0.0-0.0) | 46.5 (43.7-49.3) | 16.7 (15.2-18.1) |
| ROUGE-L | 0.0 (0.0-0.0) | 0.0 (0.0-0.0) | 46.5 (43.7-49.3) | 16.7 (15.2-18.1) |
| chrF | 0.0 (0.0-0.0) | 0.1 (0.0-0.1) | 46.5 (43.7-49.3) | 16.7 (15.3-18.2) |
| BERTScore | 0.0 (0.0-0.0) | 0.1 (0.0-0.1) | 46.5 (43.7-49.3) | 16.7 (15.3-18.2) |
| RaTEScore | 8.9 (7.8-9.9) | 3.9 (3.0-4.7) | 46.5 (43.7-49.3) | 19.9 (18.5-21.4) |
| finding_f1 (CEILING, upper bound on templated text) | 22.8 (20.1-25.3) | 35.0 (31.5-38.7) | 59.3 (56.6-61.8) | 41.7 (39.4-44.2) |

Judge subset:

**Catch rate by severity at the 5% budget** (1 minor, 2 major, 3 critical; our own labels)

| scorer | severity 1 | severity 2 | severity 3 | weighted |
|---|---|---|---|---|
| Gemma-2-9B judge | 51.5 (47.1-56.2) | 66.6 (61.9-71.6) | 100.0 (100.0-100.0) | 78.2 (75.0-81.1) |
| chrF | 0.0 (0.0-0.0) | 0.0 (0.0-0.0) | 72.2 (64.3-78.7) | 29.7 (23.5-36.6) |
| RaTEScore | 0.2 (0.0-0.7) | 0.1 (0.0-0.5) | 55.2 (43.2-64.5) | 22.8 (15.9-30.6) |
| finding_f1 (CEILING, upper bound on templated text) | 0.0 (0.0-0.0) | 15.7 (11.8-19.3) | 80.7 (74.8-85.6) | 40.1 (34.8-46.2) |

### Per organ (catch / severity-weighted catch / harmless flagged), 10% budget, full test pool

| scorer | organ | catch | severity-weighted | harmless flagged |
|---|---|---|---|---|
| BLEU | breast | 12.1 (10.6-13.6) | 18.6 (16.4-20.8) | 6.9 (5.1-8.3) |
| BLEU | thyroid | 12.5 (12.1-13.0) | 20.5 (19.7-21.4) | 2.3 (1.8-2.9) |
| BLEU | fetal head | n/a | n/a | n/a |
| ROUGE-L | breast | 12.1 (10.6-13.6) | 18.6 (16.4-20.8) | 3.1 (2.2-3.9) |
| ROUGE-L | thyroid | 12.5 (12.1-13.0) | 20.5 (19.7-21.4) | 11.3 (11.0-11.7) |
| ROUGE-L | fetal head | n/a | n/a | n/a |
| chrF | breast | 12.1 (10.6-13.6) | 18.6 (16.4-20.8) | 7.6 (4.5-10.1) |
| chrF | thyroid | 12.5 (12.1-13.0) | 20.5 (19.7-21.4) | 7.8 (7.0-8.5) |
| chrF | fetal head | n/a | n/a | n/a |
| BERTScore | breast | 12.1 (10.6-13.6) | 18.6 (16.4-20.8) | 3.9 (2.9-4.9) |
| BERTScore | thyroid | 12.5 (12.1-13.0) | 20.5 (19.7-21.4) | 1.6 (1.2-2.1) |
| BERTScore | fetal head | n/a | n/a | n/a |
| RaTEScore | breast | 12.1 (10.6-13.6) | 18.6 (16.4-20.8) | 4.8 (3.8-5.7) |
| RaTEScore | thyroid | 25.4 (24.0-26.8) | 30.2 (28.7-31.9) | 8.1 (7.0-9.4) |
| RaTEScore | fetal head | n/a | n/a | n/a |

Judge subset, 5% budget:

| scorer | organ | catch | severity-weighted | harmless flagged |
|---|---|---|---|---|
| Gemma-2-9B judge | breast | 76.6 (72.6-80.2) | 84.8 (81.7-87.5) | 8.2 (6.0-11.5) |
| Gemma-2-9B judge | thyroid | 78.8 (75.6-81.6) | 83.7 (80.6-86.3) | 1.4 (0.4-2.7) |
| Gemma-2-9B judge | fetal head | n/a | n/a | n/a |
| chrF | breast | 30.0 (21.1-37.9) | 42.1 (31.0-51.2) | 0.0 (0.0-0.0) |
| chrF | thyroid | 14.8 (12.8-17.1) | 24.7 (21.6-28.2) | 0.4 (0.0-1.1) |
| chrF | fetal head | n/a | n/a | n/a |
| RaTEScore | breast | 30.0 (21.1-37.9) | 42.1 (31.0-51.2) | 0.1 (0.0-0.2) |
| RaTEScore | thyroid | 3.5 (2.3-5.0) | 5.6 (3.6-8.0) | 1.2 (0.6-2.0) |
| RaTEScore | fetal head | n/a | n/a | n/a |

### C. Harmless rewordings flagged by type, 10% budget, full test pool

| scorer | small | matched | large | other |
|---|---|---|---|---|
| BLEU | 0.1 (0.0-0.2) | 0.1 (0.0-0.1) | 36.0 (32.9-39.1) | 10.3 (8.8-11.5) |
| ROUGE-L | 11.4 (9.9-13.0) | 0.0 (0.0-0.0) | 23.6 (21.0-26.2) | 10.1 (8.7-11.4) |
| chrF | 0.1 (0.0-0.2) | 0.1 (0.0-0.3) | 41.3 (37.8-44.7) | 6.7 (5.3-8.1) |
| BERTScore | 0.0 (0.0-0.0) | 0.0 (0.0-0.0) | 17.5 (15.7-19.3) | 20.3 (18.0-22.6) |
| RaTEScore | 3.4 (2.7-4.2) | 1.9 (1.4-2.5) | 30.0 (27.7-32.1) | 0.0 (0.0-0.0) |

Judge (judge subset, 5% budget): small 7.7 (5.7-10.2), matched 0.0 (0.0-0.0), large 8.4 (6.4-10.9), other n/a.

## D. Cascade (judge test subset; a cheap scorer first, the judge only on the flagged share)

Stage 1 flags the lowest s% by its val threshold; stage 2 flags a sent candidate if the judge score is at or below the judge val threshold for budget b. The judge val thresholds for b = 5% and 10% coincide (0.4), so those rows are identical. "Calls saved" = share of the pool never sent to the judge (replies already exist; no new call was made).

| first stage | s | judge | sent to judge | judge calls saved | planted errors caught | harmless flagged | identical flagged |
|---|---|---|---|---|---|---|---|
| (none: judge alone) | | b=5% | 100% | 0% | 71.3 (68.2-74.5) | 5.6 (4.5-7.0) | 0.0 (0.0-0.0) |
| BLEU | 10% | b=5% | 14.0 (12.1-16.0) | 86% | 19.6 (15.1-25.0) | 1.9 (1.3-2.5) | 0.0 (0.0-0.0) |
| BLEU | 20% | b=5% | 28.8 (26.7-30.9) | 71% | 19.8 (15.2-25.1) | 2.9 (2.2-3.6) | 0.0 (0.0-0.0) |
| BLEU | 40% | b=5% | 51.7 (47.2-56.3) | 48% | 22.5 (17.9-27.8) | 2.9 (2.2-3.6) | 0.0 (0.0-0.0) |
| ROUGE-L | 10% | b=5% | 12.3 (11.6-13.1) | 88% | 19.6 (15.1-25.0) | 1.6 (1.1-2.2) | 0.0 (0.0-0.0) |
| ROUGE-L | 20% | b=5% | 29.1 (25.3-33.0) | 71% | 19.6 (15.1-25.0) | 3.8 (3.0-4.8) | 0.0 (0.0-0.0) |
| ROUGE-L | 40% | b=5% | 49.8 (45.0-55.0) | 50% | 22.5 (17.9-27.8) | 5.6 (4.5-7.0) | 0.0 (0.0-0.0) |
| chrF | 10% | b=5% | 17.2 (13.6-20.6) | 83% | 19.8 (15.2-25.1) | 1.4 (1.0-1.9) | 0.0 (0.0-0.0) |
| chrF | 20% | b=5% | 32.7 (30.8-34.5) | 67% | 19.8 (15.2-25.1) | 2.8 (2.2-3.6) | 0.0 (0.0-0.0) |
| chrF | 40% | b=5% | 52.6 (50.0-55.2) | 47% | 33.9 (29.8-38.5) | 2.9 (2.2-3.6) | 0.0 (0.0-0.0) |

## E. Judge reason-match (judge test subset, planted-error pairs)

1559 planted-error pairs; the judge's listed errors were read back from the saved raw replies in `.llm_cache` (0 missing). The field match is a **keyword proxy** (frozen keyword map in `step44_monitors.py`), not a human read. The control row (added after the PREREG, not pre-registered) tests each pair's judge text against the keywords of a different field.

| measure | share of all planted errors | share among errors where the judge listed at least one error |
|---|---|---|
| a listed error has the planted **category** | 84.3 (82.2-86.4) | 84.4 (82.3-86.4) |
| a listed error's field text contains a keyword of the planted **field** | 98.8 (98.1-99.3) | 98.8 (98.2-99.4) |
| both on the same listed error | 81.3 (79.0-83.6) | 81.3 (79.0-83.7) |
| control: keywords of a different field | 4.2 (3.1-5.4) | 4.2 (3.1-5.5) |

The judge lists at least one error for almost every planted error, so the weak point of the judge as a monitor is its score threshold (it penalises by severity), not silence. By planted field (among pairs where the judge listed an error):

| planted field | pairs | field match | category match |
|---|---|---|---|
| birads | 33 | 100.0 (100.0-100.0) | 100.0 (100.0-100.0) |
| calc | 10 | 100.0 (100.0-100.0)† | 100.0 (100.0-100.0)† |
| comp | 6 | 100.0 (100.0-100.0)† | 100.0 (100.0-100.0)† |
| count | 172 | 97.7 (95.3-99.4) | 100.0 (100.0-100.0) |
| echo | 8 | 100.0 (100.0-100.0)† | 75.0 (49.7-100.0)† |
| foci | 12 | 100.0 (100.0-100.0)† | 58.3 (33.3-83.3)† |
| halo | 9 | 100.0 (100.0-100.0)† | 55.6 (22.2-88.9)† |
| hc_mm | 144 | 100.0 (100.0-100.0) | 100.0 (100.0-100.0) |
| hist | 22 | 100.0 (100.0-100.0)† | 100.0 (100.0-100.0)† |
| lesion | 306 | 100.0 (100.0-100.0) | 71.2 (58.9-79.4) |
| margin | 12 | 100.0 (100.0-100.0)† | 100.0 (100.0-100.0)† |
| orient | 160 | 99.4 (98.1-100.0) | 65.6 (57.1-73.5) |
| path | 49 | 100.0 (100.0-100.0) | 100.0 (100.0-100.0) |
| plane | 79 | 100.0 (100.0-100.0) | 0.0 (0.0-0.0) |
| pos | 83 | 100.0 (100.0-100.0) | 100.0 (100.0-100.0) |
| post | 3 | 0.0 (0.0-0.0)† | 0.0 (0.0-0.0)† |
| side | 10 | 60.0 (30.0-90.0)† | 90.0 (70.0-100.0)† |
| size_mm | 25 | 100.0 (100.0-100.0)† | 100.0 (100.0-100.0)† |
| size_pct | 400 | 98.5 (97.0-99.7) | 98.5 (97.0-99.7) |
| tirads | 16 | 100.0 (100.0-100.0)† | 100.0 (100.0-100.0)† |

Category match is low where the planted category is "wrong severity/category" for fields the judge describes as another category (plane, lesion, orient); field match is the cleaner reading.

## F. Step 39b (EXPLORATORY; does not change or replace the Step 39 H1 result: 39.2% vs 21.5%, not supported)

Flag threshold from the val P0 judge pool (judge_score <= 0.40 at both 5% and 10% budgets; val has no planted-error replies for P1-P5, so the P0 val threshold on the shared judge_score scale is applied to every prompt and ensemble). 311 of 432 Step 39 pairs have all six replies (the 3 h cap). Agreement = the two judges make the same flag / no-flag decision.

| comparison | all pairs | planted errors | harmless or identical |
|---|---|---|---|
| ensemble A (P0,P1,P2) vs ensemble B (P3,P4,P5) | 82.0 (77.7-86.0) | 63.9 (55.4-72.2) | 93.2 (89.1-96.9) |
| single P0 vs single P3 | 87.1 (83.4-90.8) | 86.6 (80.5-92.4) | 87.5 (82.4-92.6) |

| judge | flags planted errors | flags harmless or identical |
|---|---|---|
| ensemble A | 45.4 (36.4-54.1) | 4.2 (1.6-7.2) |
| ensemble B | 73.1 (65.5-79.7) | 8.9 (5.2-13.2) |
| single P0 | 63.9 (54.9-71.7) | 12.5 (8.3-16.8) |
| single P3 | 67.2 (58.6-75.6) | 9.4 (5.6-13.6) |

The two ensembles differ systematically in how many errors they flag (set A includes two paraphrase prompts that flag fewer), which lowers their agreement; averaging wordings did not make the flag decision more reproducible in this sample. No hypothesis test and no verdict is attached.

## Image check (fixed Step 20 rule; 119 test scans, mask-checkable error fields only; no val threshold exists)

Flag iff the Step 20 tolerance-aware score is below 1. **The MedSAM oracle-box row uses the true box (an upper bound, a CEILING); the U-Net row is label-free.** The false-flag shares on harmless and identical candidates are large: the check disagrees with the reference text on many correct reports, so this fixed rule is not a usable monitor on its own.

| check | candidates | flagged share | planted errors caught | severity-weighted | harmless flagged | identical flagged |
|---|---|---|---|---|---|---|
| MedSAM, true box (CEILING) | 2,207 | 57.3 (51.8-63.0) | 96.8 (95.6-98.0) | 97.0 (95.8-98.1) | 35.6 (26.6-44.7) | 35.3 (26.5-44.1) |
| U-Net, label-free | 2,207 | 57.0 (51.9-62.5) | 93.2 (91.5-95.0) | 94.9 (93.5-96.3) | 37.0 (28.7-46.1) | 36.1 (27.6-44.8) |

## Caveats

- Templated text, one model family, the benchmark prevalence (39.8% planted errors in the full pool, 33.0% in the judge subset) and the planted-error mix, not field prevalence; no precision or PPV is reported.
- The judge subset is a stratified sample (59 cases per dataset, Steps 10d + 12); the judge val pool is small and pooled over datasets, and the judge takes few distinct values, so a nominal budget cannot be hit (realised share is shown).
- A first run of the script used the test score dictionary for the val thresholds by mistake (val coverage 4,817 instead of 16,200); it was fixed before any number was written down and the whole script re-run.
- Severity labels are ours, not clinician-set; the reason-match is a keyword proxy; RadGraph-F1 covers part of the benchmark; `llm_finding_f1` and the U-Net have no val scores for a budget; HiSBreast and free text are not part of this step.
