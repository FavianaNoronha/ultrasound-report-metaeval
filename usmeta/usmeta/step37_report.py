"""Step 37 report: results/partA/step37_new_scorers/results.md (no model calls)."""
import os, json, sys, platform, time, subprocess
import numpy as np
from . import step37_new_scorers as N, step33_factorial as F, step35_lod as L, step34_metamorphic as M
D = N.OUT; R = json.load(open(os.path.join(D, 'radgraph_results.json'))); G = json.load(open(os.path.join(D, 'green_status.json')))
F33 = json.load(open(os.path.join(F.OUT, 'results.json'))); L35 = json.load(open(os.path.join(L.OUT, 'results.json'))); M34 = json.load(open(os.path.join(M.OUT, 'results.json')))
def f2(v, k=2): return '—' if v is None else f'{v:.{k}f}'
def ci(v, k=2): return '—' if not v else f'{v[0]*100:.0f}% ({v[1]*100:.0f}–{v[2]*100:.0f})'
OLD = [('bleu', 'BLEU'), ('rougeL', 'ROUGE-L'), ('chrf', 'chrF'), ('bertscore[roberta-large]', 'BERTScore'), ('ratescore', 'RaTEScore'), ('judge_score', 'judge_score (capped subset)'), ('sentence_f1', 'judge sentence_f1 (capped subset)'), ('llm_finding_f1', 'llm_finding_f1 (v3; Step 34 subset)'), ('finding_f1', 'finding_f1 (regex, upper bound)')]
fa = R['factorial']; rg_all, rg_j = fa['all blocks']['pooled'], fa['judge subset (same blocks as the judge)']['pooled']
rgl = {k: v for k, v in R['lod'].items()}
md = ['# Step 37: RadGraph-F1 and GREEN added to the Step 33, 34 and 35 analyses', '',
      'Limitations: [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md). Code: `usmeta/step37_rg_worker.py` (runs in a separate venv), `step37_new_scorers.py`, `step37_report.py` (new files; Steps 33 / 34 / 35 modules and saved results are read, not changed). Same group bootstrap (1,000, seed 0), same under-30-groups marks and decision rules. The test split was **not read again**: every score is for texts already in the earlier steps (their logged test reads). HiSBreast text stays in `usmeta/local_data` and the git-ignored annotation cache; only aggregated rates are written here.', '',
      '## What ran', '',
      f"- **RadGraph-F1: ran on everything.** Official `radgraph` package 0.1.18 with the RadGraph-XL model (`StanfordAIMI/RRG_scorers`, ~416 MB download approved by the owner), CPU, installed in the separate venv `~/.venvs/radgraph` (transformers pinned to 4.46.3: version 5 removed an API the package uses). The 'partial' reward level is the RadGraph-F1 used here (simple and complete are saved in the local score files). Scored: all Step 33 blocks (17,444 blocks; 27,694 pairs), all Step 35 candidates (13,566 pairs), all Step 34 items (3,444 pairs: templated, HiSBreast, writer reports). Total about 10 min of scoring on CPU (3,370 + 10,263 + 23,461 unique texts).",
      f"- **GREEN:** {G['summary']}", '']
if G.get('details'): md += [G['details'], '']
md += ['## Decision lines', '',
       f"**RadGraph-F1 does not beat the judge, and it does not change the Step 33 / 35 conclusions; it joins the word scorers.** Factorial (pre-registered rule, eta-squared fact > wording): RadGraph-F1 is **wording-driven** (fact {rg_all['eta']['fact']:.2f} vs wording {rg_all['eta']['wording']:.2f} on all {rg_all['n_blocks']:,} blocks; on the judge's {rg_j['n_blocks']} blocks fact {rg_j['eta']['fact']:.2f} vs wording {rg_j['eta']['wording']:.2f}), whereas the judge is fact-driven (judge_score fact {F33['judge_score']['pooled']['eta']['fact']:.2f} vs wording {F33['judge_score']['pooled']['eta']['wording']:.2f}). Limit of detection: RadGraph-F1 never reaches AUROC 0.80 at any size error up to x2 or any HC shift up to 20 mm (its AUROC vs matched synonyms is 0.2-0.3: it scores a size error above a one-word synonym because RadGraph reads entities and relations, not numbers), whereas judge_score reaches it at the smallest level (5% / 1 mm). Metamorphic: RadGraph-F1 violates the invariances (unit invariance on 100% of templated items, synonym invariance on 90%) and fails the \"number swap must lower the score\" check on 80% of templated items. **A scorer built for chest X-ray entities and relations does not see an ultrasound measurement.**", '']
if G.get('green_decision'): md += [G['green_decision'], '']
# factorial table
md += ['## Step 33 factorial: share of the score variance, fact vs wording (breast + thyroid pooled; verdict by the pre-registered rule)', '', '| scorer | blocks / groups | fact | wording | interaction | residual | verdict | AUROC c vs a (small edits) | AUROC d vs b (large edits) | error+small above correct+large |', '|---|---|---|---|---|---|---|---|---|---|']
for n, nm in OLD:
    r = F33.get(n, {}).get('pooled') if isinstance(F33.get(n), dict) else None
    if r: e = r['eta']; md.append(f"| {nm} | {r['n_blocks']:,} / {r['n_groups']} | {e['fact']:.2f} | {e['wording']:.2f} | {e['interaction']:.2f} | {e['residual']:.2f} | {'fact-driven' if r['fact_driven'] else 'wording-driven'} | {r['auroc_c_vs_a'][0]:.2f} | {r['auroc_d_vs_b'][0]:.2f} | {r['reversal_c_above_b'][0]*100:.0f}% |")
for tag, r in (('RadGraph-F1 (partial), all blocks', rg_all), ('RadGraph-F1 (partial), judge-subset blocks', rg_j)):
    e = r['eta']; md.append(f"| **{tag}** | {r['n_blocks']:,} / {r['n_groups']}{' †' if r['too_small'] else ''} | {e['fact']:.2f} | {e['wording']:.2f} | {e['interaction']:.2f} | {e['residual']:.2f} | **{'fact-driven' if r['fact_driven'] else 'wording-driven'}** | {r['auroc_c_vs_a'][0]:.2f} | {r['auroc_d_vs_b'][0]:.2f} | {r['reversal_c_above_b'][0]*100:.0f}% |")
if G.get('factorial_rows'): md += G['factorial_rows']
md += ['', 'Per organ (RadGraph-F1, all blocks): ' + '; '.join(f"{o} fact {fa['all blocks'][o]['eta']['fact']:.2f} vs wording {fa['all blocks'][o]['eta']['wording']:.2f} ({'fact' if fa['all blocks'][o]['fact_driven'] else 'wording'}-driven)" for o in ('breast', 'thyroid')) + f". On the judge's subset the breast cell is fact-driven (fact {fa['judge subset (same blocks as the judge)']['breast']['eta']['fact']:.2f} vs {fa['judge subset (same blocks as the judge)']['breast']['eta']['wording']:.2f}, 41 groups) and thyroid is wording-driven; the subset is small (71 groups pooled), so the full-block result is the one to read. † = under 30 groups.", '']
# LOD table
cells = [('breast', 'size_mm', 'breast, size (mm)'), ('breast', 'size_pct', 'breast, size (% width)'), ('thyroid', 'size_pct', 'thyroid, size (% width)'), ('fetal head', 'hc_mm', 'fetal head, HC (mm)')]
def lodv(v, c):
    if v is None: return '—'
    if v['lod'] is None: return f"not reached (> {v['levels'][-1]}{'' if c[1] == 'hc_mm' else '%'})".replace('> 1.0%', '> 100%')
    return (f"{v['lod']*100:.0f}%" if c[1] != 'hc_mm' else f"{v['lod']:g} mm")
md += ['## Step 35 limit of detection: smallest error with AUROC >= 0.80 vs matched synonyms', '', '| scorer | ' + ' | '.join(c[2] for c in cells) + ' |', '|---|' + '---|' * len(cells)]
for n, nm in OLD + [('image_medsam_oracle_exact', 'image check, oracle-box MedSAM'), ('image_unet_tolerance', 'image check, label-free U-Net')]:
    row = [lodv(L35.get(f'{n}|{c[0]}|{c[1]}'), c) for c in cells]
    if any(x != '—' for x in row): md.append(f'| {nm} | ' + ' | '.join(row) + ' |')
md.append('| **RadGraph-F1 (partial)** | ' + ' | '.join(lodv(rgl.get(f'radgraph_f1|{c[0]}|{c[1]}'), c) for c in cells) + ' |')
if G.get('lod_rows'): md += G['lod_rows']
md += ['', 'RadGraph-F1 AUROC by level (point estimates; levels as in Step 35): ' + '; '.join(f"{c[2]}: " + ', '.join(f"{x:.2f}" for x in rgl[f'radgraph_f1|{c[0]}|{c[1]}']['auroc'].values() if x is not None) for c in cells if f'radgraph_f1|{c[0]}|{c[1]}' in rgl) + '. Judge cells in the Step 35 table rest on a capped subset (many under 30 groups); RadGraph-F1 uses every Step 35 candidate.', '']
# metamorphic table
RELS = [('R1', '|0.05'), ('R2', '|0.05'), ('R3', '|0.05'), ('R4', ''), ('R5', ''), ('R6', '')]
def mm(name, st, rel, d, src=M34):
    c = src.get(f'{name}|{st}|{rel}{d}'); return '—' if not c or not c['violation'] else f"{c['violation'][0]*100:.0f}%" + (' †' if c['too_small'] else '')
md += ['## Step 34 metamorphic: violation rate (templated items; the full item sets are in the second table)', '', 'R1-R3 violation = score change > 0.05; R4 / R5 violation = the error is not scored strictly below a harmless synonym swap; R6 = a larger error raises the score. † = fewer than 30 applicable items.', '', '| scorer | R1 unit | R2 order | R3 synonym | R4 number swap | R5 negation flip | R6 monotone |', '|---|---|---|---|---|---|---|']
for n, nm in OLD: md.append(f'| {nm} | ' + ' | '.join(mm(n, 'templated', r, d) for r, d in RELS) + ' |')
rm = R['metamorphic']
for sub, tag in (('all items', 'RadGraph-F1 (partial), all items'), ('judge subset (same items as the judge)', 'RadGraph-F1 (partial), judge-subset items')):
    md.append(f'| **{tag}** | ' + ' | '.join(mm(sub, 'templated', r, d, rm) for r, d in RELS) + ' |')
if G.get('meta_rows'): md += G['meta_rows']
md += ['', '### All items and writer reports (RadGraph-F1 next to the others)', '', '| scorer | set | R1 | R2 | R3 | R4 | R5 | R6 |', '|---|---|---|---|---|---|---|---|']
for n, nm in [('bleu', 'BLEU'), ('chrf', 'chrF'), ('bertscore[roberta-large]', 'BERTScore'), ('ratescore', 'RaTEScore'), ('judge_score', 'judge_score (subset)')]:
    for st in ('ALL', 'writer'): md.append(f'| {nm} | {st} | ' + ' | '.join(mm(n, st, r, d) for r, d in RELS) + ' |')
for st in ('ALL', 'hisbreast', 'writer'): md.append(f'| **RadGraph-F1 (all items)** | {st} | ' + ' | '.join(mm('all items', st, r, d, rm) for r, d in RELS) + ' |')
md += ['', 'HiSBreast cells are almost all too small to compare (R1, R4 and R6 apply to none of the 41 texts).', '',
       '## Caveats', '',
       '- **RadGraph-F1 is a chest-X-ray entity and relation scorer** (RadGraph-XL was trained on radiology reports of several modalities, not our templated ultrasound wording); a low score here is a statement about this use, not about RadGraph on chest X-ray. The partial reward level was chosen up front as the RadGraph-F1; simple and complete levels are saved locally but not analysed.',
       '- Same limits as Steps 33 / 34 / 35: templated text, matched synonyms as the harmless side (word-level scorers follow edit size), crude rule-based transformations on free text, the judge on capped subsets.',
       '- The venv versions (radgraph 0.1.18, transformers 4.46.3, torch 2.15, CPU) are recorded in `run_info.json`; RadGraph-XL was not retrained or tuned.', '']
open(os.path.join(D, 'results.md'), 'w').write('\n'.join(md))
def g(*c):
    try: return subprocess.check_output(c, text=True, cwd=N.ROOT).strip()
    except Exception: return None
json.dump(dict(step='37', radgraph='radgraph 0.1.18, model radgraph-xl (StanfordAIMI/RRG_scorers), CPU, reward level partial', env='uv venv python 3.12.13, transformers 4.46.3, torch 2.15.0, numpy 1.26.4', green=G['summary'], git_head_at_report=g('git', 'rev-parse', '--short', 'HEAD'), date=time.strftime('%Y-%m-%d'), bootstrap='group, 1000 resamples, seed 0', min_groups=30, test_split_read='no new read (scores for texts of Steps 33-35)'), open(os.path.join(D, 'run_info.json'), 'w'), indent=1); print('wrote', len(md))
