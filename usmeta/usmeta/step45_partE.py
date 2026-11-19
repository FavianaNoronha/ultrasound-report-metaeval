"""Step 45, Part E: small learned scorer. NEW file; saved Step 5-10 scorer outputs, step19_pairs loaders, layer0 scorers (for set A pairs) and step45_numchecker are imported unchanged.
Features per (reference, candidate) pair: BLEU, ROUGE-L, chrF, BERTScore (roberta-large), RaTEScore + diff features (numbers removed / added, negation-word change, side mismatch, category mismatch, pathology-word mismatch, relative size / head-circumference deviation, count mismatch).
Models: logistic regression and gradient boosting (sklearn). Trained on the DEV split of the templated benchmark (label 1 = planted error, 0 = harmless rewording of any type: small, matched, large, other), hyper-parameters tuned on VAL (mean per-case AUROC), group-disjoint by the locked splits.
Test: per-case AUROC (error vs harmless, ties 0.5) on (i) the templated test split and (ii) set A test (writer-made free text, planted-error twins vs the case's harmless free-text reports), group bootstrap 1,000 / seed 0; the paired difference to the best single existing text scorer on set A test.
    python3 -m usmeta.step45_partE features | train | test"""
import os, sys, json, re, collections, argparse, time
import numpy as np
from . import step19_pairs as P19, step45_freetext as FT, step45_numchecker as NC, splits, graders
from .layer0 import auroc_case
from .step10d_analysis import gboot

ROOT = FT.ROOT; OUT = os.path.join(ROOT, 'results', 'partA', 'step45_improve_scorers', 'partE'); P = lambda f: os.path.join(OUT, f); os.makedirs(OUT, exist_ok=True)
SC = ['bleu', 'rougeL', 'chrf', 'bertscore[roberta-large]', 'ratescore']; HT = ('small', 'matched', 'large')
NUMRE = re.compile(r'\d+(?:\.\d+)?'); NEG = re.compile(r'\b(no|not|without|absent|none|non)\b'); SIDE = re.compile(r'\b(left|right)\b'); PATH = re.compile(r'\b(benign|malignant|normal)\b')

def diff_features(ref, cand, organ):
    r, c = ref.lower(), cand.lower(); nr, nc = collections.Counter(NUMRE.findall(r)), collections.Counter(NUMRE.findall(c)); d = NC.compare(ref, cand, organ)
    return dict(n_removed=sum((nr - nc).values()), n_added=sum((nc - nr).values()), neg_change=abs(len(NEG.findall(r)) - len(NEG.findall(c))), side_mismatch=float(set(SIDE.findall(r)) != set(SIDE.findall(c)) and bool(SIDE.findall(r) or SIDE.findall(c))),
                path_mismatch=float(set(PATH.findall(r)) != set(PATH.findall(c))), size_rel=max([v for k, v in d.items() if k.endswith('_rel') and v is not None] + [0.0]), hc_abs=float(d.get('hc_abs_mm') or 0.0),
                count_mismatch=float(bool(d.get('count_mismatch'))), cat_mismatch=float(bool(d.get('birads_mismatch') or d.get('tirads_mismatch'))))
DF = ['n_removed', 'n_added', 'neg_change', 'side_mismatch', 'path_mismatch', 'size_rel', 'hc_abs', 'count_mismatch', 'cat_mismatch']

def vec(scores, ref, cand, organ):
    f = diff_features(ref, cand, organ); return [scores[k] for k in SC] + [f[k] for k in DF]

# ---------------------------------------------------------------- templated data
def templated(split):
    rows, sc, _ = P19.load(split); keep = [r for r in rows if r['kind'] == 'error' or (r['kind'] == 'harmless' and r.get('harmless_type') is not None)]; X, y, meta = [], [], []
    for r in keep:
        k = (r['reference'], r['candidate'])
        if any(k not in sc[n] for n in SC): continue
        X.append(vec({n: sc[n][k] for n in SC}, r['reference'], r['candidate'], r['organ'])); y.append(1 if r['kind'] == 'error' else 0)
        meta.append(dict(case=r['case_id'], group=f"{r['dataset']}:{r['group_id']}", organ=r['organ'], kind=r['kind'], ht=r.get('harmless_type'), sc={n: sc[n][k] for n in SC}))
    return np.array(X, float), np.array(y), meta

def dev_templated():
    """dev split: bench_v2d.jsonl rows whose case is in the locked dev split; scores from scores_v2d_layer0.json"""
    sp = {}
    for l in open(os.path.join(ROOT, 'splits.jsonl')): r = json.loads(l); sp[r['case_id']] = r['split']
    S = P19.scores_of(os.path.join(ROOT, 'scores_v2d_layer0.json')); X, y, meta = [], [], []
    for l in open(os.path.join(ROOT, 'bench_v2d.jsonl')):
        r = json.loads(l)
        if sp.get(r['case_id']) != 'dev' or not (r['kind'] == 'error' or (r['kind'] == 'harmless' and r.get('harmless_type') is not None)): continue
        k = (r['reference'], r['candidate'])
        if any(k not in S[n] for n in SC): continue
        X.append(vec({n: S[n][k] for n in SC}, r['reference'], r['candidate'], r['organ'])); y.append(1 if r['kind'] == 'error' else 0)
        meta.append(dict(case=r['case_id'], group=f"{r['dataset']}:{r['group_id']}", organ=r['organ'], kind=r['kind'], ht=r.get('harmless_type'), sc={n: S[n][k] for n in SC}))
    return np.array(X, float), np.array(y), meta

def case_auroc(meta, score, lower_is_error=True):
    by = collections.defaultdict(lambda: ([], [])); grp = {}
    for m, s in zip(meta, score):
        if m['kind'] == 'error': by[m['case']][0].append(s)
        elif m['ht'] in HT: by[m['case']][1].append(s)
        grp[m['case']] = m['group']
    v, g = [], []
    for cid, (e, h) in by.items():
        if e and h: v.append(auroc_case(e, h)); g.append(grp[cid])
    return v, g

def fit_models(Xd, yd, devval_meta_X, devval_meta):
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import HistGradientBoostingClassifier
    out = {}; Xv, yv, mv = devval_meta_X
    cand = {'logreg': [(C, make_pipeline(StandardScaler(), LogisticRegression(C=C, max_iter=2000))) for C in (0.01, 0.1, 1.0, 10.0)],
            'gboost': [((d, lr), HistGradientBoostingClassifier(max_depth=d, learning_rate=lr, max_iter=200, random_state=0)) for d in (2, 3, 5) for lr in (0.05, 0.1)]}
    for name, lst in cand.items():
        best = None
        for hp, m in lst:
            m.fit(Xd, yd); s = 1 - m.predict_proba(Xv)[:, 1]; v, g = case_auroc(mv, s); a = float(np.mean(v))
            if best is None or a > best[0]: best = (a, hp, m)
        out[name] = dict(val_auroc=best[0], hp=best[1], model=best[2])
    return out

# ---------------------------------------------------------------- set A
def setA_pairs(which):
    A = json.load(open(FT.P('set_A.json')))['cases']; out = []
    for cid, c in sorted(A.items()):
        if c['set'] != which or not c['true_reports'] or not c['twin_report']: continue
        for r in c['true_reports']: out.append(dict(case=cid, group=c['group'], organ=c['organ'], kind='harmless', ht='small', ref=c['reference'], cand=r['text']))
        out.append(dict(case=cid, group=c['group'], organ=c['organ'], kind='error', ht=None, ref=c['reference'], cand=c['twin_report']['text']))
    return out

def score_setA(pairs, name):
    f = P(f'setA_scores_{name}.json')
    if os.path.exists(f): return json.load(open(f))
    refs = [p['ref'] for p in pairs]; hyps = [p['cand'] for p in pairs]; res = {}
    for spec, key in (('bleu', 'bleu'), ('rougeL', 'rougeL'), ('chrf', 'chrf'), ('bertscore:roberta-large', 'bertscore[roberta-large]'), ('ratescore', 'ratescore')):
        g = graders.make(spec); s = g.batch(refs, hyps) if hasattr(g, 'batch') else [g.score(a, b) for a, b in zip(refs, hyps)]; res[key] = [float(x) for x in s]; print('scored', key, len(s), flush=True)
    json.dump(res, open(f, 'w')); return res

def setA_matrix(pairs, sc):
    X = np.array([vec({n: sc[n][i] for n in SC}, p['ref'], p['cand'], p['organ']) for i, p in enumerate(pairs)], float)
    meta = [dict(case=p['case'], group=p['group'], organ=p['organ'], kind=p['kind'], ht=p['ht']) for p in pairs]; return X, meta

def paired(v_a, v_b, groups):
    d = [a - b for a, b in zip(v_a, v_b)]; return gboot(d, groups)

def cmd_features(a):
    for which in ('devval', 'test'):
        pairs = setA_pairs(which); sc = score_setA(pairs, which); print(which, len(pairs), 'pairs scored')

def cmd_train(a):
    Xd, yd, md = dev_templated(); Xv, yv, mv = templated('val'); fit = fit_models(Xd, yd, (Xv, yv, mv), mv)
    # set A dev/val is used only to REPORT how the templated-trained models transfer (not for tuning)
    pairs = setA_pairs('devval'); sc = score_setA(pairs, 'devval'); XA, mA = setA_matrix(pairs, sc); res = dict(n_dev_pairs=int(len(yd)), n_val_pairs=int(len(yv)), models={}, features=SC + DF)
    for name, d in fit.items():
        vA, gA = case_auroc(mA, 1 - d['model'].predict_proba(XA)[:, 1]); res['models'][name] = dict(val_auroc_templated=d['val_auroc'], hp=str(d['hp']), devval_setA_auroc=float(np.mean(vA)), setA_cases=len(vA))
    for n in SC:
        vA, gA = case_auroc(mA, sc[n]); res['models'].setdefault('single_scorers_setA_devval', {})[n] = float(np.mean(vA))
    import pickle; pickle.dump({k: v['model'] for k, v in fit.items()}, open(P('models.pkl'), 'wb')); json.dump(res, open(P('train.json'), 'w'), indent=1); print(json.dumps(res, indent=1))

def cmd_test(a):
    import pickle
    models = pickle.load(open(P('models.pkl'), 'rb')); splits.load('test', script='usmeta.step45_partE'); Xt, yt, mt = templated('test'); res = dict(templated={}, setA={})
    S_t = {n: [m['sc'][n] for m in mt] for n in SC}
    for name, mdl in models.items():
        v, g = case_auroc(mt, 1 - mdl.predict_proba(Xt)[:, 1]); res['templated'][name] = dict(cases=len(v), groups=len(set(g)), auroc=gboot(v, g))
    for n in SC: v, g = case_auroc(mt, S_t[n]); res['templated'][n] = dict(cases=len(v), groups=len(set(g)), auroc=gboot(v, g))
    pairs = setA_pairs('test'); sc = score_setA(pairs, 'test'); XA, mA = setA_matrix(pairs, sc); per = {}
    for name, mdl in models.items(): per[name] = case_auroc(mA, 1 - mdl.predict_proba(XA)[:, 1])
    for n in SC: per[n] = case_auroc(mA, sc[n])
    for k, (v, g) in per.items(): res['setA'][k] = dict(cases=len(v), groups=len(set(g)), auroc=gboot(v, g))
    best = max(SC, key=lambda n: np.mean(per[n][0])); res['setA_best_single'] = best; res['setA_paired'] = {}
    for name in models: res['setA_paired'][name] = dict(vs=best, diff=paired(per[name][0], per[best][0], per[name][1]))
    res['pass'] = {name: dict(auroc_ge_best_plus_0_05=bool(res['setA'][name]['auroc'][0] >= res['setA'][best]['auroc'][0] + 0.05), ci_excludes_0=bool(res['setA_paired'][name]['diff'][1] > 0)) for name in models}
    for name in models: res['pass'][name]['passed'] = res['pass'][name]['auroc_ge_best_plus_0_05'] and res['pass'][name]['ci_excludes_0']
    json.dump(res, open(P('results.json'), 'w'), indent=1); print(json.dumps(res['pass'])); print({k: (round(v['auroc'][0], 3), round(v['auroc'][1], 3), round(v['auroc'][2], 3)) for k, v in res['setA'].items()}); print({k: round(v['auroc'][0], 3) for k, v in res['templated'].items()})

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd'); a = ap.parse_args(); {'features': cmd_features, 'train': cmd_train, 'test': cmd_test}[a.cmd](a)
