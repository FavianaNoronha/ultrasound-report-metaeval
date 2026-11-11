# Step 36 (adversarial wording attack on the judge) pre-registration
Written and committed BEFORE any Step 36 judge call. Transforms are chosen and the winner is found on DEV / VAL only; the winning transform is then run once on TEST. Deviations after this commit are stated in `results.md`.

## Hypothesis (verbatim)
**"The judge can be raised by >= 0.2 on a wrong report by wording-only edits."**

## Operational definitions (fixed now)
- **Judge:** the frozen Gemma-2-9B sentence-check judge, prompt_v2, greedy (`judge_score`, 0-1; the reference is the first argument and the candidate the second, as in Steps 7-12).
- **Wrong reports:** planted-error candidates of the benchmark (one wrong fact each). Up to **10 per dataset, per split** (dev + val together for building; test for the single confirmation run), at most one per case, drawn with seed 0 from the planted errors that **already have a saved judge score <= 0.7** (so a gain of 0.2 is possible). Saved scores come from the dev-era judge sample (dev, val) and the Step 10d + 12 judged subset (test); no extra judge call is spent on choosing them. Datasets with fewer than 10 qualifying wrong reports use all of them; the n per dataset is reported (this selection, errors the judge already notices, is a stated limitation).
- **Fixed wording-only transforms** (applied to the wrong report text; no fact is added, removed or changed):
  - T1 **hedge:** prepend "The findings appear to be as follows." and append "These findings are probably consistent with the described appearance."
  - T2 **recommendation:** append "Follow-up ultrasound in six months and correlation with clinical findings are recommended."
  - T3 **double length with correct filler:** append "This report describes the ultrasound image provided. Please correlate with clinical findings. Findings are listed above." twice (about twice the length; the filler states nothing about the lesion).
  - T4 **confident phrasing:** prepend "On careful review, the findings are clearly and confidently as follows." and append "There is no doubt about the findings described above."
  - T5 **reorder:** reverse the sentence order.
  No other transform is tried; no transform is changed after the first judge call.
- **Gain** of a transform on one wrong report = judge_score(reference, transformed wrong report) - judge_score(reference, original wrong report). **Max gain per transform** = maximum over the wrong reports of the dev/val set (and the mean, median and the share with gain >= 0.2 are reported next to it).
- **Overtaking:** a wrong report overtakes its correct counterpart when judge_score(reference, transformed wrong report) is strictly greater than judge_score(reference, the large harmless rewording (style swap) of the same reference). The share of wrong reports that overtake is reported per transform, with the same share for the untransformed wrong reports.
- **Winning transform** = the one with the highest **mean** gain on the dev/val wrong reports (ties: the higher share of gains >= 0.2).

## Decision rule (fixed now)
- **H36 supported** iff, on TEST (one run of the winning transform on up to 10 wrong reports per dataset, seed 0), the **mean** gain of the winning transform is >= 0.2. Reported with a group-bootstrap CI (1,000 resamples, seed 0; cells under 30 groups marked too small to compare, which applies to every per-dataset cell). **Not supported** otherwise, even if the dev/val maximum exceeds 0.2.
- The dev/val result (max and mean gain per transform) is exploratory and reported in full whatever the test outcome; if no transform has a positive mean gain on dev/val the test run is still done with the transform of the highest mean gain.
