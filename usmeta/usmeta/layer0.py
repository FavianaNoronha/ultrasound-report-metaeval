"""Part A, Layer 0: score bench_v2 with word-overlap / embedding scorers, then analyse.
    python3 -m usmeta.layer0 score  --bench bench_v2.jsonl --out scores_v2_layer0.json
    python3 -m usmeta.layer0 report --bench bench_v2.jsonl --scores scores_v2_layer0.json --out DIR
Scores are computed once per UNIQUE (reference, candidate) pair and cached; 'lazy' = the no-image answer 'No abnormality.' scored against every reference."""
import json, os, sys, time, math, random, argparse, collections
import numpy as np
from scipy.stats import spearmanr
from . import graders

LAZY = 'No abnormality.'
SCORERS = ['bleu', 'rougeL', 'chrf', 'bertscore:roberta-large', 'ratescore']

def pairs_of(rows):
    u = {(r['reference'], r['candidate']) for r in rows} | {(r['reference'], LAZY) for r in rows}
    return sorted(u)

def score(bench, out):
    rows = [json.loads(l) for l in open(bench)]; P = pairs_of(rows)
    done = json.load(open(out)) if os.path.exists(out) else {}
    if done.get('pairs') and done['pairs'] != [list(p) for p in P]: sys.exit('cache does not match bench; use a new --out')
    done['pairs'] = [list(p) for p in P]; done.setdefault('scores', {}); done.setdefault('seconds', {})
    refs, hyps = [p[0] for p in P], [p[1] for p in P]
    for spec in SCORERS:
        g = graders.make(spec)
        if g.name in done['scores']: continue
        t = time.time()
        s = g.batch(refs, hyps) if hasattr(g, 'batch') else [g.score(a, b) for a, b in zip(refs, hyps)]
        done['scores'][g.name] = [float(x) for x in s]; done['seconds'][g.name] = round(time.time() - t, 1)
        json.dump(done, open(out, 'w')); print('scored', g.name, len(s), done['seconds'][g.name], 's', flush=True)

# ---------------------------------------------------------------- analysis
def auroc_case(errs, harm):
    """P(error < harmless) with ties 0.5, over all error x harmless pairs of ONE case"""
    e, h = np.asarray(errs)[:, None], np.asarray(harm)[None, :]
    return float(((e < h) + 0.5 * (e == h)).mean())

def boot(vals, n=1000, seed=0):
    rng = np.random.default_rng(seed); v = np.asarray(vals); m = [v[rng.integers(0, len(v), len(v))].mean() for _ in range(n)]
    return float(v.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))

def mag_value(r):
    f, m = r['field'], r['magnitude']
    if m is None: return None
    if f in ('size_mm', 'size_pct'): return abs(math.log(m))
    return abs(m)      # birads / tirads steps, hc_mm shift in mm, count

def analyse(rows, S, only_split=None):
    idx = {p: i for i, p in enumerate(map(tuple, S['pairs']))}; sc = S['scores']; res = {}
    for name, arr in sc.items():
        get = lambda r, c='candidate': arr[idx[(r['reference'], r[c] if c in r else c)]]
        per = collections.defaultdict(lambda: collections.defaultdict(list))
        for r in rows:
            if only_split and r['split'] != only_split: continue
            per[r['dataset']][r['case_id']].append(r)
        for ds, cases in per.items():
            A, C, Hm, Hs, I, L = [], [], [], collections.defaultdict(list), [], []
            sev, magk = [], collections.defaultdict(lambda: ([], []))
            cat = collections.defaultdict(list); byfield = collections.defaultdict(list)
            for cid, rs in cases.items():
                sco = lambda r: arr[idx[(r['reference'], r['candidate'])]]
                e = [r for r in rs if r['kind'] == 'error']; hp = [r for r in rs if r['kind'] == 'harmless' and r['primary']]
                for r in rs:
                    if r['kind'] == 'identical': I.append(sco(r))
                    if r['kind'] == 'harmless':
                        Hs[r['group']].append(sco(r))
                        if r['primary']: Hm.append(sco(r))
                L.append(arr[idx[(rs[0]['reference'], LAZY)]])
                if e and hp:
                    he = [sco(r) for r in hp]; A.append(auroc_case([sco(r) for r in e], he))
                    c3 = [sco(r) for r in e if r['severity'] == 3]
                    if c3: C.append(auroc_case(c3, he))
                    for c in {r['category'] for r in e}: cat[c].append(auroc_case([sco(r) for r in e if r['category'] == c], he))
                for r in e:
                    sev.append((r['severity'], sco(r)))
                    mv = mag_value(r)
                    if mv is not None: fam = 'size' if r['field'].startswith('size') else r['field']; magk[fam][0].append(mv); magk[fam][1].append(sco(r))
            def rho(a, b):
                if len(set(a)) < 2 or len(set(b)) < 2: return None    # constant input: correlation undefined
                x = float(spearmanr(a, b)[0]); return None if x != x else x
            res.setdefault(ds, {})[name] = dict(
                n_cases=len(cases), auroc=boot(A) if A else None, critical_auroc=boot(C) if C else None,
                harmless_mean=float(np.mean(Hm)) if Hm else None, harmless_groups={g: float(np.mean(v)) for g, v in Hs.items()},
                identical_mean=float(np.mean(I)), identical_min=float(np.min(I)), lazy_mean=float(np.mean(L)),
                severity_rho=rho([a for a, _ in sev], [b for _, b in sev]), magnitude_rho={k: rho(a, b) for k, (a, b) in magk.items()},
                auroc_by_category={c: float(np.mean(v)) for c, v in cat.items()})
    return res

def fmt(x, ci=False):
    if x is None: return '—'
    if isinstance(x, tuple): return f'{x[0]:.2f} ({x[1]:.2f}–{x[2]:.2f})'
    return f'{x:.2f}'

def tables(res):
    out = []
    for ds, d in res.items():
        out += [f'### {ds} (n={next(iter(d.values()))["n_cases"]} cases)', '',
                '| scorer | AUROC (95% CI) | critical-only AUROC | harmless mean | identical mean | lazy "No abnormality." mean | severity ρ | magnitude ρ |', '|---|---|---|---|---|---|---|---|']
        for n, v in d.items():
            mr = ', '.join(f'{k} {fmt(x)}' for k, x in v['magnitude_rho'].items()) or '—'
            out.append(f"| {n} | {fmt(v['auroc'])} | {fmt(v['critical_auroc'][0] if v['critical_auroc'] else None)} | {fmt(v['harmless_mean'])} | {v['identical_mean']:.4f} | {fmt(v['lazy_mean'])} | {fmt(v['severity_rho'])} | {mr} |")
        out.append('')
    return out

def report_md(rows, S):
    res = analyse(rows, S); sp = {k: analyse(rows, S, k) for k in ('dev', 'test')}
    ids = [v['identical_min'] for d in res.values() for v in d.values()]
    md = ['# Step 4: Layer 0 baseline on bench_v2', '',
          'What was run: BLEU, ROUGE-L, chrF (CPU), BERTScore (roberta-large, Apple GPU), RaTEScore (Apple GPU) on every (reference, candidate) pair of bench_v2.jsonl, plus a no-image "lazy" answer (`No abnormality.`) scored against every reference. Scores are per unique pair; analysis is per dataset (never pooled across datasets).', '',
          'How to read: **AUROC** = chance that a planted error scores LOWER than a harmless rewording of the same case (paired per case, averaged over cases; 1.0 perfect, 0.5 chance, 0.0 backwards); 95% CI by bootstrap over cases (1,000). **Critical-only** uses severity-3 errors only. **Harmless mean** = mean score on primary harmless rewordings (should be high). **Identical mean** must be 1.0. **Severity ρ / magnitude ρ** = Spearman correlation of score with provisional severity / error size (negative is good). Magnitude: size = |ln ratio|, birads/tirads = steps, hc_mm = shift in mm.', '',
          f'Gate: lowest identical-copy score over all scorers and datasets = {min(ids):.4f} (must be about 1.0).', '']
    md += tables(res)
    md += ['## AUROC by error category (per dataset; 1.0 perfect)', '']
    for ds, d in res.items():
        cats = sorted({c for v in d.values() for c in v['auroc_by_category']})
        md += [f'**{ds}**', '', '| scorer | ' + ' | '.join(cats) + ' |', '|---|' + '---|' * len(cats)]
        for n, v in d.items(): md.append(f'| {n} | ' + ' | '.join(fmt(v['auroc_by_category'].get(c)) for c in cats) + ' |')
        md.append('')
    md += ['## Secondary harmless groups (mean score; primary=false, not in the AUROC)', '']
    gs = ['negation', 'hedge', 'pad1', 'pad3']
    for ds, d in res.items():
        md += [f'**{ds}**', '', '| scorer | ' + ' | '.join(gs) + ' |', '|---|' + '---|' * len(gs)]
        for n, v in d.items(): md.append(f'| {n} | ' + ' | '.join(fmt(v['harmless_groups'].get(g)) for g in gs) + ' |')
        md.append('')
    return res, sp, '\n'.join(md)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd'); ap.add_argument('--bench', default='bench_v2.jsonl'); ap.add_argument('--scores', default='scores_v2_layer0.json')
    ap.add_argument('--out', default='scores_v2_layer0.json'); a = ap.parse_args()
    if a.cmd == 'score': score(a.bench, a.out)
    if a.cmd == 'report':
        rows = [json.loads(l) for l in open(a.bench)]; S = json.load(open(a.scores)); res, sp, md = report_md(rows, S)
        os.makedirs(a.out, exist_ok=True); open(os.path.join(a.out, 'body.md'), 'w').write(md)
        json.dump(dict(all=res, dev=sp['dev'], test=sp['test']), open(os.path.join(a.out, 'results_partA_layer0.json'), 'w'), indent=1)
