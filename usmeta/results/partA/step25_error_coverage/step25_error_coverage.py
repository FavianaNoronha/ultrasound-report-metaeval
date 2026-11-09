"""Step 25: error-type coverage. NEW file. Text scorers (SAVED scores) plus omission candidates built here from existing references.
1. Every planted error type per organ (test split) with counts, mapped to: laterality, measurement, category, negation (finding stated present/absent), omission, other.
2. 'Omission' (a stated finding dropped while the others stay) is not among the planted types, so it is BUILT: for every test reference with >= 2 sentences, drop ONE sentence other than the first (the first sentence holds the main lesion / fetal-head statement),
   one candidate per dropped sentence. Scored with the project text scorers (BLEU, ROUGE-L, chrF, BERTScore roberta-large, RaTEScore, finding_f1); the saved judge does not cover these candidates, so no judge number for omission.
3. Paired preference and AUROC vs the harmless rewordings (small / matched / large), same method as Step 19a: per case, error x harmless pairs; strict = error scores lower; AUROC = strict + 0.5 tie; group bootstrap 1,000 resamples, seed 0; under 30 groups: too small to compare.
    python3 -m usmeta.step25_error_coverage build | report"""
import json, sys, os, re, collections
import numpy as np
from . import splits, step19_pairs as p, layer0, layer1
from .step10d_analysis import gboot

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results', 'partA', 'step25_error_coverage'); MIN_N = 30
CLS = {'side': 'laterality', 'size_pct': 'measurement', 'size_mm': 'measurement', 'hc_mm': 'measurement', 'lesion': 'negation', 'halo': 'negation', 'calc': 'negation', 'foci': 'negation', 'count': 'other', 'pos': 'other'}
CATFIELDS = ('birads', 'tirads', 'path', 'hist', 'margin', 'echo', 'shape', 'comp', 'post', 'orient', 'plane')
def cls_of(r): return 'category' if r['field'] in CATFIELDS else CLS[r['field']]
WHY = {'laterality': 'wrong side (left / right breast)', 'measurement': 'wrong size (mm, % of image width) or head circumference', 'category': 'wrong BI-RADS / TI-RADS / pathology / histology / margin / echo / shape / composition / posterior features / orientation / fetal plane',
       'negation': 'a finding stated present when absent or absent when present ("No focal lesion is seen", calcifications, halo, foci)', 'omission': 'a stated finding sentence dropped, the others stay (BUILT here)', 'other': 'lesion count and position in the image (not in the six requested groups)'}
SCORERS = ['bleu', 'rougeL', 'chrf', 'bertscore[roberta-large]', 'ratescore', 'finding_f1', 'sentence_f1', 'judge_score']; NM = {'bleu': 'BLEU', 'rougeL': 'ROUGE-L', 'chrf': 'chrF', 'bertscore[roberta-large]': 'BERTScore', 'ratescore': 'RaTEScore', 'finding_f1': 'finding_f1 (upper bound)', 'sentence_f1': 'judge sentence_f1', 'judge_score': 'judge_score'}
MODEL_ORG = {'breast': 'breast', 'thyroid': 'thyroid', 'fetal head': 'fetal'}; ORGANS = ('breast', 'thyroid', 'fetal head'); CLASSES = ['laterality', 'measurement', 'category', 'negation', 'omission', 'other']

def sentences(ref): return [x for x in re.split(r'(?<=[.])\s+', ref.strip()) if x]

def build():
    os.makedirs(OUT, exist_ok=True); rows = [json.loads(l) for l in open('bench_test_v2d.jsonl')]; ids = {r['case_id'] for r in splits.load('test', script='usmeta.step25_error_coverage')}; assert all(r['case_id'] in ids for r in rows)
    refs = {}
    for r in rows: refs[r['case_id']] = r
    om = []
    for cid, r in refs.items():
        S = sentences(r['reference'])
        if len(S) < 2: continue
        for i in range(1, len(S)):
            om.append(dict(case_id=cid, dataset=r['dataset'], organ=MODEL_ORG[p.ORGAN[r['dataset']]], organ_name=p.ORGAN[r['dataset']], group_id=r['group_id'], reference=r['reference'], candidate=' '.join(S[:i] + S[i + 1:]), kind='error', field='omission', dropped=S[i], dropped_index=i, n_sentences=len(S)))
    open(os.path.join(OUT, 'omission_bench.jsonl'), 'w').write(''.join(json.dumps(o) + '\n' for o in om))
    layer0.score(os.path.join(OUT, 'omission_bench.jsonl'), os.path.join(OUT, 'scores_layer0.json')); layer1.score(os.path.join(OUT, 'omission_bench.jsonl'), os.path.join(OUT, 'scores_layer1.json')); print(len(om), 'omission candidates')

def pctl(a): return a

def main_report():
    rows = [json.loads(l) for l in open('bench_test_v2d.jsonl')]
    sc = {**p.scores_of('scores_test_layer0.json'), 'finding_f1': p.scores_of('scores_test_layer1.json')['finding_f1']}; sc.update(p.judge_lookup(['judge_test_v2.jsonl', 'judge_big_v2.jsonl']))
    for f, names in (('scores_layer0.json', None), ('scores_layer1.json', ('finding_f1',))):
        S = p.scores_of(os.path.join(OUT, f))
        for n, d in S.items():
            if names is None or n in names: sc[n].update(d)
    om = [json.loads(l) for l in open(os.path.join(OUT, 'omission_bench.jsonl'))]
    C = {}
    for r in rows:
        if r['kind'] == 'error' or (r['kind'] == 'harmless' and r['harmless_type'] in p.HT):
            c = C.setdefault(r['case_id'], dict(ds=r['dataset'], organ=p.ORGAN[r['dataset']], group=f"{r['dataset']}:{r['group_id']}", E={k: [] for k in CLASSES}, H=[]))
            if r['kind'] == 'error': c['E'][cls_of(r)].append(r)
            else: c['H'].append(r)
    for o in om:
        if o['case_id'] in C: C[o['case_id']]['E']['omission'].append(o)
    def stat(organ, cl, name):
        s, t, h, g = [], [], [], []
        for c in C.values():
            if c['organ'] != organ: continue
            e = [p.score_of(sc, name, r) for r in c['E'][cl]]; hh = [p.score_of(sc, name, r) for r in c['H']]; e = [x for x in e if x is not None]; hh = [x for x in hh if x is not None]
            if not e or not hh: continue
            E, H = np.array(e)[:, None], np.array(hh)[None, :]; lt, eq = float((E < H).mean()), float((E == H).mean()); s.append(lt); t.append(eq); h.append(lt + .5 * eq); g.append(c['group'])
        d = dict(n_cases=len(s), n_groups=len(set(g)))
        if len(set(g)) >= MIN_N: d.update(strict=gboot(s, g), tie=float(np.mean(t)), auroc=gboot(h, g))
        elif s: d.update(small=True, strict_pt=float(np.mean(s)), auroc_pt=float(np.mean(h)), tie=float(np.mean(t)))
        return d
    cell = lambda d, k: '—' if d['n_cases'] == 0 else (f"too small to compare ({d['n_groups']} groups)" if d.get('small') else f'{d[k][0]:.2f} ({d[k][1]:.2f}–{d[k][2]:.2f})')
    M = ['# Step 25 — Error-type coverage (test split)', '',
         'Questions: (1) which planted error types exist and how do they map onto laterality / measurement / category / negation / omission / other; (2) omission is not a planted type, so it was built and scored; (3) how do the scorers do on each group, same method as Step 19a (error x harmless small / matched / large pairs per case, group bootstrap 1,000, seed 0; under 30 groups: too small to compare). Code: `usmeta/step25_error_coverage.py`; omission candidates: `omission_bench.jsonl`; their scores: `scores_layer0.json`, `scores_layer1.json`.', '',
         '## 1. Planted error types per organ and their mapping (test candidates; number of reference cases in brackets)', '', '| organ | planted type (category / field) | group | candidates | cases |', '|---|---|---|---|---|']
    cnt = collections.defaultdict(lambda: [0, set()])
    for r in rows:
        if r['kind'] == 'error': k = (p.ORGAN[r['dataset']], r['category'], r['field'], cls_of(r)); cnt[k][0] += 1; cnt[k][1].add(r['case_id'])
    for (o, cat, fld, cl), (n, cs) in sorted(cnt.items()): M.append(f'| {o} | {cat} / {fld} | {cl} | {n} | {len(cs)} |')
    M += ['', '| group | what it contains |', '|---|---|'] + [f'| {k} | {WHY[k]} |' for k in CLASSES]
    M += ['', '**Coverage gaps:** `omission` is not a planted type (the "missed finding" candidates either replace the whole report with "No focal lesion is seen." or flip one finding to "no X"; both are negation, not omission); the planted set has no candidate that simply drops a stated finding. Position and count errors sit in `other`.', '']
    om = [json.loads(l) for l in open(os.path.join(OUT, 'omission_bench.jsonl'))]
    dc = collections.Counter((o['organ_name'], 'first-sentence kept' if True else '') for o in om)
    M += ['## 2. Built omission candidates', '', f'{len(om)} candidates from {len({o["case_id"] for o in om})} of 1,399 test references (references with at least two sentences; one sentence other than the first dropped per candidate): ' + ', '.join(f'{k}: {sum(1 for o in om if o["organ_name"] == k)}' for k in ORGANS) + '. Dropped sentences, by first words: ' + ', '.join(f'"{w}" {n}' for w, n in collections.Counter(' '.join(o['dropped'].split()[:2]) for o in om).most_common(8)) + '. The saved judge has no scores for them.', '']
    res = {}
    for key, title in (('strict', 'Paired preference accuracy (share of error x harmless pairs where the error scores LOWER; ties not preferred)'), ('auroc', 'AUROC (= strict + 0.5 x tie share)')):
        M += [f'## 3. {title}', '']
        for o in ORGANS:
            M += [f'### {o}', '', '| scorer | ' + ' | '.join(CLASSES) + ' |', '|---|' + '---|' * len(CLASSES)]
            for n in SCORERS:
                cs = []
                for cl in CLASSES:
                    d = stat(o, cl, n); res[f'{o}|{n}|{cl}'] = d; cs.append(cell(d, key))
                M.append(f'| {NM[n]} | ' + ' | '.join(cs) + ' |')
            M.append('')
    M += ['Cases / groups per cell (word scorers):', '', '| organ | ' + ' | '.join(CLASSES) + ' |', '|---|' + '---|' * len(CLASSES)]
    for o in ORGANS: M.append(f'| {o} | ' + ' | '.join(f"{res[f'{o}|bleu|{cl}']['n_cases']} / {res[f'{o}|bleu|{cl}']['n_groups']}" for cl in CLASSES) + ' |')
    M += ['', 'Judge columns use only candidates the saved judge scored (Steps 10d + 12 samples), so their groups are fewer; the omission column has no judge. `finding_f1` is the upper bound (it reads the same template vocabulary).', '']
    json.dump(res, open(os.path.join(OUT, 'coverage.json'), 'w'), indent=1, default=float); open(os.path.join(OUT, 'tables.md'), 'w').write('\n'.join(M)); print('\n'.join(M[-60:]))

if __name__ == '__main__': {'build': build, 'report': main_report}[sys.argv[1]]()
