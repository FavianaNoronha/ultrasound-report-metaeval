"""Step 44: scorers as monitors (catch rate at audit budgets, severity weighting, safety vs usefulness, cascade, judge reason-match, Step 39b flag agreement).
NEW file. Follows results/partA/step44_monitors/PREREG.md (committed before any test number). SAVED scores and cached judge replies only: NO model call.
Thresholds: val only (X-th percentile of the val pool, flag = score <= t). Report: test. Group bootstrap (group = dataset:group_id), 1,000 resamples, seed 0; cells under 30 groups are marked too_small.
    python3 -m usmeta.step44_monitors"""
import os, sys, json, hashlib, collections, platform, time, subprocess
import numpy as np
from . import step19_pairs as P, judge2, step37_new_scorers as S37, step39_judge_ensemble as S39

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(ROOT, 'results', 'partA', 'step44_monitors')
BUDGETS = (1, 2, 5, 10); MIN_G = 30; NB = 1000; EPS = 1e-9
TEXT = ['bleu', 'rougeL', 'chrf', 'bertscore[roberta-large]', 'ratescore']; CEIL = ['finding_f1']; JUDGE = ['judge_score']; RG = ['radgraph_f1']
ORGANS = ('breast', 'thyroid', 'fetal head'); HTYPES = ('small', 'matched', 'large', 'other')
CASCADE_S = (10, 20, 40); CASCADE_B = (5, 10); CHEAP = ['bleu', 'rougeL', 'chrf']
MODEL = 'mlx-community/gemma-2-9b-it-4bit'
KW = {'size_pct': ['size', 'measur', 'mm', 'cm', 'width', '%'], 'size_mm': ['size', 'measur', 'mm', 'cm', 'width'], 'hc_mm': ['head', 'circumference', 'hc'], 'lesion': ['mass', 'lesion', 'nodule', 'finding'],
      'orient': ['orient', 'wider', 'taller', 'shape'], 'count': ['count', 'number', 'foci', 'nodule'], 'pos': ['locat', 'position', 'quadrant', 'central', 'upper', 'lower'], 'side': ['side', 'left', 'right'],
      'birads': ['bi-rads', 'birads', 'assessment'], 'tirads': ['ti-rads', 'tirads'], 'path': ['patholog', 'malignan', 'benign'], 'hist': ['histolog'], 'margin': ['margin'], 'plane': ['plane'], 'echo': ['echo'],
      'shape': ['shape'], 'calc': ['calc'], 'halo': ['halo'], 'foci': ['foci'], 'comp': ['composition', 'solid', 'cystic'], 'post': ['posterior']}

# ------------------------------------------------------------------ bootstrap
def boot_ratio(num, den, groups, nb=NB):
    """ratio of sums num/den with a group bootstrap; returns dict(est, lo, hi, n, groups, too_small)"""
    num = np.asarray(num, float); den = np.asarray(den, float)
    if len(num) == 0 or den.sum() == 0: return None
    ug, inv = np.unique(np.asarray(groups), return_inverse=True); G = len(ug)
    gn = np.bincount(inv, weights=num, minlength=G); gd = np.bincount(inv, weights=den, minlength=G); est = float(gn.sum() / gd.sum())
    rng = np.random.default_rng(0); C = rng.multinomial(G, np.full(G, 1.0 / G), size=nb).astype(float); d = C @ gd; ok = d > 0; b = (C @ gn)[ok] / d[ok]
    return dict(est=est, lo=float(np.percentile(b, 2.5)), hi=float(np.percentile(b, 97.5)), n=int(round(den.sum())), groups=G, too_small=G < MIN_G)

def pct_t(vals, x): return float(np.percentile(np.asarray(vals, float), x))

# ------------------------------------------------------------------ data
def rg_all():
    out = {}
    for st in (33, 34, 35):
        try: out.update(S37.rg_scores(st)[0])
        except FileNotFoundError: pass
    return out

def load_split(split):
    rows, sc, jset = P.load(split); sc = dict(sc); sc['radgraph_f1'] = rg_all(); out = []
    for r in rows:
        k = (r['reference'], r['candidate']); out.append(dict(key=k, kind=r['kind'], ht=(r.get('harmless_type') if r['kind'] == 'harmless' else None), organ=r['organ'], group=f"{r['dataset']}:{r['group_id']}", dataset=r['dataset'], sev=int(r.get('severity') or 0), field=r.get('field'), cat=r.get('category'), case=r['case_id'], inj=k in jset))
    return out, sc

def sub(rows, sc, name, judge_only=False):
    """rows that have a score for this scorer (and, if judge_only, belong to the judge subset); returns rows, scores"""
    f = sc[name]; R = [r for r in rows if r['key'] in f and (r['inj'] or not judge_only)]
    if name == 'judge_score': R = [r for r in R if r['inj']]
    return R, np.array([f[r['key']] for r in R], float)

def thresholds(val_rows, sc, name):
    R, s = sub(val_rows, sc, name)
    return {x: pct_t(s, x) for x in (1, 2, 5, 10, 20, 40)} if len(s) else None, dict(val_rows=len(R), val_groups=len({r['group'] for r in R}))

# ------------------------------------------------------------------ cells
def cell(R, flag, organs=True):
    """metrics of one monitor on rows R (flag = bool array)"""
    g = np.array([r['group'] for r in R]); kind = np.array([r['kind'] for r in R]); sev = np.array([r['sev'] for r in R], float); ht = np.array([r['ht'] or '' for r in R]); f = flag.astype(float); err = kind == 'error'; hm = kind == 'harmless'; idn = kind == 'identical'
    o = dict(pool=len(R), flagged_share=boot_ratio(f, np.ones(len(R)), g))
    o['catch'] = boot_ratio(f[err], np.ones(err.sum()), g[err]); o['catch_severity_weighted'] = boot_ratio((f * sev)[err], sev[err], g[err])
    o['catch_by_severity'] = {str(s): boot_ratio(f[err & (sev == s)], np.ones((err & (sev == s)).sum()), g[err & (sev == s)]) for s in (1, 2, 3)}
    o['flag_harmless_all'] = boot_ratio(f[hm], np.ones(hm.sum()), g[hm]); o['flag_harmless_by_type'] = {t: boot_ratio(f[hm & (ht == t)], np.ones((hm & (ht == t)).sum()), g[hm & (ht == t)]) for t in HTYPES}
    o['flag_identical'] = boot_ratio(f[idn], np.ones(idn.sum()), g[idn])
    if organs:
        org = np.array([r['organ'] for r in R]); o['by_organ'] = {}
        for og in ORGANS:
            m = org == og; e = m & err; h = m & hm
            o['by_organ'][og] = dict(catch=boot_ratio(f[e], np.ones(e.sum()), g[e]), catch_severity_weighted=boot_ratio((f * sev)[e], sev[e], g[e]), flag_harmless_all=boot_ratio(f[h], np.ones(h.sum()), g[h]))
    return o

def monitor_table(test_rows, val_rows, sc, vsc, names, judge_only):
    res = {}
    for n in names:
        th, cov = thresholds(val_rows, vsc, n)
        if th is None: res[n] = dict(available=False, reason='no val scores'); continue
        R, s = sub(test_rows, sc, n, judge_only=judge_only)
        if not len(R): res[n] = dict(available=False, reason='no test scores'); continue
        res[n] = dict(available=True, coverage=dict(cov, test_rows=len(R), test_groups=len({r['group'] for r in R})), budgets={})
        for x in BUDGETS: res[n]['budgets'][str(x)] = dict(threshold=th[x], **cell(R, s <= th[x] + EPS))
    return res

# ------------------------------------------------------------------ D cascade
def cascade(test_rows, val_rows, sc, vsc):
    R = [r for r in test_rows if r['inj'] and r['key'] in sc['judge_score']]; J = np.array([sc['judge_score'][r['key']] for r in R]); tj, _ = thresholds(val_rows, vsc, 'judge_score'); out = {}
    for b in CASCADE_B:
        out[f'judge_alone|b{b}'] = dict(**cell(R, J <= tj[b] + EPS, organs=False), calls_saved=0.0)
    for c in CHEAP:
        th, _ = thresholds(val_rows, vsc, c); s1 = np.array([sc[c][r['key']] for r in R])
        for s in CASCADE_S:
            sent = s1 <= th[s] + EPS
            for b in CASCADE_B:
                fin = sent & (J <= tj[b] + EPS); o = cell(R, fin, organs=False); o['sent_to_judge'] = boot_ratio(sent.astype(float), np.ones(len(R)), np.array([r['group'] for r in R])); o['calls_saved'] = float(1 - sent.mean()); out[f'{c}|s{s}|b{b}'] = o
    return out, dict(judge_thresholds={str(b): tj[b] for b in BUDGETS})

# ------------------------------------------------------------------ E reason match
def cached_errors(ref, cand):
    R, H = judge2.sentences(ref), judge2.sentences(cand); p = judge2.PROMPT.format(ref=judge2.numbered(R), hyp=judge2.numbered(H)); f = os.path.join(ROOT, '.llm_cache', hashlib.sha256((MODEL + '\0' + p).encode()).hexdigest() + '.txt')
    if not os.path.exists(f): return None
    js = judge2.parse(open(f).read(), len(R), len(H)); return None if js is None else [e for e in js['errors'] if isinstance(e, dict)]

def reason_match(test_rows):
    rows = [r for r in test_rows if r['kind'] == 'error' and r['inj']]; miss = 0; rec = []
    for r in rows:
        er = cached_errors(*r['key'])
        if er is None: miss += 1; continue
        cats = [e.get('category') for e in er]; txt = [str(e.get('field') or '').lower() for e in er]; kws = KW.get(r['field'], [])
        fl_all = sorted(KW); other = fl_all[(fl_all.index(r['field']) + 1) % len(fl_all)] if r['field'] in KW else None
        ctl = float(any(any(k in t for k in KW[other]) for t in txt)) if other else 0.0
        rec.append(dict(group=r['group'], field=r['field'], ctl=ctl, flagged=len(er) > 0, cat=float(r['cat'] in cats), fld=float(any(any(k in t for k in kws) for t in txt)), both=float(any((e.get('category') == r['cat']) and any(k in str(e.get('field') or '').lower() for k in kws) for e in er))))
    g = np.array([x['group'] for x in rec]); out = dict(error_pairs=len(rows), cache_missing=miss)
    for tag, sel in (('all_planted_errors', np.ones(len(rec), bool)), ('judge_listed_at_least_one_error', np.array([x['flagged'] for x in rec]))):
        o = {}
        for k in ('cat', 'fld', 'both', 'ctl'): v = np.array([x[k] for x in rec]); o[k] = boot_ratio(v[sel], np.ones(sel.sum()), g[sel])
        o['n'] = int(sel.sum()); out[tag] = o
    fl = np.array([x['field'] for x in rec]); sel = np.array([x['flagged'] for x in rec]); out['by_field'] = {}
    for fld in sorted(set(fl)):
        m = (fl == fld); mm = m & sel; v = np.array([x['fld'] for x in rec]); c = np.array([x['cat'] for x in rec]); out['by_field'][fld] = dict(n=int(m.sum()), flagged=int(mm.sum()), field_match_among_flagged=boot_ratio(v[mm], np.ones(mm.sum()), g[mm]), category_match_among_flagged=boot_ratio(c[mm], np.ones(mm.sum()), g[mm]))
    return out

# ------------------------------------------------------------------ F Step 39b
def step39b(val_rows, vsc):
    tj, _ = thresholds(val_rows, vsc, 'judge_score'); Sc = S39.load_scores(); rows = S39.h1_rows(); P6 = ('P0', 'P1', 'P2', 'P3', 'P4', 'P5'); recs = []
    for r in rows:
        k = (r['reference'], r['candidate']); v = {n: (Sc.get(n, {}).get(k) or {}).get('judge') for n in P6}
        if any(x is None for x in v.values()): continue
        recs.append(dict(group=f"{r['dataset']}:{r['group_id']}", kind=r['kind'], A=float(np.mean([v['P0'], v['P1'], v['P2']])), B=float(np.mean([v['P3'], v['P4'], v['P5']])), P0=float(v['P0']), P3=float(v['P3'])))
    out = dict(pairs=len(recs), pairs_planned=len(rows), val_thresholds={str(b): tj[b] for b in (5, 10)}, budgets={}); g = np.array([x['group'] for x in recs]); kind = np.array([x['kind'] for x in recs])
    for b in (5, 10):
        t = tj[b] + EPS; fl = {k: np.array([x[k] <= t for x in recs]) for k in ('A', 'B', 'P0', 'P3')}; o = {}
        for pair_name, (a, c) in (('ensembleA_vs_ensembleB', ('A', 'B')), ('P0_vs_P3_single', ('P0', 'P3'))):
            agree = (fl[a] == fl[c]).astype(float); o[pair_name] = {sel_name: boot_ratio(agree[m], np.ones(m.sum()), g[m]) for sel_name, m in (('all_pairs', np.ones(len(recs), bool)), ('planted_errors', kind == 'error'), ('harmless_or_identical', kind != 'error'))}
        o['flag_rate_on_errors'] = {k: boot_ratio(fl[k][kind == 'error'].astype(float), np.ones((kind == 'error').sum()), g[kind == 'error']) for k in fl}
        o['flag_rate_on_non_errors'] = {k: boot_ratio(fl[k][kind != 'error'].astype(float), np.ones((kind != 'error').sum()), g[kind != 'error']) for k in fl}; out['budgets'][str(b)] = o
    return out

# ------------------------------------------------------------------ image check (fixed Step 20 rule)
def image_check(test_rows):
    from . import step30_severity as S30
    rows, S = S30.image_scores(); tset = {r['case'] for r in test_rows}; rows = [r for r in rows if r['case_id'] in tset]; out = {}
    for name, sc in S.items():
        R = []
        for r in rows:
            v = sc.get((r['reference'], r['candidate']))
            if v is None: continue
            R.append(dict(group=f"{r['dataset']}:{r['group_id']}", kind=r['kind'], ht=(r.get('harmless_type') if r['kind'] == 'harmless' else None), organ=r['organ'], sev=int(r.get('severity') or 0), v=float(v)))
        flag = np.array([x['v'] < 1 - EPS for x in R]); o = cell(R, flag, organs=False); o['scans_in_test'] = len({r['case_id'] for r in rows}); o['rule'] = 'flag iff the Step 20 tolerance-aware score < 1 (tau and position tolerance fixed on dev/val in Step 20)'; out[name] = o
    return out

def main():
    t0 = time.time(); os.makedirs(OUT, exist_ok=True); val, vsc = load_split('val'); test, tsc = load_split('test'); res = dict(budgets=list(BUDGETS))
    print('loaded', len(val), len(test), flush=True)
    res['A_full_test'] = monitor_table(test, val, tsc, vsc, TEXT + CEIL, judge_only=False); print('A full', flush=True)
    res['A_judge_subset'] = monitor_table(test, val, tsc, vsc, TEXT + CEIL + JUDGE + RG, judge_only=True); print('A judge subset', flush=True)
    res['radgraph_partial_full_rows'] = monitor_table(test, val, tsc, vsc, RG, judge_only=False); print('A rg', flush=True)
    res['D_cascade'], res['D_meta'] = cascade(test, val, tsc, vsc); print('D', flush=True)
    res['E_reason_match'] = reason_match(test); print('E', flush=True)
    res['F_step39b'] = step39b(val, vsc); print('F', flush=True)
    try: res['image_check'] = image_check(test)
    except Exception as e: res['image_check'] = dict(error=f'{type(e).__name__}: {e}')
    print('image', flush=True)
    res['pools'] = dict(val_rows=len(val), test_rows=len(test), test_judge_rows=sum(r['inj'] for r in test), val_judge_rows=sum(r['inj'] for r in val), test_groups=len({r['group'] for r in test}))
    json.dump(res, open(os.path.join(OUT, 'results.json'), 'w'), indent=1)
    head = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], capture_output=True, text=True).stdout.strip()
    json.dump(dict(step='44', prereg='PREREG.md', git_head=head, python=platform.python_version(), platform=platform.platform(), bootstrap=f'group, {NB} resamples, seed 0', min_groups=MIN_G, model_calls=0, seconds=round(time.time() - t0, 1), date=time.strftime('%Y-%m-%d')), open(os.path.join(OUT, 'run_info.json'), 'w'), indent=1)
    print('saved', round(time.time() - t0), 's')

if __name__ == '__main__': main()
