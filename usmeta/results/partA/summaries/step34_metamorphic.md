# Step 34: metamorphic checks (no ground truth needed)

Limitations: [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md). Code: `usmeta/step34_metamorphic.py`, `step34_report.py` (new files; saved Step 28 reports; frozen scorers imported unchanged). Test split read once, logged (`usmeta.step34_metamorphic`). **The HiSBreast texts and translations never leave `usmeta/local_data` (scores and caches for them are git-ignored); only aggregated violation rates appear here.**

**Relations** (T = a transformation of a text x; s(r, y) = a scorer comparing y with the reference r; for sets (i) and (ii) r = x, for (iii) r = the label reference and x = the writer report): **R1** unit invariance (mm to cm or back); **R2** sentence-order invariance (reverse the order); **R3** synonym invariance (one one-token synonym swap); **R4** a number swap must lower the score; **R5** a negation flip must lower the score; **R6** the score must be monotone in error size (the first measurement number x 0.75, 0.5 down and x 1.25, 2.0 up). For R1-R3 a **violation** is |s(r, T(x)) - s(r, x)| > 0.05 (sensitivity 0.10); for R4 and R5 it is s(r, error text) >= s(r, harmless rewording of the same text), i.e. the error is NOT scored strictly lower than a one-token synonym swap (or, if none applies, a reorder, or x itself); for R6 any step to a larger error that raises the score. The full definitions, the thresholds and the item sets are in the docstring of `step34_metamorphic.py`, fixed before any score was computed. **Violation rate = violations / applicable items** (an item is applicable when the transformation exists); 95% CI by bootstrap over items; † = fewer than 30 applicable items: too small to compare.

Items: 300 templated test references (100 per organ), 41 HiSBreast test texts, 180 writer reports. Applicable items per relation: templated: R1 112, R2 297, R3 247, R4 276, R5 200, R6 276; hisbreast: R1 0, R2 17, R3 2, R4 0, R5 11, R6 0; writer: R1 61, R2 179, R3 159, R4 63, R5 151, R6 63. LLM-based scorers (judge, `llm_finding_f1`) run on a capped subset: 24 templated, 10 HiSBreast, 20 writer reports.

## Headline

- **Invariance (R1-R3, delta 0.05), mean violation rate over the three relations, all items:** BLEU 60%, ROUGE-L 48%, chrF 36%, RaTEScore 35%, judge_score (subset) 30%, finding_f1 (regex; templated only) 6%, BERTScore 5%, llm_finding_f1 (v3; subset) 5%. A scorer that is invariant to harmless rewording has a low rate; the word scorers are the least invariant because they react to how many characters change.
- **"Must lower" (R4, R5), mean violation rate, all items:** ROUGE-L 93%, chrF 79%, BERTScore 64%, RaTEScore 60%, finding_f1 (regex; templated only) 44%, BLEU 40%, llm_finding_f1 (v3; subset) 39%, judge_score (subset) 29%. A low rate means the error is scored lower than a harmless synonym swap of the same text; a high rate means the scorer cannot tell the error from the harmless edit.
- A scorer can be invariant because it is insensitive to everything (R1-R3 low, R4-R5 high); read the two groups together. Per relation and item set, with intervals, below.

## R1: unit invariance (violation = change > 0.05; the 0.10 sensitivity is in the second table)

| scorer | (i) templated test references | (ii) HiSBreast test texts (local only) | (iii) Step 28 writer reports | all items |
|---|---|---|---|---|
| BLEU | 100% (100–100) n=112 | — | 0% (0–0) n=61 | 65% (57–72) n=173 |
| ROUGE-L | 96% (93–99) n=112 | — | 0% (0–0) n=61 | 62% (55–70) n=173 |
| chrF | 88% (81–94) n=112 | — | 0% (0–0) n=61 | 57% (49–64) n=173 |
| BERTScore | 0% (0–0) n=112 | — | 0% (0–0) n=61 | 0% (0–0) n=173 |
| RaTEScore | 79% (71–86) n=112 | — | 0% (0–0) n=61 | 51% (43–59) n=173 |
| finding_f1 (regex; templated only) | 0% (0–0) n=112 | — | 0% (0–0) n=61 | 0% (0–0) n=173 |
| llm_finding_f1 (v3; subset) | 0% (0–0) n=7 † | — | 0% (0–0) n=3 † | 0% (0–0) n=10 † |
| judge_score (subset) | 86% (57–100) n=7 † | — | 0% (0–0) n=3 † | 60% (33–89) n=10 † |

R1 with delta = 0.10:

| scorer | (i) templated test references | (ii) HiSBreast test texts (local only) | (iii) Step 28 writer reports | all items |
|---|---|---|---|---|
| BLEU | 88% (81–94) n=112 | — | 0% (0–0) n=61 | 57% (49–64) n=173 |
| ROUGE-L | 88% (81–94) n=112 | — | 0% (0–0) n=61 | 57% (49–64) n=173 |
| chrF | 46% (37–54) n=112 | — | 0% (0–0) n=61 | 29% (23–36) n=173 |
| BERTScore | 0% (0–0) n=112 | — | 0% (0–0) n=61 | 0% (0–0) n=173 |
| RaTEScore | 44% (34–53) n=112 | — | 0% (0–0) n=61 | 28% (22–35) n=173 |
| finding_f1 (regex; templated only) | 0% (0–0) n=112 | — | 0% (0–0) n=61 | 0% (0–0) n=173 |
| llm_finding_f1 (v3; subset) | 0% (0–0) n=7 † | — | 0% (0–0) n=3 † | 0% (0–0) n=10 † |
| judge_score (subset) | 71% (43–100) n=7 † | — | 0% (0–0) n=3 † | 50% (18–80) n=10 † |

## R2: sentence-order invariance (violation = change > 0.05; the 0.10 sensitivity is in the second table)

| scorer | (i) templated test references | (ii) HiSBreast test texts (local only) | (iii) Step 28 writer reports | all items |
|---|---|---|---|---|
| BLEU | 98% (97–100) n=297 | 100% (100–100) n=17 † | 0% (0–0) n=179 | 63% (58–67) n=493 |
| ROUGE-L | 100% (100–100) n=297 | 71% (47–88) n=17 † | 1% (0–3) n=179 | 63% (59–67) n=493 |
| chrF | 24% (20–29) n=297 | 35% (18–59) n=17 † | 0% (0–0) n=179 | 16% (13–19) n=493 |
| BERTScore | 26% (21–31) n=297 | 24% (6–47) n=17 † | 0% (0–0) n=179 | 16% (13–20) n=493 |
| RaTEScore | 1% (0–2) n=297 | 18% (0–35) n=17 † | 5% (2–8) n=179 | 3% (2–4) n=493 |
| finding_f1 (regex; templated only) | 0% (0–0) n=297 | — | 2% (1–4) n=179 | 1% (0–2) n=476 |
| llm_finding_f1 (v3; subset) | 0% (0–0) n=24 † | 60% (20–100) n=5 † | 20% (5–40) n=20 † | 14% (6–24) n=49 |
| judge_score (subset) | 33% (17–54) n=24 † | 20% (0–60) n=5 † | 11% (0–26) n=19 † | 23% (12–35) n=48 |

R2 with delta = 0.10:

| scorer | (i) templated test references | (ii) HiSBreast test texts (local only) | (iii) Step 28 writer reports | all items |
|---|---|---|---|---|
| BLEU | 40% (35–45) n=297 | 76% (53–94) n=17 † | 0% (0–0) n=179 | 27% (23–31) n=493 |
| ROUGE-L | 93% (89–96) n=297 | 71% (47–88) n=17 † | 0% (0–0) n=179 | 58% (54–63) n=493 |
| chrF | 0% (0–0) n=297 | 0% (0–0) n=17 † | 0% (0–0) n=179 | 0% (0–0) n=493 |
| BERTScore | 0% (0–0) n=297 | 0% (0–0) n=17 † | 0% (0–0) n=179 | 0% (0–0) n=493 |
| RaTEScore | 1% (0–2) n=297 | 18% (0–35) n=17 † | 0% (0–0) n=179 | 1% (0–2) n=493 |
| finding_f1 (regex; templated only) | 0% (0–0) n=297 | — | 2% (0–4) n=179 | 1% (0–1) n=476 |
| llm_finding_f1 (v3; subset) | 0% (0–0) n=24 † | 60% (20–100) n=5 † | 10% (0–25) n=20 † | 10% (2–19) n=49 |
| judge_score (subset) | 21% (4–38) n=24 † | 20% (0–60) n=5 † | 11% (0–26) n=19 † | 17% (6–28) n=48 |

## R3: synonym invariance (violation = change > 0.05; the 0.10 sensitivity is in the second table)

| scorer | (i) templated test references | (ii) HiSBreast test texts (local only) | (iii) Step 28 writer reports | all items |
|---|---|---|---|---|
| BLEU | 84% (79–88) n=247 | 100% (100–100) n=2 † | 0% (0–0) n=159 | 51% (46–56) n=408 |
| ROUGE-L | 28% (23–34) n=247 | 100% (100–100) n=2 † | 0% (0–0) n=159 | 17% (14–21) n=408 |
| chrF | 59% (53–65) n=247 | 100% (100–100) n=2 † | 0% (0–0) n=159 | 36% (32–41) n=408 |
| BERTScore | 0% (0–0) n=247 | 0% (0–0) n=2 † | 0% (0–0) n=159 | 0% (0–0) n=408 |
| RaTEScore | 80% (75–85) n=247 | 100% (100–100) n=2 † | 8% (4–12) n=159 | 52% (47–57) n=408 |
| finding_f1 (regex; templated only) | 28% (22–33) n=247 | — | 0% (0–0) n=159 | 17% (13–21) n=406 |
| llm_finding_f1 (v3; subset) | 0% (0–0) n=20 † | 0% (0–0) n=1 † | 0% (0–0) n=17 † | 0% (0–0) n=38 |
| judge_score (subset) | 5% (0–15) n=20 † | 100% (100–100) n=1 † | 6% (0–18) n=17 † | 8% (0–18) n=38 |

R3 with delta = 0.10:

| scorer | (i) templated test references | (ii) HiSBreast test texts (local only) | (iii) Step 28 writer reports | all items |
|---|---|---|---|---|
| BLEU | 28% (23–34) n=247 | 100% (100–100) n=2 † | 0% (0–0) n=159 | 17% (14–21) n=408 |
| ROUGE-L | 9% (5–13) n=247 | 50% (0–100) n=2 † | 0% (0–0) n=159 | 6% (4–8) n=408 |
| chrF | 28% (23–34) n=247 | 50% (0–100) n=2 † | 0% (0–0) n=159 | 17% (14–21) n=408 |
| BERTScore | 0% (0–0) n=247 | 0% (0–0) n=2 † | 0% (0–0) n=159 | 0% (0–0) n=408 |
| RaTEScore | 68% (62–74) n=247 | 100% (100–100) n=2 † | 0% (0–0) n=159 | 42% (37–47) n=408 |
| finding_f1 (regex; templated only) | 28% (22–33) n=247 | — | 0% (0–0) n=159 | 17% (13–21) n=406 |
| llm_finding_f1 (v3; subset) | 0% (0–0) n=20 † | 0% (0–0) n=1 † | 0% (0–0) n=17 † | 0% (0–0) n=38 |
| judge_score (subset) | 0% (0–0) n=20 † | 100% (100–100) n=1 † | 6% (0–18) n=17 † | 5% (0–14) n=38 |

## R4: number swap must lower

| scorer | (i) templated test references | (ii) HiSBreast test texts (local only) | (iii) Step 28 writer reports | all items |
|---|---|---|---|---|
| BLEU | 26% (21–32) n=276 | — | 89% (79–95) n=63 | 38% (33–43) n=339 |
| ROUGE-L | 100% (100–100) n=276 | — | 90% (83–97) n=63 | 98% (97–99) n=339 |
| chrF | 82% (77–86) n=276 | — | 62% (49–75) n=63 | 78% (73–82) n=339 |
| BERTScore | 81% (76–86) n=276 | — | 75% (63–84) n=63 | 80% (75–84) n=339 |
| RaTEScore | 62% (56–67) n=276 | — | 41% (30–54) n=63 | 58% (53–64) n=339 |
| finding_f1 (regex; templated only) | 0% (0–0) n=276 | — | 97% (92–100) n=63 | 18% (14–22) n=339 |
| llm_finding_f1 (v3; subset) | 0% (0–0) n=21 † | — | 100% (100–100) n=3 † | 12% (0–27) n=24 † |
| judge_score (subset) | 0% (0–0) n=21 † | — | 100% (100–100) n=3 † | 12% (0–27) n=24 † |

## R5: negation flip must lower

| scorer | (i) templated test references | (ii) HiSBreast test texts (local only) | (iii) Step 28 writer reports | all items |
|---|---|---|---|---|
| BLEU | 24% (18–30) n=200 | 0% (0–0) n=11 † | 69% (61–75) n=151 | 42% (36–47) n=362 |
| ROUGE-L | 100% (100–100) n=200 | 45% (18–73) n=11 † | 75% (68–81) n=151 | 88% (85–91) n=362 |
| chrF | 100% (100–100) n=200 | 0% (0–0) n=11 † | 61% (53–69) n=151 | 81% (76–85) n=362 |
| BERTScore | 38% (32–45) n=200 | 45% (18–73) n=11 † | 63% (55–70) n=151 | 49% (44–54) n=362 |
| RaTEScore | 86% (80–90) n=200 | 0% (0–0) n=11 † | 36% (28–44) n=151 | 62% (57–67) n=362 |
| finding_f1 (regex; templated only) | 49% (42–56) n=200 | — | 100% (100–100) n=151 | 71% (66–75) n=351 |
| llm_finding_f1 (v3; subset) | 37% (16–58) n=19 † | 50% (0–100) n=4 † | 100% (100–100) n=17 † | 65% (51–79) n=40 |
| judge_score (subset) | 0% (0–0) n=19 † | 25% (0–75) n=4 † | 100% (100–100) n=17 † | 45% (29–59) n=40 |

## R6: monotone in error size

| scorer | (i) templated test references | (ii) HiSBreast test texts (local only) | (iii) Step 28 writer reports | all items |
|---|---|---|---|---|
| BLEU | 0% (0–0) n=276 | — | 3% (0–8) n=63 | 1% (0–1) n=339 |
| ROUGE-L | 2% (0–3) n=276 | — | 0% (0–0) n=63 | 1% (0–3) n=339 |
| chrF | 22% (17–27) n=276 | — | 49% (37–62) n=63 | 27% (22–32) n=339 |
| BERTScore | 46% (40–51) n=276 | — | 94% (87–98) n=63 | 55% (49–60) n=339 |
| RaTEScore | 43% (38–50) n=276 | — | 87% (79–95) n=63 | 52% (46–57) n=339 |
| finding_f1 (regex; templated only) | 0% (0–0) n=276 | — | 11% (5–19) n=63 | 2% (1–4) n=339 |
| llm_finding_f1 (v3; subset) | 0% (0–0) n=21 † | — | 33% (0–100) n=3 † | 4% (0–13) n=24 † |
| judge_score (subset) | 0% (0–0) n=21 † | — | 0% (0–0) n=3 † | 0% (0–0) n=24 † |

Share of items whose whole chain is flat (the score does not change with the error size at all):

| scorer | (i) templated test references | (ii) HiSBreast test texts (local only) | (iii) Step 28 writer reports | all items |
|---|---|---|---|---|
| BLEU | 0% | — | 94% | 17% |
| ROUGE-L | 0% | — | 98% | 18% |
| chrF | 0% | — | 29% | 5% |
| BERTScore | 0% | — | 0% | 0% |
| RaTEScore | 26% | — | 6% | 22% |
| finding_f1 (regex; templated only) | 0% | — | 87% | 16% |
| llm_finding_f1 (v3; subset) | 0% | — | 67% | 8% |
| judge_score (subset) | 0% | — | 100% | 12% |

## Caveats

- **No ground truth, but also no clinical validity:** a relation says how a scorer should move, not whether the text is right. The transformations are rule-based and crude on free text (R5 deletes the first "no " or " not ", R4 changes a number), so some transformed texts are unnatural; the same rules were applied to every scorer.
- **HiSBreast texts are short conclusions with few measurements:** R1, R4 and R6 apply to 0, 0 and 0 of the 41 texts and R3 to 2, so nearly every HiSBreast cell is too small to compare. They are machine translations of licence-blank patient data (local only).
- **Judge and `llm_finding_f1` on a capped subset** (24 templated rather than 20 items, because a case id picked for the writer subset also flags the same case's templated reference) (a few dozen items; most cells under 30 applicable items: too small to compare); the judge is prompt-sensitive (Step 21c) and was run once.
- **delta = 0.05** is a fixed choice on a scale where BERTScore only spans a narrow band; the 0.10 tables show the sensitivity. R4 / R5 compare the error with a harmless synonym swap, which makes them a no-label version of the discrimination test, not an independent check of facts.
- **Writer reports are scored against the label reference** and are long markdown text; word-overlap scores are near zero for them whatever the transformation, which makes invariance look good (nothing to lose) and "must lower" fail (nothing to lower).
