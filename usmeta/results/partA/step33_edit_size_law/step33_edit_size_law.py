"""Step 33: edit-size law (SAVED scores only, no model call). NEW file.
For every text scorer and every organ x harmless-group cell (small, matched, large, other, human 21d): paired AUROC of planted error vs harmless (per case, ties 0.5, mean over cases) and the median edit-size ratio
(harmless edit size / error edit size, over all error x harmless pairs of the cell; edit size = normalised character Levenshtein distance to the reference, Step 21e). One model per scorer: AUROC = a + b * ln(ratio), ordinary least squares across that scorer's cells.
Slope b, R^2 and their 95% intervals by group bootstrap (resample patient / exam groups with replacement, recompute every cell and refit; 1,000 resamples, seed 0). Cells under 30 groups are marked; the primary fit uses all cells,
a sensitivity fit uses only cells with >= 30 groups. Decision: R^2 >= 0.6 = 'scorer behaviour is largely predicted by edit size'.
Sources: bench_test_v2d + saved test scores (Steps 5-10d, 12), llm_finding_f1 from the Step 27 saved pair scores (judged subset), the human rewordings of Step 21d from their saved scores and the Step 27 extraction cache (no judge scores were saved per pair for them).
    python3 -m usmeta.step33_edit_size_law"""
import os, json, collections, sys, platform, time, subprocess
import numpy as np
from . import splits, step19_pairs as P, step21_edit_matched as E21
from .layer0 import auroc_case

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'); OUT = os.path.join(ROOT, 'results', 'partA', 'step33_edit_size_law'); MIN_G = 30; NBOOT = 1000
SCORERS = [('bleu', 'BLEU'), ('rougeL', 'ROUGE-L'), ('chrf', 'chrF'), ('bertscore[roberta-large]', 'BERTScore'), ('ratescore', 'RaTEScore'), ('judge_score', 'judge_score'), ('sentence_f1', 'judge sentence_f1'), ('llm_finding_f1', 'llm_finding_f1')]
GROUPS = ('small', 'matched', 'large', 'other', 'human'); ORGANS = ('breast', 'thyroid', 'fetal head')

def load():
    splits.load('test', script='usmeta.step33_edit_size_law')                               # logged access; only saved test scores are used below
    rows = [json.loads(l) for l in open(os.path.join(ROOT, 'bench_test_v2d.jsonl'))]
    sc = {**P.scores_of(os.path.join(ROOT, 'scores_test_layer0.json')), **P.judge_lookup([os.path.join(ROOT, 'results/partA/step10d_test_results/judge_test_v2.jsonl'), os.path.join(ROOT, 'judge_big_v2.jsonl')])}
    sc['llm_finding_f1'] = {(r['reference'], r['candidate']): r['llm_finding_f1'] for r in json.load(open(os.path.join(ROOT, 'results/partA/step27_llm_extractor/test_pair_scores.json')))}
    return rows, sc

def human_items():
    """21d: per item the 8 sampled planted errors vs the human rewording; scores from the saved layer 0 file and the Step 27 cache (no model call)"""
    D = os.path.join(ROOT, 'results', 'partA', 'step21d_human_sheet'); B = [json.loads(l) for l in open(os.path.join(D, 'human_bench.jsonl'))]
    s0 = P.scores_of(os.path.join(D, 'scores_layer0.json')); sc = {n: v for n, v in s0.items() if n in dict(SCORERS)}
    from . import step27_extractor as X
    ex = X.Extractor('main'); org = {'breast': 'breast', 'thyroid': 'thyroid', 'fetal head': 'fetal'}; llm = {}; flat = {}
    def fl(o, t):
        if (o, t) not in flat: f, ok = ex.facts(o, t); flat[(o, t)] = f
        return flat[(o, t)]
    for b in B:
        o = org[b['organ']]; llm[(b['reference'], b['candidate'])] = X.llm_finding_f1(fl(o, b['reference']), fl(o, b['candidate']), o)
    sc['llm_finding_f1'] = llm; by = collections.defaultdict(lambda: dict(E=[], H=[]))
    for b in B:
        if b['kind'] == 'error': by[b['item']]['E'].append(b)
        elif b['kind'] == 'human': by[b['item']]['H'].append(b)
    return by, sc, {b['item']: b['organ'] for b in B}

def build_cells(rows, sc, hum, hsc, horg):
    """cell (scorer, organ, group) -> dict(cases=[(group_id, auroc)], pairs=[(group_id, ratio)])"""
    cache = {}
    def es(ref, cand):
        k = (ref, cand)
        if k not in cache: cache[k] = E21.edit_size(ref, cand)
        return cache[k]
    C = collections.defaultdict(lambda: dict(E=[], H=collections.defaultdict(list)))
    for r in rows:
        if r['kind'] == 'error': C[r['case_id']]['E'].append(r)
        elif r['kind'] == 'harmless' and r['harmless_type'] in ('small', 'matched', 'large', 'other'): C[r['case_id']]['H'][r['harmless_type']].append(r)
        C[r['case_id']].setdefault('meta', (P.ORGAN[r['dataset']], f"{r['dataset']}:{r['group_id']}"))
    cells = {}
    def add(name, organ, grp, gid, e_pairs, h_pairs, scores):
        e = [(scores.get(k), es(*k)) for k in e_pairs]; h = [(scores.get(k), es(*k)) for k in h_pairs]; e = [(a, x) for a, x in e if a is not None]; h = [(a, x) for a, x in h if a is not None]
        if not e or not h: return
        auc = auroc_case([a for a, _ in e], [a for a, _ in h]); ratios = [hx / ex for _, hx in h for _, ex in e if ex > 0]
        c = cells.setdefault((name, organ, grp), dict(cases=[], pairs=[])); c['cases'].append((gid, auc)); c['pairs'] += [(gid, x) for x in ratios]
    for cid, c in C.items():
        organ, gid = c['meta']; ep = [(r['reference'], r['candidate']) for r in c['E']]
        for grp, rs in c['H'].items():
            hp = [(r['reference'], r['candidate']) for r in rs]
            for name, _ in SCORERS: add(name, organ, grp, gid, ep, hp, sc[name])
    for it, d in hum.items():
        if not d['E'] or not d['H']: continue
        organ = horg[it]; ep = [(b['reference'], b['candidate']) for b in d['E']]; hp = [(b['reference'], b['candidate']) for b in d['H']]
        for name, _ in SCORERS:
            if name in hsc: add(name, organ, 'human', f'human:{it}', ep, hp, hsc[name])
    return cells

def wmedian(vals_sorted, w_sorted):
    cw = np.cumsum(w_sorted); half = cw[-1] / 2; return vals_sorted[int(np.searchsorted(cw, half))]

def fit(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 3 or np.ptp(x) == 0 or np.ptp(y) == 0: return None
    b, a = np.polyfit(x, y, 1); r = np.corrcoef(x, y)[0, 1]; return float(b), float(a), float(r * r)

def analyse(cells):
    out = {}; rng = np.random.default_rng(0)
    for name, nm in SCORERS:
        cs = {k: v for k, v in cells.items() if k[0] == name}
        if not cs: continue
        gl = sorted({g for v in cs.values() for g, _ in v['cases']}); gi = {g: i for i, g in enumerate(gl)}; prep = {}
        for k, v in cs.items():
            cg = np.array([gi[g] for g, _ in v['cases']]); ca = np.array([a for _, a in v['cases']]); pg = np.array([gi[g] for g, _ in v['pairs']]); pr = np.array([x for _, x in v['pairs']]); o = np.argsort(pr)
            prep[k] = (cg, ca, pg[o], pr[o])
        def stats(counts):
            xs, ys, keys = [], [], []
            for k, (cg, ca, pg, pr) in prep.items():
                w = counts[cg]
                if w.sum() == 0: continue
                pw = counts[pg]
                if pw.sum() == 0: continue
                xs.append(np.log(wmedian(pr, pw))); ys.append(float((w * ca).sum() / w.sum())); keys.append(k)
            return xs, ys, keys
        xs, ys, keys = stats(np.ones(len(gl)))
        ng = {k: len({g for g, _ in cs[k]['cases']}) for k in keys}; big = [i for i, k in enumerate(keys) if ng[k] >= MIN_G]
        f_all = fit(xs, ys); f_big = fit([xs[i] for i in big], [ys[i] for i in big]); bs, br, bsb, brb = [], [], [], []
        for _ in range(NBOOT):
            counts = np.bincount(rng.integers(0, len(gl), len(gl)), minlength=len(gl)); x, y, kk = stats(counts); f = fit(x, y)
            if f: bs.append(f[0]); br.append(f[2])
            bg = [i for i, k in enumerate(kk) if ng.get(k, 0) >= MIN_G]; f2 = fit([x[i] for i in bg], [y[i] for i in bg])
            if f2: bsb.append(f2[0]); brb.append(f2[2])
        pc = lambda v: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] if v else None
        out[name] = dict(label=nm, n_cells=len(keys), n_cells_ge30=len(big), primary=dict(slope=f_all[0], intercept=f_all[1], r2=f_all[2], slope_ci=pc(bs), r2_ci=pc(br)) if f_all else None,
                         sensitivity_ge30=dict(slope=f_big[0], intercept=f_big[1], r2=f_big[2], slope_ci=pc(bsb), r2_ci=pc(brb)) if f_big else None,
                         cells=[dict(organ=k[1], group=k[2], auroc=ys[i], median_ratio=float(np.exp(xs[i])), groups=ng[k], cases=len(cs[k]['cases']), too_small=ng[k] < MIN_G) for i, k in enumerate(keys)])
    return out

def main():
    os.makedirs(OUT, exist_ok=True); rows, sc = load(); hum, hsc, horg = human_items(); cells = build_cells(rows, sc, hum, hsc, horg); res = analyse(cells); json.dump(res, open(os.path.join(OUT, 'results.json'), 'w'), indent=1)
    import csv
    with open(os.path.join(OUT, 'cells.csv'), 'w', newline='') as fh:
        w = csv.writer(fh); w.writerow(['scorer', 'organ', 'group', 'cases', 'groups', 'too_small', 'auroc', 'median_edit_ratio', 'ln_ratio'])
        for n, v in res.items():
            for c in v['cells']: w.writerow([n, c['organ'], c['group'], c['cases'], c['groups'], c['too_small'], f"{c['auroc']:.4f}", f"{c['median_ratio']:.4f}", f"{np.log(c['median_ratio']):.4f}"])
    print('saved', {n: (v['n_cells'], round(v['primary']['r2'], 2) if v['primary'] else None) for n, v in res.items()})

if __name__ == '__main__': main()
