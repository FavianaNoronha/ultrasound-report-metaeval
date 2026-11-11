"""Step 34 report: results/partA/step34_metamorphic/results.md (no model calls; no HiSBreast text is read or written here)."""
import os, json, sys, platform, time, subprocess
import numpy as np
from . import step34_metamorphic as M
D = M.OUT; R = json.load(open(os.path.join(D, 'results.json'))); meta = R['_meta']
SC = [('bleu', 'BLEU'), ('rougeL', 'ROUGE-L'), ('chrf', 'chrF'), ('bertscore[roberta-large]', 'BERTScore'), ('ratescore', 'RaTEScore'), ('finding_f1', 'finding_f1 (regex; templated only)'), ('llm_finding_f1', 'llm_finding_f1 (v3; subset)'), ('judge_score', 'judge_score (subset)')]
SETS = [('templated', '(i) templated test references'), ('hisbreast', '(ii) HiSBreast test texts (local only)'), ('writer', '(iii) Step 28 writer reports'), ('ALL', 'all items')]
def cell(name, st, rel, delta=None):
    c = R.get(f'{name}|{st}|{rel}' + (f'|{delta}' if delta else ''))
    if not c or not c['violation']: return '—'
    v = c['violation']; return f"{v[0]*100:.0f}% ({v[1]*100:.0f}–{v[2]*100:.0f}) n={c['n']}" + (' †' if c['too_small'] else '')
def rate(name, st, rel, delta=None):
    c = R.get(f'{name}|{st}|{rel}' + (f'|{delta}' if delta else '')); return None if not c or not c['violation'] else c['violation'][0]
md = ['# Step 34: metamorphic checks (no ground truth needed)', '',
      'Limitations: [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md). Code: `usmeta/step34_metamorphic.py`, `step34_report.py` (new files; saved Step 28 reports; frozen scorers imported unchanged). Test split read once, logged (`usmeta.step34_metamorphic`). **The HiSBreast texts and translations never leave `usmeta/local_data` (scores and caches for them are git-ignored); only aggregated violation rates appear here.**', '',
      '**Relations** (T = a transformation of a text x; s(r, y) = a scorer comparing y with the reference r; for sets (i) and (ii) r = x, for (iii) r = the label reference and x = the writer report): **R1** unit invariance (mm to cm or back); **R2** sentence-order invariance (reverse the order); **R3** synonym invariance (one one-token synonym swap); **R4** a number swap must lower the score; **R5** a negation flip must lower the score; **R6** the score must be monotone in error size (the first measurement number x 0.75, 0.5 down and x 1.25, 2.0 up). For R1-R3 a **violation** is |s(r, T(x)) - s(r, x)| > 0.05 (sensitivity 0.10); for R4 and R5 it is s(r, error text) >= s(r, harmless rewording of the same text), i.e. the error is NOT scored strictly lower than a one-token synonym swap (or, if none applies, a reorder, or x itself); for R6 any step to a larger error that raises the score. The full definitions, the thresholds and the item sets are in the docstring of `step34_metamorphic.py`, fixed before any score was computed. **Violation rate = violations / applicable items** (an item is applicable when the transformation exists); 95% CI by bootstrap over items; † = fewer than 30 applicable items: too small to compare.', '',
      f"Items: {meta['items']['templated']} templated test references (100 per organ), {meta['items']['hisbreast']} HiSBreast test texts, {meta['items']['writer']} writer reports. Applicable items per relation: " + '; '.join(f"{st}: " + ', '.join(f'{r} {n}' for r, n in meta['applicable'][st].items()) for st in ('templated', 'hisbreast', 'writer')) + f". LLM-based scorers (judge, `llm_finding_f1`) run on a capped subset: {meta['llm_subset']['templated']} templated, {meta['llm_subset']['hisbreast']} HiSBreast, {meta['llm_subset']['writer']} writer reports.", '']
# headline
def worst(rels, st='ALL'):
    v = [(nm, np.mean([x for x in (rate(n, st, r, 0.05 if r in ('R1', 'R2', 'R3') else None) for r in rels) if x is not None] or [np.nan])) for n, nm in SC]; return [(a, b) for a, b in v if not np.isnan(b)]
inv = worst(['R1', 'R2', 'R3']); lowr = worst(['R4', 'R5']) if True else []
md += ['## Headline', '',
       '- **Invariance (R1-R3, delta 0.05), mean violation rate over the three relations, all items:** ' + ', '.join(f'{a} {b*100:.0f}%' for a, b in sorted(inv, key=lambda x: -x[1])) + '. A scorer that is invariant to harmless rewording has a low rate; the word scorers are the least invariant because they react to how many characters change.',
       '- **"Must lower" (R4, R5), mean violation rate, all items:** ' + ', '.join(f'{a} {b*100:.0f}%' for a, b in sorted(lowr, key=lambda x: -x[1])) + '. A low rate means the error is scored lower than a harmless synonym swap of the same text; a high rate means the scorer cannot tell the error from the harmless edit.',
       '- A scorer can be invariant because it is insensitive to everything (R1-R3 low, R4-R5 high); read the two groups together. Per relation and item set, with intervals, below.', '']
for rel in M.REL:
    md += [f'## {rel}: {M.RELNAME[rel]}' + (' (violation = change > 0.05; the 0.10 sensitivity is in the second table)' if rel in ('R1', 'R2', 'R3') else ''), '', '| scorer | ' + ' | '.join(nm for _, nm in SETS) + ' |', '|---|' + '---|' * len(SETS)]
    for n, nm in SC: md.append(f'| {nm} | ' + ' | '.join(cell(n, st, rel, 0.05 if rel in ('R1', 'R2', 'R3') else None) for st, _ in SETS) + ' |')
    if rel in ('R1', 'R2', 'R3'):
        md += ['', f'{rel} with delta = 0.10:', '', '| scorer | ' + ' | '.join(nm for _, nm in SETS) + ' |', '|---|' + '---|' * len(SETS)]
        for n, nm in SC: md.append(f'| {nm} | ' + ' | '.join(cell(n, st, rel, 0.1) for st, _ in SETS) + ' |')
    if rel == 'R6':
        md += ['', 'Share of items whose whole chain is flat (the score does not change with the error size at all):', '', '| scorer | ' + ' | '.join(nm for _, nm in SETS) + ' |', '|---|' + '---|' * len(SETS)]
        for n, nm in SC: md.append(f'| {nm} | ' + ' | '.join((lambda c: '—' if not c or 'flat_share' not in c else f"{c['flat_share']*100:.0f}%")(R.get(f'{n}|{st}|R6')) for st, _ in SETS) + ' |')
    md.append('')
md += ['## Caveats', '',
       '- **No ground truth, but also no clinical validity:** a relation says how a scorer should move, not whether the text is right. The transformations are rule-based and crude on free text (R5 deletes the first "no " or " not ", R4 changes a number), so some transformed texts are unnatural; the same rules were applied to every scorer.',
       f"- **HiSBreast texts are short conclusions with few measurements:** R1, R4 and R6 apply to {meta['applicable']['hisbreast']['R1']}, {meta['applicable']['hisbreast']['R4']} and {meta['applicable']['hisbreast']['R6']} of the {meta['items']['hisbreast']} texts and R3 to {meta['applicable']['hisbreast']['R3']}, so nearly every HiSBreast cell is too small to compare. They are machine translations of licence-blank patient data (local only).",
       '- **Judge and `llm_finding_f1` on a capped subset** (24 templated rather than 20 items, because a case id picked for the writer subset also flags the same case\'s templated reference) (a few dozen items; most cells under 30 applicable items: too small to compare); the judge is prompt-sensitive (Step 21c) and was run once.',
       '- **delta = 0.05** is a fixed choice on a scale where BERTScore only spans a narrow band; the 0.10 tables show the sensitivity. R4 / R5 compare the error with a harmless synonym swap, which makes them a no-label version of the discrimination test, not an independent check of facts.',
       '- **Writer reports are scored against the label reference** and are long markdown text; word-overlap scores are near zero for them whatever the transformation, which makes invariance look good (nothing to lose) and "must lower" fail (nothing to lower).', '']
open(os.path.join(D, 'results.md'), 'w').write('\n'.join(md))
def g(*c):
    try: return subprocess.check_output(c, text=True, cwd=M.ROOT).strip()
    except Exception: return None
json.dump(dict(step='34_metamorphic', git_head_at_report=g('git', 'rev-parse', '--short', 'HEAD'), python=sys.version.split()[0], platform=platform.platform(), date=time.strftime('%Y-%m-%d'), bootstrap='items, 1000 resamples, seed 0', delta=meta['delta'], deltas=meta['deltas'], min_applicable=30), open(os.path.join(D, 'run_info.json'), 'w'), indent=1); print('wrote', len(md))
