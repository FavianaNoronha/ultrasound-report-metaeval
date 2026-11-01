# Step 21d — Human-rewording sheet (prepared, NOT scored; waiting for the owner)

**Status: prepared only. No scoring has been run, and none will be until the sheet is filled in.**

What exists: `sheet.md` (instructions + the 30 references) and `sheet.csv` (columns `id, organ, reference_text, human_rewording, note`), `sheet_key.json` (id → case and dataset, for the scorer). The 30 references come from the locked TEST split via `usmeta.splits.load` (access logged): 10 breast (BrEaST 2, BUS-BRA 2, BUSI 2, UDIAT 2, BUS-UCLM 2), 10 thyroid (TN3K 3, TN5000 3, DDTI 4), 10 fetal head (HC18 5, FetalHead 5), one per patient/exam group, each with at least 3 planted errors in `bench_test_v2d`. They are templated, fact-correct reports, not clinician text.

Rules for the rewriter (also at the top of `sheet.md`): reword by hand in your own words, keep every fact (side, category, size, finding), do not copy template phrasing, do not use an AI tool. If you checked by hand that no fact changed but the rule extractor flags the row (it was written for the template wording), write `OK` in `note`.

## When the CSV is filled
```
python3 -m usmeta.step21_human_score check     # facts check only (rule extractor); writes flagged.csv
python3 -m usmeta.step21_human_score score     # check + BLEU, ROUGE-L, chrF, BERTScore, RaTEScore, finding_f1, Gemma judge (prompt_v2)
```
`score` drops rewordings where a fact changed (unless marked `OK`) or that equal the reference, builds each valid human rewording as a harmless candidate, and compares it with up to 8 planted errors of the SAME reference: per item AUROC (error scores lower than the human rewording; ties 0.5), group = item, 1,000 resamples, seed 0, next to the same AUROC for the template harmless groups (small / matched / large) on the same references. Each organ cell has n = 10 items, so every organ cell will carry "too small to compare"; only the pooled 30-item row (labelled pooled) can reach n ≥ 30.

## Checked so far (no model calls)
The fact checker was exercised on three throwaway rewordings (not the real sheet): a one-word synonym passed, a changed size (18 → 28 mm) was flagged (`size_mm` credit 0), and a free-form rewording was flagged because the rule extractor cannot parse non-template phrasing (hence the `OK` note). The scorer itself has NOT been run.
