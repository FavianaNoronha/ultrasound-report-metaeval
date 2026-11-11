"""Step 35 report: results/partA/step35_lod/results.md (no model calls)."""
import os, json, sys, platform, time, subprocess
import numpy as np
from . import step35_lod as L
D = L.OUT; R = json.load(open(os.path.join(D, 'results.json')))
NM = {'bleu': 'BLEU', 'rougeL': 'ROUGE-L', 'chrf': 'chrF', 'bertscore[roberta-large]': 'BERTScore', 'ratescore': 'RaTEScore', 'finding_f1': 'finding_f1 (upper bound)', 'sentence_f1': 'judge sentence_f1', 'judge_score': 'judge_score', 'image_medsam_oracle_exact': 'image check, oracle-box MedSAM (Step 16 rule)', 'image_unet_tolerance': 'image check, label-free U-Net (Step 20 rule)'}
CELLS = [('breast', 'size_mm', 'breast, size in mm (BrEaST only)'), ('breast', 'size_pct', 'breast, size as % of image width'), ('thyroid', 'size_pct', 'thyroid, size as % of image width'), ('fetal head', 'hc_mm', 'fetal head, head circumference (mm shift)')]
def lv(c, x): return (f'{x*100:.0f}%' if c[1] != 'hc_mm' else f'{x:g} mm')
def lodtxt(v, c):
    if v['lod'] is None: return f"not reached (> {lv(c, v['levels'][-1])})"
    lo, hi = v['lod_ci']; f = lambda s: s if s.startswith('>') else lv(c, float(s)); return f"{lv(c, v['lod'])} ({f(lo)} to {f(hi)})" + (' (non-monotone)' if v['nonmonotone'] else '')
md = ['# Step 35: limit of detection', '',
      'Limitations: [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md). Code: `usmeta/step35_lod.py`, `step35_report.py` (new files; Step 21b candidates and saved scores reused; frozen templates and scorers imported unchanged). Test split: the Step 21b test references (`bench_test_v2d`), saved scores reused, new candidates scored now.', '',
      '**Definition.** For each scorer and field: the **smallest error level at which the AUROC of planted size (or head-circumference) errors against the matched one-word synonyms of the same reference reaches 0.80**. Size errors: multiplicative factors of the stated size (Step 21b ×0.5, 0.7, 0.8, 0.9, 0.95, 1.3, 1.5, 2.0 plus new ×1.05, 1.10, 1.25), pooled over both directions into the levels 5, 10, 20, 25, 30, 50 and 100% relative error. Head circumference: new additive shifts of ±1, 2, 5, 10, 20 mm (both signs pooled; the Step 21b factor errors for HC are not used here). AUROC per case (ties 0.5), mean over cases; the 95% interval of the limit of detection is the percentile range of the same rule over 1,000 group bootstrap resamples (seed 0; resamples where no level reaches 0.80 count as "above the largest level"). Non-monotone curves are flagged. Judge rows use the capped subset (12 cases per dataset for the new candidates, Step 21b replies reused); cells with fewer than 30 groups at a level are marked †.', '', '## Headline', '']
for c in CELLS:
    rows = [(n, R[f'{n}|{c[0]}|{c[1]}']) for n in NM if f'{n}|{c[0]}|{c[1]}' in R]
    if not rows: continue
    reached = [(NM[n], v) for n, v in rows if v['lod'] is not None]; none = [NM[n] for n, v in rows if v['lod'] is None]
    md.append(f"- **{c[2]}:** limit of detection (AUROC >= 0.80 vs matched synonyms): " + (', '.join(f"{nm} {lv(c, v['lod'])}" + (' (judge cells under 30 groups)' if v['too_small_levels'] and 'judge' in nm else '') for nm, v in sorted(reached, key=lambda x: x[1]['lod'])) or 'none') + '; not reached at any level tested by ' + (', '.join(none) or 'none') + '.')
md += ['', 'A limit of detection of 5% is the smallest size error tested (head circumference: 1 mm). A scorer that "reaches" 0.80 at a level can still be below 0.80 at a larger level (flagged non-monotone), and `finding_f1` reads our template, so its limit is the smallest tested level by construction (upper bound).', '']
for c in CELLS:
    rows = [(n, R[f'{n}|{c[0]}|{c[1]}']) for n in NM if f'{n}|{c[0]}|{c[1]}' in R]
    if not rows: continue
    levels = rows[0][1]['levels']
    md += [f'## {c[2][0].upper() + c[2][1:]}', '', '| scorer | limit of detection (95% CI) | ' + ' | '.join(lv(c, x) for x in levels) + ' |', '|---|---|' + '---|' * len(levels)]
    for n, v in rows:
        cells = []
        for x in levels:
            a = v['auroc'].get(str(x)) if str(x) in v['auroc'] else v['auroc'].get(x); ci = v['auroc_ci'].get(str(x)) if str(x) in v['auroc_ci'] else v['auroc_ci'].get(x)
            cells.append('—' if a is None else f"{a:.2f}" + (' †' if x in v['too_small_levels'] or str(x) in map(str, v['too_small_levels']) else ''))
        md.append(f"| {NM[n]} | {lodtxt(v, c)} | " + ' | '.join(cells) + ' |')
    md += ['', 'AUROC (point estimates) by error level; † = fewer than 30 groups at that level. Confidence intervals of every AUROC are in `results.json`.', '']
md += ['## Caveats', '',
       '- **Templated text, matched synonyms as the harmless side:** the AUROC vs a one-word synonym measures whether a scorer separates a one-number change from a one-word change; word scorers\' values follow edit size (Step 33 edit-size law), so a limit of detection is not "the smallest error a scorer understands".',
       '- **Rounding:** size values are integers (mm or %), so small factors on small sizes round to the same value and the candidate is dropped; levels therefore have fewer cases for small sizes (case counts per level are in `results.json`).',
       '- **Levels pool both directions** (×0.95 and ×1.05 are both "5%"); the image-check curve is asymmetric (Step 21b: sizes too small are scored as better), so its pooled value can hide one side.',
       '- **Head circumference:** only the additive-shift candidates are used; the image checks for fetal head are Step 16 masks only (oracle box, exact rule); the Step 29 U-Net rows are breast and thyroid only.',
       '- Judge rows: capped subset, one prompt, greedy; `llm_finding_f1` was not run here (extraction of every candidate was out of scope).', '']
open(os.path.join(D, 'results.md'), 'w').write('\n'.join(md))
def g(*c):
    try: return subprocess.check_output(c, text=True, cwd=L.ROOT).strip()
    except Exception: return None
json.dump(dict(step='35', git_head_at_report=g('git', 'rev-parse', '--short', 'HEAD'), python=sys.version.split()[0], platform=platform.platform(), date=time.strftime('%Y-%m-%d'), bootstrap='group, 1000 resamples, seed 0', threshold=L.THRESH, min_groups=30), open(os.path.join(D, 'run_info.json'), 'w'), indent=1); print('wrote', len(md))
