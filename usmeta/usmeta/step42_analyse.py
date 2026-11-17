"""Step 42 analysis: GREEN (4-bit) scores -> factorial (as Step 33) and limit of detection (as Step 35), results.md, results.json, run_info.json. NEW file; the Step 33 / 35 analysis code is imported unchanged.
Inputs in local_data/step42 (git-ignored): green_pairs.jsonl, pair_key.json, green_scores.jsonl, n_chosen.json, dev_timing.json, colab_env.json (back from Colab).
    python3 -m usmeta.step42_analyse [--dir local_data/step42] [--out results/partA/step42_green]"""
import os, sys, json, collections, argparse, platform, time, subprocess
import numpy as np
from . import step33_factorial as F, step35_lod as L
from .layer0 import auroc_case
from .step10d_analysis import gboot

ROOT = F.ROOT; MIN_G = 30

def load(d):
    pairs = {json.loads(l)['id']: json.loads(l) for l in open(os.path.join(d, 'green_pairs.jsonl'))}; key = json.load(open(os.path.join(d, 'pair_key.json'))); nc = json.load(open(os.path.join(d, 'n_chosen.json')))
    sc = {}; unparsed = 0; rows = 0
    for l in open(os.path.join(d, 'green_scores.jsonl')):
        r = json.loads(l); rows += 1
        if r['green_score'] is None: unparsed += 1
        else: sc[r['id']] = float(r['green_score'])
    return pairs, key, nc, sc, dict(scored=rows, unparsed=unparsed)

def complete_units(key, nc, scored_ids):
    """units of the chosen prefix whose pairs were all scored (parsed or not)"""
    chosen = set(nc['units']); by = collections.defaultdict(list)
    for pid, k in key.items():
        if k['unit'] in chosen: by[k['unit']].append(pid)
    return {u: p for u, p in by.items() if all(x in scored_ids for x in p)}

def factorial(pairs, key, units, sc):
    blocks = []; S = {}
    for u, pids in units.items():
        ks = [key[p] for p in pids]
        if ks[0]['type'] != 'F': continue
        r = {(k['role'], k['k']): p for p, k in zip(pids, ks)}; ref = pairs[pids[0]]['reference']; a = [pairs[r[('a', str(i))]]['candidate'] for i in (0, 1)]; k0 = ks[0]
        for e in range(3):
            for st in ('terse', 'long'):
                blocks.append(dict(case=k0['case'], group=k0['group'], organ=k0['organ'], dataset=k0['dataset'], style=st, ref=ref, a_texts=a, b_text=pairs[r[('b', st)]]['candidate'], c_text=pairs[r[('c', str(e))]]['candidate'], d_text=pairs[r[('d', f'{e}|{st}')]]['candidate'], field=None))
    for p, s in sc.items(): S[(pairs[p]['reference'], pairs[p]['candidate'])] = s
    out = {}
    for tag, org in (('pooled', None), ('breast', 'breast'), ('thyroid', 'thyroid')):
        vals = F.block_scores(blocks, 'green', {'green': S}, S, None); out[tag] = F.analyse_scorer(blocks, vals, org)
    kept = sum(1 for v in F.block_scores(blocks, 'green', {'green': S}, S, None) if v is not None)
    return out, dict(blocks_built=len(blocks), blocks_complete=kept, f_units=sum(1 for u, p in units.items() if key[p[0]]['type'] == 'F'))

def lod(pairs, key, units, sc):
    rng = np.random.default_rng(0); out = {}; cells = collections.defaultdict(list)
    for u, pids in units.items():
        k0 = key[pids[0]]
        if k0['type'] != 'L': continue
        m = [sc.get(p) for p in pids if key[p]['role'] == 'm' and sc.get(p) is not None]; errs = collections.defaultdict(list)
        for p in pids:
            if key[p]['role'] == 'e' and sc.get(p) is not None: errs[float(key[p]['k'].split('|')[0])].append(sc[p])
        cells[k0['cell']].append((k0['group'], m, errs))
    for cell, units_ in cells.items():
        org, field = cell.split('|'); levels = L.HC_LEVELS if field == 'hc_mm' else L.SIZE_LEVELS; per = {lv: [] for lv in levels}; grp = {lv: [] for lv in levels}
        for g, m, errs in units_:
            if not m: continue
            for lv in levels:
                e = errs.get(float(lv))
                if e: per[lv].append(auroc_case(e, m)); grp[lv].append(g)
        if not any(per[lv] for lv in levels): continue
        point = {lv: (float(np.mean(per[lv])) if per[lv] else None) for lv in levels}; ng = {lv: len(set(grp[lv])) for lv in levels}; ci = {lv: (gboot(per[lv], grp[lv]) if per[lv] else None) for lv in levels}
        lodi = L.lod_of(point, levels); allg = sorted({g for lv in levels for g in grp[lv]}); gi = {g: i for i, g in enumerate(allg)}; arrs = {lv: (np.array([gi[g] for g in grp[lv]]), np.array(per[lv])) for lv in levels if per[lv]}; boots = []
        for _ in range(1000):
            counts = np.bincount(rng.integers(0, len(allg), len(allg)), minlength=len(allg)); pt = {}
            for lv, (g_, a_) in arrs.items():
                w = counts[g_]; pt[lv] = float((w * a_).sum() / w.sum()) if w.sum() else None
            boots.append(L.lod_of(pt, levels))
        enc = [(len(levels) if b is None else b) for b in boots]; lo, hi = int(np.percentile(enc, 2.5)), int(np.percentile(enc, 97.5)); lab = lambda i: ('>' + str(levels[-1])) if i >= len(levels) else str(levels[i])
        out[cell] = dict(levels=levels, auroc=point, auroc_ci=ci, groups=ng, units=len(units_), lod=(levels[lodi] if lodi is not None else None), lod_ci=[lab(lo), lab(hi)], too_small_levels=[lv for lv in levels if ng[lv] < MIN_G], max_groups=max(ng.values()))
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--dir', default=os.path.join(ROOT, 'local_data', 'step42')); ap.add_argument('--out', default=os.path.join(ROOT, 'results', 'partA', 'step42_green')); a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    pairs, key, nc, sc, cnt = load(a.dir); scored_ids = {json.loads(l)['id'] for l in open(os.path.join(a.dir, 'green_scores.jsonl'))}; units = complete_units(key, nc, scored_ids)
    fa, fb = factorial(pairs, key, units, sc); lo = lod(pairs, key, units, sc)
    res = dict(factorial=fa, factorial_counts=fb, lod=lo, counts=dict(cnt, units_chosen=nc['n_units'], pairs_chosen=nc['n_pairs'], units_complete=len(units), seconds_per_pair_dev=nc['seconds_per_pair_dev']), n_chosen={k: v for k, v in nc.items() if k != 'units'})
    for f in ('dev_timing.json', 'colab_env.json'):
        if os.path.exists(os.path.join(a.dir, f)): res[f.split('.')[0]] = json.load(open(os.path.join(a.dir, f)))
    json.dump(res, open(os.path.join(a.out, 'results.json'), 'w'), indent=1); print('saved results.json'); return res

if __name__ == '__main__': main()
