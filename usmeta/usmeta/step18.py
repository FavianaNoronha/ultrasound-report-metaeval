"""Step 18: analysis + judge runner for bench_v3_threshold (synthetic size, real TI-RADS level; DDTI). New file.
    python3 -m usmeta.step18 judge  devval|test  [n_dose]     (resumable; Gemma-2-9B sentence_check, frozen prompt_v2, greedy)
    python3 -m usmeta.step18 report devval|test  OUT.json
Contrast d = score(non-crossing) - score(crossing) for a matched pair (same replica, same |change| in mm, exactly one of the two crosses a cutoff).
DiD = mean over pairs of (d - control analogue of the same orientation); controls = replicas >= 6 mm from every cutoff. Group = patient (resampled)."""
import json, os, sys, time, random, collections, hashlib
import numpy as np
from . import layer0

MIN_N = 30; LEVELS = ('TR3', 'TR4', 'TR5')
JUDGE_KEYS = (('sentence_f1', 'f1'), ('sentence_precision', 'precision'), ('sentence_recall', 'recall'), ('judge_score', 'judge'))

def bench(split): return [json.loads(l) for l in open(f'bench_v3_threshold_{split}.jsonl')]

def load_scores(split):
    """-> {scorer: {(ref, cand): value}}"""
    out = {}
    for f in (f'scores_v3_{split}_layer0.json', f'scores_v3_{split}_layer1.json'):
        if not os.path.exists(f): continue
        S = json.load(open(f)); P = [tuple(p) for p in S['pairs']]
        for n, arr in S['scores'].items():
            if n.startswith('legacy') or n in ('finding_precision', 'finding_recall'): continue
            out[n] = dict(zip(P, arr))
    jf = f'judge_v3_{split}.jsonl'
    if os.path.exists(jf):
        R = {}
        for l in open(jf):
            d = json.loads(l)
            if d['result'] is not None: R[(d['reference'], d['candidate'])] = d['result']
        for n, k in JUDGE_KEYS: out[n] = {p: r[k] for p, r in R.items()}
    return out

def units_of(rows):
    U = collections.OrderedDict()
    for r in rows: U.setdefault(r['unit'], []).append(r)
    return U

def pairs_and_controls(rows, sc, delta, digit_matched=True):
    """-> pair list [(group, level, orient(+1 crossing is up), d)], control list [(group, level, c = score(down) - score(up))] for one scorer"""
    P, C = [], []
    for u, rs in units_of(rows).items():
        up = [r for r in rs if r['kind'] == 'error' and r['delta_type'] == 'mm' and r['nominal'] == delta and r['direction'] == 'up']
        dn = [r for r in rs if r['kind'] == 'error' and r['delta_type'] == 'mm' and r['nominal'] == delta and r['direction'] == 'down']
        if not up or not dn: continue
        up, dn = up[0], dn[0]; a, b = sc.get((up['reference'], up['candidate'])), sc.get((dn['reference'], dn['candidate']))
        if a is None or b is None: continue
        if up['role'] == 'control':
            if not up['crossing'] and not dn['crossing']: C.append((up['group_id'], up['level'], b - a))
        elif up['crossing'] != dn['crossing']:
            if digit_matched and up['digits_new'] != dn['digits_new']: continue
            o = 1 if up['crossing'] else -1; P.append((up['group_id'], up['level'], o, (b - a) if o == 1 else (a - b)))
    return P, C

def boot_did(P, C, n=1000, seed=0):
    """P: [(g, level, o, d)], C: [(g, level, c)] -> dict with mean d, DiD, share>0/=0/<0 and group-bootstrap 95% CIs"""
    if not P: return None
    gs = sorted({p[0] for p in P} | {c[0] for c in C}); gi = {g: i for i, g in enumerate(gs)}; G = len(gs)
    sd = np.zeros(G); npr = np.zeros(G); so = np.zeros(G); sc_ = np.zeros(G); nc = np.zeros(G); pos = np.zeros(G); neg = np.zeros(G)
    for g, _, o, d in P: i = gi[g]; sd[i] += d; npr[i] += 1; so[i] += o; pos[i] += d > 1e-9; neg[i] += d < -1e-9
    for g, _, c in C: i = gi[g]; sc_[i] += c; nc[i] += 1
    def stat(w):
        Np = (w * npr).sum()
        if Np == 0: return (np.nan,) * 4
        md = (w * sd).sum() / Np; cb = (w * sc_).sum() / (w * nc).sum() if (w * nc).sum() else 0.0
        return md, md - cb * (w * so).sum() / Np, (w * pos).sum() / Np, (w * neg).sum() / Np
    pt = stat(np.ones(G)); rng = np.random.default_rng(seed); B = np.array([stat(np.bincount(rng.integers(0, G, G), minlength=G).astype(float)) for _ in range(n)])
    ci = lambda k: [float(np.nanpercentile(B[:, k], 2.5)), float(np.nanpercentile(B[:, k], 97.5))]
    return dict(n_pairs=len(P), n_groups=int(sum(npr > 0)), n_controls=len(C), mean_d=float(pt[0]), mean_d_ci=ci(0), did=float(pt[1]), did_ci=ci(1),
                share_crossing_penalised_more=float(pt[2]), share_tie=float(1 - pt[2] - pt[3]), share_less=float(pt[3]), control_mean=float(sc_.sum() / nc.sum()) if nc.sum() else None)

def auroc_unit(e, h): e, h = np.asarray(e)[:, None], np.asarray(h)[None, :]; return float(((e < h) + 0.5 * (e == h)).mean())

def dose_response(rows, sc, n=1000, seed=0):
    """per replica: AUROC of the size errors in a bin vs the matched synonyms; group bootstrap. bins: ('mm', 1..5), ('pct', 5..50). Also split by crossing."""
    res = {}
    for u, rs in units_of(rows).items():
        syn = [sc.get((r['reference'], r['candidate'])) for r in rs if r['kind'] == 'harmless']; syn = [x for x in syn if x is not None]
        if not syn: continue
        for r in rs:
            if r['kind'] != 'error': continue
        for ty in ('mm', 'pct'):
            for nom in sorted({r['nominal'] for r in rs if r['kind'] == 'error' and r['delta_type'] == ty}):
                for lab, sel in (('all', lambda r: True), ('crossing', lambda r: r['crossing']), ('non-crossing', lambda r: not r['crossing'])):
                    e = [sc.get((r['reference'], r['candidate'])) for r in rs if r['kind'] == 'error' and r['delta_type'] == ty and r['nominal'] == nom and sel(r)]
                    e = [x for x in e if x is not None]
                    if e: res.setdefault((ty, nom, lab), []).append((rs[0]['group_id'], auroc_unit(e, syn)))
    out = {}
    rng = np.random.default_rng(seed)
    for k, v in res.items():
        gs = sorted({g for g, _ in v}); gi = {g: i for i, g in enumerate(gs)}; G = len(gs); s = np.zeros(G); c = np.zeros(G)
        for g, a in v: s[gi[g]] += a; c[gi[g]] += 1
        m = s.sum() / c.sum(); B = [(lambda w: (w * s).sum() / (w * c).sum())(np.bincount(rng.integers(0, G, G), minlength=G).astype(float)) for _ in range(n)]
        out['|'.join(map(str, k))] = dict(n_units=len(v), n_groups=G, auroc=float(m), ci=[float(np.percentile(B, 2.5)), float(np.percentile(B, 97.5))])
    return out

def identical_gate(rows, sc):
    v = [sc[(r['reference'], r['candidate'])] for r in rows if r['kind'] == 'identical' and (r['reference'], r['candidate']) in sc]
    return dict(n=len(v), mean=float(np.mean(v)) if v else None, min=float(np.min(v)) if v else None)

def edit_sizes(rows):
    e = [r for r in rows if r['kind'] == 'error' and r['delta_type'] == 'mm' and r['nominal'] == 3]
    return dict(token_edit_mean=float(np.mean([r['token_edit_frac'] for r in e])), char_edit_mean=float(np.mean([r['char_edit_frac'] for r in e])),
                token_edit_crossing=float(np.mean([r['token_edit_frac'] for r in e if r['crossing']])), token_edit_non=float(np.mean([r['token_edit_frac'] for r in e if not r['crossing']])),
                char_edit_crossing=float(np.mean([r['char_edit_frac'] for r in e if r['crossing']])), char_edit_non=float(np.mean([r['char_edit_frac'] for r in e if not r['crossing']])))

def report(split, out):
    rows = bench(split); S = load_scores(split); R = dict(split=split, edit=edit_sizes(rows), scorers={})
    for name, sc in S.items():
        d = dict(identical=identical_gate(rows, sc), pairs={}, dose=dose_response(rows, sc))
        for delta in (2, 3, 5):
            for dm in (True, False):
                P, C = pairs_and_controls(rows, sc, delta, dm); key = f'delta{delta}|{"digit-matched" if dm else "all-valid"}'
                d['pairs'][key + '|ALL'] = boot_did(P, C)
                for lv in LEVELS:
                    d['pairs'][key + '|' + lv] = boot_did([p for p in P if p[1] == lv], [c for c in C if c[1] == lv] or C)     # TR3/TR5 have few controls: borrow all controls
        R['scorers'][name] = d
    json.dump(R, open(out, 'w'), indent=1); return R

# ---------------------------------------------------------------- judge runner
def judge_plan(rows, n_dose, seed=0):
    """rows to judge, in priority order: (1) delta=3 mm up/down of every valid digit-matched pair replica and of controls (all, or a seeded sample of controls up to the pair count),
    matched synonym (first available) and identical copy for the same replicas; (2) dose-response extras for n_dose replicas: +-1, 2, 5 mm and the % bins"""
    rng = random.Random(seed); U = units_of(rows); first, extra = [], []
    pair_u, ctrl_u = [], []
    for u, rs in U.items():
        e = {(r['delta_type'], r['nominal'], r['direction']): r for r in rs if r['kind'] == 'error'}
        if ('mm', 3, 'up') not in e or ('mm', 3, 'down') not in e: continue
        a, b = e[('mm', 3, 'up')], e[('mm', 3, 'down')]
        if a['role'] == 'control': ctrl_u.append(u)
        elif a['crossing'] != b['crossing'] and a['digits_new'] == b['digits_new']: pair_u.append(u)
    rng.shuffle(ctrl_u); ctrl_u = ctrl_u[:max(len(pair_u), 1)]; chosen = pair_u + ctrl_u
    for k, u in enumerate(chosen):
        rs = U[u]; e = {(r['delta_type'], r['nominal'], r['direction']): r for r in rs if r['kind'] == 'error'}
        first += [e[('mm', 3, 'up')], e[('mm', 3, 'down')]]
        syn = [r for r in rs if r['kind'] == 'harmless']
        if syn: first.append(syn[k % len(syn)])
        if k % 4 == 0: first += [r for r in rs if r['kind'] == 'identical']
    ex_u = chosen[:]; rng.shuffle(ex_u)
    for u in ex_u[:n_dose]:
        rs = U[u]; extra += [r for r in rs if r['kind'] == 'error' and ((r['delta_type'] == 'mm' and r['nominal'] in (1, 2, 5)) or (r['delta_type'] == 'pct' and r['nominal'] in (10, 30)))]
        extra += [r for r in rs if r['kind'] == 'harmless' and r not in first]
    return first, extra

def judge_run(split, n_dose=0):
    from . import judge2, judge2_test
    rows = bench(split); first, extra = judge_plan(rows, n_dose); out = f'judge_v3_{split}.jsonl'
    open(f'judge_v3_{split}_plan.jsonl', 'w').write(''.join(json.dumps(r) + '\n' for r in first + extra))
    done = {(json.loads(l)['reference'], json.loads(l)['candidate']) for l in open(out)} if os.path.exists(out) else set()
    todo = list(dict.fromkeys((r['reference'], r['candidate']) for r in first + extra if (r['reference'], r['candidate']) not in done))
    print(len(first), 'priority rows,', len(extra), 'extra rows;', len(todo), 'pairs to judge', flush=True)
    sc = judge2_test.SC(judge2.PROMPT_V2); t0 = time.time()
    for i, (a, b) in enumerate(todo):
        s = sc.run(a, b); open(out, 'a').write(json.dumps(dict(reference=a, candidate=b, result=s)) + '\n')
        if i % 25 == 0: print(i, len(todo), round(time.time() - t0), 's', flush=True)
    print('done', round(time.time() - t0), 's missing', sc.missing, flush=True)

if __name__ == '__main__':
    if sys.argv[1] == 'judge': judge_run(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 0)
    if sys.argv[1] == 'report': report(sys.argv[2], sys.argv[3])
