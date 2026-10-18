"""Meta-evaluation: how good is each grader at telling clinical errors from harmless rewording?

Definitions (score: higher = better report)
  discrimination AUROC   P(score(error) < score(harmless rewording of the SAME case)); 1 perfect, 0.5 chance, 0 inverted
  robustness             mean score of harmless rewordings (1.0 ideal); identical copy must score 1.0 (sanity)
  severity correlation   Spearman(severity level, score) over errors; strongly negative = tracks severity, ~0 = blind
  magnitude correlation  Spearman(error size, score) within one perturbation (BI-RADS steps, mm)
"""
import numpy as np, pandas as pd
from scipy.stats import spearmanr

def to_frame(items, scores):
    df = pd.DataFrame([{k: v for k, v in i.items() if k not in ('reference', 'candidate', 'evidence')} for i in items])
    for g, s in scores.items(): df[g] = s
    return df

def _paired_auroc(df, g, err_mask, harm_mask):
    e = df[err_mask].groupby('case_id')[g].apply(np.array); h = df[harm_mask].groupby('case_id')[g].apply(np.array)
    common = e.index.intersection(h.index); vals = []
    for c in common:
        a, b = e[c], h[c]
        vals.append(np.mean(a[:, None] < b[None, :]) + 0.5*np.mean(a[:, None] == b[None, :]))
    return np.array(vals)

def auroc(df, g, err_mask=None, n_boot=200, seed=0):
    err = (df.kind == 'error') if err_mask is None else err_mask
    v = _paired_auroc(df, g, err, df.kind == 'harmless')
    if len(v) == 0: return dict(auroc=None, lo=None, hi=None, n=0)
    rng = np.random.default_rng(seed); bs = [rng.choice(v, len(v)).mean() for _ in range(n_boot)]
    return dict(auroc=float(v.mean()), lo=float(np.percentile(bs, 2.5)), hi=float(np.percentile(bs, 97.5)), n=int(len(v)))

def _rho(x, y):
    if len(set(x)) < 2 or len(set(y)) < 2: return None
    r = spearmanr(x, y)[0]; return None if np.isnan(r) else float(r)

def summarize(df, graders):
    out = {}
    for organ in ['all'] + sorted(df.organ.unique()):
        d = df if organ == 'all' else df[df.organ == organ]
        res = {}
        for g in graders:
            err = d[d.kind == 'error']
            r = dict(discrimination=auroc(d, g),
                     by_severity={int(s): auroc(d, g, d.kind.eq('error') & d.severity.eq(s)) for s in sorted(err.severity.unique())},
                     by_perturbation={p: auroc(d, g, d.kind.eq('error') & d.perturbation.eq(p)) for p in sorted(err.perturbation.unique())},
                     robustness=dict(harmless_mean=float(d[d.kind == 'harmless'][g].mean()),
                                     identical_mean=float(d[d.kind == 'identical'][g].mean()) if (d.kind == 'identical').any() else None),
                     severity_spearman=_rho(err.severity.tolist(), err[g].tolist()),
                     magnitude_spearman={p: _rho(x.magnitude.tolist(), x[g].tolist())
                                         for p, x in err[err.magnitude.notna()].groupby('perturbation')})
            res[g] = r
        out[organ] = res
    return out

def _f(x, p=2): return '—' if x is None else f'{x:.{p}f}'

def to_markdown(summary, graders):
    L = []
    for organ, res in summary.items():
        L += [f'### {organ}', '', '| grader | AUROC (95% CI) | critical-only AUROC | harmless mean | identical mean | severity ρ |', '|---|---|---|---|---|---|']
        for g in graders:
            r = res[g]; d = r['discrimination']; c = r['by_severity'].get(3)
            L.append(f"| {g} | {_f(d['auroc'])} ({_f(d['lo'])}–{_f(d['hi'])}) | {_f(c['auroc']) if c else '—'} | "
                     f"{_f(r['robustness']['harmless_mean'])} | {_f(r['robustness']['identical_mean'])} | {_f(r['severity_spearman'])} |")
        L.append('')
    return '\n'.join(L)
