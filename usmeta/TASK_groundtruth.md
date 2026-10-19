# Task: Ground-truth v2 — build the TRUE report from the image masks (do this BEFORE TASK_layers.md)

Read CLAUDE.md first. Same rules: no "first ultrasound benchmark" claims, don't overwrite existing
results or bench files (write new ones), commit after each step, short status after each step.

## Why
Today the true report is a fixed template filled from dataset labels (class, BI-RADS, a rough location grid).
Segmentation masks let us MEASURE the image instead, so the true report is closer to what a person
would write while looking at the scan. Everything below is computed deterministically from masks, pixel
size and expert labels. No LLM writes the ground truth (UltraG-Bench used GPT-5.5 for theirs, so we say so
and differ on purpose).

## What we can measure (reliable) vs. what we cannot (do not fake it)
Reliable from a mask: lesion count, side (left/right of image centre), position (upper/middle/lower,
central/lateral), longest diameter and area in mm (needs pixel size), orientation (wider-than-tall or not),
shape descriptors (solidity, circularity/roundness, ellipse fit, contour irregularity), margin smoothness
(contour roughness), relative lesion size vs image.
Rough, label as "approximate": echo contrast of lesion vs surrounding tissue (mean intensity inside mask vs a
ring around it), posterior shadowing/enhancement (intensity below the lesion vs beside it).
Not measurable from masks: pathology, histology, BI-RADS/TI-RADS category, calcifications. Keep these
from expert labels exactly as now.
BrEaST has expert descriptors (shape, margin, echogenicity, posterior features, halo, calcifications):
use the expert descriptor as truth and use the mask-computed value only as a cross-check
(report agreement % per descriptor — this validates our mask features, and is a result worth keeping).

## Pixel sizes / units
- BrEaST: Pixel_size column in breast.xlsx. HC18: training_set_pixel_size_and_HC.csv (mm per pixel).
- BUS-BRA, TN3K, TN5000: no pixel size -> report size as % of image only. Never invent mm.

## Step 1 — usmeta/usmeta/measure.py
- Functions: load mask -> binary, connected components, per-lesion measurements (list above), HC18 ellipse
  -> head circumference (Ramanujan) vs the CSV's value (report mean abs error mm as a check on our code).
- TN5000: boxes only -> position, relative size, count (no shape descriptors).
- Tests with synthetic masks (circle of known radius -> known area/diameter/circularity).
- Table of cases measured per dataset, and any case where mask and image sizes disagree (list them).

## Step 2 — richer true reports: usmeta/usmeta/templates_v2.py
- For each dataset write a template that includes measured fields, e.g. breast:
  "A {shape} {margin} mass, {size} mm (longest diameter), is seen in the {side} breast at {position}.
   {echo contrast, marked approximate}. Assessment: BI-RADS {n}. Pathology: {path}."
- Keep the old templates; new benchmark files are bench_v2.jsonl and bench_v2_small.jsonl (same builder style).
- New planted-mistake types now possible, each tagged with an error category:
  wrong measurement (size x0.5 / x1.5 / x2), wrong position, wrong shape, missed lesion, extra lesion,
  plus the existing pathology / BI-RADS / side mistakes. Harmless rewordings stay as before, plus
  unit rewrite (mm <-> cm) for sizes.
- Severity table stays provisional; list every severity assumption in docs/severity.md for clinician review.

## Step 3 — validate and compare
- Re-score the existing baseline scorers (bleu, rougeL, chrf, bertscore, ratescore, fact_checker) on
  bench_v2_small.jsonl, 100 cases per dataset, same outputs as results_stage2 -> results_v2_baseline.md/json.
  Question to answer: do the text-similarity scorers still miss mistakes now that reports contain numbers?
  (Expectation, to be tested not assumed: a size error changes one number, so BLEU should still barely move.)
- Identical-copy mean must be 1.0 for every scorer; if not, stop and fix.

## Step 4 — update README + CLAUDE.md, then continue with usmeta/TASK_layers.md (Layer 1/2/3 now run on bench_v2).

## Stop and ask me if
- mask files don't match image filenames for >5% of cases (give 3 examples),
- mask-computed descriptors agree with BrEaST expert descriptors on <60% (show the table before going on),
- anything needs a download or a gated model.
