"""Step 22: paper-support tables from SAVED results only (no model calls). NEW file.
Table 1: paired preference by error type for each organ (Step 19a method on saved test scores, pooled within one organ, group bootstrap).
Table 2: failure taxonomy (numbers copied from saved result files; path given per row).
Table 3: monotonicity (Spearman rho between error size and score drop) per scorer per organ from Step 21b.
    python3 -m usmeta.step22_paper_support OUT_DIR"""
import json, sys, os, csv, collections
import numpy as np
from . import step19_pairs as P

MIN_N = 30
FIELDNAME = {'lesion': 'lesion present / absent', 'count': 'number of lesions', 'pos': 'position', 'orient': 'orientation', 'size_pct': 'size (% of image width)', 'size_mm': 'size (mm)', 'hc_mm': 'head circumference (mm)',
             'birads': 'BI-RADS category', 'tirads': 'TI-RADS category', 'path': 'pathology (benign / malignant)', 'hist': 'histology', 'side': 'side', 'shape': 'shape', 'margin': 'margin', 'echo': 'echo pattern',
             'post': 'posterior features', 'halo': 'echogenic halo', 'calc': 'calcifications', 'comp': 'composition', 'foci': 'echogenic foci', 'plane': 'fetal plane'}
SC = [('bleu', 'BLEU'), ('rougeL', 'ROUGE-L'), ('chrf', 'chrF'), ('bertscore[roberta-large]', 'BERTScore'), ('ratescore', 'RaTEScore'), ('judge_score', 'Gemma judge (judge_score)'), ('finding_f1', 'finding_f1 (upper bound)')]

def table1(out):
    rt, st, jt = P.load('test'); Ct, Ctj = P.cases_of(rt), P.cases_of(rt, jt); rows = []; md = []
    for org in ('breast', 'thyroid', 'fetal head'):
        dss = [d for d in P.ORGAN if P.ORGAN[d] == org]; fields = sorted({r['field'] for c in Ct.values() if c['ds'] in dss for r in c['E']}, key=lambda f: list(FIELDNAME).index(f) if f in FIELDNAME else 99)
        md += [f'### {org}', '', 'Paired preference = share of (planted error, harmless rewording) pairs of the same reference in which the error scores LOWER; ties (shown as strict preference) count as not preferred; AUROC = strict + ½ ties. n = test cases with that error type (groups in the CSV). † = fewer than 30 groups: too small to compare. Judge column: judged subset only.', '',
               '| error type | n cases | ' + ' | '.join(l for _, l in SC) + ' |', '|---|---|' + '---|' * len(SC)]
        for f in fields:
            cells = []; ncase = None
            for n, lab in SC:
                C, sc = (Ctj, st) if n in P.JUDGE else (Ct, st); Cs = {k: v for k, v in C.items() if v['ds'] in dss}
                s, t, h, g = P.pref(Cs, sc, n, sel=lambda r, f=f: r['field'] == f)
                if s:
                    from .step10d_analysis import gboot
                    a = gboot(s, g); cells.append(f"{a[0]:.2f}{' †' if len(set(g)) < MIN_N else ''}"); rows.append(dict(organ=org, error_type=f, scorer=lab, n_cases=len(s), n_groups=len(set(g)), pref_strict=round(a[0], 4), ci_lo=round(a[1], 4), ci_hi=round(a[2], 4), tie=round(float(np.mean(t)), 4), pref_half_auroc=round(float(np.mean(h)), 4), too_small=len(set(g)) < MIN_N))
                    if n == 'bleu': ncase = len(s)
                else: cells.append('—')
            md.append(f'| {FIELDNAME.get(f, f)} | {ncase if ncase else "—"} | ' + ' | '.join(cells) + ' |')
        md.append('')
    with open(os.path.join(out, 'table1_pref_by_error_type.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    return md

def table3():
    R = json.load(open('results/partA/step21b_dose/dose_results.json')); S = ['bleu', 'rougeL', 'chrf', 'bertscore[roberta-large]', 'ratescore', 'finding_f1', 'sentence_f1', 'judge_score', 'image_check']
    NAME = {'bleu': 'BLEU', 'rougeL': 'ROUGE-L', 'chrf': 'chrF', 'bertscore[roberta-large]': 'BERTScore', 'ratescore': 'RaTEScore', 'finding_f1': 'finding_f1 (upper bound)', 'sentence_f1': 'Gemma judge (sentence_f1)', 'judge_score': 'Gemma judge (judge_score)', 'image_check': 'image check (predicted masks, exact box)'}
    md = ['| scorer | breast ρ (n) | thyroid ρ (n) | fetal head ρ (n) |', '|---|---|---|---|']
    for n in S:
        c = []
        for org in ('breast', 'thyroid', 'fetal head'):
            d = R[f'{n}|{org}|spearman']; c.append('—' if d['rho'] is None else f"{d['rho']:+.2f} ({d['n']})")
        md.append(f'| {NAME[n]} | ' + ' | '.join(c) + ' |')
    return md

def main(out):
    t1 = table1(out)
    r = json.load(open('results/partA/step21c_judge_sens/sens_results.json'))['change']; d19 = json.load(open('results/partA/step19a_pairs/cells.json')); b19 = json.load(open('results/partA/step19b_boxsweep/sweep_results.json')); a21 = json.load(open('results/partA/step21a_localisation/sweep_results.json'))
    pct = lambda x: f'{100*x:.0f}%'; f2 = lambda a: f'{a[0]:.2f}'
    bt = 'breast+thyroid (pooled)'
    tax = [
     ('Lexical sensitivity (scores follow how much text changed, not what changed)', 'BLEU, ROUGE-L, chrF, BERTScore, RaTEScore', f"Step 10d, BrEaST, AUROC vs matched one-word synonym: BLEU 0.61, chrF 0.25, BERTScore 0.53; Step 19a strict preference breast: BLEU {d19['bleu|ORGAN:breast|all']['pref_strict'][0]:.2f}, ROUGE-L {d19['rougeL|ORGAN:breast|all']['pref_strict'][0]:.2f}, chrF {d19['chrf|ORGAN:breast|all']['pref_strict'][0]:.2f}, BERTScore {d19['bertscore[roberta-large]|ORGAN:breast|all']['pref_strict'][0]:.2f}", 'BrEaST, BUS-BRA (Step 10d); breast, thyroid, fetal head (19a)', 'results/partA/step10d_test_results/results.md; results/partA/step19a_pairs/cells.json'),
     ('Factual insensitivity (the scorer does not register which fact changed or by how much)', 'BLEU, ROUGE-L, chrF, BERTScore, RaTEScore; Step 18 all text scorers', "Step 21b: BLEU/ROUGE-L dose-response flat (rho -0.01 breast); chrF AUROC 0.00 and BERTScore 0.02 on breast size errors at x2 (error scored as more similar than a synonym); Step 18: equal-size errors that cross vs do not cross a TI-RADS cut-off differ by 0 (BLEU, ROUGE-L, finding_f1) to 0.001 (chrF, BERTScore) [synthetic sizes]", 'size errors; breast, thyroid, fetal head (21b); DDTI synthetic size (18)', 'results/partA/step21b_dose/dose_results.json; results/partA/step18_threshold_crossing/results.md'),
     ('Prompt instability (the judge changes with prompt wording or order)', 'Gemma-2-9B sentence_check (judge_score)', f"Step 21c: judge_score changes by more than 0.1 in {pct(r['swap|ALL']['share_judge_changed_gt_0_1'])} (swap), {pct(r['paraphraseA|ALL']['share_judge_changed_gt_0_1'])} (paraphrase A), {pct(r['paraphraseB|ALL']['share_judge_changed_gt_0_1'])} (paraphrase B) of pairs; AUROC breast {r['swap|breast']['auroc_original']:.2f} -> {r['paraphraseB|breast']['auroc_variant']:.2f}; repeat with the same prompt: 0 of 93 pairs changed. Step 7 (rerun 2): AUROC vs harmless small changed by up to 0.30 between two prompts (BUS-BRA 0.91 -> 0.61)", 'Step 21c: 89 test cases (10 per dataset; per-dataset cells too small); Step 7: 20 cases per dataset (dev)', 'results/partA/step21c_judge_sens/sens_results.json; results/partA/step7_layer2_sentence_check_gemma_rerun2/results.md'),
     ('Benchmark circularity (a scorer scores perfectly because it reads the same template or mask that built the reference)', 'finding_f1; true-mask image check', "finding_f1: AUROC 1.00 and false-alarm rate 0.00 on all 10 datasets (Step 19a) and 1.00 down to a x0.95 size error (Step 21b); true-mask check mask_verified_facts 1.00 by construction (Step 8)", 'all 10 datasets (templated reports)', 'results/partA/step19a_pairs/cells.json; results/partA/step21b_dose/dose_results.json; results/partA/step8_layer3_location_true_masks/results.md'),
     ('Evidence dependence (the image check works only when handed the lesion location)', 'predicted-mask image check (MedSAM)', f"Position AUROC {f2(a21[bt+'|exact']['auroc_position'])} with the true-mask box, {f2(a21[bt+'|whole']['auroc_position'])} whole-image box, {f2(a21[bt+'|random']['auroc_position'])} random box (Step 21a); size AUROC {f2(b19[bt+'|exact']['auroc_size'])} exact box -> {f2(b19[bt+'|shrink25']['auroc_size'])} (box shrunk 25%) -> {f2(b19[bt+'|shrink50']['auroc_size'])} (50%) (Step 19b)", 'breast + thyroid, 228 test scans', 'results/partA/step21a_localisation/results.md; results/partA/step19b_boxsweep/results.md'),
     ('Generalisation failure (does not carry to another dataset, organ or real text)', 'predicted-mask image check; cut-offs; word-overlap scorers on real text; VLM-report fact check', f"Image check on fetal head AUROC 0.46 (HC18) and 0.50 (FetalHead) (Step 16); a val cut-off borrowed from another dataset of the same organ changes the false-alarm rate by -0.72 to +0.62 for single pairs (Step 19a); HiSBreast real text: BLEU, ROUGE-L, chrF AUROC 0.04-0.24 against an LLM paraphrase (n=21) and BERTScore 0.43 overall (n=41) (Step 15); finding_f1 on Qwen reports 0.18-0.30 on BrEaST, BUS-BRA, TN3K, TN5000 (Steps 11, 14)", 'fetal head (16); within-organ pairs (19a); HiSBreast, 41 test exams (15); free-text VLM reports, 14-22 per dataset (11, 14)', 'results/partA/step16_partB/results.md; results/partA/step19a_pairs/transfer.csv; results/partA/step15_hisbreast/results.md; results/partA/step11_qwen_real_reports_rerun2/results.md'),
    ]
    md = ['# Step 22: paper-support tables (saved results only, no model calls)', '', 'All numbers come from saved result files (paths given). Test split, group bootstrap (1,000 resamples, seed 0), † = fewer than 30 groups: too small to compare. `finding_f1` is an upper bound on templated text.', '',
          '## Table 1. Paired preference accuracy by error type, per organ (Step 19a method, test)', ''] + t1 + ['## Table 2. Failure taxonomy', '', '| failure type | scorer(s) | metric and number | dataset scope | result file |', '|---|---|---|---|---|']
    md += [f'| {a} | {b} | {c} | {d} | `{e}` |' for a, b, c, d, e in tax]
    md += ['', '## Table 3. Monotonicity: Spearman rho between error size (|log factor|) and score drop (1 − score), Step 21b', '', 'Positive = bigger errors score lower. Pooled over all error candidates (factors ×0.5 to ×2.0) of an organ, so it mixes errors that make the stated size larger and smaller. n = number of scored error candidates. Judge cells use the capped Step 21b sample; the image check covers the Step 16 scans only.', ''] + table3()
    open(os.path.join(out, 'results.md'), 'w').write('\n'.join(md) + '\n'); print('\n'.join(md[:30]))

if __name__ == '__main__': main(sys.argv[1])
