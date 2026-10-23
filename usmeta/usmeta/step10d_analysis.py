"""Step 10d analysis: per-dataset AUROC (vs harmless small / matched / large) with 95% CI from a bootstrap that resamples GROUPS (not cases).
Point estimates match usmeta.layer0b.analyse; this file only adds group-level CIs. Not a change to the frozen scorers."""
import json, collections
import numpy as np
from scipy.stats import spearmanr
from .layer0 import auroc_case, LAZY

def gboot(vals, groups, n=1000, seed=0):
    """mean and 95% CI of per-case values, resampling groups with replacement"""
    if not vals: return None
    g = collections.defaultdict(list)
    for v, k in zip(vals, groups): g[k].append(v)
    keys = list(g); rng = np.random.default_rng(seed); s = np.array([sum(g[k]) for k in keys]); c = np.array([len(g[k]) for k in keys]); m = []
    for _ in range(n):
        i = rng.integers(0, len(keys), len(keys)); m.append(s[i].sum() / c[i].sum())
    return float(np.mean(vals)), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))

def analyse(rows, S, gid):
    idx = {tuple(p): i for i, p in enumerate(S['pairs'])}; res = {}
    for name, arr in S['scores'].items():
        sc = lambda r: arr[idx[(r['reference'], r['candidate'])]]; per = collections.defaultdict(lambda: collections.defaultdict(list))
        for r in rows: per[r['dataset']][r['case_id']].append(r)
        for ds, cases in per.items():
            A = {t: ([], []) for t in ('small', 'matched', 'large')}; C = ([], []); cat = {t: collections.defaultdict(lambda: ([], [])) for t in ('small', 'matched', 'large')}
            HM = {t: [] for t in ('small', 'matched', 'large')}; I, L, sev = [], [], []
            for cid, rs in cases.items():
                e = [r for r in rs if r['kind'] == 'error']; g = gid[cid]
                I += [sc(r) for r in rs if r['kind'] == 'identical']
                if (rs[0]['reference'], LAZY) in idx: L.append(arr[idx[(rs[0]['reference'], LAZY)]])
                for t in ('small', 'matched', 'large'):
                    h = [sc(r) for r in rs if r['kind'] == 'harmless' and r['harmless_type'] == t]; HM[t] += h
                    if e and h:
                        A[t][0].append(auroc_case([sc(r) for r in e], h)); A[t][1].append(g)
                        if t == 'small':
                            c3 = [sc(r) for r in e if r['severity'] == 3]
                            if c3: C[0].append(auroc_case(c3, h)); C[1].append(g)
                        for c in {r['category'] for r in e}: cat[t][c][0].append(auroc_case([sc(r) for r in e if r['category'] == c], h)); cat[t][c][1].append(g)
                sev += [(r['severity'], sc(r)) for r in e]
            sv = [a for a, _ in sev]; ss = [b for _, b in sev]
            rho = float(spearmanr(sv, ss)[0]) if len(set(sv)) > 1 and len(set(ss)) > 1 else None
            res.setdefault(ds, {})[name] = dict(n_cases=len(cases), n_groups=len({gid[c] for c in cases}),
                **{f'auroc_{t}': gboot(*A[t]) for t in A}, critical_small=gboot(*C)[0] if C[0] else None,
                **{f'harmless_{t}_mean': float(np.mean(HM[t])) if HM[t] else None for t in HM},
                identical_mean=float(np.mean(I)) if I else None, identical_min=float(np.min(I)) if I else None, lazy_mean=float(np.mean(L)) if L else None, severity_rho=rho,
                **{f'cat_{t}': {c: float(np.mean(v[0])) for c, v in cat[t].items()} for t in cat})
    return res

def fm(x):
    if x is None: return '—'
    return f'{x[0]:.2f} ({x[1]:.2f}–{x[2]:.2f})' if isinstance(x, (tuple, list)) else f'{x:.2f}'

def table(res, names=None):
    out = []
    for ds, d in res.items():
        out += [f'### {ds} ({next(iter(d.values()))["n_cases"]} cases, {next(iter(d.values()))["n_groups"]} groups)', '', '| scorer | AUROC vs small (95% CI, group bootstrap) | vs matched | vs large | critical-only (small) | harmless_small mean | harmless_large mean | identical mean | lazy | severity ρ |', '|---|---|---|---|---|---|---|---|---|---|']
        for n, v in d.items():
            if names and n not in names: continue
            out.append(f"| {n} | {fm(v['auroc_small'])} | {fm(v['auroc_matched'])} | {fm(v['auroc_large'])} | {fm(v['critical_small'])} | {fm(v['harmless_small_mean'])} | {fm(v['harmless_large_mean'])} | {'—' if v['identical_mean'] is None else format(v['identical_mean'], '.4f')} | {fm(v['lazy_mean'])} | {fm(v['severity_rho'])} |")
        out.append('')
    return out
