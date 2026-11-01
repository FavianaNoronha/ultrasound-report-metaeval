# Step 18 — Do scorers understand clinical thresholds, or only the size of an edit? (exploratory; synthetic size, real TI-RADS level; DDTI only)

**Label on everything below: "synthetic size, real TI-RADS level".** No dataset has both a real size in mm and a TI-RADS level (`feasibility.md`: 0 eligible cases), so with the owner's approval the nodule size in mm is **synthetic** (set near the ACR TI-RADS cut-offs, margins 1–5 mm either side, plus control cases far from any cut-off) and the TI-RADS level is the **real DDTI label** (4a/4b/4c mapped to ACR TR4, "to confirm"; TR1/TR2 dropped; no level invented). Cut-offs (ACR TI-RADS 2017, "to confirm against Tessler 2017"): TR3 follow-up ≥ 15 mm, FNA ≥ 25 mm; TR4 ≥ 10 / ≥ 15; TR5 ≥ 5 / ≥ 10. The thresholds apply to the nodule's maximum dimension; our synthetic size is simply taken as that dimension. Pre-registration: `HYPOTHESES.md` (original text, Amendment 1 synthetic sizes + H3 on BrEaST, Amendment 2 design). Dev/val design notes: `dev_val_notes.md`. Locked test split; final numbers below are test.

**Design in one paragraph.** 307 DDTI cases with a real TR3–TR5 label × 4 independent synthetic sizes (1,228 size sets; test 512). Per size set: a correct report, size errors of ±1, 2, 3, 5 mm and ±5…50 %, and three matched one-word synonyms. A *matched pair* = the up and the down error of the same |change| in the same size set where exactly one crosses a cut-off. Contrast d = score(non-crossing) − score(crossing) (positive = the scorer penalises the crossing error more); difference-in-differences (DiD) subtracts the same asymmetry measured on control size sets. Primary cell: δ = 3 mm, digit-matched pairs, test, pooled TR3–TR5. Intervals resample patient groups (1,000, seed 0). † = fewer than 30 pairs or groups: too small to compare. Edit size is matched: token edit 0.0321 (crossing) vs 0.0324 (non-crossing), character edit 0.0069 vs 0.0059.

## Gates
Identical copies score 1.0 on every scorer (512 copies for Layers 0/1, 91 for the judge; mean = min = 1.0000):
| scorer | identical copies | mean | min |
|---|---|---|---|
| bleu | 512 | 1.0000 | 1.0000 |
| rougeL | 512 | 1.0000 | 1.0000 |
| chrf | 512 | 1.0000 | 1.0000 |
| bertscore[roberta-large] | 512 | 1.0000 | 1.0000 |
| ratescore | 512 | 1.0000 | 1.0000 |
| finding_f1 | 512 | 1.0000 | 1.0000 |
| sentence_f1 | 91 | 1.0000 | 1.0000 |
| judge_score | 91 | 1.0000 | 1.0000 |


## Headline (plain words)
- **Almost no scorer treats a size error that crosses a clinical cut-off differently from one of the same size that does not.** BLEU, ROUGE-L and `finding_f1` give exactly the same score to both (all 139 pairs tie), chrF and BERTScore differ by 0.001 or less, in the *wrong* direction.
- **Two small exceptions.** RaTEScore penalises the crossing error slightly more (DiD +0.015, CI +0.006 to +0.023; 35% of pairs penalise it more, 46% tie, 19% penalise it less; not seen at δ = 2 mm; reversed in TR5). The judge's `judge_score` does too (DiD +0.024, CI +0.0004 to +0.049: lower bound barely above 0; 11% more, 78% tie, 12% less). `sentence_f1` shows no difference (−0.012, CI −0.029 to +0.002).
- **What the judge does is mostly "a size differs", not "a size that matters".** It detects even 1 mm (AUROC 0.89 against matched synonyms, 40 size sets) and 10% changes (0.96), and at ±3 mm it detects crossing and non-crossing errors equally well (0.98 vs 0.99); the other bins have too few crossing errors (< 30) to compare.
- **Word-overlap scorers cannot tell 1 mm from 5 mm** (their dose-response is flat by construction: every size error changes one token), and chrF and BERTScore even score a size error as *more* similar than a one-word synonym (AUROC 0.00), because the synonym changes more characters than a changed number.
- **The image check (H3, BrEaST, 20 mm staging-style cut-off, n = 39 malignant test cases):** MedSAM's median size error with the exact (true-mask) box is 2.0 mm (13%, typically an under-estimate: median signed −2.0 mm); only 1 of 39 cases (2.6%) land on the other side of 20 mm than the true size (5% with a 10% jittered box, 10% with a 20% jittered box). Most cases sit far from the cut-off (median distance 7 mm), so the check rarely has to resolve a decision-relevant margin here; among the 10 cases within 3 mm of the cut-off, 1 flip.

## Hypotheses (pre-registered; all reported)
| hypothesis | verdict | evidence (test) |
|---|---|---|
| **H1** Layer 0 scorers give the same penalty to a threshold-crossing and a non-crossing size error | **Falsified by the letter, effect tiny.** 4 of 5 held | RaTEScore DiD +0.0150 [+0.0064, +0.0230] (139 pairs, 79 groups): crossing penalised slightly more. BLEU, ROUGE-L exactly 0; chrF −0.0008 and BERTScore −0.0001 (crossing penalised *less*, negligible). The RaTEScore effect is not stable: δ = 2 mm [−0.006, +0.014], TR5 negative († n < 30), all-valid pairs [−0.003, +0.009]. |
| **H2** finding_f1 and Gemma sentence_check also fail to separate them | **Partly held** (2 of 3 columns) | finding_f1: exactly 0 (as predicted by construction). sentence_f1: −0.0123 [−0.0285, +0.0015] held. judge_score: +0.0245 [+0.0004, +0.0489], falsified by the pre-registered CI rule, but the lower bound is 0.0004 and it is absent at TR4-only (+0.020, [−0.007, +0.050]) and in the all-valid-pairs sensitivity ([−0.001, +0.046]). |
| **H3** (Amendment 1: BrEaST, 20 mm) the predicted-mask check cannot resolve decision-relevant differences below its own error | **Not supported** (conditions for "holds" not met; the AUROC clause could not be tested) | (a) median error 2.0 mm is not larger than 2 mm; (b) 2.6% flips < 10% (j20 prompt: 10.3%, borderline); (c) BrEaST has no ±mm candidates, so no AUROC. Original thyroid H3 impossible (no real thyroid size). |
| **H4** giving the judge the cut-offs (prompt_v3) improves separation | **Not run** | Skipped: H2 is mixed (sentence_f1 does not separate, judge_score barely does) and a tuned + frozen prompt_v3 run was estimated at about 2 h, the limit. Recommended only if the owner wants it. |

## Primary result: matched pairs, δ = 3 mm, digit-matched, TR3–TR5 pooled (test)
| scorer | pairs (groups) | controls | mean d = non-crossing − crossing | DiD | crossing penalised more / tie / less | verdict |
|---|---|---|---|---|---|---|
| bleu | 139 (79) | 153 | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | 0.00 / 1.00 / 0.00 | no difference (CI includes 0) |
| rougeL | 139 (79) | 153 | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | 0.00 / 1.00 / 0.00 | no difference (CI includes 0) |
| chrf | 139 (79) | 153 | -0.0008 [-0.0012, -0.0004] | -0.0008 [-0.0012, -0.0004] | 0.00 / 0.87 / 0.13 | penalises crossing LESS (CI below 0) |
| bertscore[roberta-large] | 139 (79) | 153 | -0.0001 [-0.0002, -0.0000] | -0.0001 [-0.0002, -0.0000] | 0.28 / 0.02 / 0.70 | penalises crossing LESS (CI below 0) |
| ratescore | 139 (79) | 153 | +0.0156 [+0.0073, +0.0231] | +0.0150 [+0.0064, +0.0230] | 0.35 / 0.46 / 0.19 | penalises crossing MORE (CI above 0) |
| finding_f1 | 139 (79) | 153 | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] | 0.00 / 1.00 / 0.00 | no difference (CI includes 0) |
| sentence_f1 | 139 (79) | 139 | -0.0173 [-0.0351, -0.0016] | -0.0123 [-0.0285, +0.0015] | 0.08 / 0.76 / 0.17 | no difference (CI includes 0) |
| judge_score | 139 (79) | 139 | +0.0144 [-0.0083, +0.0387] | +0.0245 [+0.0004, +0.0489] | 0.11 / 0.78 / 0.12 | penalises crossing MORE (CI above 0) |

By level (δ = 3 mm, digit-matched; DiD [95% CI]; † too small to compare — TR3 has 4 patient groups, TR5 8):
| scorer | TR3 pairs (groups): DiD [CI] | TR4 pairs (groups): DiD [CI] | TR5 pairs (groups): DiD [CI] |
|---|---|---|---|
| bleu | 14 (4) †: +0.0000 [+0.0000, +0.0000] | 112 (67): +0.0000 [+0.0000, +0.0000] | 13 (8) †: +0.0000 [+0.0000, +0.0000] |
| rougeL | 14 (4) †: +0.0000 [+0.0000, +0.0000] | 112 (67): +0.0000 [+0.0000, +0.0000] | 13 (8) †: +0.0000 [+0.0000, +0.0000] |
| chrf | 14 (4) †: -0.0022 [-0.0033, +0.0011] | 112 (67): -0.0007 [-0.0011, -0.0003] | 13 (8) †: -0.0000 [-0.0012, +0.0005] |
| bertscore[roberta-large] | 14 (4) †: +0.0001 [-0.0008, +0.0004] | 112 (67): -0.0001 [-0.0002, -0.0001] | 13 (8) †: -0.0001 [-0.0002, +0.0001] |
| ratescore | 14 (4) †: +0.0448 [+0.0121, +0.0807] | 112 (67): +0.0161 [+0.0082, +0.0243] | 13 (8) †: -0.0261 [-0.0694, -0.0012] |
| finding_f1 | 14 (4) †: +0.0000 [+0.0000, +0.0000] | 112 (67): +0.0000 [+0.0000, +0.0000] | 13 (8) †: +0.0000 [+0.0000, +0.0000] |
| sentence_f1 | 14 (4) †: +0.0000 [+0.0000, +0.0000] | 112 (67): -0.0169 [-0.0327, +0.0009] | 13 (8) †: +0.0063 [-0.0051, +0.0382] |
| judge_score | 14 (4) †: -0.0198 [-0.0429, +0.0333] | 112 (67): +0.0204 [-0.0072, +0.0500] | 13 (8) †: +0.0804 [-0.0301, +0.1625] |

Sensitivity (δ = 2, 5 mm; all valid pairs including unequal digit counts):
| scorer | δ=2 mm, digit-matched | δ=3 mm, digit-matched (primary) | δ=5 mm, digit-matched | δ=3 mm, all valid pairs |
|---|---|---|---|---|
| bleu | n=118: +0.0000 [+0.0000, +0.0000] | n=139: +0.0000 [+0.0000, +0.0000] | n=98: +0.0000 [+0.0000, +0.0000] | n=246: +0.0000 [+0.0000, +0.0000] |
| rougeL | n=118: +0.0000 [+0.0000, +0.0000] | n=139: +0.0000 [+0.0000, +0.0000] | n=98: +0.0000 [+0.0000, +0.0000] | n=246: +0.0000 [+0.0000, +0.0000] |
| chrf | n=118: +0.0000 [-0.0001, +0.0001] | n=139: -0.0008 [-0.0012, -0.0004] | n=98: -0.0060 [-0.0068, -0.0050] | n=246: +0.0006 [+0.0001, +0.0010] |
| bertscore[roberta-large] | n=118: +0.0001 [+0.0001, +0.0002] | n=139: -0.0001 [-0.0002, -0.0000] | n=98: -0.0000 [-0.0001, +0.0001] | n=246: -0.0000 [-0.0001, +0.0000] |
| ratescore | n=118: +0.0042 [-0.0056, +0.0139] | n=139: +0.0150 [+0.0064, +0.0230] | n=98: +0.0188 [+0.0098, +0.0276] | n=246: +0.0031 [-0.0029, +0.0088] |
| finding_f1 | n=118: +0.0000 [+0.0000, +0.0000] | n=139: +0.0000 [+0.0000, +0.0000] | n=98: +0.0000 [+0.0000, +0.0000] | n=246: +0.0000 [+0.0000, +0.0000] |
| sentence_f1 | n=8 †: +0.0000 [-0.0071, +0.0111] | n=139: -0.0123 [-0.0285, +0.0015] | n=9 †: +0.0417 [+0.0000, +0.0924] | n=142: -0.0128 [-0.0285, +0.0008] |
| judge_score | n=8 †: -0.0625 [-0.1565, +0.0067] | n=139: +0.0245 [+0.0004, +0.0489] | n=9 †: +0.0875 [-0.0372, +0.2429] | n=142: +0.0224 [-0.0009, +0.0464] |

## Dose-response: AUROC of size errors vs the matched one-word synonyms (all size sets; judge = 40 size sets per bin except ±3 mm = 281)
Smallest detectable change = the smallest bin whose CI is above 0.5 (and n ≥ 30). Intervals resample patient groups.
| scorer | ±1 mm | ±2 mm | ±3 mm | ±5 mm | smallest bin with CI above 0.5 |
|---|---|---|---|---|---|
| bleu | 0.66 (0.64–0.67) n=512 | 0.66 (0.64–0.67) n=512 | 0.66 (0.64–0.67) n=512 | 0.66 (0.64–0.67) n=512 | ±1 mm |
| rougeL | 0.49 (0.48–0.50) n=512 | 0.49 (0.48–0.50) n=512 | 0.49 (0.48–0.50) n=512 | 0.49 (0.48–0.50) n=512 | none (or too small) |
| chrf | 0.00 (0.00–0.00) n=512 | 0.00 (0.00–0.00) n=512 | 0.00 (0.00–0.00) n=512 | 0.00 (0.00–0.00) n=512 | none (or too small) |
| bertscore[roberta-large] | 0.00 (0.00–0.00) n=512 | 0.00 (0.00–0.00) n=512 | 0.00 (0.00–0.00) n=512 | 0.00 (0.00–0.00) n=512 | none (or too small) |
| ratescore | 0.47 (0.44–0.50) n=512 | 0.47 (0.44–0.49) n=512 | 0.51 (0.48–0.54) n=512 | 0.48 (0.46–0.52) n=512 | none (or too small) |
| finding_f1 | 0.99 (0.98–1.00) n=512 | 0.99 (0.98–1.00) n=512 | 0.99 (0.98–1.00) n=512 | 0.99 (0.98–1.00) n=512 | ±1 mm |
| sentence_f1 | 0.50 (0.50–0.50) n=40 | 0.51 (0.50–0.52) n=40 | 0.56 (0.54–0.58) n=281 | 0.54 (0.51–0.58) n=40 | ±3 mm |
| judge_score | 0.89 (0.79–1.00) n=40 | 0.90 (0.79–1.00) n=40 | 0.99 (0.96–1.00) n=281 | 0.90 (0.79–1.00) n=40 | ±1 mm |

| scorer | ±5 pct | ±10 pct | ±20 pct | ±30 pct | ±50 pct | smallest bin with CI above 0.5 |
|---|---|---|---|---|---|---|
| bleu | 0.66 (0.65–0.67) n=399 | 0.66 (0.64–0.67) n=505 | 0.66 (0.64–0.67) n=512 | 0.66 (0.64–0.67) n=512 | 0.66 (0.64–0.67) n=512 | ±5 pct |
| rougeL | 0.49 (0.48–0.50) n=399 | 0.49 (0.48–0.50) n=505 | 0.49 (0.48–0.50) n=512 | 0.49 (0.48–0.50) n=512 | 0.49 (0.48–0.50) n=512 | none (or too small) |
| chrf | 0.00 (0.00–0.00) n=399 | 0.00 (0.00–0.00) n=505 | 0.00 (0.00–0.00) n=512 | 0.00 (0.00–0.00) n=512 | 0.00 (0.00–0.00) n=512 | none (or too small) |
| bertscore[roberta-large] | 0.00 (0.00–0.00) n=399 | 0.00 (0.00–0.00) n=505 | 0.00 (0.00–0.00) n=512 | 0.00 (0.00–0.00) n=512 | 0.00 (0.00–0.00) n=512 | none (or too small) |
| ratescore | 0.43 (0.40–0.46) n=399 | 0.46 (0.43–0.48) n=505 | 0.49 (0.46–0.52) n=512 | 0.50 (0.47–0.53) n=512 | 0.49 (0.46–0.52) n=512 | none (or too small) |
| finding_f1 | 0.99 (0.98–1.00) n=399 | 0.99 (0.98–1.00) n=505 | 0.99 (0.98–1.00) n=512 | 0.99 (0.98–1.00) n=512 | 0.99 (0.98–1.00) n=512 | ±5 pct |
| sentence_f1 | 0.50 (0.50–0.50) n=35 † | 0.53 (0.52–0.56) n=94 | 0.57 (0.54–0.60) n=132 | 0.54 (0.51–0.58) n=40 | 0.55 (0.50–0.65) n=19 † | ±10 pct |
| judge_score | 0.93 (0.83–1.00) n=35 † | 0.96 (0.90–1.00) n=94 | 0.97 (0.93–1.00) n=132 | 0.90 (0.79–1.00) n=40 | 0.79 (0.63–1.00) n=19 † | ±10 pct |

## Where MedSAM stands against the decision margins (H3, BrEaST malignant, test, n = 39; size = longest diameter of the whole mask in mm)
| prompt | median abs. error (mm) | median rel. error | median signed error (mm) | cases on the other side of 20 mm | flips among cases within 3 mm of 20 mm |
|---|---|---|---|---|---|
| exact | 2.0 | 13% | -2.0 | 1 of 39 (2.6%) | 1 of 10 |
| j10 | 2.0 | 8% | -1.0 | 2 of 39 (5.1%) | 2 of 10 |
| j20 | 1.0 | 8% | -1.0 | 4 of 39 (10.3%) | 3 of 10 |

Median distance from the true size to 20 mm: 7 mm; 16 of 39 cases are ≥ 20 mm. The case is "easy": boxes come from the TRUE mask (oracle localisation); Qwen/MedGemma boxes were too poor to use. No image check was run for the synthetic-size DDTI part (there is no real thyroid size to measure).

## Limits
Templated references; **synthetic sizes** (so no result here says how real nodule sizes sit relative to the cut-offs); one dataset (DDTI) and mostly one level (TR4: 112 of 139 pairs; TR3 and TR5 too small); 4 sizes per real case are not independent (patient groups are resampled); severity guideline-derived, not clinician-confirmed; thresholds "to confirm"; size definition is a stand-in for the maximum dimension; controls sit at larger sizes than the pair cases; the matched synonym is not matched in characters (chrF/BERTScore dose-response is an edit-size artefact); the judge cut-off comparison uses the judge's own 0–1 scores and a 40-size-set dose sample; MedSAM and the judge may have seen the public datasets; one machine. We found no work that tests report scorers on guideline-threshold crossing in ultrasound (search not exhaustive).

Raw: `test_report.json`, `dev_val_report.json`, `h3_breast_raw.json`, `h3_breast_summary.json`, `../../../judge_v3_test.jsonl` (judge replies; scores `scores_v3_*.json` are git-ignored and are recreated with `usmeta.layer0/layer1 score` on `bench_v3_threshold_test.jsonl`). Code: `usmeta/bench_v3_threshold.py`, `step18.py`, `step18_tables.py`, `step18_h3.py`.
