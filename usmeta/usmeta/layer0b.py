"""Step 5: Layer 0 analysis on bench_v2b with AUROC reported separately vs harmless_small and harmless_large.
Scores come from the same (reference, candidate) pairs as Step 4 (bench_v2b changes labels, not text), so the cached scores
are reused; `check_pairs` verifies this. python3 -m usmeta.layer0b --out DIR"""
import json, os, math, collections, argparse
import numpy as np
from . import layer0
from .layer0 import auroc_case, boot, mag_value, LAZY, fmt

def check_pairs(rows, S): return layer0.pairs_of(rows) == [tuple(p) for p in S['pairs']]

def analyse(rows, S):
    idx = {tuple(p): i for i, p in enumerate(S['pairs'])}; res = {}
    for name, arr in S['scores'].items():
        sc = lambda r: arr[idx[(r['reference'], r['candidate'])]]
        per = collections.defaultdict(lambda: collections.defaultdict(list))
        for r in rows: per[r['dataset']][r['case_id']].append(r)
        for ds, cases in per.items():
            A = {'small': [], 'large': [], 'matched': []}; C = {'small': [], 'large': [], 'matched': []}; HM = {'small': [], 'large': [], 'matched': []}; I, L = [], []
            cat = {'small': collections.defaultdict(list), 'large': collections.defaultdict(list), 'matched': collections.defaultdict(list)}; G = collections.defaultdict(list)
            sev, magk, sizeby = [], collections.defaultdict(lambda: ([], [])), collections.defaultdict(list)
            for cid, rs in cases.items():
                e = [r for r in rs if r['kind'] == 'error']
                I += [sc(r) for r in rs if r['kind'] == 'identical']; L.append(arr[idx[(rs[0]['reference'], LAZY)]])
                if e:
                    for g in {r['group'] for r in rs if r['kind'] == 'harmless'}:
                        G[g].append(auroc_case([sc(r) for r in e], [sc(r) for r in rs if r['kind'] == 'harmless' and r['group'] == g]))
                for t in ('small', 'matched', 'large'):
                    h = [sc(r) for r in rs if r['kind'] == 'harmless' and r['harmless_type'] == t]; HM[t] += h
                    if e and h:
                        A[t].append(auroc_case([sc(r) for r in e], h))
                        c3 = [sc(r) for r in e if r['severity'] == 3]
                        if c3: C[t].append(auroc_case(c3, h))
                        for c in {r['category'] for r in e}: cat[t][c].append(auroc_case([sc(r) for r in e if r['category'] == c], h))
                for r in e:
                    sev.append((r['severity'], sc(r))); mv = mag_value(r)
                    if mv is not None:
                        fam = 'size' if r['field'].startswith('size') else r['field']; magk[fam][0].append(mv); magk[fam][1].append(sc(r))
                    if r['field'].startswith('size'): sizeby[r['magnitude']].append(sc(r))
            def rho(a, b):
                from scipy.stats import spearmanr
                if len(set(a)) < 2 or len(set(b)) < 2: return None
                x = float(spearmanr(a, b)[0]); return None if x != x else x
            res.setdefault(ds, {})[name] = dict(
                auroc_by_group={g: float(np.mean(v)) for g, v in G.items()}, n_cases=len(cases), n_small=len(A['small']), n_large=len(A['large']), n_matched=len(A['matched']),
                auroc_matched=boot(A['matched']) if A['matched'] else None, critical_matched=boot(C['matched'])[0] if C['matched'] else None,
                harmless_matched_mean=float(np.mean(HM['matched'])) if HM['matched'] else None, cat_matched={c: float(np.mean(v)) for c, v in cat['matched'].items()},
                auroc_small=boot(A['small']) if A['small'] else None, auroc_large=boot(A['large']) if A['large'] else None,
                critical_small=boot(C['small'])[0] if C['small'] else None, critical_large=boot(C['large'])[0] if C['large'] else None,
                harmless_small_mean=float(np.mean(HM['small'])) if HM['small'] else None, harmless_large_mean=float(np.mean(HM['large'])) if HM['large'] else None,
                identical_mean=float(np.mean(I)), identical_min=float(np.min(I)), lazy_mean=float(np.mean(L)),
                severity_rho=rho([a for a, _ in sev], [b for _, b in sev]), magnitude_rho={k: rho(a, b) for k, (a, b) in magk.items()},
                size_error_mean_score={str(k): float(np.mean(v)) for k, v in sizeby.items()},
                cat_small={c: float(np.mean(v)) for c, v in cat['small'].items()}, cat_large={c: float(np.mean(v)) for c, v in cat['large'].items()})
    return res

def tables(res):
    out = []; org = {'breast': ['BrEaST', 'BUS-BRA', 'BUSI', 'UDIAT', 'BUS-UCLM'], 'thyroid': ['TN3K', 'TN5000', 'DDTI'], 'fetal': ['HC18', 'FetalHead']}
    for o, dss in org.items():
        out += [f'## {o}', '']
        for ds in dss:
            d = res[ds]
            out += [f'### {ds} ({next(iter(d.values()))["n_cases"]} cases)', '',
                    '| scorer | AUROC vs small (95% CI) | AUROC vs matched 1-word (95% CI) | AUROC vs large (95% CI) | critical-only small / matched / large | harmless_small mean | harmless_matched mean | harmless_large mean | identical mean | lazy mean | severity ρ | magnitude ρ |', '|---|---|---|---|---|---|---|---|---|---|---|---|']
            for n, v in d.items():
                mr = ', '.join(f'{k} {fmt(x)}' for k, x in v['magnitude_rho'].items()) or '—'
                out.append(f"| {n} | {fmt(v['auroc_small'])} | {fmt(v['auroc_matched'])} | {fmt(v['auroc_large'])} | {fmt(v['critical_small'])} / {fmt(v['critical_matched'])} / {fmt(v['critical_large'])} | {fmt(v['harmless_small_mean'])} | {fmt(v['harmless_matched_mean'])} | {fmt(v['harmless_large_mean'])} | {v['identical_mean']:.4f} | {fmt(v['lazy_mean'])} | {fmt(v['severity_rho'])} | {mr} |")
            out.append('')
    return out

def cat_tables(res):
    out = ['## AUROC by error category (vs harmless_small / vs matched 1-word / vs harmless_large)', '']
    for ds, d in res.items():
        cats = sorted({c for v in d.values() for c in v['cat_small']})
        out += [f'**{ds}**', '', '| scorer | ' + ' | '.join(cats) + ' |', '|---|' + '---|' * len(cats)]
        for n, v in d.items(): out.append(f'| {n} | ' + ' | '.join(f"{fmt(v['cat_small'].get(c))} / {fmt(v['cat_matched'].get(c))} / {fmt(v['cat_large'].get(c))}" for c in cats) + ' |')
        out.append('')
    return out

GROUPS = ['synonym1', 'synonyms', 'reorder', 'unit_cm', 'style_terse', 'style_long', 'negation', 'hedge', 'pad1', 'pad3']
def group_tables(res):
    out = ['## AUROC against each harmless group separately (errors vs that group only)', '']
    for ds, d in res.items():
        out += [f'**{ds}**', '', '| scorer | ' + ' | '.join(GROUPS) + ' |', '|---|' + '---|' * len(GROUPS)]
        for n, v in d.items(): out.append(f'| {n} | ' + ' | '.join(fmt(v['auroc_by_group'].get(g)) for g in GROUPS) + ' |')
        out.append('')
    return out

def _main():
    ap = argparse.ArgumentParser(); ap.add_argument('--bench', default='bench_v2b.jsonl'); ap.add_argument('--scores', default='scores_v2_layer0.json'); ap.add_argument('--out', required=True)
    ap.add_argument('--incremental', nargs=3, metavar=('BENCH', 'BASE_SCORES', 'OUT'))
    a = ap.parse_args()
    if a.incremental: return score_incremental(*a.incremental)
    rows = [json.loads(l) for l in open(a.bench)]; S = json.load(open(a.scores))
    assert check_pairs(rows, S), 'bench_v2b pairs differ from the scored pairs: re-score'
    res = analyse(rows, S); os.makedirs(a.out, exist_ok=True)
    json.dump(res, open(os.path.join(a.out, 'results_partA_layer0b.json'), 'w'), indent=1)
    gate = min(v['identical_min'] for d in res.values() for v in d.values()); print('identical-copy minimum over all scorers/datasets:', gate)
    open(os.path.join(a.out, 'tables.md'), 'w').write('\n'.join(tables(res) + cat_tables(res) + group_tables(res)))
    # numbers for the plain-language size-error paragraph
    for ds in ('BrEaST', 'BUS-BRA', 'TN5000', 'HC18'):
        for n in ('bleu', 'bertscore[roberta-large]', 'ratescore'):
            v = res[ds][n]; print(ds, n, 'size-error mean scores', {k: round(x, 3) for k, x in v['size_error_mean_score'].items()}, 'harmless_small', round(v['harmless_small_mean'], 3))

def score_incremental(bench, base_scores, out):
    """score only the pairs missing from base_scores (same scorers), write a new scores file aligned to pairs_of(bench)"""
    import time
    from . import graders
    rows = [json.loads(l) for l in open(bench)]; P = layer0.pairs_of(rows); B = json.load(open(base_scores))
    have = {tuple(p): i for i, p in enumerate(B['pairs'])}; new = [p for p in P if p not in have]; print(len(new), 'new pairs', flush=True)
    S = {'pairs': [list(p) for p in P], 'scores': {}, 'seconds': {}, 'base': base_scores}
    for name, arr in B['scores'].items():
        spec = {'bleu': 'bleu', 'rougeL': 'rougeL', 'chrf': 'chrf', 'bertscore[roberta-large]': 'bertscore:roberta-large', 'ratescore': 'ratescore'}[name]
        g = graders.make(spec); t = time.time()
        ns = dict(zip(new, g.batch([a for a, _ in new], [b for _, b in new]) if hasattr(g, 'batch') else [g.score(a, b) for a, b in new]))
        S['scores'][name] = [float(arr[have[p]]) if p in have else float(ns[p]) for p in P]; S['seconds'][name] = round(time.time() - t, 1)
        print('scored', name, round(time.time() - t, 1), 's', flush=True)
    json.dump(S, open(out, 'w'))

if __name__ == '__main__': _main()
