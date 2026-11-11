"""Step 33 (factorial) report: results.md + results summary json (no model calls)."""
import os, json, sys, platform, time, subprocess
import numpy as np
from . import step33_factorial as F
D = F.OUT; R = json.load(open(os.path.join(D, 'results.json'))); PRE = '[PREREG.md](PREREG.md)'
def ci(v, k=2): return '—' if not v else f"{v[0]:.{k}f} ({v[1]:.{k}f}–{v[2]:.{k}f})"
def cc(v, k=2): return '—' if not v else f"{v[0]:.{k}f}–{v[1]:.{k}f}"
names = [(n, nm) for n, nm in F.SCORERS if R.get(n) and R[n].get('pooled')]
fd = [nm for n, nm in names if R[n]['pooled']['fact_driven']]; wd = [nm for n, nm in names if not R[n]['pooled']['fact_driven']]
B = R['_build']
md = ['# Step 33: 2x2 factorial, fact x wording', '',
      f'Limitations: [docs/LIMITATIONS.md](../../../docs/LIMITATIONS.md). Pre-registration (committed before any cell (d) score or test number): {PRE}. Code: `usmeta/step33_factorial.py`, `step33_factorial_report.py` (new files; frozen `bench_v2.errors`, `templates_v2.render`, saved test scores and the scorer classes imported unchanged). Test split read once, logged (`usmeta.step33_factorial`).', '',
      '**Design.** Four cells per reference (breast and thyroid test references): (a) no error, small edit (existing `small` + `matched` harmless), (b) no error, large edit (existing style swaps), (c) error, small edit (existing planted error), (d) **error, large edit (new): the same planted error rendered in the large style** (the frozen large-rewording generator applied to the erroneous report; the regex extractor must show the planted value, else the candidate is dropped). Unit = block (reference, error, large style) with four scores; the two-way variance decomposition splits the score variance into fact, wording, interaction and residual (within-cell spread across references and errors).', '',
      '## Decision line (pre-registered: "fact-driven" if eta-squared(fact) > eta-squared(wording), pooled breast + thyroid)', '',
      f"**Fact-driven: {', '.join(fd) if fd else 'none'}. Wording-driven: {', '.join(wd) if wd else 'none'}.** " + '; '.join(f"{nm} fact {R[n]['pooled']['eta']['fact']:.2f} vs wording {R[n]['pooled']['eta']['wording']:.2f}" for n, nm in names) + '.', '',
      '**What the AUROCs add.** ' + 'At matched large wording the word scorers do separate an error from a correct text (AUROC (d vs b): ' + ', '.join(f"{nm} {R[n]['pooled']['auroc_d_vs_b'][0]:.2f}" for n, nm in names if n in ('bleu', 'rougeL', 'chrf', 'bertscore[roberta-large]', 'ratescore')) + '), because an error adds its own changes on top of the rewrite; at matched small wording they cannot (AUROC (c vs a): ' + ', '.join(f"{nm} {R[n]['pooled']['auroc_c_vs_a'][0]:.2f}" for n, nm in names if n in ('bleu', 'rougeL', 'chrf', 'bertscore[roberta-large]', 'ratescore')) + '). The clinically relevant reversal, an error with a small edit outranking a correct text in a large rewrite, happens in ' + ', '.join(f"{nm} {R[n]['pooled']['reversal_c_above_b'][0]*100:.0f}%" for n, nm in names if n in ('bleu', 'rougeL', 'chrf', 'bertscore[roberta-large]', 'ratescore')) + ' of (c, b) pairs and in ' + ', '.join(f"{nm} {R[n]['pooled']['reversal_c_above_b'][0]*100:.0f}%" for n, nm in names if n in ('judge_score', 'sentence_f1')) + ' for the judge (capped subset, 71 groups).', '',
      f"Built: {B['stats'].get('kept', 0):,} (d) candidates kept of {B['stats'].get('candidates (d) attempted', 0):,} attempted ({B['stats'].get('dropped', 0)} dropped: {', '.join(f'{k} x{v}' for k, v in B['reasons'].items()) or 'none'}); {B['stats'].get('error rows not regenerated (skipped)', 0)} planted-error rows could not be regenerated from the frozen builder (histology errors) and are not in the factorial; blocks kept: " + ', '.join(f'{o} {n:,}' for o, n in B['kept_by_organ'].items()) + f". The judge rows use the capped subset ({B['judge_blocks']} blocks, at most 12 cases per dataset and 3 planted errors per case, all four cells judged).", '',
      '## Variance decomposition (share of the total sum of squares; 95% bootstrap CI over reference groups)', '', '| scorer | organ | blocks / groups | fact | wording | interaction | residual | fact - wording (CI) | verdict |', '|---|---|---|---|---|---|---|---|---|']
for n, nm in names:
    for o in ('pooled', 'breast', 'thyroid'):
        r = R[n].get(o)
        if not r: continue
        e = r['eta']; c = r['eta_ci']; md.append(f"| {nm} | {o} | {r['n_blocks']:,} / {r['n_groups']}{' †' if r['too_small'] else ''} | {e['fact']:.2f} ({cc(c.get('fact'))}) | {e['wording']:.2f} ({cc(c.get('wording'))}) | {e['interaction']:.2f} | {e['residual']:.2f} | {ci([e['fact'] - e['wording']] + (r['eta_diff_ci'] or [float('nan'), float('nan')]))} | {'fact-driven' if r['fact_driven'] else 'wording-driven'} |")
md += ['', '† = under 30 groups: too small to compare (judge rows). Interaction means the effect of an error depends on the wording (for example an error is hidden by a large rewrite).', '',
       '## AUROC of error vs harmless at matched wording, and reversal rates (95% CI by group bootstrap, per-reference means)', '',
       '| scorer | organ | AUROC (c vs a): error vs correct, small edits | AUROC (d vs b): error vs correct, large edits | reversal as specified: share of (d, a) pairs with d < a | clinically relevant reversal: share of (c, b) pairs with error+small ABOVE correct+large | share of (d, a) pairs with d above a |', '|---|---|---|---|---|---|---|']
for n, nm in names:
    for o in ('pooled', 'breast', 'thyroid'):
        r = R[n].get(o)
        if r: md.append(f"| {nm} | {o} | {ci(r['auroc_c_vs_a'])} | {ci(r['auroc_d_vs_b'])} | {ci(r['reversal_d_below_a'])} | {ci(r['reversal_c_above_b'])} | {ci(r['d_above_a'])} |")
md += ['', 'The reversal share as specified (d below a) is expected to be high for **any** scorer that reacts to either factor, because (d) carries both an error and a large rewrite; it does not separate fact from wording. The clinically relevant reversal is the share of pairs where an error with a small edit outranks a harmless large rewrite (a wrong report scored better than a correct one in another wording); the last column is the share where the doubly changed text still scores above the correct small-edit text.', '',
       '## Deviations from the pre-registration', '', '- None in the design or decision rule. Implementation notes: histology errors cannot be regenerated from the frozen builder and are excluded (counted above); the judge subset is chosen with seed 0 among judged cases whose (a), (b), (c) were judged, so it may be smaller than 12 per dataset.', '',
       '## Caveats', '',
       '- **Templated text only.** (d) is the same error in the terse or long template; real paraphrases of an erroneous report are not tested. The regex extractor that verifies (d) reads the same template (it verifies the planted fact is present, not that the text reads naturally).',
       '- **Block structure:** blocks share references and errors, so the bootstrap resamples reference groups, not blocks; the eta-squared shares also include the spread across error types and references in the residual.',
       '- **Judge rows** use at most 12 cases per dataset (< 30 groups for several cells); the judge was run once with prompt_v2, greedy.',
       '- `finding_f1` (regex) is an upper bound on templated text and is shown for reference.', '']
open(os.path.join(D, 'results.md'), 'w').write('\n'.join(md))
def g(*c):
    try: return subprocess.check_output(c, text=True, cwd=F.ROOT).strip()
    except Exception: return None
json.dump(dict(step='33_factorial', git_head_at_report=g('git', 'rev-parse', '--short', 'HEAD'), python=sys.version.split()[0], platform=platform.platform(), date=time.strftime('%Y-%m-%d'), bootstrap='reference group, 1000 resamples, seed 0', min_groups=30, decision='fact-driven iff eta2(fact) > eta2(wording), pooled breast+thyroid'), open(os.path.join(D, 'run_info.json'), 'w'), indent=1); print('wrote', len(md), 'fact-driven:', fd)
