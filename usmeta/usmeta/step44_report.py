"""Step 44: build results.md (verdicts first) from results/partA/step44_monitors/results.json. NEW file; no recomputation.
    python3 -m usmeta.step44_report"""
import os, json
from .step44_monitors import OUT, BUDGETS

NAMES = {'bleu': 'BLEU', 'rougeL': 'ROUGE-L', 'chrf': 'chrF', 'bertscore[roberta-large]': 'BERTScore', 'ratescore': 'RaTEScore', 'finding_f1': 'finding_f1 (CEILING, upper bound on templated text)', 'judge_score': 'Gemma-2-9B judge', 'radgraph_f1': 'RadGraph-F1 (partial coverage)'}
def p(c, d=1):
    if not c: return 'n/a'
    return f"{c['est'] * 100:.{d}f} ({c['lo'] * 100:.{d}f}-{c['hi'] * 100:.{d}f})" + ('†' if c['too_small'] else '')
def e(c): return f"{c['est'] * 100:.1f}"

R = json.load(open(os.path.join(OUT, 'results.json'))); A = R['A_full_test']; J = R['A_judge_subset']; L = []
pr = R['pools']; errshare = 10295 / 25887; sub_share = R['E_reason_match']['error_pairs'] / pr['test_judge_rows']
j10 = J['judge_score']['budgets']['10']; j5 = J['judge_score']['budgets']['5']; r = lambda d, n, b: d[n]['budgets'][str(b)]
best_text10 = max((n for n in ('bleu', 'rougeL', 'chrf', 'bertscore[roberta-large]', 'ratescore')), key=lambda n: r(J, n, 10)['catch']['est'])
Fb = R['F_step39b']['budgets']['5']; Em = R['E_reason_match']; D = R['D_cascade']; IM = R['image_check']

L += ['# Step 44: scorers as monitors (audit budgets, severity weighting, cascade, reason-match, flag agreement)', '',
 f"**Verdicts (pre-registered analyses; PREREG.md committed before any number; saved scores and cached replies only, no model call; thresholds from val, results on test; group bootstrap 1,000, seed 0; † = under 30 groups).**", '',
 f"1. **At the pre-registered val thresholds the judge catches most planted errors; the word and embedding scorers catch a minority, but the budgets are not matched in realised share, so this is not a like-for-like comparison.** On the judge test subset ({pr['test_judge_rows']:,} candidates, {sub_share * 100:.1f}% planted errors) the judge (5% budget threshold; 10% gives the same threshold) flags {e(j5['flagged_share'])}% of candidates (realised; it scores in coarse steps) and catches **{p(j5['catch'])}%** of planted errors (severity-weighted {p(j5['catch_severity_weighted'])}%), flagging {p(j5['flag_harmless_all'])}% of harmless rewordings and {p(j5['flag_identical'])}% of identical copies. The best word/embedding scorer at the 10% budget ({NAMES[best_text10]}) catches {p(r(J, best_text10, 10)['catch'])}% while flagging {p(r(J, best_text10, 10)['flagged_share'])}% of the pool and {p(r(J, best_text10, 10)['flag_harmless_all'])}% of harmless rewordings. The ceiling finding_f1 catches {p(r(J, 'finding_f1', 10)['catch'])}% at a realised {p(r(J, 'finding_f1', 10)['flagged_share'])}% flagged with 0% of harmless flagged.",
 f"2. **Catch at a fixed budget is capped by prevalence**: with 39.8% planted errors in the full test pool (33.0% in the judge subset), a monitor that flags 1 / 2 / 5 / 10% of candidates can catch at most 2.5 / 5.0 / 12.6 / 25.1% of errors. Read the *realised* flagged share beside each catch rate, not the nominal budget.",
 f"3. **Cascade (cheap scorer first, judge on the flagged share): large call savings, but most of the judge's catch is lost**, because small-edit planted errors score high on word scorers and are never sent to the judge: e.g. chrF at s=40% sends {p(D['chrf|s40|b5']['sent_to_judge'])}% to the judge (saves {D['chrf|s40|b5']['calls_saved'] * 100:.0f}% of judge calls) and catches {p(D['chrf|s40|b5']['catch'])}% against {p(D['judge_alone|b5']['catch'])}% for the judge alone.",
 f"4. **Judge reason-match: the judge's listed error names the planted field in {p(Em['all_planted_errors']['fld'])}% of planted errors (keyword proxy; a control with another field's keywords matches {p(Em['all_planted_errors']['ctl'])}%) and the planted category in {p(Em['all_planted_errors']['cat'])}%.**",
 f"5. **Step 39b (exploratory): by flag decision, the 3-prompt ensembles do not agree with each other more than the two single prompts do.** Ensemble A vs B agree on {p(Fb['ensembleA_vs_ensembleB']['all_pairs'])}% of {R['F_step39b']['pairs']} pairs against {p(Fb['P0_vs_P3_single']['all_pairs'])}% for P0 vs P3 (on planted errors alone {p(Fb['ensembleA_vs_ensembleB']['planted_errors'])}% vs {p(Fb['P0_vs_P3_single']['planted_errors'])}%), because set A flags fewer errors ({p(Fb['flag_rate_on_errors']['A'])}%) than set B ({p(Fb['flag_rate_on_errors']['B'])}%). The original Step 39 H1 result (39.2% vs 21.5%, not supported) is unchanged.", '',
 f"Severity levels are **our own provisional labels, not clinician-set** (Step 30). Severity-based monitoring is prior art (DrugBench, arXiv 2606.20663, the id resolves to DrugBench, an AI-control paper on medication harm; its coverage of severity-based monitoring was not read in full, so the prior-art statement follows the brief), so no novelty is claimed. Pool: test {pr['test_rows']:,} candidates ({pr['test_groups']:,} groups), val {pr['val_rows']:,}; judge subset test {pr['test_judge_rows']:,}, val judge pool {pr['val_judge_rows']:,} rows in this analysis (pooled across datasets; too small to read per organ). Pre-registration: [PREREG.md](PREREG.md). Code: `usmeta/step44_monitors.py`, `step44_report.py`.", '']

def monitor_rows(d, names, with_flag=True):
    out = ['| scorer | nominal budget | val threshold | realised flagged share | planted errors caught | severity-weighted catch | harmless flagged | identical flagged |', '|---|---|---|---|---|---|---|---|']
    for n in names:
        if n not in d or not d[n].get('available'): out.append(f"| {NAMES.get(n, n)} | not available ({d.get(n, {}).get('reason', 'no val scores')}) | | | | | | |"); continue
        for b in BUDGETS:
            c = d[n]['budgets'][str(b)]; out.append(f"| {NAMES.get(n, n)} | {b}% | {c['threshold']:.3f} | {p(c['flagged_share'])} | {p(c['catch'])} | {p(c['catch_severity_weighted'])} | {p(c['flag_harmless_all'])} | {p(c['flag_identical'])} |")
    return out

L += ['## A + B + C. Catch rate, severity-weighted catch, safety vs usefulness', '',
 'All values are percentages with 95% group-bootstrap intervals. Flag = score <= the val percentile of that scorer (X-th percentile of val scores over error + harmless + identical candidates). "Harmless" = small, matched, large and other rewordings; "identical" = copies of the reference.', '',
 '### Full test pool (text scorers; 25,887 candidates)', ''] + monitor_rows(A, ['bleu', 'rougeL', 'chrf', 'bertscore[roberta-large]', 'ratescore']) + ['',
 '### Ceiling (not a deployable monitor): finding_f1', '', 'finding_f1 reads the same fields the templates are built from, so it is an upper bound on templated text, not a real monitor.', ''] + monitor_rows(A, ['finding_f1']) + ['',
 f"### Judge test subset ({pr['test_judge_rows']:,} candidates): every scorer on the same candidates", '', 'Thresholds for the text scorers still come from their full val pool; the judge threshold comes from the val judge sample (pooled, small). Ties make the realised share differ from the nominal budget (the judge, RadGraph-F1 and finding_f1 take few distinct values).', ''] + monitor_rows(J, ['bleu', 'rougeL', 'chrf', 'bertscore[roberta-large]', 'ratescore', 'judge_score', 'radgraph_f1', 'finding_f1']) + ['',
 '**Not available as budgeted monitors (no val scores, so no val threshold; nothing taken from test):** `llm_finding_f1` (saved for the same 2,568 test pairs, no val pair). **RadGraph-F1** has saved scores only for a non-random part of the benchmark (Steps 33-35 designs): partial coverage, shown above and in the table below; its val threshold is 0.000 at every budget (more than 10% of val RadGraph rows score 0), so all budgets coincide.', '', '### RadGraph-F1 on every test row that has a saved score (partial coverage, not comparable with the full-pool tables)', ''] + monitor_rows(R['radgraph_partial_full_rows'], ['radgraph_f1']) + ['']

def sev_rows(d, names, b):
    out = [f'**Catch rate by severity at the {b}% budget** (1 minor, 2 major, 3 critical; our own labels)', '', '| scorer | severity 1 | severity 2 | severity 3 | weighted |', '|---|---|---|---|---|']
    for n in names:
        if n in d and d[n].get('available'): c = d[n]['budgets'][str(b)]; out.append(f"| {NAMES.get(n, n)} | {p(c['catch_by_severity']['1'])} | {p(c['catch_by_severity']['2'])} | {p(c['catch_by_severity']['3'])} | {p(c['catch_severity_weighted'])} |")
    return out + ['']
L += ['### B. By severity', ''] + sev_rows(A, ['bleu', 'rougeL', 'chrf', 'bertscore[roberta-large]', 'ratescore', 'finding_f1'], 10) + ['Judge subset:', ''] + sev_rows(J, ['judge_score', 'chrf', 'ratescore', 'finding_f1'], 5)
L += ['### Per organ (catch / severity-weighted catch / harmless flagged), 10% budget, full test pool', '', '| scorer | organ | catch | severity-weighted | harmless flagged |', '|---|---|---|---|---|']
for n in ('bleu', 'rougeL', 'chrf', 'bertscore[roberta-large]', 'ratescore'):
    for og, c in A[n]['budgets']['10']['by_organ'].items(): L.append(f"| {NAMES[n]} | {og} | {p(c['catch'])} | {p(c['catch_severity_weighted'])} | {p(c['flag_harmless_all'])} |")
L += ['', 'Judge subset, 5% budget:', '', '| scorer | organ | catch | severity-weighted | harmless flagged |', '|---|---|---|---|---|']
for n in ('judge_score', 'chrf', 'ratescore'):
    for og, c in J[n]['budgets']['5']['by_organ'].items(): L.append(f"| {NAMES[n]} | {og} | {p(c['catch'])} | {p(c['catch_severity_weighted'])} | {p(c['flag_harmless_all'])} |")
L += ['', '### C. Harmless rewordings flagged by type, 10% budget, full test pool', '', '| scorer | small | matched | large | other |', '|---|---|---|---|---|']
for n in ('bleu', 'rougeL', 'chrf', 'bertscore[roberta-large]', 'ratescore'):
    t = A[n]['budgets']['10']['flag_harmless_by_type']; L.append(f"| {NAMES[n]} | {p(t['small'])} | {p(t['matched'])} | {p(t['large'])} | {p(t['other'])} |")
L += ['', 'Judge (judge subset, 5% budget): ' + ', '.join(f"{k} {p(v)}" for k, v in j5['flag_harmless_by_type'].items()) + '.', '']

L += ['## D. Cascade (judge test subset; a cheap scorer first, the judge only on the flagged share)', '', 'Stage 1 flags the lowest s% by its val threshold; stage 2 flags a sent candidate if the judge score is at or below the judge val threshold for budget b. The judge val thresholds for b = 5% and 10% coincide (0.4), so those rows are identical. "Calls saved" = share of the pool never sent to the judge (replies already exist; no new call was made).', '', '| first stage | s | judge | sent to judge | judge calls saved | planted errors caught | harmless flagged | identical flagged |', '|---|---|---|---|---|---|---|---|', f"| (none: judge alone) | | b=5% | 100% | 0% | {p(D['judge_alone|b5']['catch'])} | {p(D['judge_alone|b5']['flag_harmless_all'])} | {p(D['judge_alone|b5']['flag_identical'])} |"]
for c in ('bleu', 'rougeL', 'chrf'):
    for s in (10, 20, 40):
        o = D[f'{c}|s{s}|b5']; L.append(f"| {NAMES[c]} | {s}% | b=5% | {p(o['sent_to_judge'])} | {o['calls_saved'] * 100:.0f}% | {p(o['catch'])} | {p(o['flag_harmless_all'])} | {p(o['flag_identical'])} |")
E_ = Em; L += ['', '## E. Judge reason-match (judge test subset, planted-error pairs)', '', f"{E_['error_pairs']} planted-error pairs; the judge's listed errors were read back from the saved raw replies in `.llm_cache` ({E_['cache_missing']} missing). The field match is a **keyword proxy** (frozen keyword map in `step44_monitors.py`), not a human read. The control row (added after the PREREG, not pre-registered) tests each pair's judge text against the keywords of a different field.", '', '| measure | share of all planted errors | share among errors where the judge listed at least one error |', '|---|---|---|',
 f"| a listed error has the planted **category** | {p(E_['all_planted_errors']['cat'])} | {p(E_['judge_listed_at_least_one_error']['cat'])} |", f"| a listed error's field text contains a keyword of the planted **field** | {p(E_['all_planted_errors']['fld'])} | {p(E_['judge_listed_at_least_one_error']['fld'])} |", f"| both on the same listed error | {p(E_['all_planted_errors']['both'])} | {p(E_['judge_listed_at_least_one_error']['both'])} |", f"| control: keywords of a different field | {p(E_['all_planted_errors']['ctl'])} | {p(E_['judge_listed_at_least_one_error']['ctl'])} |", '',
 'The judge lists at least one error for almost every planted error, so the weak point of the judge as a monitor is its score threshold (it penalises by severity), not silence. By planted field (among pairs where the judge listed an error):', '', '| planted field | pairs | field match | category match |', '|---|---|---|---|']
for k, v in E_['by_field'].items(): L.append(f"| {k} | {v['n']} | {p(v['field_match_among_flagged'])} | {p(v['category_match_among_flagged'])} |")
L += ['', 'Category match is low where the planted category is "wrong severity/category" for fields the judge describes as another category (plane, lesion, orient); field match is the cleaner reading.', '']

b5, b10 = R['F_step39b']['budgets']['5'], R['F_step39b']['budgets']['10']
L += ['## F. Step 39b (EXPLORATORY; does not change or replace the Step 39 H1 result: 39.2% vs 21.5%, not supported)', '',
 f"Flag threshold from the val P0 judge pool (judge_score <= {R['F_step39b']['val_thresholds']['5']:.2f} at both 5% and 10% budgets; val has no planted-error replies for P1-P5, so the P0 val threshold on the shared judge_score scale is applied to every prompt and ensemble). {R['F_step39b']['pairs']} of {R['F_step39b']['pairs_planned']} Step 39 pairs have all six replies (the 3 h cap). Agreement = the two judges make the same flag / no-flag decision.", '',
 '| comparison | all pairs | planted errors | harmless or identical |', '|---|---|---|---|']
for k, lab in (('ensembleA_vs_ensembleB', 'ensemble A (P0,P1,P2) vs ensemble B (P3,P4,P5)'), ('P0_vs_P3_single', 'single P0 vs single P3')):
    o = b5[k]; L.append(f"| {lab} | {p(o['all_pairs'])} | {p(o['planted_errors'])} | {p(o['harmless_or_identical'])} |")
L += ['', '| judge | flags planted errors | flags harmless or identical |', '|---|---|---|']
for k in ('A', 'B', 'P0', 'P3'): L.append(f"| {'ensemble ' + k if k in 'AB' else 'single ' + k} | {p(b5['flag_rate_on_errors'][k])} | {p(b5['flag_rate_on_non_errors'][k])} |")
L += ['', 'The two ensembles differ systematically in how many errors they flag (set A includes two paraphrase prompts that flag fewer), which lowers their agreement; averaging wordings did not make the flag decision more reproducible in this sample. No hypothesis test and no verdict is attached.', '']

L += ['## Image check (fixed Step 20 rule; 119 test scans, mask-checkable error fields only; no val threshold exists)', '', 'Flag iff the Step 20 tolerance-aware score is below 1. **The MedSAM oracle-box row uses the true box (an upper bound, a CEILING); the U-Net row is label-free.** The false-flag shares on harmless and identical candidates are large: the check disagrees with the reference text on many correct reports, so this fixed rule is not a usable monitor on its own.', '', '| check | candidates | flagged share | planted errors caught | severity-weighted | harmless flagged | identical flagged |', '|---|---|---|---|---|---|---|']
if 'error' in IM: L.append(f"| error | {IM['error']} | | | | | |")
else:
    for n, lab in (('image_medsam_oracle_box', 'MedSAM, true box (CEILING)'), ('image_unet_label_free', 'U-Net, label-free')): c = IM[n]; L.append(f"| {lab} | {c['pool']:,} | {p(c['flagged_share'])} | {p(c['catch'])} | {p(c['catch_severity_weighted'])} | {p(c['flag_harmless_all'])} | {p(c['flag_identical'])} |")
L += ['', '## Caveats', '', '- Templated text, one model family, the benchmark prevalence (39.8% planted errors in the full pool, 33.0% in the judge subset) and the planted-error mix, not field prevalence; no precision or PPV is reported.',
 '- The judge subset is a stratified sample (59 cases per dataset, Steps 10d + 12); the judge val pool is small and pooled over datasets, and the judge takes few distinct values, so a nominal budget cannot be hit (realised share is shown).',
 '- A first run of the script used the test score dictionary for the val thresholds by mistake (val coverage 4,817 instead of 16,200); it was fixed before any number was written down and the whole script re-run.',
 '- Severity labels are ours, not clinician-set; the reason-match is a keyword proxy; RadGraph-F1 covers part of the benchmark; `llm_finding_f1` and the U-Net have no val scores for a budget; HiSBreast and free text are not part of this step.', '']
open(os.path.join(OUT, 'results.md'), 'w').write('\n'.join(L)); print('wrote', len(L))
