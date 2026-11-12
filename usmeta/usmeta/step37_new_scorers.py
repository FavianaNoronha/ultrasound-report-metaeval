"""Step 37: RadGraph-F1 (and GREEN where feasible) added to the Step 33 (factorial), Step 34 (metamorphic) and Step 35 (limit of detection) analyses. NEW file; the earlier steps' modules and saved results are imported / read, not changed.
RadGraph-F1 = the official `radgraph` package (0.1.18, RadGraph-XL model from StanfordAIMI/RRG_scorers, CPU) run in the separate venv ~/.venvs/radgraph by `step37_rg_worker.py`; the 'partial' reward level is used as RadGraph-F1 (simple and complete are saved too).
The scores come from local_data/step37/rg_scores_step{33,34,35}.json (git-ignored: Step 34 includes HiSBreast text). Same group bootstrap (1,000, seed 0), same 'under 30 groups' marks, same decision rules as Steps 33 / 34 / 35.
    python3 -m usmeta.step37_new_scorers analyse"""
import os, sys, json, collections, functools, time
import numpy as np
from . import step33_factorial as F, step34_metamorphic as M, step35_lod as L
from .layer0 import auroc_case
from .step10d_analysis import gboot

ROOT = F.ROOT; OUT = os.path.join(ROOT, 'results', 'partA', 'step37_new_scorers'); LOCAL = os.path.join(ROOT, 'local_data', 'step37'); LEVEL = 1       # index of 'partial' in [simple, partial, complete]
NEW = [('radgraph_f1', 'RadGraph-F1 (partial)')]

def rg_scores(step):
    d = json.load(open(os.path.join(LOCAL, f'rg_scores_step{step}.json'))); return {tuple(k.split('|||', 1)): v[LEVEL] for k, v in d.items()}, {tuple(k.split('|||', 1)): v for k, v in d.items()}

# ---------------------------------------------------------------- Step 33
def factorial():
    R = json.load(open(os.path.join(F.OUT, 'results.json'))); blocks = json.load(open(os.path.join(F.OUT, 'test_blocks.json')))['blocks']; S = json.load(open(os.path.join(F.OUT, 'd_scores.json'))); sc, _ = rg_scores(33); res = {}
    jset = {(b['case'], b['c_text'], b['style']) for b in S.get('judge_blocks', [])}; jb = [b for b in blocks if (b['case'], b['c_text'], b['style']) in jset]
    for tag, bl in (('all blocks', blocks), ('judge subset (same blocks as the judge)', jb)):
        vals = F.block_scores(bl, 'radgraph_f1', {'radgraph_f1': sc}, sc, None); res[tag] = {o or 'pooled': F.analyse_scorer(bl, vals, o) for o in (None, 'breast', 'thyroid')}
    return res

# ---------------------------------------------------------------- Step 35
def lod():
    sc, _ = rg_scores(35); rows = L.all_rows(); by = collections.defaultdict(list); out = {}
    for r in rows: by[r['case_id']].append(r)
    rng = np.random.default_rng(0)
    for org, field in (('breast', 'size_mm'), ('breast', 'size_pct'), ('thyroid', 'size_pct'), ('fetal head', 'hc_mm')):
        levels = L.HC_LEVELS if field == 'hc_mm' else L.SIZE_LEVELS; cs = {c: rs for c, rs in by.items() if rs[0]['organ'] == org and any(r['kind'] == 'error' and r['field'] == field for r in rs)}
        per = {lv: [] for lv in levels}; grp = {lv: [] for lv in levels}
        for c, rs in cs.items():
            h = [sc.get((r['reference'], r['candidate'])) for r in rs if r['kind'] == 'matched']; h = [x for x in h if x is not None]
            if not h: continue
            for lv in levels:
                e = [sc.get((r['reference'], r['candidate'])) for r in rs if r['kind'] == 'error' and r['field'] == field and r['level'] == lv]; e = [x for x in e if x is not None]
                if e: per[lv].append(auroc_case(e, h)); grp[lv].append(rs[0]['group_id'])
        if not any(per[lv] for lv in levels): continue
        point = {lv: (float(np.mean(per[lv])) if per[lv] else None) for lv in levels}; ng = {lv: len(set(grp[lv])) for lv in levels}; ci = {lv: (gboot(per[lv], grp[lv]) if per[lv] else None) for lv in levels}
        lodi = L.lod_of(point, levels); allg = sorted({g for lv in levels for g in grp[lv]}); gi = {g: i for i, g in enumerate(allg)}; arrs = {lv: (np.array([gi[g] for g in grp[lv]]), np.array(per[lv])) for lv in levels if per[lv]}; boots = []
        for _ in range(1000):
            counts = np.bincount(rng.integers(0, len(allg), len(allg)), minlength=len(allg)); pt = {}
            for lv, (g_, a_) in arrs.items():
                w = counts[g_]; pt[lv] = float((w * a_).sum() / w.sum()) if w.sum() else None
            boots.append(L.lod_of(pt, levels))
        enc = [(len(levels) if b is None else b) for b in boots]; lo, hi = int(np.percentile(enc, 2.5)), int(np.percentile(enc, 97.5)); lab = lambda i: ('>' + str(levels[-1])) if i >= len(levels) else str(levels[i])
        out[f'radgraph_f1|{org}|{field}'] = dict(levels=levels, auroc=point, auroc_ci=ci, groups=ng, lod=(levels[lodi] if lodi is not None else None), lod_ci=[lab(lo), lab(hi)], nonmonotone=lodi is not None and any((point[levels[j]] is not None and point[levels[j]] < L.THRESH) for j in range(lodi + 1, len(levels))), too_small_levels=[lv for lv in levels if ng[lv] < 30])
    return out

# ---------------------------------------------------------------- Step 34
def metamorphic():
    items = json.load(open(os.path.join(M.LOCAL, 'items.json'))); sc, _ = rg_scores(34); res = {}
    def get(r, t): return sc.get((r, t))
    for sub, only_llm in (('all items', False), ('judge subset (same items as the judge)', True)):
        for st in ('templated', 'hisbreast', 'writer', 'ALL'):
            for rel in M.REL:
                for delta in (M.DELTAS if rel in ('R1', 'R2', 'R3') else (None,)):
                    viol, flat, grp = [], [], []
                    for it in items:
                        if st != 'ALL' and it['set'] != st: continue
                        if only_llm and not it['llm']: continue
                        r, x = it['ref'], it['x']; s0 = get(r, x)
                        if s0 is None: continue
                        vs = it['variants'].get(rel)
                        if not vs: continue
                        if rel in ('R1', 'R2', 'R3'):
                            s1 = get(r, vs[0][1])
                            if s1 is None: continue
                            viol.append(float(abs(s1 - s0) > delta)); grp.append(it['group'])
                        elif rel in ('R4', 'R5'):
                            s1 = get(r, vs[0][1]); sh = get(r, it['variants']['H'][0][1])
                            if s1 is None or sh is None: continue
                            viol.append(float(s1 >= sh)); grp.append(it['group'])
                        else:
                            cd = [s0] + [get(r, t) for k, t in vs if k.startswith('d')]; cu = [s0] + [get(r, t) for k, t in vs if k.startswith('u')]
                            if any(v is None for v in cd + cu) or (len(cd) < 2 and len(cu) < 2): continue
                            viol.append(float(any(b > a_ for ch in (cd, cu) for a_, b in zip(ch, ch[1:])))); flat.append(float(len(set(cd + cu)) == 1)); grp.append(it['group'])
                    res[f'{sub}|{st}|{rel}' + (f'|{delta}' if delta else '')] = dict(n=len(viol), violation=(gboot(viol, grp) if viol else None), too_small=len(viol) < M.MIN_N, **({'flat_share': float(np.mean(flat))} if flat else {}))
    return res

def main():
    os.makedirs(OUT, exist_ok=True); res = {}
    for name, fn in (('factorial', factorial), ('lod', lod), ('metamorphic', metamorphic)):
        try:
            res[name] = fn(); print(name, 'done', flush=True)
        except FileNotFoundError as e: res[name] = dict(error=f'missing RadGraph scores: {e}'); print(name, 'MISSING', e)
    json.dump(res, open(os.path.join(OUT, 'radgraph_results.json'), 'w'), indent=1)

if __name__ == '__main__': main()
