# Step 18 — Pre-registration (written 2026-10-28, before any scorer was run on any threshold candidate)

Exploratory. Question: **do report scorers understand clinical thresholds (a size that changes management), or only the size of an edit?**
Uses the frozen versions (`freeze-v1`: templates_v2, bench builders, scorers, judge prompt_v2) and the locked splits. Design and any tuning on dev/val only; final numbers on test via `usmeta.splits.load('test')`. The hypotheses below are fixed now and will not be changed after seeing results; all are reported, including the ones that fail. Written before step 1 (feasibility counts), so the counts cannot shape the wording.

## Setup shared by all hypotheses
- Thresholds: ACR TI-RADS 2017 as given by the owner (TR3 follow-up ≥15 mm, FNA ≥25 mm; TR4 ≥10 / ≥15 mm; TR5 ≥5 / ≥10 mm; TR1/TR2 none), "to confirm against Tessler 2017".
- A **matched pair** = two planted size errors in the SAME case with the SAME absolute change (delta = 3 mm primary; 5 mm and 2 mm secondary), one direction up and one down, where one crosses a follow-up/FNA threshold ("crossing") and the other does not ("non-crossing"). Digit count and token edit fraction are matched where possible and logged. **Controls** = cases where neither direction crosses.
- Contrast per scorer: **d = score(non-crossing) − score(crossing)** per pair (positive = the scorer penalises the crossing error more). Direction-only asymmetry is removed by a difference-in-differences: **DiD = mean d over matched pairs − mean d over controls** (controls use the same up/down labelling). Group-level bootstrap, 1,000 resamples, seed 0, 95% CI. Cells with n < 30 groups/cases are "too small to compare".
- "Penalises crossing more" is claimed only when the DiD CI excludes 0 on the test split.
- Primary analysis: the pooled-by-dataset rows on TEST at delta = 3 mm, per dataset and per TI-RADS level (no pooling that hides differences). 5 mm and 2 mm are secondary and are reported but do not rescue or sink a hypothesis.

## H1 — Layer 0 scorers see edit size, not thresholds
BLEU, ROUGE-L, chrF, BERTScore and RaTEScore give the same penalty to a crossing and a non-crossing size error of equal absolute change and equal edit size.
- **Holds** (per scorer) if the DiD CI includes 0, or the DiD is negative (crossing penalised less), on test at delta = 3 mm.
- **Falsified** (per scorer) if the DiD CI is entirely above 0 (crossing penalised more). H1 as a whole is falsified if any one of the five is falsified in at least one dataset with n ≥ 30 pairs.
- Sanity requirement: identical copies score 1.0 on every scorer (if not, stop; no claim is made).

## H2 — finding_f1 and the Gemma sentence_check also fail to separate them
Both see "the size differs" but not whether it matters.
- finding_f1 gives size credit that is linear in the relative error, so equal absolute change from the same reference size gives the same credit by construction; we predict the DiD is 0. **Falsified** only if its DiD CI is above 0 (it would then be reading something we did not expect).
- sentence_check (frozen prompt_v2, greedy): **Holds** if the DiD CI includes 0 or is below 0. **Falsified** if the DiD CI is above 0 on test (the judge penalises the crossing error more) in at least one dataset with n ≥ 30 pairs.
- H2 is reported separately for the two scorers.

## H3 — the predicted-mask image check cannot resolve decision-relevant differences below its own measurement error
Layer 3 (`mask_verified_facts`) with MedSAM masks prompted by TRUE boxes (the Step 16 setup, so this is the easy case).
- **Holds** if, per dataset with n ≥ 30 scans, (a) the median absolute size error of the predicted mask is **larger than the smallest delta tested (2 mm)**, AND (b) the share of cases where the predicted size lands on the other side of a threshold than the true size is **≥ 10%**, AND (c) the AUROC of the predicted-mask check against matched synonyms, in the size-change bin of 3 mm, has a CI that includes 0.5 or is below the true-mask AUROC by more than 0.15.
- **Falsified** if (a) is false (median error ≤ 2 mm) AND the AUROC at 3 mm has a CI entirely above 0.5 within 0.15 of the true-mask AUROC.
- Mixed outcomes (some of a, b, c true) are reported as "partly holds", with each part shown.
- The true-mask check is a circular upper bound (reference came from the same masks); it is a reference row, not a result.

## H4 (optional ablation) — giving the judge the cutoffs helps
A new judge prompt_v3 that adds the TI-RADS cutoffs, tuned on dev/val only, frozen, run once on test, compared with prompt_v2 ("prompt_v3, cutoffs given").
- **Holds** if the prompt_v3 DiD CI is above 0 on test AND is larger than the prompt_v2 DiD by more than the CI width of the difference (paired bootstrap), with identical copies still 1.0.
- **Falsified** if the prompt_v3 DiD CI includes 0, or identical copies drop below 1.0, or the AUROC against matched synonyms falls by more than 0.05.
- Skipped (and reported as "not run") if it would take more than 2 extra hours.

## Not claimed
No "first" claims: we found no work that tests report scorers on guideline-threshold crossing in ultrasound (search not exhaustive). Thresholds and severity are guideline-derived, not clinician-confirmed.

---

# Amendment 1 (2026-10-28, appended before any scorer was run; the original text above is unchanged)

Step 1 found 0 eligible cases (no dataset has both a size in mm and a TI-RADS level; see `feasibility.md`). The owner then approved synthetic sizes. What changes:

1. **Main experiment (H1, H2, H4; text scorers only): synthetic size, real TI-RADS level.** Cases are DDTI cases with a real TI-RADS level TR3–TR5 (TR1/TR2 dropped, they have no cutoffs). DDTI has no size in mm, so the nodule size in mm is **synthetic**, set near the ACR TI-RADS cutoffs (margins of 2, 3 and 5 mm either side) plus control cases far from any cutoff. The TI-RADS level is never invented; DDTI's 4a/4b/4c are mapped to ACR TR4 ("to confirm"). Every such report, candidate and table is labelled **"synthetic size, real TI-RADS level"**. There is **no image check** in the main experiment (there is no real thyroid size to measure).
2. **H3 moves to BrEaST at 20 mm (secondary, "to confirm", not a BI-RADS rule).** H3 is tested on BrEaST malignant cases with real pixel-size millimetres, MedSAM prompted with TRUE boxes (Step 16 setup), against the 20 mm staging-style cutoff. The three H3 conditions are applied with these definitions: (a) median absolute size error of the predicted mask larger than the smallest delta (2 mm); (b) share of cases whose predicted size lies on the other side of 20 mm than the true size ≥ 10%; (c) the AUROC part of the original H3 can only be computed where size-error candidates exist for these cases and is reported if n ≥ 30, otherwise H3 is judged on (a) and (b) only and the cell is marked "too small to compare" if n < 30. DDTI is not used for H3.
3. H1, H2, H4 keep their wording, falsifiers and the primary analysis (test, delta = 3 mm, per dataset and level); the dataset is DDTI only, so "per dataset" is DDTI and the per-level rows are TR3, TR4, TR5 (TR3 has only 19 DDTI cases in all splits, so it will be "too small to compare" and is shown but not pooled).
4. Everything else is unchanged: frozen versions, dev/val for design, test via `usmeta.splits.load('test')`, identical copies must score 1.0, stop-and-ask conditions.

---

# Amendment 2 (2026-10-28; design details fixed from counts only, before any scorer was run; Amendment 1 and the original text are unchanged)

Built `usmeta/bench_v3_threshold.py` → `bench_v3_threshold.jsonl` (new file; `bench_v2d` is untouched). Every row carries `data_label = "synthetic size, real TI-RADS level"`.
- **Cases:** DDTI cases with a real TI-RADS label 3, 4a, 4b, 4c or 5 (307 of 349 labelled; TR2 = 42 dropped). Levels for thresholds: 3→TR3 (15/25 mm), 4a–4c→TR4 (10/15 mm; mapping "to confirm"), 5→TR5 (5/10 mm). The report states the real label as DDTI writes it ("TI-RADS 4a").
- **Synthetic size:** 4 independent replicas per real case (seeded by crc32 of case id and replica number, not by any score). Role "pair" (70%): size = cutoff ± margin with margin ∈ {1, 2, 3, 5} mm (the owner's 2, 3, 5 plus 1, so that δ = 2 and 3 pairs are not too rare), size ≥ 4 mm. Role "control" (30%): 4–40 mm, at least 6 mm from every cutoff of its level, so no ±5 mm change crosses one.
- **Candidates per replica:** size errors ±1, 2, 3, 5 mm and ±5, 10, 20, 30, 50 % (each tagged crossing yes/no, thresholds crossed, distance to the nearest cutoff, digit counts, word and character edit fractions); the Step 5 rerun2 matched one-word synonyms (`nodule→lesion`, `Assessment:→Impression:`, `is seen→is demonstrated`); one identical copy. 26,214 rows over 1,228 replicas (dev 480, val 252, test 496 — see the counts in results.md).
- **Pairs:** for a replica and δ ∈ {2, 3, 5} mm, the up and down errors form a valid matched pair if exactly one of them crosses a cutoff (crossing ⇔ (size ≥ t) changes). **Primary analysis = valid pairs whose two candidates have the same digit count (digit-matched), δ = 3 mm, pooled over TR3–TR5 on the test split, plus TR4 alone.** All valid pairs (digit-matched or not) are the sensitivity analysis. Per-level cells with fewer than 30 pairs/groups are "too small to compare" (TR3 and TR5 will mostly be).
- **DiD (as in the pre-registered contrast):** each pair has an orientation (crossing is the up error, or the down error); d = score(non-crossing) − score(crossing); the control analogue for the same orientation is score(down) − score(up) over control replicas (sign-flipped for the other orientation); DiD = mean over pairs of (d − control mean of the same orientation). Group (patient) level bootstrap over pairs and controls jointly, 1,000 resamples, seed 0. The controls sit at larger sizes than the pair cases (a limitation: control sizes cannot be near a cutoff).
- **Units are not independent:** four replicas of one real case share their group; all intervals resample patient groups, never replicas.
- **Dose-response:** per-replica AUROC of the errors in a size-change bin against the matched synonyms (ties 0.5), averaged over replicas; bins = |change| of 1, 2, 3, 5 mm and 5, 10, 20, 30, 50 %; smallest detectable change = the smallest bin whose group-bootstrap CI excludes 0.5.
- **Judge:** run on the pairs needed for the primary contrast first (δ = 3 mm up and down of every pair/control replica, plus the matched synonyms and identical copies), then the dose-response bins if time allows within the 3-hour limit; n reported.
- **H3 on BrEaST** (Amendment 1) is run separately in `partb`-style code with the Step 16 setup.

**Erratum to Amendment 2:** the replica counts are dev 476, val 240, test 512 (1,228 in all), not the numbers written above.
