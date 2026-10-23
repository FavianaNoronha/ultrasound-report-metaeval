"""Step 9: one combined table of every scorer x every dataset, grouped by layer. Reads the saved results.json files of Steps 5 (rerun3), 6, 7 (rerun2), 8."""
import json, sys, os
R = 'results/partA/'
L0 = json.load(open(R + 'step5_harmless_split_layer0_rerun3/results_partA_layer0b.json'))
L1 = json.load(open(R + 'step6_layer1_finding_f1/results_partA_layer1.json'))
L2 = json.load(open(R + 'step7_layer2_sentence_check_gemma_rerun2/results_partA_layer2.json'))
L3 = json.load(open(R + 'step8_layer3_location_true_masks/results_partA_layer3.json'))
IDEA = {  # scorer -> (layer, idea borrowed from)
 'bleu': ('0 word overlap', 'standard n-gram metric (Papineni et al. 2002)'), 'rougeL': ('0 word overlap', 'standard (Lin 2004)'), 'chrf': ('0 word overlap', 'standard character n-gram (Popovic 2015)'),
 'bertscore[roberta-large]': ('0 embedding similarity', 'BERTScore (Zhang et al. 2020)'), 'ratescore': ('0 radiology entities', 'RaTEScore (built for chest/CT; run unchanged)'),
 'finding_f1': ('1 structured facts', 'ours: findings schema from the BI-RADS / TI-RADS lexicons; precision/recall over attributes (graded credit for numbers)'),
 'sentence_f1': ('2 AI judge', 'RadFact protocol (sentence support both ways), our own Gemma-2-9B prompt, not the original RadFact'),
 'judge_score': ('2 AI judge', 'ours: severity-weighted error list from the judge (penalties 0.6 / 0.3 / 0.1)'),
 'location_check': ('3 image/location', 'box IoU as in grounded chest X-ray reporting (MAIRA-2 / RadFact line; to confirm); true masks'),
 'grounded_check': ('3 image/location', 'ours: finding_f1 x box IoU'), 'mask_verified_facts': ('3 image/location', 'ours: text claims checked against the true mask'),
 'semacc': ('3 image/location', 'UltraG-Bench SemAcc (presence, category, location, size yes/no)'), 'box_support_gtbox': ('3 image/location', 'spatial support rule (>= 50% of the box in the true region)'),
 'oracle_label_check': ('3 oracle', 'old evidence_check idea: text vs dataset labels (upper bound)'),
}
ORDER = ['BrEaST', 'BUS-BRA', 'BUSI', 'UDIAT', 'BUS-UCLM', 'TN3K', 'TN5000', 'DDTI', 'HC18', 'FetalHead']
ORG = {'BrEaST': 'breast', 'BUS-BRA': 'breast', 'BUSI': 'breast', 'UDIAT': 'breast', 'BUS-UCLM': 'breast', 'TN3K': 'thyroid', 'TN5000': 'thyroid', 'DDTI': 'thyroid', 'HC18': 'fetal', 'FetalHead': 'fetal'}
f = lambda x: '—' if x is None else '%.2f' % (x[0] if isinstance(x, (list, tuple)) else x)
SRC = [(L0, ['bleu', 'rougeL', 'chrf', 'bertscore[roberta-large]', 'ratescore'], 'all cases'), (L1, ['finding_f1'], 'all cases'), (L2, ['sentence_f1', 'judge_score'], '20 cases')]

def main(out):
    md = ['# Every scorer x every dataset, grouped by layer (Part A, bench_v2d)', '',
          'AUROC = chance that a planted error scores LOWER than a harmless rewording of the same case (1.0 perfect, 0.5 chance, below 0.5 = the scorer prefers the error). Three harmless comparisons: **small** = synonyms / sentence reorder / unit rewrite (5-36% of tokens changed), **matched** = ONE-word synonym (about the same edit size as an error), **large** = style swap. `identical` must be 1.0. Layers 0-2 use bench_v2d (150 cases per dataset, 256 BrEaST; Layer 2 only 20 cases per dataset: wide intervals). Layer 3 uses its own benchmark with boxes (table at the end).', '',
          '**Keep visible:** reports are templated from labels (synthetic but fact-correct); severity is provisional pending a clinician; template sources are marked "to confirm" and must be verified before any paper claim; results are per dataset only, never pooled; Layer 1 and the oracle row are upper bounds because their extractor is written for the same templates; Layer 3 Test 1 uses TRUE masks (circular for position/size). We found no ultrasound work that tests the scorers with planted errors, severity and harmless rewordings (our search was not exhaustive).', '']
    for org in ('breast', 'thyroid', 'fetal'):
        md += [f'## {org}', '']
        for ds in [d for d in ORDER if ORG[d] == org]:
            n = L0[ds]['bleu']['n_cases']
            md += [f'### {ds} ({n} cases)', '', '| layer | scorer | AUROC vs small | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy "No abnormality." | idea borrowed from |', '|---|---|---|---|---|---|---|---|---|---|---|']
            for src, names, note in SRC:
                for s in names:
                    v = src[ds][s]; ly, idea = IDEA[s]; tag = ' (n=20)' if note == '20 cases' else ''
                    md.append(f"| {ly} | {s}{tag} | {f(v['auroc_small'])} | {f(v['auroc_matched'])} | {f(v['auroc_large'])} | {f(v['critical_small'])} | {f(v['harmless_small_mean'])} | {f(v['harmless_large_mean'])} | {'—' if v['identical_mean'] is None else format(v['identical_mean'], '.4f')} | {f(v['lazy_mean'])} | {idea} |")
            md.append('')
    md += ['## AUROC per error category (vs harmless_small / vs matched one-word synonym)', '', 'Only categories a dataset supports appear. Layer 2 cells use ~40 errors per dataset.', '']
    for ds in ORDER:
        cats = sorted({c for src, names, _ in SRC for s in names for c in src[ds][s]['cat_small']})
        md += [f'**{ds}**', '', '| scorer | ' + ' | '.join(cats) + ' |', '|---|' + '---|' * len(cats)]
        for src, names, _ in SRC:
            for s in names:
                v = src[ds][s]; md.append(f'| {s} | ' + ' | '.join(f"{f(v['cat_small'].get(c))} / {f(v['cat_matched'].get(c))}" for c in cats) + ' |')
        md.append('')
    md += ['## Layer 3: image / location check against the TRUE masks (own benchmark `bench_loc`, text + box; 100 cases per dataset)', '',
           'Groups: box-only = text unchanged, box moved (text scorers cannot see it: by construction); text pos = wrong position sentence, correct box; text pos + box = wrong sentence and box moved to match; size = wrong size in text, correct box. Harmless = jittered box, jittered box + reworded text.', '',
           '| dataset | scorer | AUROC box-only | text pos | text pos + box | size | harmless mean | identical mean | idea borrowed from |', '|---|---|---|---|---|---|---|---|---|']
    for ds in ORDER:
        for s in ('bleu', 'bertscore[roberta-large]', 'oracle_label_check', 'mask_verified_facts', 'semacc', 'location_check', 'grounded_check', 'box_support_gtbox'):
            v = L3[ds][s]; g = v['auroc_by_group']; idea = IDEA.get(s, ('0', IDEA.get('bleu')[1]))[1]
            md.append(f"| {ds} | {s} | {f(g.get('box_only'))} | {f(g.get('text_pos'))} | {f(g.get('text_pos_box'))} | {f(g.get('size'))} | {f(v['harmless_mean'])} | {v['identical_mean']:.4f} | {idea} |")
    md += ['', 'Not run yet: GREEN (7B model too large for 16 GB), Claude judge (no credit), original RadFact, SAM/MedSAM predicted masks (Part B), real VLM-written reports on bench_v2d, any clinician-confirmed severity.']
    open(out, 'w').write('\n'.join(md) + '\n')

if __name__ == '__main__': main(sys.argv[1])
