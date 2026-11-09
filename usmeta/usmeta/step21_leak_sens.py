"""Step 21g: leakage sensitivity (SAVED scores only, no model calls). NEW file.
1. From the <= 8-bit dHash clusters of Step 21f (duplicates.jsonl, within one dataset), list TEST images whose cluster also has members in dev or val.
2. Recompute the headline test AUROCs after dropping those images and all their candidates: word scorers, finding_f1 and the judge (error vs small / matched / large harmless, as in Step 19a),
   and the image check (Step 24 'exact' box, position and size, Step 20 tolerance rule and Step 16 exact-match rule).
3. Per organ: full-test value, reduced value, change (paired group bootstrap, 1,000 resamples, seed 0: groups resampled jointly so the change has its own interval), cases dropped. Any |change| > 0.05 is listed at the top.
Cells under 30 groups: too small to compare. The 8-bit clusters are a LOOSE check, not verified duplicates (Step 21f).
    python3 -m usmeta.step21_leak_sens OUT_DIR"""
import json, sys, os, collections
import numpy as np
from . import splits, step19_pairs as p, step24_box_reliability as s24

MIN_N = 30; FLAG = 0.05
WORD = ['bleu', 'rougeL', 'chrf', 'bertscore[roberta-large]', 'ratescore']; NAMES = {'bleu': 'BLEU', 'rougeL': 'ROUGE-L', 'chrf': 'chrF', 'bertscore[roberta-large]': 'BERTScore', 'ratescore': 'RaTEScore', 'finding_f1': 'finding_f1 (upper bound)', 'sentence_f1': 'judge sentence_f1', 'judge_score': 'judge_score'}
ORGANS = ('breast', 'thyroid', 'fetal head')

def leaky_test_images():
    sp = {}
    for l in open('splits.jsonl'):
        r = json.loads(l); sp[r['case_id']] = r
    par = {}
    def find(x):
        par.setdefault(x, x)
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    for l in open('duplicates.jsonl'):
        r = json.loads(l)
        if r['dist'] <= 8 and r['ds_a'] == r['ds_b'] and not r['ds_a'].startswith('Diverse') and r['a'] in sp and r['b'] in sp: par[find(r['a'])] = find(r['b'])
    cl = collections.defaultdict(set)
    for x in list(par): cl[find(x)].add(x)
    leaky = {}
    for c in cl.values():
        if len({sp[x]['split'] for x in c}) > 1 and 'test' in {sp[x]['split'] for x in c} and ({sp[x]['split'] for x in c} & {'dev', 'val'}):
            for x in c:
                if sp[x]['split'] == 'test': leaky[x] = sorted(sp[y]['split'] for y in c if y != x)
    return leaky, sp

def per_case(C, sc, name):
    """case -> (AUROC value over error x harmless pairs, group)"""
    out = {}
    for cid, c in C.items():
        e = [p.score_of(sc, name, r) for r in c['E']]; h = [p.score_of(sc, name, r) for r in c['H']]; e = [x for x in e if x is not None]; h = [x for x in h if x is not None]
        if not e or not h: continue
        E, H = np.array(e)[:, None], np.array(h)[None, :]; out[cid] = (float((E < H).mean() + 0.5 * (E == H).mean()), c['group'])
    return out

def paired(vals, dropped, seed=0, B=1000):
    """vals: {id: (value, group)}; returns full / reduced mean with CI, change with CI, n, groups, dropped"""
    ids = list(vals); g = np.array([vals[i][1] for i in ids]); v = np.array([vals[i][0] for i in ids]); keep = np.array([i not in dropped for i in ids])
    ug = sorted(set(g)); idx = {k: np.where(g == k)[0] for k in ug}; rng = np.random.default_rng(seed); F, R, D = [], [], []
    for _ in range(B):
        pick = rng.integers(0, len(ug), len(ug)); ii = np.concatenate([idx[ug[k]] for k in pick]); f = v[ii].mean(); kk = ii[keep[ii]]
        if len(kk) == 0: continue
        r = v[kk].mean(); F.append(f); R.append(r); D.append(r - f)
    ci = lambda a: (float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5)))
    full = float(v.mean()); red = float(v[keep].mean()) if keep.any() else None
    return dict(n=len(ids), groups=len(ug), n_dropped=int((~keep).sum()), groups_reduced=len(set(g[keep])), full=full, full_ci=ci(F), reduced=red, reduced_ci=ci(R) if R else None, change=(red - full) if red is not None else None, change_ci=ci(D) if D else None)

def fmt(x, ci=None): return '—' if x is None else (f'{x:.2f}' if ci is None else f'{x:.2f} ({ci[0]:.2f}–{ci[1]:.2f})')

def main(out):
    os.makedirs(out, exist_ok=True); leaky, sp = leaky_test_images(); rows = [json.loads(l) for l in open('bench_test_v2d.jsonl')]
    ids = {r['case_id'] for r in splits.load('test', script='usmeta.step21_leak_sens')}; assert all(r['case_id'] in ids for r in rows)
    sc = {**p.scores_of('scores_test_layer0.json'), 'finding_f1': p.scores_of('scores_test_layer1.json')['finding_f1']}; sc.update(p.judge_lookup(['judge_test_v2.jsonl', 'judge_big_v2.jsonl']))
    jr = []
    for f in ('judge_test_v2_bench.jsonl', 'judge_big_v2_bench.jsonl'): jr += [json.loads(l) for l in open(f)]
    jset = {(r['reference'], r['candidate']) for r in jr}; Call = p.cases_of(rows); Cj = p.cases_of(rows, jset); org = lambda C, o: {k: c for k, c in C.items() if p.ORGAN[c['ds']] == o}
    ds_of = {r['case_id']: r['dataset'] for r in rows}; res = {}; lines = []
    # ---- leaky images list
    by = collections.Counter(); tot = collections.Counter(sp[c]['dataset'] for c in sp if sp[c]['split'] == 'test')
    for c in leaky: by[sp[c]['dataset']] += 1
    benchtest = {r['case_id'] for r in rows}; lk = {c for c in leaky if c in benchtest}
    L = {o: sum(1 for c in lk if p.ORGAN[sp[c]['dataset']] == o) for o in ORGANS}
    # ---- text scorers + judge
    for o in ORGANS:
        for n in WORD + ['finding_f1']: res[f'{o}|{n}'] = paired(per_case(org(Call, o), sc, n), lk)
        for n in ('sentence_f1', 'judge_score'): res[f'{o}|{n}'] = paired(per_case(org(Cj, o), sc, n), lk)
    # ---- image check (Step 24 'exact' rows: same 228 scans; position and size, both rules)
    D = json.load(open(os.path.join(s24.OUT, 'case_rows.json')))['rows']; ex = [r for r in D if r['cond'] == 'exact']; lk_img = set(lk) | set(leaky)
    for o in ('breast', 'thyroid'):
        for var, vn in (('tol', 'Step 20 tolerance'), ('exact', 'Step 16 exact-match')):
            for k in ('position', 'size', 'all'):
                vals = {r['case_id']: (r[f'auc_{var}_{k}'], r['group']) for r in ex if r['organ'] == o and r[f'auc_{var}_{k}'] is not None}
                res[f'{o}|image {k} ({vn})'] = paired(vals, lk_img)
    json.dump(dict(leaky_test_images={c: v for c, v in sorted(leaky.items())}, results=res), open(os.path.join(out, 'leak_sens.json'), 'w'), indent=1)
    # ---- markdown
    big = [(k, v) for k, v in res.items() if v['change'] is not None and abs(v['change']) > FLAG]
    M = ['# Step 21g — Leakage sensitivity (test split, saved scores only)', '',
         f'**What was dropped:** test images whose near-duplicate cluster (dHash ≤ 8 bits within one dataset, Step 21f; a LOOSE check, not verified duplicates) also has members in dev or val: {len(leaky)} test images in total, {len(lk)} of them have candidates in `bench_test_v2d` (breast {L["breast"]}, thyroid {L["thyroid"]}, fetal head {L["fetal head"]}); per dataset: ' + ', '.join(f'{d} {by[d]} of {tot[d]}' for d in sorted(by)) + '. All their candidates are removed from the test comparison; nothing else changes (same scorers, same pairs, same method as Step 19a).', '',
         '## Flag: changes above 0.05', '']
    M += (['| group | scorer | full | reduced | change |', '|---|---|---|---|---|'] + [f"| {k.split('|')[0]} | {k.split('|')[1]} | {fmt(v['full'])} | {fmt(v['reduced'])} | {v['change']:+.3f} ({v['change_ci'][0]:+.3f} to {v['change_ci'][1]:+.3f}) |" for k, v in big]) if big else ['**No cell changes by more than 0.05.**']
    M += ['', 'Method: AUROC per case (error vs small / matched / large harmless candidates, ties 0.5), mean over cases; group bootstrap, 1,000 resamples, seed 0, with the full and the reduced set resampled together so the change has its own interval. Under 30 groups = too small to compare. Judge rows use only the judged subset (Steps 10d + 12).', '']
    for o in ORGANS:
        M += [f'## {o.capitalize()}', '', '| scorer | cases | groups | dropped | groups kept | full-test AUROC | reduced AUROC | change |', '|---|---|---|---|---|---|---|---|']
        for k, v in res.items():
            if not k.startswith(o + '|'): continue
            small = v['groups'] < MIN_N or (v['groups_reduced'] < MIN_N)
            M.append(f"| {k.split('|')[1].replace('bleu', 'BLEU').replace('rougeL', 'ROUGE-L').replace('chrf', 'chrF').replace('bertscore[roberta-large]', 'BERTScore').replace('ratescore', 'RaTEScore')} | {v['n']} | {v['groups']} | {v['n_dropped']} | {v['groups_reduced']} | " + ('too small to compare' if small else f"{fmt(v['full'], v['full_ci'])} | {fmt(v['reduced'], v['reduced_ci'])} | {v['change']:+.3f} ({v['change_ci'][0]:+.3f} to {v['change_ci'][1]:+.3f})") + ' |' if not small else f"| {k.split('|')[1]} | {v['n']} | {v['groups']} | {v['n_dropped']} | {v['groups_reduced']} | too small to compare | | |")
        M.append('')
    open(os.path.join(out, 'results.md'), 'w').write('\n'.join(M)); print('\n'.join(M[:25])); return res

if __name__ == '__main__': main(sys.argv[1] if len(sys.argv) > 1 else 'results/partA/step21g_leak_sens')
