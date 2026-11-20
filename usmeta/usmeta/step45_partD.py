"""Step 45, Part D: claim-by-claim Gemma-2-9B-it judge (two prompt variants c1 / c2) on a seeded sample of the Step 44 judge subset. NEW file; replies from step45_gemma (cached under .llm_cache), saved Step 44 holistic judge scores for the same pairs.
Score = 1 - (candidate claims not supported + reference facts omitted) / (candidate claims + omitted). Per variant, the flag threshold is fixed on the VAL sample (largest observed score with harmless rewordings flagged <= 5.6%) and applied to the TEST sample: catch of planted errors, harmless flagged, identical copies flagged; flag agreement between the variants.
PASS rule (both variants): catch >= 71.3% with harmless flagged <= 5.6%, and variant flag agreement >= 90%.
    python3 -m usmeta.step45_partD"""
import os, sys, json, collections, time, platform, subprocess
import numpy as np
from . import step45_gemma as GM, step45_freetext as FT
from .step10d_analysis import gboot

OUT = os.path.join(FT.ROOT, 'results', 'partA', 'step45_improve_scorers', 'partD'); P = lambda f: os.path.join(OUT, f); os.makedirs(OUT, exist_ok=True); MAXH = 0.056; CATCH = 0.713; AGREE = 0.90

def load(v):
    d = {}
    for l in open(GM.P(f'd_{v}.jsonl')): r = json.loads(l); d[r['id']] = r
    return d

def thr(rows, key):
    H = [r for r in rows if r['kind'] == 'harmless']; best = None
    for t in sorted({r[key] for r in rows}):
        if np.mean([r[key] <= t for r in H]) <= MAXH: best = t
    return best

def stats(rows, key, t):
    k = np.array([r['kind'] for r in rows]); g = np.array([r['group'] for r in rows]); f = np.array([float(r[key] <= t) for r in rows]); out = {}
    for nm, m in (('catch', k == 'error'), ('harmless_flagged', k == 'harmless'), ('identical_flagged', k == 'identical')):
        out[nm] = gboot(f[m].tolist(), g[m].tolist()) if m.sum() else None; out[nm + '_n'] = int(m.sum())
    return out

def main():
    D = {v: load(v) for v in GM.VARIANTS}; ids = sorted(set(D['c1']) & set(D['c2'])); rows = []
    for i in ids:
        a, b = D['c1'][i], D['c2'][i]
        if a['result'] is None or b['result'] is None: continue
        rows.append(dict(id=i, set=a['set'], kind=a['kind'], organ=a['organ'], group=a['group'], c1=a['result']['score'], c2=b['result']['score'], holistic=a['holistic']))
    miss = len(ids) - len(rows); val = [r for r in rows if r['set'] == 'val']; te = [r for r in rows if r['set'] == 'test']; res = dict(pairs=dict(val=len(val), test=len(te), unparsed=miss, planned=len(GM.d_pairs())), variants={})
    st = json.load(open(GM.P('d_status.json'))) if os.path.exists(GM.P('d_status.json')) else {}; res['status'] = st
    flags = {}
    for v in ('c1', 'c2'):
        t = thr(val, v); res['variants'][v] = dict(threshold=t, val=dict(n_harmless=sum(r['kind'] == 'harmless' for r in val), n_error=sum(r['kind'] == 'error' for r in val))) if t is not None else dict(threshold=None)
        if t is None: continue
        res['variants'][v]['val'].update(stats(val, v, t)); res['variants'][v]['test'] = stats(te, v, t); flags[v] = np.array([float(r[v] <= t) for r in te])
    # holistic judge (Step 44) on the same sampled pairs, at its val threshold 0.4
    hol = {s: [r for r in rows if r['set'] == s] for s in ('val', 'test')}; res['holistic_step44_same_pairs'] = dict(threshold=0.4, test=stats(hol['test'], 'holistic', 0.4))
    if len(flags) == 2:
        g = np.array([r['group'] for r in te]); kind = np.array([r['kind'] for r in te]); ag = (flags['c1'] == flags['c2']).astype(float)
        res['agreement'] = dict(all=gboot(ag.tolist(), g.tolist()), errors=gboot(ag[kind == 'error'].tolist(), g[kind == 'error'].tolist()), harmless=gboot(ag[kind == 'harmless'].tolist(), g[kind == 'harmless'].tolist()))
        ok = {v: bool(res['variants'][v]['test']['catch'][0] >= CATCH and res['variants'][v]['test']['harmless_flagged'][0] <= MAXH) for v in ('c1', 'c2')}
        res['pass'] = dict(c1_catch_and_harmless=ok['c1'], c2_catch_and_harmless=ok['c2'], agreement_ge_90=bool(res['agreement']['all'][0] >= AGREE), passed=bool(all(ok.values()) and res['agreement']['all'][0] >= AGREE and not st.get('stopped_by_cap')), incomplete=bool(st.get('stopped_by_cap')))
    json.dump(res, open(P('results.json'), 'w'), indent=1); print(json.dumps(res.get('pass'))); print(json.dumps({v: {k: res['variants'][v].get('test', {}).get(k) for k in ('catch', 'harmless_flagged', 'identical_flagged')} for v in res['variants']}, indent=0)[:900]); print(res.get('agreement'))

if __name__ == '__main__': main()
