"""Step 45 Part A report: results/partA/step45_improve_scorers/freetext/results.md from gold_summary.json and set_A.json (no model call)."""
import os, json, collections
from . import step45_freetext as FT
S = json.load(open(FT.P('gold_summary.json'))); A = json.load(open(FT.P('set_A.json'))); C = A['cases']; plan = json.load(open(FT.P('plan.json')))
gen_secs = [json.loads(l)['seconds'] for l in open(FT.P('gen_cache.jsonl'))]
def n(d, k): return d.get(k, 0)
L = ['# Step 45, Part A: free-text set with automatic gold (writer-made; no human grader)', '',
     'Pre-registration: [../PREREG.md](../PREREG.md) (committed before any Step 45 number). Code: `usmeta/step45_freetext.py`, `step45_partA_report.py`. Writer: Qwen2.5-7B-Instruct 4-bit (MLX), temperature 0.7, per-item seed, three styles (terse, narrative, impression-first); the writer gets only the supplied facts. Prompts saved in `plan.json` and in every record of `gen_cache.jsonl`.', '',
     '## What was built (and how it differs from the PREREG)', '',
     f"- **Sizes are smaller than the PREREG.** PREREG: 600 dev/val cases and 600 test cases, 3 styles, a planted-error twin each. Built: **270 dev/val cases (90 per organ: 60 dev + 30 val) and 270 test cases (90 per organ)**, 3 styles for the true facts, one planted-error twin in one rotating style, plus **{sum(1 for _ in A['lod'])} kept graded size / head-circumference reports** (up to 40 test cases per field group, 4 levels: size x1.05, x1.10, x1.25, x2.0; head circumference 1, 2, 5, 10 mm, sign alternating) for the limit of detection in Part C. Reason: the writer needs about 4-6 s per report on this 16 GB Mac ({sum(gen_secs)/3600:.1f} h of generation here; the PREREG size would take about 10 h for Part A alone).",
     '- **Case selection:** seeded (seed 45), balanced over organs, datasets round-robin inside an organ, group-disjoint by the locked splits (dev / val / test); each case has at least one planted-error candidate in the benchmark. The twin uses one of the case\'s own planted-error candidates (its facts re-extracted from the templated candidate); the twin\'s field / category / severity are recorded in `cases.json`.',
     '- **Gold** = the flat facts of the templated reference (`schema.extract_rule`). A deterministic lexicon check (synonyms + exact numbers; independent of every extractor under test) keeps a report only if it states **every gold value**. Fields: count, side, position, orientation, size (mm / cm / % of the image width), head circumference, shape, margin (with its qualifiers), echo, posterior features, calcifications, halo, BI-RADS / TI-RADS category, pathology, histology, composition, foci, plane.',
     '- **Added after the first look at the writer\'s replies (a deviation, listed here and in the PREREG-relative notes):** the writer often added facts that were not in its list (a BI-RADS category when none was given, BI-RADS on thyroid and fetal-head reports, a side for a breast lesion with no side). Such a report is not a harmless rewording, so an **extras check** (also deterministic) drops any report that states an unsupplied category, pathology, side, number with a unit, calcification / halo / echo / shape value, or a conflicting enumerated value. The PREREG only required that every gold value is stated; the extras filter is stricter and removes more reports. Drops are counted below and are not charged to any extractor or scorer.', '',
     '## Reports generated, dropped and kept', '',
     '| set | organ | kind | generated | dropped | of which: gold value not stated | of which: extras only | kept |', '|---|---|---|---|---|---|---|---|']
for st in ('devval', 'test'):
    for o in ('breast', 'thyroid', 'fetal'):
        for k in ('true', 'twin', 'lod'):
            key = f'{st}|{o}|{k}'; g = n(S['generated'], key)
            if not g: continue
            d = n(S['dropped'], key); m = n(S['drop_reason'], key + '|missing_gold'); e = n(S['drop_reason'], key + '|extras_only'); L.append(f"| {st} | {o} | {'true facts (3 styles)' if k == 'true' else 'planted-error twin' if k == 'twin' else 'graded size / HC twin'} | {g} | {d} ({d / g * 100:.0f}%) | {m} | {e} | {g - d} |")
tot_g = sum(S['generated'].values()); tot_d = sum(S['dropped'].values())
L += ['', f"Overall {tot_d} of {tot_g} generated reports dropped ({tot_d / tot_g * 100:.0f}%). Most frequent unsupplied statements (extras): " + ', '.join(f"{k} {v}" for k, v in list(S['extra_fields'].items())[:6]) + '. Most frequent supplied values the writer left out: ' + ', '.join(f"{k} {v}" for k, v in list(S['missed_gold_fields'].items())[:6]) + '. The lesion count (the writer often wrote "a mass" without saying "single") is the main omission in breast.', '',
     '## The set used in Parts B, C, E, F', '', '| set | organ | cases | kept true-fact reports | cases with a kept planted-error twin | cases with both |', '|---|---|---|---|---|---|']
for st in ('devval', 'test'):
    for o in ('breast', 'thyroid', 'fetal'):
        cs = [v for v in C.values() if v['set'] == st and v['organ'] == o]; L.append(f"| {st} | {o} | {len(cs)} | {sum(len(v['true_reports']) for v in cs)} | {sum(1 for v in cs if v['twin_report'])} | {sum(1 for v in cs if v['twin_report'] and v['true_reports'])} |")
L += ['', 'Planted-error twins kept per organ are 44-89 cases, so every rate on the twins has wide intervals (cells under 30 groups are marked too small to compare in the later parts).', '',
      '## Three kept test reports (the first kept case of each organ in seeded order; writer output unedited)', '']
import random
cs = [v for v in C.values() if v['set'] == 'test' and v['true_reports']]; random.Random(7).shuffle(cs)
for o in ('breast', 'thyroid', 'fetal'):
    x = next(v for v in cs if v['organ'] == o); r = x['true_reports'][0]; L += [f"- **{o}** ({r['style']}): reference \"{x['reference'][:150]}\" -> writer \"{r['text'][:300].replace(chr(10), ' / ')}\""]
L += ['', '## Caveats', '',
      '- **Writer-made free text is a proxy** for real radiologist or VLM text; it does not replace a clinician-written set. The writer copies the structure of the supplied fact list (many reports are list-like), so it is closer to the templates than real prose is; a pass in a later part is "better on writer-made free text", not "clinically validated".',
      '- **Writer and extractor share a model family** (Qwen2.5-7B-Instruct writes the reports; extractors v4 / v5 are Qwen2.5-7B-Instruct). The extractor may read its own family\'s text more easily than other writers\' text. The judge (Gemma) and the writer are different families, as the standing rule requires.',
      '- The lexicon check is a deterministic approximation of "states the value" (it can accept a mention that is not exactly the stated fact and reject an unusual paraphrase); it was checked on the templated styles of dev cases (thyroid and fetal head 90 of 90; breast fails only on the lesion count, which templated breast text does not state, by design of the check).',
      '- Dropping reports that omit values or add unsupplied facts selects the writer\'s better outputs; rates in Parts B-F describe those, not all writer outputs.', '']
open(FT.P('results.md'), 'w').write('\n'.join(L)); print('wrote', len(L))
