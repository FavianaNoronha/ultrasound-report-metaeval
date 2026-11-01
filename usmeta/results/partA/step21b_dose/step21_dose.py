"""Step 21b: error-size dose-response (size / measurement errors only; head circumference for fetal head). NEW file; frozen code untouched.
New candidates from the SAME references (bench_test_v2d, test split) at multiplicative factors 0.5, 0.7, 0.8, 0.9, 0.95, 1.3, 1.5, 2.0 of the stated size (size_mm / size_pct; hc_mm for fetal head;
rounded as the templates round; candidates equal to the reference are dropped). Harmless comparison = the matched one-word synonyms of bench_test_v2d (same reference).
Scorers: BLEU, ROUGE-L, chrF, BERTScore, RaTEScore, finding_f1 (UPPER BOUND on templated text), Gemma judge (prompt_v2, capped sample), predicted-mask image check (Step 16 scans, exact box).
    python3 -m usmeta.step21_dose build | text | judge | analyse"""
import os, sys, json, math, random, collections, time
import numpy as np
from scipy.stats import spearmanr
from . import templates_v2 as T, layer0, layer1, partb, layer3, unified
from .layer0 import auroc_case
from .step10d_analysis import gboot

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'); OUT = os.path.join(ROOT, 'results', 'partA', 'step21b_dose')
FACTORS = [0.5, 0.7, 0.8, 0.9, 0.95, 1.3, 1.5, 2.0]; SIZE = ('size_mm', 'size_pct', 'hc_mm'); N_JUDGE = 12
ORGAN = {'BrEaST': 'breast', 'BUS-BRA': 'breast', 'BUSI': 'breast', 'UDIAT': 'breast', 'BUS-UCLM': 'breast', 'TN3K': 'thyroid', 'TN5000': 'thyroid', 'DDTI': 'thyroid', 'HC18': 'fetal head', 'FetalHead': 'fetal head'}
LOADER = {'BUS-BRA': 'BUSBRA', 'BUS-UCLM': 'BUSUCLM'}
P = lambda f: os.path.join(OUT, f)

def build():
    bench = [json.loads(l) for l in open(os.path.join(ROOT, 'bench_test_v2d.jsonl'))]; by = collections.defaultdict(list)
    for b in bench: by[b['case_id']].append(b)
    recs = {}
    for ds in ORGAN:
        for c in T.load(LOADER.get(ds, ds)): recs[c['case_id']] = c
    judged = {json.loads(l)['reference'] + '||' + json.loads(l)['candidate'] for f in ('judge_test_v2.jsonl', 'judge_big_v2.jsonl') for l in open(f) if json.loads(l)['result'] is not None}
    rows = []; skipped = 0
    for cid, bs in by.items():
        rec = recs[cid]; f = T.facts(rec); ref = bs[0]['reference']; key = next((k for k in SIZE if k in f), None)
        if key is None or T.render(f, rec['organ'], 'standard') != ref: skipped += 1; continue
        v = f[key][0]; prov = f[key][1]
        for fac in FACTORS:
            new = round(v * fac, 1) if key == 'hc_mm' else round(v * fac); new = min(new, 100) if key == 'size_pct' else new
            if new == v or new <= 0: continue
            g = dict(f); g[key] = (new, prov); txt = T.render(g, rec['organ'], 'standard')
            if txt != ref: rows.append(dict(case_id=cid, dataset=bs[0]['dataset'], organ=ORGAN[bs[0]['dataset']], group_id=bs[0]['group_id'], kind='error', field=key, factor=fac, old=v, new=new, reference=ref, candidate=txt))
        for b in bs:
            if b['kind'] == 'harmless' and b['harmless_type'] == 'matched': rows.append(dict(case_id=cid, dataset=b['dataset'], organ=ORGAN[b['dataset']], group_id=b['group_id'], kind='matched', field=None, factor=None, reference=ref, candidate=b['candidate'], judged=(ref + '||' + b['candidate']) in judged))
    open(P('candidates.jsonl'), 'w').write(''.join(json.dumps(r) + '\n' for r in rows)); print(len(rows), 'rows;', skipped, 'cases skipped (no size field / reference mismatch)')
    print(collections.Counter((r['organ'], r['kind']) for r in rows))

def text_scores():
    rows = [json.loads(l) for l in open(P('candidates.jsonl'))]; tmp = [dict(r, organ={'breast': 'breast', 'thyroid': 'thyroid', 'fetal head': 'fetal'}[r['organ']]) for r in rows]
    open(P('_bench.jsonl'), 'w').write(''.join(json.dumps(r) + '\n' for r in tmp))
    layer1.score(P('_bench.jsonl'), P('scores_layer1.json')); layer0.score(P('_bench.jsonl'), P('scores_layer0.json'))

def judge_plan():
    rows = [json.loads(l) for l in open(P('candidates.jsonl'))]; rng = random.Random(0); by = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in rows: by[r['dataset']][r['case_id']].append(r)
    jids = set()
    for f in ('judge_test_v2_bench.jsonl', 'judge_big_v2_bench.jsonl'): jids |= {json.loads(l)['case_id'] for l in open(os.path.join(ROOT, f))}        # the Step 12 sample
    out = []
    for ds, cs in by.items():
        ids = sorted(c for c in cs if c in jids and any(r['kind'] == 'matched' and r.get('judged') for r in cs[c])); rng.shuffle(ids)
        for c in ids[:N_JUDGE]: out += [r for r in cs[c] if r['kind'] == 'error']
    return out

def judge():
    from . import judge2, judge2_test
    plan = judge_plan(); out = P('judge_replies.jsonl'); done = {(json.loads(l)['reference'], json.loads(l)['candidate']) for l in open(out)} if os.path.exists(out) else set()
    todo = list(dict.fromkeys((r['reference'], r['candidate']) for r in plan if (r['reference'], r['candidate']) not in done)); print(len(plan), 'error rows;', len(todo), 'pairs to judge', flush=True)
    sc = judge2_test.SC(judge2.PROMPT_V2); t0 = time.time()
    for i, (a, b) in enumerate(todo):
        s = sc.run(a, b); open(out, 'a').write(json.dumps(dict(reference=a, candidate=b, result=s)) + '\n')
        if i % 25 == 0: print(i, len(todo), round(time.time() - t0), 's', flush=True)
    print('done', round(time.time() - t0), 's missing', sc.missing, flush=True)

def lookups():
    S = {}
    for f, skip in (('scores_layer0.json', ()), ('scores_layer1.json', ('legacy_fact_checker', 'legacy_fact_f1', 'finding_precision', 'finding_recall'))):
        s = json.load(open(P(f))); Pp = [tuple(p) for p in s['pairs']]
        for n, a in s['scores'].items():
            if n not in skip: S[n] = dict(zip(Pp, a))
    # judge: Step 12 replies for the matched synonyms + the new replies for the errors
    J = {}
    for f in (os.path.join(ROOT, 'judge_test_v2.jsonl'), os.path.join(ROOT, 'judge_big_v2.jsonl'), P('judge_replies.jsonl')):
        if os.path.exists(f):
            for l in open(f):
                d = json.loads(l)
                if d['result'] is not None: J[(d['reference'], d['candidate'])] = d['result']
    S['sentence_f1'] = {k: v['f1'] for k, v in J.items()}; S['judge_score'] = {k: v['judge'] for k, v in J.items()}
    return S

def image_scores(rows):
    """predicted-mask check (exact box, Step 16 masks) for the cases of the Step 16 selection: mask_verified on each candidate (1.0 if no checkable claim, as in Step 16)"""
    sel = json.load(open(os.path.join(partb.LOCAL, 'selected.json'))); recs = {}
    for ds in partb.DATASETS:
        for c in unified.load(partb.LOADER.get(ds, ds)): recs[c['case_id']] = c
    M = {}
    for s in sel:
        pm, _ = partb.load_pred(s['case_id'], 'exact'); M[s['case_id']] = partb.pred_meas(recs[s['case_id']], pm)
    out = {}
    for r in rows:
        if r['case_id'] in M:
            v = layer3.mask_verified(r['candidate'], {'breast': 'breast', 'thyroid': 'thyroid', 'fetal head': 'fetal'}[r['organ']], M[r['case_id']])[0]; out[(r['reference'], r['candidate'])] = 1.0 if v is None else v
    return out

SCORERS = ['bleu', 'rougeL', 'chrf', 'bertscore[roberta-large]', 'ratescore', 'finding_f1', 'sentence_f1', 'judge_score', 'image_check']

def analyse():
    rows = [json.loads(l) for l in open(P('candidates.jsonl'))]; S = lookups(); S['image_check'] = image_scores(rows); res = {}
    by = collections.defaultdict(list)
    for r in rows: by[r['case_id']].append(r)
    for n in SCORERS:
        sc = S[n]
        for org in ('breast', 'thyroid', 'fetal head'):
            cs = {c: rs for c, rs in by.items() if rs[0]['organ'] == org}
            # AUROC per factor vs matched synonyms (same case)
            for fac in FACTORS + ['ALL']:
                v, g = [], []
                for c, rs in cs.items():
                    e = [sc.get((r['reference'], r['candidate'])) for r in rs if r['kind'] == 'error' and (fac == 'ALL' or r['factor'] == fac)]; h = [sc.get((r['reference'], r['candidate'])) for r in rs if r['kind'] == 'matched']
                    e = [x for x in e if x is not None]; h = [x for x in h if x is not None]
                    if e and h: v.append(auroc_case(e, h)); g.append(rs[0]['group_id'])
                res[f'{n}|{org}|{fac}'] = dict(n_cases=len(v), n_groups=len(set(g)), auroc=gboot(v, g) if v else None)
            # monotonicity: Spearman of |log factor| vs score drop (1 - score; identical copies score 1.0) over all error candidates of the organ with a score
            x, y = [], []
            for c, rs in cs.items():
                for r in rs:
                    if r['kind'] == 'error':
                        s_ = sc.get((r['reference'], r['candidate']))
                        if s_ is not None: x.append(abs(math.log(r['factor']))); y.append(1 - s_)
            res[f'{n}|{org}|spearman'] = dict(n=len(x), rho=(float(spearmanr(x, y)[0]) if len(set(x)) > 1 and len(set(y)) > 1 else None))
            # mean score per factor (for the table)
            res[f'{n}|{org}|mean_score'] = {str(fac): (float(np.mean([sc[(r['reference'], r['candidate'])] for rs in cs.values() for r in rs if r['kind'] == 'error' and r['factor'] == fac and (r['reference'], r['candidate']) in sc])) if any(r['factor'] == fac and (r['reference'], r['candidate']) in sc for rs in cs.values() for r in rs if r['kind'] == 'error') else None) for fac in FACTORS}
    json.dump(res, open(P('dose_results.json'), 'w'), indent=1); return res

if __name__ == '__main__':
    {'build': build, 'text': text_scores, 'judge': judge, 'analyse': analyse}[sys.argv[1]]()
