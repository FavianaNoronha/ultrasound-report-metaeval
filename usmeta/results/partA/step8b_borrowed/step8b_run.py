"""Step 8b runner: thresholds from VAL (judge: dev+val rows of the existing dev-era judge run), numbers on TEST. New file; frozen code untouched."""
import json, sys, collections
import numpy as np
from . import step8b, layer0b, layer1, splits

def merged_scores(bench, l0, l1):
    rows = [json.loads(l) for l in open(bench)]; S0 = json.load(open(l0)); S1 = json.load(open(l1)); assert layer0b.check_pairs(rows, S0) and S1['pairs'] == S0['pairs']
    S = {'pairs': S0['pairs'], 'scores': dict(S0['scores'])}; S['scores']['finding_f1'] = S1['scores']['finding_f1']; return rows, S

def thresholds(rows, S, names):
    idx = {tuple(p): i for i, p in enumerate(S['pairs'])}; out = {}
    for n in names:
        for ds in sorted({r['dataset'] for r in rows}):
            e = [S['scores'][n][idx[(r['reference'], r['candidate'])]] for r in rows if r['dataset'] == ds and r['kind'] == 'error']
            if e: out[(ds, n)] = step8b.threshold(e)
    return out

def case_vs_error(rows, S, thr, n):
    """sentence_check sample has 2 planted errors per case: share of cases where at least one is flagged vs share of errors flagged"""
    idx = {tuple(p): i for i, p in enumerate(S['pairs'])}; by = collections.defaultdict(list)
    for r in rows:
        if r['kind'] == 'error' and (r['dataset'], n) in thr: by[(r['dataset'], r['case_id'])].append(S['scores'][n][idx[(r['reference'], r['candidate'])]] <= thr[(r['dataset'], n)])
    out = {}
    for ds in {k[0] for k in by}:
        cs = [v for k, v in by.items() if k[0] == ds and len(v) >= 2]; er = [x for k, v in by.items() if k[0] == ds for x in v]
        out[ds] = dict(cases=len(cs), report_level_any=float(np.mean([any(v) for v in cs])) if cs else None, error_level=float(np.mean(er)), all_caught=float(np.mean([all(v) for v in cs])) if cs else None)
    return out
