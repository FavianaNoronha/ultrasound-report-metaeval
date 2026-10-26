"""HiSBreast: score bench_his with the frozen Layer 0 scorers, a HiSBreast field-F1 (finding_f1_his), and the Qwen2.5-7B sentence_check judge (v2q); analyse on the locked exam splits.
All inputs/outputs stay in usmeta/local_data/hisbreast/ (git-ignored); only aggregate numbers are copied into results.  python3 -m usmeta.hisbreast_run layer0 | judge | analyse OUT_DIR"""
import json, os, sys, collections, time
import numpy as np
from scipy.stats import spearmanr
from . import hisbreast, hisbreast_validate as V, hisbreast_parse as P, hisbreast_bench as B, graders, judge2, judge2_test, layer0
from .step10d_analysis import gboot
D = hisbreast.OUT; LAZY = 'No abnormality recorded.'
def rows(): return [json.loads(l) for l in open(os.path.join(D, 'bench_his.jsonl'))]

def attrs(t):
    f = P.parse(t, 'en'); a = {}
    if f['side'] != 'unspecified': a['side'] = f['side']
    if f['birads']: a['birads'] = f['birads']
    a['finding'] = f['finding']
    if f['axillary']: a['axillary'] = True
    if f['recommendation']: a['recommendation'] = f['recommendation']
    if f['suspicious']: a['suspicious'] = True
    return a
def field_f1(ref, hyp):
    """same definition as finding_f1 (precision / recall over stated attributes, exact match) on the HiSBreast fields"""
    R, C = attrs(ref), attrs(hyp); tp_r = sum(R[k] == C.get(k) for k in R); tp_p = sum(R.get(k) == v for k, v in C.items()); rec = tp_r / len(R) if R else 1.0; pre = tp_p / len(C) if C else (1.0 if not R else 0.0)
    return (2 * pre * rec / (pre + rec) if pre + rec else 0.0)

def layer0_scores():
    R = rows(); P_ = sorted({(r['reference'], r['candidate']) for r in R} | {(r['reference'], LAZY) for r in R}); refs = [p[0] for p in P_]; hyps = [p[1] for p in P_]; res = {}
    for spec in ('bleu', 'rougeL', 'chrf', 'bertscore:roberta-large', 'ratescore'):
        g = graders.make(spec); s = g.batch(refs, hyps) if hasattr(g, 'batch') else [g.score(a, b) for a, b in zip(refs, hyps)]; res[{'bertscore:roberta-large': 'bertscore[roberta-large]'}.get(spec, spec)] = [float(x) for x in s]
    res['finding_f1_his'] = [field_f1(a, b) for a, b in P_]
    json.dump(dict(pairs=[list(p) for p in P_], scores=res), open(os.path.join(D, 'scores_his_layer0.json'), 'w'), ensure_ascii=False); print('scored', len(P_), 'pairs')

def judge():
    cli = graders.LocalLLM(V.JUDGE, cache_dir=os.path.join(D, '.llm_cache_q'), max_tokens=500)
    class SCQ(judge2_test.SC):
        def run(self, ref, hyp):
            R, H = judge2.sentences(ref), judge2.sentences(hyp)
            p = self.prompt.format(ref=judge2.numbered(R), hyp=judge2.numbered(H)) + f"\nThe REFERENCE has exactly {len(R)} sentences and the CANDIDATE has exactly {len(H)} sentences: candidate_supported must contain exactly {len(H)} values and reference_covered exactly {len(R)} values.\n"
            t = self.cli.ask(p, valid=lambda x: judge2.parse(x, len(R), len(H)) is not None); js = judge2.parse(t, len(R), len(H))
            if js is None: self.missing += 1; return None
            return judge2.scores_from(js)
    sel = [r for r in rows() if r['split'] == 'test' and r['strict']]; out = os.path.join(D, 'judge_his_v2q.jsonl'); done = {(json.loads(l)['a'], json.loads(l)['b']) for l in open(out)} if os.path.exists(out) else set()
    sc = SCQ(judge2.PROMPT_V2, cli=cli); todo = list(dict.fromkeys((r['reference'], r['candidate']) for r in sel if (r['reference'], r['candidate']) not in done)); t0 = time.time(); print(len(todo), 'pairs', flush=True)
    for i, (a, b) in enumerate(todo):
        res = sc.run(a, b); open(out, 'a').write(json.dumps(dict(a=a, b=b, result=res), ensure_ascii=False) + '\n')
        if i % 25 == 0: print(i, round(time.time() - t0), 's, missing', sc.missing, flush=True)

if __name__ == '__main__' and sys.argv[1] in ('layer0', 'judge'): {'layer0': layer0_scores, 'judge': judge}[sys.argv[1]]()

SC = ['bleu', 'rougeL', 'chrf', 'bertscore[roberta-large]', 'ratescore', 'finding_f1_his']
def auroc_case(e, h):
    e, h = np.asarray(e)[:, None], np.asarray(h)[None, :]; return float(((e < h) + 0.5 * (e == h)).mean())

def analyse_set(R, S, names, label):
    idx = {tuple(p): i for i, p in enumerate(S['pairs'])}; out = {}
    for name in names:
        arr = S['scores'][name]; sc = lambda r: arr[idx[(r['reference'], r['candidate'])]]
        cases = collections.defaultdict(list)
        for r in R: cases[r['case_id']].append(r)
        A = {k: ([], []) for k in ('all', 'small', 'matched', 'paraphrase')}; cat = collections.defaultdict(lambda: ([], [])); H = {k: [] for k in A}; I = []; L = []; sev = []
        for cid, rs in cases.items():
            e = [r for r in rs if r['kind'] == 'error']; I += [sc(r) for r in rs if r['kind'] == 'identical']
            if (rs[0]['reference'], LAZY) in idx: L.append(arr[idx[(rs[0]['reference'], LAZY)]])
            for k in A:
                h = [sc(r) for r in rs if r['kind'] == 'harmless' and (k == 'all' or r['harmless_type'] == k)]; H[k] += h
                if e and h: A[k][0].append(auroc_case([sc(r) for r in e], h)); A[k][1].append(cid)
            for c in {r['category'] for r in e}:
                h = [sc(r) for r in rs if r['kind'] == 'harmless']
                if h: cat[c][0].append(auroc_case([sc(r) for r in e if r['category'] == c], h)); cat[c][1].append(cid)
            sev += [(r['severity'], sc(r)) for r in e]
        sv = [a for a, _ in sev]; ss = [b for _, b in sev]
        out[name] = dict(n_cases=len(cases), **{f'auroc_{k}': gboot(*A[k]) if A[k][0] else None for k in A}, **{f'n_auroc_{k}': len(A[k][0]) for k in A}, **{f'harmless_{k}_mean': float(np.mean(H[k])) if H[k] else None for k in H},
                         identical_mean=float(np.mean(I)) if I else None, identical_min=float(np.min(I)) if I else None, lazy_mean=float(np.mean(L)) if L else None,
                         severity_rho=float(spearmanr(sv, ss)[0]) if len(set(sv)) > 1 and len(set(ss)) > 1 else None, cat={c: (float(np.mean(v[0])), len(v[0])) for c, v in cat.items()})
    return out

def parser_agreement():
    ex = V.exams(); val = json.load(open(os.path.join(D, 'validation.json')))['texts']; res = {}
    for label, sel in (('all 427 exams', ex), ('kept (passed 3 checks)', [e for e in ex if val[e['vi_clean']]['passes']])):
        c = collections.Counter(); n = 0
        for e in sel:
            a, b = P.parse(e['vi_clean'], 'vi'), P.parse(V.strip_prefix(e['en']), 'en'); n += 1
            for k in ('side', 'birads', 'finding', 'axillary', 'recommendation', 'suspicious'): c[k] += a[k] == b[k]
        res[label] = dict(n=n, **{k: c[k] / n for k in c})
    res['exams whose Vietnamese original states a BI-RADS code'] = sum(bool(V.facts(e['vi_clean'], 'vi')['birads']) for e in ex); res['exams (English) stating a BI-RADS code'] = sum(bool(V.facts(V.strip_prefix(e['en']), 'en')['birads']) for e in ex)
    return res

def main(out):
    os.makedirs(out, exist_ok=True); R = rows(); S = json.load(open(os.path.join(D, 'scores_his_layer0.json'))); res = {}
    sets = {'strict_test': [r for r in R if r['strict'] and r['split'] == 'test'], 'strict_dev_val': [r for r in R if r['strict'] and r['split'] in ('dev', 'val')], 'looser_test': [r for r in R if r['split'] == 'test']}
    for k, v in sets.items(): res[k] = analyse_set(v, S, SC, k)
    jp = os.path.join(D, 'judge_his_v2q.jsonl')
    if os.path.exists(jp):
        J = {(json.loads(l)['a'], json.loads(l)['b']): json.loads(l)['result'] for l in open(jp)}; T = sets['strict_test']; keep = [r for r in T if J.get((r['reference'], r['candidate'])) is not None]
        P_ = sorted({(r['reference'], r['candidate']) for r in keep}); S2 = {'pairs': [list(p) for p in P_], 'scores': {'sentence_f1': [J[p]['f1'] for p in P_], 'judge_score': [J[p]['judge'] for p in P_]}}
        res['strict_test_judge'] = analyse_set(keep, S2, ['sentence_f1', 'judge_score'], 'judge'); res['judge_missing'] = len(T) - len(keep); res['judge_len_mismatch'] = sum(1 for v in J.values() if v and v['len_mismatch']); res['judge_pairs'] = len(J)
    res['parser_agreement'] = parser_agreement(); json.dump(res, open(os.path.join(out, 'results.json'), 'w'), indent=1); return res

if __name__ == '__main__' and sys.argv[1] == 'analyse': main(sys.argv[2])
