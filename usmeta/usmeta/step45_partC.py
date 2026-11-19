"""Step 45, Part C: deterministic number checker on set A. NEW file; step45_numchecker (parser and score), step45_freetext (set A), step35_lod.lod_of and layer0.auroc_case are imported unchanged.
Tolerances (relative size, absolute head circumference in mm) are fixed on the dev/val part of set A: the smallest pair of grid values for which at most 2% of the harmless free-text rewordings are flagged (flag = score < 1). Then ONE evaluation on the test part:
harmless flagged share, catch of the planted-error twins, and the limit of detection as in Step 35 (smallest planted size / head-circumference change with AUROC >= 0.80 against the matched harmless rewordings of the same case; group bootstrap 1,000, seed 0).
    python3 -m usmeta.step45_partC tune | test"""
import os, sys, json, collections, argparse
import numpy as np
from . import step45_numchecker as NC, step45_freetext as FT, step35_lod as L35
from .layer0 import auroc_case
from .step10d_analysis import gboot

OUT = os.path.join(FT.ROOT, 'results', 'partA', 'step45_improve_scorers', 'partC'); P = lambda f: os.path.join(OUT, f); os.makedirs(OUT, exist_ok=True)
REL_GRID = [0.0, 0.005, 0.01, 0.02, 0.03, 0.05]; HC_GRID = [0.0, 0.05, 0.1, 0.25, 0.5]; MAXH = 0.02; MIN_G = 30
SIZE_LEVELS = [0.05, 0.10, 0.25, 1.0]; HC_LEVELS = [1, 2, 5, 10]

def load():
    A = json.load(open(FT.P('set_A.json'))); return A['cases'], A['lod']

def harmless_rows(cases, which):
    out = []
    for cid, c in cases.items():
        if c['set'] != which: continue
        for r in c['true_reports']: out.append(dict(case_id=cid, organ=c['organ'], group=c['group'], ref=c['reference'], cand=r['text']))
    return out

def cmd_tune(a):
    cases, _ = load(); H = harmless_rows(cases, 'devval'); res = []
    for tr in REL_GRID:
        for th in HC_GRID:
            fl = [NC.score(h['ref'], h['cand'], h['organ'], tr, th) < 1.0 for h in H]; res.append(dict(tol_rel=tr, tol_hc=th, harmless_flagged=float(np.mean(fl))))
    ok = [r for r in res if r['harmless_flagged'] <= MAXH]; chosen = min(ok, key=lambda r: (r['tol_rel'] + r['tol_hc'] / 10.0)) if ok else min(res, key=lambda r: r['harmless_flagged'])
    # where the harmless rewordings are flagged at the chosen tolerance (parse failures / count / side / category), for the write-up
    why = collections.Counter(); ex = []
    for h in H:
        d = NC.compare(h['ref'], h['cand'], h['organ'])
        if NC.score(h['ref'], h['cand'], h['organ'], chosen['tol_rel'], chosen['tol_hc']) < 1.0:
            for k, v in d.items():
                if v not in (None, False, 0.0) and not (k.endswith('_rel') and v <= chosen['tol_rel']) and not (k == 'hc_abs_mm' and v <= chosen['tol_hc']): why[k] += 1
            if len(ex) < 12: ex.append(dict(ref=h['ref'][:140], cand=h['cand'][:200], dev={k: v for k, v in d.items() if v not in (None, False)}))
    json.dump(dict(grid=res, chosen=chosen, n_harmless=len(H), met_target=bool(ok), flagged_by=dict(why), examples=ex, target_max_harmless_flagged=MAXH), open(P('tuning.json'), 'w'), indent=1); print(json.dumps(dict(chosen=chosen, n=len(H), met=bool(ok), why=dict(why)), indent=0))

def cmd_test(a):
    cases, lod = load(); tune = json.load(open(P('tuning.json'))); tr, th = tune['chosen']['tol_rel'], tune['chosen']['tol_hc']; sc = lambda ref, cand, o: NC.score(ref, cand, o, tr, th)
    H = harmless_rows(cases, 'test'); hf = [float(sc(h['ref'], h['cand'], h['organ']) < 1.0) for h in H]; res = dict(tolerance=dict(rel=tr, hc_mm=th), harmless=dict(reports=len(H), groups=len({h['group'] for h in H}), flagged=gboot(hf, [h['group'] for h in H])))
    for o in ('breast', 'thyroid', 'fetal'):
        s = [(float(sc(h['ref'], h['cand'], h['organ']) < 1.0), h['group']) for h in H if h['organ'] == o]
        if s: res['harmless'][o] = dict(reports=len(s), flagged=gboot([x for x, _ in s], [g for _, g in s]))
    tw = []
    for cid, c in cases.items():
        if c['set'] == 'test' and c['twin_report'] and c['true_reports']: tw.append(dict(case_id=cid, organ=c['organ'], group=c['group'], field=c['twin_field'], flag=float(sc(c['reference'], c['twin_report']['text'], c['organ']) < 1.0)))
    res['twin_catch'] = dict(all=dict(n=len(tw), catch=gboot([t['flag'] for t in tw], [t['group'] for t in tw]) if tw else None), by_field={})
    for fld in sorted({t['field'] for t in tw}):
        s = [t for t in tw if t['field'] == fld]; res['twin_catch']['by_field'][fld] = dict(n=len(s), catch=float(np.mean([t['flag'] for t in s])), groups=len({t['group'] for t in s}))
    # limit of detection
    by_case = {cid: [h for h in H if h['case_id'] == cid] for cid in cases}; res['lod'] = {}
    for (organ, grp), levels in ((('breast', 'size'), SIZE_LEVELS), (('thyroid', 'size'), SIZE_LEVELS), (('fetal', 'hc_mm'), HC_LEVELS)):
        per = {lv: [] for lv in levels}; grp_of = {lv: [] for lv in levels}
        for r in lod:
            if r['organ'] != organ or (r['field'] == 'hc_mm') != (grp == 'hc_mm') or r['level'] not in levels: continue
            hs = by_case.get(r['case_id'], [])
            if not hs: continue
            e = sc(cases[r['case_id']]['reference'], r['text'], organ); h = [sc(x['ref'], x['cand'], organ) for x in hs]; per[r['level']].append(auroc_case([e], h)); grp_of[r['level']].append(cases[r['case_id']]['group'])
        point = {lv: (float(np.mean(per[lv])) if per[lv] else None) for lv in levels}; ng = {lv: len(set(grp_of[lv])) for lv in levels}; ci = {lv: (gboot(per[lv], grp_of[lv]) if per[lv] else None) for lv in levels}
        i = L35.lod_of(point, levels); rng = np.random.default_rng(0); allg = sorted({g for lv in levels for g in grp_of[lv]}); gi = {g: k for k, g in enumerate(allg)}; arrs = {lv: (np.array([gi[g] for g in grp_of[lv]]), np.array(per[lv])) for lv in levels if per[lv]}; boots = []
        for _ in range(1000):
            counts = np.bincount(rng.integers(0, max(1, len(allg)), max(1, len(allg))), minlength=max(1, len(allg))); pt = {}
            for lv, (g_, a_) in arrs.items(): w = counts[g_]; pt[lv] = float((w * a_).sum() / w.sum()) if w.sum() else None
            boots.append(L35.lod_of(pt, levels))
        enc = [(len(levels) if b is None else b) for b in boots]; lo, hi = int(np.percentile(enc, 2.5)), int(np.percentile(enc, 97.5)); lab = lambda k: ('>' + str(levels[-1])) if k >= len(levels) else str(levels[k])
        res['lod'][f'{organ}|{grp}'] = dict(levels=levels, auroc=point, auroc_ci=ci, cases=len(set(grp_of[levels[0]]) | set(g for lv in levels for g in grp_of[lv])), groups_per_level=ng, lod=(levels[i] if i is not None else None), lod_ci=[lab(lo), lab(hi)], too_small=[lv for lv in levels if ng[lv] < MIN_G])
    flagged = res['harmless']['flagged'][0]; size_ok = all(res['lod'][k]['lod'] is not None and res['lod'][k]['lod'] <= 0.05 for k in ('breast|size', 'thyroid|size') if k in res['lod']); hc_ok = res['lod'].get('fetal|hc_mm', {}).get('lod') is not None and res['lod']['fetal|hc_mm']['lod'] <= 1
    res['pass'] = dict(size_lod_le_5pct=bool(size_ok), hc_lod_le_1mm=bool(hc_ok), harmless_flagged_le_2pct=bool(flagged <= 0.02), passed=bool(size_ok and hc_ok and flagged <= 0.02))
    json.dump(res, open(P('results.json'), 'w'), indent=1); print(json.dumps(res['pass'])); print(json.dumps({k: (v['lod'], v['lod_ci']) for k, v in res['lod'].items()})); print('harmless flagged', res['harmless']['flagged'])

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd'); a = ap.parse_args(); {'tune': cmd_tune, 'test': cmd_test}[a.cmd](a)
