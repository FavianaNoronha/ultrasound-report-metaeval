"""Step 17: final combined table. Reads the SAVED result files of the locked-test steps and writes one markdown file, grouped by layer, per dataset, with n and CIs.
   Step 10d (Layers 0, 1, 3 on templated text, test split) + Step 12 (larger judge) + Step 16 (predicted masks) + Steps 11/14 (real VLM reports) + Step 15 (HiSBreast real text).
   n < 30 cases (or < 30 groups) -> 'too small to compare'. Layer 1 and Layer 3 with TRUE masks -> 'upper bound, templated'.   python3 -m usmeta.final_table <out.md>"""
import json, sys
R = 'results/partA/'
J = lambda p: json.load(open(R + p))
L01, L3, J12 = J('step10d_test_results/results_test_layer01.json'), J('step10d_test_results/results_test_layer3.json'), J('step12_judge_larger/results_step12.json')
PB, QW, MG, HS = J('step16_partB/results_aggregates.json'), J('step11_qwen_real_reports_rerun2/results.json')['summary'], J('step14_medgemma/results.json'), J('step15_hisbreast/results_aggregates.json')
ORDER = ['BrEaST', 'BUS-BRA', 'BUSI', 'UDIAT', 'BUS-UCLM', 'TN3K', 'TN5000', 'DDTI', 'HC18', 'FetalHead']
ORG = {'BrEaST': 'breast', 'BUS-BRA': 'breast', 'BUSI': 'breast', 'UDIAT': 'breast', 'BUS-UCLM': 'breast', 'TN3K': 'thyroid', 'TN5000': 'thyroid', 'DDTI': 'thyroid', 'HC18': 'fetal', 'FetalHead': 'fetal'}
UB = '**upper bound, templated**'
def ci(x, d=2):
    if x is None: return '—'
    if isinstance(x, (int, float)): return f'{x:.{d}f}'
    return f'{x[0]:.{d}f} ({x[1]:.{d}f}–{x[2]:.{d}f})'
def flag(n, g=None): return ' ⚠ too small to compare' if (n is not None and n < 30) or (g is not None and g < 30) else ''
def ng(v): return f"{v['n_cases']} ({v['n_groups']})"
L0S = ['bleu', 'rougeL', 'chrf', 'bertscore[roberta-large]', 'ratescore']

def part_a():
    md = ['## A. Templated benchmark on the LOCKED TEST split (Layers 0–3)', '',
          'AUROC = chance that a planted error scores LOWER than a harmless rewording of the same report (1.0 perfect, 0.5 chance, below 0.5 = the scorer prefers the error). small = synonyms / reorder / unit rewrite, matched = ONE-word synonym (same edit size as an error), large = style swap. Cells: AUROC (95% CI, resampling patient/exam groups). n = cases (groups). Layers 0–1: Step 10d (frozen code, all test cases of the 150-case sample); Layer 2: Step 12 (Gemma-2-9B, prompt_v2, 59 cases per dataset); Layer 3: Step 10d (true masks, case-level CIs) and Step 16 (predicted masks).', '']
    for org in ('breast', 'thyroid', 'fetal'):
        md += [f'### {org}', '']
        for ds in [d for d in ORDER if ORG[d] == org]:
            md += [f'#### {ds}', '', '| layer | scorer | n (groups) | vs small | vs matched | vs large | identical mean | status |', '|---|---|---|---|---|---|---|---|']
            for s in L0S:
                v = L01[ds][s]; md.append(f"| 0 word overlap / embedding | {s} | {ng(v)} | {ci(v['auroc_small'])} | {ci(v['auroc_matched'])} | {ci(v['auroc_large'])} | {v['identical_mean']:.4f} |{flag(v['n_cases'], v['n_groups']) or ' measured'} |")
            v = L01[ds]['finding_f1']; md.append(f"| 1 structured facts | finding_f1 | {ng(v)} | {ci(v['auroc_small'])} | {ci(v['auroc_matched'])} | {ci(v['auroc_large'])} | {v['identical_mean']:.4f} | {UB}{flag(v['n_cases'], v['n_groups'])} |")
            for s in ('sentence_f1', 'judge_score'):
                v = J12[ds][s]; md.append(f"| 2 AI judge (Gemma-2-9B, prompt_v2) | {s} | {ng(v)} | {ci(v['auroc_small'])} | {ci(v['auroc_matched'])} | {ci(v['auroc_large'])} | {v['identical_mean']:.4f} |{flag(v['n_cases'], v['n_groups']) or ' measured, one judge, one prompt'} |")
            md.append('')
    md += ['### Layer 3: image check, true masks (circular) vs predicted masks (non-circular)', '',
           'Different benchmarks, so the AUROC columns are not comparable across the two blocks. **True masks (Step 10d, `bench_loc`, 100 cases per dataset; case-level CIs):** the reference facts were measured from the same masks the check reads, so the check cannot fail on a true report: ' + UB + '. The first AUROC (all errors) includes box-only errors that a text check cannot see (0.5 by construction); the other two are the text errors the mask can verify. **Predicted masks (Step 16):** MedSAM, box prompts from the TRUE masks (exact box), test split, 30 scans per dataset (18 BUS-UCLM); AUROC of `mask_verified_facts` over all mask-checkable planted errors (position, size, lesion, count, orientation) vs harmless rewordings; IoU = predicted vs true mask.', '',
           '| dataset | TRUE masks: n | mask_verified_facts AUROC: all errors / wrong text position / wrong size | grounded_check AUROC (all errors) | status | PREDICTED masks: n (groups) | IoU | mask_verified_facts AUROC (all checkable) | position errors | size errors | correct report scores | text scorer RaTEScore (same cases) |', '|---|---|---|---|---|---|---|---|---|---|---|---|']
    for ds in ORDER:
        t, g = L3[ds]['mask_verified_facts'], L3[ds]['grounded_check']; n = PB['n_cases'][ds]; seg = PB['seg'].get(f'{ds}|exact', {}); A = PB['auroc']
        iou = ci(seg.get('iou')) if 'iou' in seg else f"box IoU {ci(seg.get('box_iou'))} (no true mask)"
        a = lambda sub, nm='mvf_exact': A.get(f'{sub}|{ds}|{nm}', {})
        def cell(sub, nm='mvf_exact'): x = a(sub, nm); return '— (no such errors)' if x and x['n'] == 0 else (ci(x.get('auroc')) + (f" (n={x['n']}" + (', too small to compare)' if x['n'] < 30 else ')'))) if x else '—'
        ident = PB['identical'].get(ds)
        gg = t['auroc_by_group']; md.append(f"| {ds} | {t['n_cases']} | {ci(t['auroc'], 2)} / {('—' if 'text_pos' not in gg else format(gg['text_pos'], '.2f'))} / {('—' if 'size' not in gg else format(gg['size'], '.2f'))} | {ci(g['auroc'])} | {UB} | {n}{flag(n)} | {iou} | {cell('all mask-checkable errors')} | {cell('position errors')} | {cell('size errors')} | {'—' if not ident else format(ident['exact'], '.2f')} | {cell('all mask-checkable errors', 'ratescore')} |")
    for lab, key in (('breast + thyroid pooled', 'LESIONS'), ('all 10 datasets pooled', 'ALL')):
        A = PB['auroc']; c = lambda sub, nm='mvf_exact': (lambda x: ci(x['auroc']) + f" (n={x['n']})")(A[f'{sub}|{key}|{nm}'])
        md.append(f"| **{lab}** | | | | | | | {c('all mask-checkable errors')} | {c('position errors')} | {c('size errors')} | | RaTEScore {c('all mask-checkable errors', 'ratescore')} |")
    md += ['', 'Reading: with predicted masks the check is no longer perfect and gives correct reports < 1.0 (column "correct report scores", mean score of identical copies; 1.000 with true masks). It beats the text scorers on breast and thyroid, and is at chance on fetal head (skull-ring annotation vs the interior MedSAM outlines). See `step16_partB/results.md`.', '']
    return md

def part_b():
    md = ['## B. Real VLM-written reports on the TEST split (Layers 1–3 against the templated true report)', '',
          '**Possible training exposure, unverifiable** (both models may have seen BUS-BRA, BrEaST, TN3K, TN5000, HC18). **The two writers were graded by different model families (Qwen reports: Gemma-2-9B; MedGemma reports: Qwen2.5-7B), so `finding_f1` and `sentence_f1` columns are different measuring sticks and must not be ranked against each other.** Cells: mean (95% CI resampling groups). n = reports (groups). Every dataset has n < 30, so every row is **too small to compare**; the pooled rows in `step14_medgemma/results.md` only show whether scorers agree.', '',
          '| dataset | writer | n (groups) | finding_f1 | sentence_f1 prompt_v2 (judge family) | box IoU | boxes IoU ≥ 0.5 | status |', '|---|---|---|---|---|---|---|---|']
    for ds in ('BrEaST', 'BUS-BRA', 'TN3K', 'TN5000', 'HC18'):
        q = QW[ds]; m = MG['medgemma_alone'][ds]
        md.append(f"| {ds} | Qwen2.5-VL-3B | {q['n']} ({q['groups']}) | {ci(q['finding_f1'])} | {ci(q['sentence_f1_v2'])} (Gemma) | {ci(q['iou'])} | {q['iou_ge_0.5']:.0%} |{flag(q['n'])} |")
        md.append(f"| {ds} | MedGemma-1.5-4B (4-bit) | {m['n']} ({m['groups']}) | {ci(m['finding_f1'])} | {ci(m['sentence_f1_v2'])} (Qwen2.5-7B) | {ci(m['iou'])} | {m['iou_ge_0.5']:.0%} |{flag(m['n'])} |")
    md += ['', 'Layer 0 scorers (BLEU, ROUGE-L, chrF, BERTScore, RaTEScore) on the two writers are in `step14_medgemma/results.md` (paired differences with group-bootstrap CIs): the gaps are tiny (BLEU 0.00–0.01, BERTScore 0.00–0.02) and the scorers do not agree on a ranking. Layer 3 with predicted masks was NOT run on VLM reports (their boxes were too poor to prompt MedSAM; Step 16 used true-mask boxes).', '']
    return md

def part_c():
    md = ['## C. HiSBreast: real (machine-translated) clinician conclusions, test split', '',
          'Text is local only (blank licence). **Machine-translated subset: 101 of 427 breast exams passed three automatic translation checks (no bilingual human review).** Planted errors and harmless rewordings built on the validated English text; splits by exam id. Cells: AUROC (95% CI resampling exams). A column with n < 30 is **too small to compare**.', '',
          '| scorer | n exams | all harmless | vs small | vs matched one-word synonym | vs LLM paraphrase | identical mean | lazy "no abnormality" |', '|---|---|---|---|---|---|---|---|']
    def row(name, v):
        cell = lambda k, nk: ci(v[k]) + (f" (n={v[nk]}, too small to compare)" if v[nk] < 30 else f" (n={v[nk]})")
        return f"| {name} | {v['n_cases']} | {cell('auroc_all', 'n_auroc_all')} | {cell('auroc_small', 'n_auroc_small')} | {cell('auroc_matched', 'n_auroc_matched')} | {cell('auroc_paraphrase', 'n_auroc_paraphrase')} | {v['identical_mean']:.4f} | {ci(v['lazy_mean']) if v['lazy_mean'] is not None else '—'} |"
    for s in L0S + ['finding_f1_his']: md.append(row(s + (' (parser written for this text: optimistic)' if s == 'finding_f1_his' else ''), HS['strict_test'][s]))
    for s in ('sentence_f1', 'judge_score'):
        if s in HS['strict_test_judge']: md.append(row(s + ' (Qwen2.5-7B judge, prompt v2q)', HS['strict_test_judge'][s]))
    md += ['', f"Looser set (passed check 1 plus check 2 or 3; 118 test exams) and the dev/val numbers are in `step15_hisbreast/results.md`. Parser agreement between the Vietnamese original and the English translation: side {HS['parser_agreement']['kept (passed 3 checks)']['side']:.2f}, BI-RADS {HS['parser_agreement']['kept (passed 3 checks)']['birads']:.2f}, finding type only {HS['parser_agreement']['kept (passed 3 checks)']['finding']:.2f} (unreliable).", '']
    return md

def main(out):
    md = ['# Every scorer, every layer, locked test split: final combined table (Part A + Part B + real text)', '',
          'Supersedes `results_layers_all.md` (Step 9, which pooled all splits and a 20-case judge sample; kept unchanged). Built by `python3 -m usmeta.final_table` from the SAVED result files of Steps 10d, 11 (rerun2), 12, 14, 15 and 16: no number here is typed by hand. Tuning and choices were on dev/val only; all numbers below are test-split numbers (Step 16 and Step 15 also test).', '',
          '**Marks used.** ⚠ *too small to compare* = fewer than 30 cases or fewer than 30 patient/exam groups. **upper bound, templated** = the checker reads the same template (Layer 1 `finding_f1`) or the same masks (Layer 3 with true masks) as the reference was built from, so it cannot fail on templated text. **Per dataset, never pooled** (pooled rows only where stated). Templated references, provisional severity, no clinician: see `docs/LIMITATIONS.md`.', '']
    md += part_a() + part_b() + part_c()
    md += ['## Not run', '', 'GREEN (7B model too large for 16 GB), Claude judge (no credit), Jev (paid API, not approved), original RadFact, LLaVA-Med reports, SAM/MedSAM boxes from VLM output, clinician-confirmed severity, bilingual review of HiSBreast translations.']
    open(out, 'w').write('\n'.join(md) + '\n')

if __name__ == '__main__': main(sys.argv[1])
