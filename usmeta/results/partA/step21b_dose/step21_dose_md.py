"""Step 21b: markdown tables from dose_results.json."""
import json, sys
from .step21_dose import SCORERS, FACTORS
D = sys.argv[1]; R = json.load(open(f'{D}/dose_results.json')); MIN_N = 30
NAME = {'finding_f1': 'finding_f1 (UPPER BOUND, templated)', 'image_check': 'image check (predicted masks, exact box)', 'sentence_f1': 'judge sentence_f1', 'judge_score': 'judge judge_score'}
f = lambda a: '—' if a is None else f'{a[0]:.2f} ({a[1]:.2f}–{a[2]:.2f})'
md = []
for org in ('breast', 'thyroid', 'fetal head'):
    md += [f'### {org}', '', 'AUROC of size errors of factor × (stated size) against the matched one-word synonyms of the same reference (95% CI, patient/exam groups; n cases in brackets; † = fewer than 30 groups: too small to compare). Spearman ρ = rank correlation between |log factor| and the score drop (1 − score) over all error candidates (positive = bigger errors score lower).', '',
           '| scorer | ' + ' | '.join(f'×{x}' for x in FACTORS) + ' | all factors | Spearman ρ |', '|---|' + '---|' * (len(FACTORS) + 2)]
    for n in SCORERS:
        cells = []
        for k in FACTORS + ['ALL']:
            d = R[f'{n}|{org}|{k}']; cells.append('—' if not d['auroc'] else f"{f(d['auroc'])} ({d['n_cases']}){' †' if d['n_groups'] < MIN_N else ''}")
        rho = R[f'{n}|{org}|spearman']['rho']; md.append(f"| {NAME.get(n, n)} | " + ' | '.join(cells) + f" | {'—' if rho is None else f'{rho:+.2f}'} |")
    md += ['', f'Mean score per factor ({org}):', '', '| scorer | ' + ' | '.join(f'×{x}' for x in FACTORS) + ' |', '|---|' + '---|' * len(FACTORS)]
    for n in SCORERS:
        m = R[f'{n}|{org}|mean_score']; md.append(f"| {NAME.get(n, n)} | " + ' | '.join('—' if m[str(x)] is None else f'{m[str(x)]:.3f}' for x in FACTORS) + ' |')
    md.append('')
open(f'{D}/tables.md', 'w').write('\n'.join(md)); print('\n'.join(md[:6]))
