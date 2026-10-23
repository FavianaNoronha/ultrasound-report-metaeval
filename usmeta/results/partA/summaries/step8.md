# Step 8: Layer 3 image / location check against the TRUE masks (Test 1) (plain-language summary)

**What was built.** `usmeta/location.py`: loaders for the true mask or box of every dataset (BrEaST, BUS-BRA, BUSI, UDIAT, BUS-UCLM, TN3K, HC18 and fetal-head masks; DDTI outlines drawn from the XML; TN5000 boxes only), box/mask IoU, Dice, Hungarian best-match for several lesions (unmatched boxes count as 0), "share of a box inside the mask", head circumference from the filled ellipse. Checks: mask-derived boxes equal the stored boxes (IoU 1.0 on 40 sampled cases of every dataset, so no filename mismatch); **true mask vs true mask gives IoU = Dice = 1.0 on every case (sanity row)**. `usmeta/bench_loc.py` -> `bench_loc.jsonl`: 9,797 candidates = text + box(es) on 957 cases (100 per dataset; BUS-UCLM 57 with a lesion): identical; harmless (same text + box jitter with IoU >= 0.85; reworded text + jitter); box-only errors (IoU ~0.5 = severity 1, ~0.2 = 2, 0 on the wrong side = 3); text position errors with the box kept correct; text position errors with the box moved to match the wrong text; text size errors (box correct). `usmeta/layer3.py`: scorers `location_check` (best-match box IoU), `grounded_check` (= `finding_f1` x `location_check`, so a report scores well only if text AND box are right), `mask_verified_facts` (share of the text's mask-checkable claims that the true mask backs: lesion present, count, image position, orientation, size), `semacc` (UltraG-Bench-style yes/no checks for presence, category, location, size; idea from UltraG-Bench, not new: their reports are GPT-5.5-written from masks, not radiologists), `box_support` (>= 50% of the box inside the true region; plus pixel precision/recall in the json) and `oracle_label_check` (= `finding_f1` against the label-built reference: the old label-based "evidence check" kept as the oracle upper bound). Layer 0 text scorers are looked up from the Step 4/5 scores (0 missing pairs). Not done: SAM/MedSAM (Part B, as instructed).

**The one thing to read first (honesty).** For text claims about position, size, orientation and count, the reference was measured from the same masks with the same code, so `mask_verified_facts` cannot fail on true text: **on the identical texts 100% of the checkable claims are backed (BrEaST 500/500, BUS-BRA 500/500, BUSI 500/500, UDIAT 500/500, BUS-UCLM 285/285, TN3K 500/500, TN5000 500/500, DDTI 500/500, HC18 100/100, fetal head 100/100).** `mask_verified_facts`, `semacc` and `oracle_label_check` therefore behave almost identically here. Test 1 shows what the check catches *when a correct mask is available*; the real test is with a *predicted* mask (Part B). Box-only errors do not change the text, so text-only scorers cannot see them by construction: that row is a sanity check, not a finding.

**Wiring gate.** Identical-copy mean = 1.0000 for every scorer on every dataset, with these exceptions, both explained: `box_support` (mask rule) is 0.94 on BrEaST and 0.99 on BUSI/UDIAT, because the tight bounding box of an irregular lesion can have < 50% of its area inside the mask, so even the true box fails the 50% rule. I added `box_support_gtbox` (same 50% rule against the true *box* region), which is 1.0000. `mask_verified_facts` on HC18 is 0.9992 (head circumference credit is graded; text rounds to 0.1 mm). One bug found and fixed on the way: the thyroid wording stops at "three or more nodules", so a mask with 5 components was marked unbacked (TN3K identical mean was 0.99); the count is now capped at 3 for thyroid.

**Results (per dataset; full tables below).** AUROC of planted error vs harmless; the "all" column pools box-only and text errors against harmless candidates of two kinds (same text with a jittered box, and reworded text), so it is dominated by that mix: read the group columns.
- **Text position and size errors with a correct box (BrEaST / BUS-BRA / TN5000 / HC18):** `mask_verified_facts` 1.00 / 1.00 / 1.00 / 1.00 for size; `oracle_label_check` 1.00; Layer 0 text scorers 0.50 for BLEU, ROUGE-L, chrF, BERTScore (RaTEScore 0.25-0.53); `location_check` 0.00 (the box is right, so it cannot see a wrong sentence).
- **Text and box both consistently wrong:** `location_check` 1.00, `grounded_check` 1.00, `mask_verified_facts` 1.00, text scorers 0.25-0.50.
- **Box-only errors (text unchanged):** `location_check` 1.00, `grounded_check` 1.00, `box_support` 0.83-0.89, all text-only scorers and `mask_verified_facts` 0.25-0.50 (cannot see boxes: by construction).
- **`grounded_check`** is the only scorer that is high on all three groups on TN5000 (1.00 / 1.00 / 1.00 / 0.99 for size) and HC18 (1.00 for box and size); on BrEaST it is 1.00 for box-only and consistent-wrong but 0.24 for text-only position errors and 0.16 for size, on BUS-BRA 0.61 and 0.53: because the harmless candidates include box jitter (IoU ~0.9, so the product is ~0.9), a text error with a correct box scores about the same as a jittered harmless one on some datasets. The product is simple and not tuned.
- Severity Spearman for `location_check` / `grounded_check`: about -0.3 on breast and TN5000, -0.89 for `grounded_check` on HC18; text-only scorers are near 0 or positive.

**Caveats (keep visible).** Reports are templated from labels; severity is provisional pending clinician; template sources "to confirm"; per dataset only; 100 cases per dataset; mask-verified facts are circular for text built from the same masks (see above); the planted boxes are synthetic shifts, not model output; TN5000 has boxes only (its "mask" is the box); BUS-BRA side is not mask-checkable and is not checked; no SAM/MedSAM yet.

---

## Per-dataset tables

### BrEaST (100 cases)

| scorer | AUROC (95% CI) | box-only | text position (box right) | text position + box moved | size | harmless mean | identical mean | severity ρ |
|---|---|---|---|---|---|---|---|---|
| bleu | 0.39 (0.39–0.39) | 0.25 | 0.50 | 0.50 | 0.50 | 0.84 | 1.0000 | 0.28 |
| rougeL | 0.39 (0.39–0.39) | 0.25 | 0.50 | 0.50 | 0.50 | 0.91 | 1.0000 | 0.28 |
| chrf | 0.39 (0.39–0.39) | 0.25 | 0.50 | 0.50 | 0.50 | 0.90 | 1.0000 | 0.38 |
| bertscore[roberta-large] | 0.39 (0.39–0.39) | 0.25 | 0.50 | 0.50 | 0.50 | 0.99 | 1.0000 | 0.34 |
| ratescore | 0.36 (0.36–0.36) | 0.25 | 0.26 | 0.26 | 0.50 | 0.90 | 1.0000 | 0.01 |
| oracle_label_check | 0.78 (0.77–0.79) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.29 |
| mask_verified_facts | 0.78 (0.77–0.79) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.30 |
| semacc | 0.78 (0.77–0.79) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.31 |
| location_check | 0.50 (0.50–0.50) | 1.00 | 0.00 | 1.00 | 0.00 | 0.90 | 1.0000 | -0.32 |
| grounded_check | 0.58 (0.55–0.61) | 1.00 | 0.24 | 1.00 | 0.16 | 0.90 | 1.0000 | -0.31 |
| box_support | 0.70 (0.68–0.71) | 0.89 | 0.49 | 0.95 | 0.50 | 0.94 | 0.9400 | -0.29 |
| box_support_gtbox | 0.67 (0.66–0.67) | 0.81 | 0.50 | 1.00 | 0.50 | 1.00 | 1.0000 | -0.47 |

### BUS-BRA (100 cases)

| scorer | AUROC (95% CI) | box-only | text position (box right) | text position + box moved | size | harmless mean | identical mean | severity ρ |
|---|---|---|---|---|---|---|---|---|
| bleu | 0.39 (0.39–0.40) | 0.25 | 0.50 | 0.50 | 0.50 | 0.86 | 1.0000 | 0.30 |
| rougeL | 0.39 (0.39–0.40) | 0.25 | 0.50 | 0.50 | 0.50 | 0.92 | 1.0000 | 0.30 |
| chrf | 0.39 (0.39–0.40) | 0.25 | 0.50 | 0.50 | 0.50 | 0.90 | 1.0000 | 0.42 |
| bertscore[roberta-large] | 0.39 (0.39–0.40) | 0.25 | 0.50 | 0.50 | 0.50 | 0.99 | 1.0000 | 0.28 |
| ratescore | 0.36 (0.35–0.36) | 0.25 | 0.25 | 0.25 | 0.50 | 0.92 | 1.0000 | -0.03 |
| oracle_label_check | 0.79 (0.78–0.79) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.31 |
| mask_verified_facts | 0.79 (0.78–0.79) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.32 |
| semacc | 0.77 (0.76–0.78) | 0.50 | 1.00 | 1.00 | 0.97 | 1.00 | 1.0000 | 0.31 |
| location_check | 0.50 (0.50–0.50) | 1.00 | 0.00 | 1.00 | 0.00 | 0.90 | 1.0000 | -0.30 |
| grounded_check | 0.77 (0.74–0.81) | 1.00 | 0.61 | 1.00 | 0.53 | 0.90 | 1.0000 | -0.29 |
| box_support | 0.70 (0.69–0.71) | 0.89 | 0.50 | 1.00 | 0.49 | 0.99 | 1.0000 | -0.32 |
| box_support_gtbox | 0.66 (0.66–0.67) | 0.80 | 0.50 | 1.00 | 0.50 | 1.00 | 1.0000 | -0.44 |

### BUSI (100 cases)

| scorer | AUROC (95% CI) | box-only | text position (box right) | text position + box moved | size | harmless mean | identical mean | severity ρ |
|---|---|---|---|---|---|---|---|---|
| bleu | 0.40 (0.39–0.40) | 0.25 | 0.50 | 0.50 | 0.50 | 0.85 | 1.0000 | 0.33 |
| rougeL | 0.40 (0.39–0.40) | 0.25 | 0.50 | 0.50 | 0.50 | 0.91 | 1.0000 | 0.33 |
| chrf | 0.40 (0.39–0.40) | 0.25 | 0.50 | 0.50 | 0.50 | 0.90 | 1.0000 | 0.47 |
| bertscore[roberta-large] | 0.40 (0.39–0.40) | 0.25 | 0.50 | 0.50 | 0.50 | 0.99 | 1.0000 | 0.28 |
| ratescore | 0.35 (0.35–0.36) | 0.25 | 0.25 | 0.25 | 0.50 | 0.90 | 1.0000 | -0.08 |
| oracle_label_check | 0.80 (0.79–0.80) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.34 |
| mask_verified_facts | 0.80 (0.79–0.80) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.34 |
| semacc | 0.79 (0.78–0.80) | 0.50 | 1.00 | 1.00 | 0.98 | 1.00 | 1.0000 | 0.34 |
| location_check | 0.50 (0.50–0.50) | 1.00 | 0.00 | 1.00 | 0.00 | 0.90 | 1.0000 | -0.26 |
| grounded_check | 0.98 (0.97–1.00) | 1.00 | 1.00 | 1.00 | 0.97 | 0.90 | 1.0000 | -0.25 |
| box_support | 0.70 (0.69–0.71) | 0.89 | 0.50 | 1.00 | 0.50 | 0.99 | 0.9900 | -0.30 |
| box_support_gtbox | 0.67 (0.67–0.68) | 0.82 | 0.50 | 1.00 | 0.50 | 1.00 | 1.0000 | -0.40 |

### UDIAT (100 cases)

| scorer | AUROC (95% CI) | box-only | text position (box right) | text position + box moved | size | harmless mean | identical mean | severity ρ |
|---|---|---|---|---|---|---|---|---|
| bleu | 0.40 (0.40–0.40) | 0.25 | 0.50 | 0.50 | 0.50 | 0.86 | 1.0000 | 0.35 |
| rougeL | 0.40 (0.40–0.40) | 0.25 | 0.50 | 0.50 | 0.50 | 0.92 | 1.0000 | 0.35 |
| chrf | 0.40 (0.40–0.40) | 0.25 | 0.50 | 0.50 | 0.50 | 0.91 | 1.0000 | 0.47 |
| bertscore[roberta-large] | 0.40 (0.40–0.40) | 0.25 | 0.50 | 0.50 | 0.50 | 0.99 | 1.0000 | 0.32 |
| ratescore | 0.35 (0.35–0.35) | 0.25 | 0.25 | 0.25 | 0.50 | 0.92 | 1.0000 | -0.08 |
| oracle_label_check | 0.80 (0.79–0.81) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.35 |
| mask_verified_facts | 0.80 (0.79–0.81) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.35 |
| semacc | 0.80 (0.79–0.81) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.35 |
| location_check | 0.50 (0.50–0.50) | 1.00 | 0.00 | 1.00 | 0.00 | 0.89 | 1.0000 | -0.25 |
| grounded_check | 0.95 (0.92–0.97) | 1.00 | 0.88 | 1.00 | 0.89 | 0.89 | 1.0000 | -0.24 |
| box_support | 0.70 (0.69–0.71) | 0.89 | 0.49 | 0.99 | 0.49 | 0.98 | 0.9900 | -0.29 |
| box_support_gtbox | 0.68 (0.68–0.68) | 0.83 | 0.50 | 1.00 | 0.50 | 1.00 | 1.0000 | -0.40 |

### BUS-UCLM (57 cases)

| scorer | AUROC (95% CI) | box-only | text position (box right) | text position + box moved | size | harmless mean | identical mean | severity ρ |
|---|---|---|---|---|---|---|---|---|
| bleu | 0.39 (0.39–0.40) | 0.25 | 0.50 | 0.50 | 0.50 | 0.85 | 1.0000 | 0.31 |
| rougeL | 0.39 (0.39–0.40) | 0.25 | 0.50 | 0.50 | 0.50 | 0.91 | 1.0000 | 0.31 |
| chrf | 0.39 (0.39–0.40) | 0.25 | 0.50 | 0.50 | 0.50 | 0.90 | 1.0000 | 0.42 |
| bertscore[roberta-large] | 0.39 (0.39–0.40) | 0.25 | 0.50 | 0.50 | 0.50 | 0.99 | 1.0000 | 0.27 |
| ratescore | 0.36 (0.35–0.36) | 0.25 | 0.25 | 0.25 | 0.50 | 0.89 | 1.0000 | -0.01 |
| oracle_label_check | 0.78 (0.77–0.79) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.31 |
| mask_verified_facts | 0.78 (0.77–0.79) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.31 |
| semacc | 0.78 (0.77–0.79) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.32 |
| location_check | 0.50 (0.50–0.50) | 1.00 | 0.00 | 1.00 | 0.00 | 0.89 | 1.0000 | -0.30 |
| grounded_check | 0.99 (0.99–1.00) | 1.00 | 1.00 | 1.00 | 0.99 | 0.89 | 1.0000 | -0.29 |
| box_support | 0.70 (0.69–0.71) | 0.88 | 0.50 | 1.00 | 0.50 | 1.00 | 1.0000 | -0.36 |
| box_support_gtbox | 0.67 (0.67–0.68) | 0.82 | 0.50 | 1.00 | 0.50 | 1.00 | 1.0000 | -0.45 |

### TN3K (100 cases)

| scorer | AUROC (95% CI) | box-only | text position (box right) | text position + box moved | size | harmless mean | identical mean | severity ρ |
|---|---|---|---|---|---|---|---|---|
| bleu | 0.39 (0.39–0.40) | 0.25 | 0.50 | 0.50 | 0.50 | 0.83 | 1.0000 | 0.32 |
| rougeL | 0.39 (0.39–0.40) | 0.25 | 0.50 | 0.50 | 0.50 | 0.91 | 1.0000 | 0.32 |
| chrf | 0.39 (0.39–0.40) | 0.25 | 0.50 | 0.50 | 0.50 | 0.87 | 1.0000 | 0.46 |
| bertscore[roberta-large] | 0.39 (0.39–0.40) | 0.25 | 0.50 | 0.50 | 0.50 | 0.98 | 1.0000 | 0.23 |
| ratescore | 0.28 (0.27–0.29) | 0.25 | 0.32 | 0.32 | 0.29 | 0.88 | 1.0000 | 0.16 |
| oracle_label_check | 0.79 (0.78–0.80) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.33 |
| mask_verified_facts | 0.79 (0.78–0.80) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.33 |
| semacc | 0.78 (0.77–0.79) | 0.50 | 1.00 | 1.00 | 0.98 | 1.00 | 1.0000 | 0.33 |
| location_check | 0.50 (0.50–0.51) | 1.00 | 0.00 | 1.00 | 0.00 | 0.89 | 1.0000 | -0.28 |
| grounded_check | 0.98 (0.97–0.99) | 1.00 | 1.00 | 1.00 | 0.96 | 0.89 | 1.0000 | -0.27 |
| box_support | 0.69 (0.69–0.70) | 0.87 | 0.50 | 1.00 | 0.50 | 1.00 | 1.0000 | -0.36 |
| box_support_gtbox | 0.67 (0.67–0.68) | 0.82 | 0.50 | 1.00 | 0.50 | 1.00 | 1.0000 | -0.41 |

### TN5000 (100 cases)

| scorer | AUROC (95% CI) | box-only | text position (box right) | text position + box moved | size | harmless mean | identical mean | severity ρ |
|---|---|---|---|---|---|---|---|---|
| bleu | 0.39 (0.39–0.39) | 0.25 | 0.50 | 0.50 | 0.50 | 0.83 | 1.0000 | 0.32 |
| rougeL | 0.39 (0.39–0.39) | 0.25 | 0.50 | 0.50 | 0.50 | 0.91 | 1.0000 | 0.32 |
| chrf | 0.39 (0.39–0.39) | 0.25 | 0.50 | 0.50 | 0.50 | 0.87 | 1.0000 | 0.41 |
| bertscore[roberta-large] | 0.39 (0.39–0.39) | 0.25 | 0.50 | 0.50 | 0.50 | 0.98 | 1.0000 | 0.28 |
| ratescore | 0.27 (0.26–0.28) | 0.25 | 0.28 | 0.28 | 0.29 | 0.88 | 1.0000 | 0.05 |
| oracle_label_check | 0.78 (0.78–0.79) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.31 |
| mask_verified_facts | 0.78 (0.78–0.79) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.31 |
| semacc | 0.78 (0.77–0.79) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.32 |
| location_check | 0.50 (0.50–0.50) | 1.00 | 0.00 | 1.00 | 0.00 | 0.90 | 1.0000 | -0.31 |
| grounded_check | 1.00 (0.99–1.00) | 1.00 | 1.00 | 1.00 | 0.99 | 0.90 | 1.0000 | -0.30 |
| box_support | 0.68 (0.67–0.68) | 0.83 | 0.50 | 1.00 | 0.50 | 1.00 | 1.0000 | -0.47 |
| box_support_gtbox | 0.68 (0.67–0.68) | 0.83 | 0.50 | 1.00 | 0.50 | 1.00 | 1.0000 | -0.47 |

### DDTI (100 cases)

| scorer | AUROC (95% CI) | box-only | text position (box right) | text position + box moved | size | harmless mean | identical mean | severity ρ |
|---|---|---|---|---|---|---|---|---|
| bleu | 0.39 (0.39–0.40) | 0.25 | 0.50 | 0.50 | 0.50 | 0.84 | 1.0000 | 0.31 |
| rougeL | 0.39 (0.39–0.40) | 0.25 | 0.50 | 0.50 | 0.50 | 0.91 | 1.0000 | 0.32 |
| chrf | 0.39 (0.39–0.40) | 0.25 | 0.50 | 0.50 | 0.50 | 0.89 | 1.0000 | 0.39 |
| bertscore[roberta-large] | 0.39 (0.39–0.40) | 0.25 | 0.50 | 0.50 | 0.50 | 0.99 | 1.0000 | 0.25 |
| ratescore | 0.28 (0.27–0.30) | 0.25 | 0.36 | 0.36 | 0.29 | 0.88 | 1.0000 | 0.18 |
| oracle_label_check | 0.79 (0.78–0.80) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.29 |
| mask_verified_facts | 0.79 (0.78–0.80) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.33 |
| semacc | 0.79 (0.78–0.80) | 0.50 | 1.00 | 1.00 | 1.00 | 1.00 | 1.0000 | 0.34 |
| location_check | 0.50 (0.50–0.50) | 1.00 | 0.00 | 1.00 | 0.00 | 0.89 | 1.0000 | -0.27 |
| grounded_check | 0.75 (0.72–0.79) | 1.00 | 0.56 | 1.00 | 0.51 | 0.89 | 1.0000 | -0.26 |
| box_support | 0.70 (0.70–0.71) | 0.90 | 0.50 | 1.00 | 0.50 | 1.00 | 1.0000 | -0.33 |
| box_support_gtbox | 0.68 (0.68–0.69) | 0.84 | 0.50 | 0.99 | 0.50 | 1.00 | 1.0000 | -0.41 |

### HC18 (100 cases)

| scorer | AUROC (95% CI) | box-only | text position (box right) | text position + box moved | size | harmless mean | identical mean | severity ρ |
|---|---|---|---|---|---|---|---|---|
| bleu | 0.39 (0.39–0.39) | 0.25 | — | — | 0.50 | 0.75 | 1.0000 | 0.00 |
| rougeL | 0.54 (0.54–0.54) | 0.25 | — | — | 0.75 | 0.93 | 1.0000 | 0.00 |
| chrf | 0.39 (0.39–0.39) | 0.25 | — | — | 0.50 | 0.89 | 1.0000 | -0.06 |
| bertscore[roberta-large] | 0.39 (0.39–0.39) | 0.25 | — | — | 0.50 | 0.99 | 1.0000 | -0.12 |
| ratescore | 0.41 (0.40–0.42) | 0.25 | — | — | 0.53 | 0.90 | 1.0000 | -0.14 |
| oracle_label_check | 0.79 (0.79–0.79) | 0.50 | — | — | 1.00 | 1.00 | 1.0000 | -0.30 |
| mask_verified_facts | 0.79 (0.79–0.79) | 0.50 | — | — | 1.00 | 1.00 | 0.9992 | -0.28 |
| semacc | 0.61 (0.61–0.62) | 0.50 | — | — | 0.70 | 1.00 | 1.0000 | -0.45 |
| location_check | 0.43 (0.43–0.43) | 1.00 | — | — | 0.00 | 0.90 | 1.0000 | -0.21 |
| grounded_check | 1.00 (1.00–1.00) | 1.00 | — | — | 1.00 | 0.90 | 1.0000 | -0.89 |
| box_support | 0.64 (0.64–0.64) | 0.83 | — | — | 0.50 | 1.00 | 1.0000 | -0.42 |
| box_support_gtbox | 0.62 (0.62–0.63) | 0.79 | — | — | 0.50 | 1.00 | 1.0000 | -0.44 |

### FetalHead (100 cases)

| scorer | AUROC (95% CI) | box-only | text position (box right) | text position + box moved | size | harmless mean | identical mean | severity ρ |
|---|---|---|---|---|---|---|---|---|
| bleu | 0.39 (0.39–0.39) | 0.25 | — | — | 0.50 | 0.88 | 1.0000 | 0.00 |
| rougeL | 0.54 (0.54–0.54) | 0.25 | — | — | 0.75 | 0.95 | 1.0000 | 0.00 |
| chrf | 0.39 (0.39–0.39) | 0.25 | — | — | 0.50 | 0.95 | 1.0000 | -0.14 |
| bertscore[roberta-large] | 0.39 (0.39–0.39) | 0.25 | — | — | 0.50 | 0.99 | 1.0000 | -0.09 |
| ratescore | 0.42 (0.41–0.43) | 0.25 | — | — | 0.55 | 0.93 | 1.0000 | -0.05 |
| oracle_label_check | 0.79 (0.79–0.79) | 0.50 | — | — | 1.00 | 1.00 | 1.0000 | -0.30 |
| mask_verified_facts | 0.79 (0.79–0.79) | 0.50 | — | — | 1.00 | 1.00 | 1.0000 | -0.30 |
| semacc | 0.57 (0.57–0.57) | 0.50 | — | — | 0.62 | 1.00 | 1.0000 | -0.54 |
| location_check | 0.43 (0.43–0.43) | 1.00 | — | — | 0.00 | 0.89 | 1.0000 | -0.21 |
| grounded_check | 0.88 (0.87–0.88) | 1.00 | — | — | 0.78 | 0.89 | 1.0000 | -0.59 |
| box_support | 0.64 (0.64–0.64) | 0.83 | — | — | 0.50 | 1.00 | 1.0000 | -0.42 |
| box_support_gtbox | 0.63 (0.62–0.63) | 0.79 | — | — | 0.50 | 1.00 | 1.0000 | -0.44 |

---
Limitations: see [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md) (templated reports, upper bounds, prompt-sensitive judge, provisional severity, possible exposure). 
