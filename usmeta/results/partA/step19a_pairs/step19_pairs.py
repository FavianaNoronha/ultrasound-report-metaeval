"""Step 19a: paired preference, ties, cut-off sensitivity / false-alarm rate, error-type breakdown, held-out cut-off transfer. SAVED scores only, no model calls. New file.
Pairs: within one case, every planted-error candidate x every harmless rewording (small + matched + large) of the same reference. Score direction: LOWER score = flagged / error.
  pref_strict = share of pairs with error score < harmless score; tie = share equal; pref_half = pref_strict + 0.5 tie (= the AUROC of Steps 5-12).
Cut-off per (scorer, dataset) = the 90th percentile of the planted-error scores on VAL (flag = score <= cut-off, so >= 90% of val errors are flagged), applied unchanged to TEST:
  sensitivity = share of test error candidates flagged; false-alarm rate (FPR) = share of test harmless candidates flagged.
Judge: val judge samples exist only from the dev-era 20-case sample (201 rows in the new val split) so its cut-off is pooled over ALL val datasets (labelled). Test judge rows = Steps 10d + 12.
Bootstrap: 1,000 group resamples, seed 0 (group = patient / exam, or image id where none). Cells with < 30 groups: 'too small to compare'.
    python3 -m usmeta.step19_pairs OUT_DIR"""
import json, sys, os, csv, collections
import numpy as np
from . import splits
from .step10d_analysis import gboot

HT = ('small', 'matched', 'large'); MIN_N = 30
ORGAN = {'BrEaST': 'breast', 'BUS-BRA': 'breast', 'BUSI': 'breast', 'UDIAT': 'breast', 'BUS-UCLM': 'breast', 'TN3K': 'thyroid', 'TN5000': 'thyroid', 'DDTI': 'thyroid', 'HC18': 'fetal head', 'FetalHead': 'fetal head'}
L0 = ['bleu', 'rougeL', 'chrf', 'bertscore[roberta-large]', 'ratescore']; TEXT = L0 + ['finding_f1']; JUDGE = ['sentence_f1', 'judge_score']; ALL = TEXT + JUDGE

def scores_of(path):
    S = json.load(open(path)); P = [tuple(p) for p in S['pairs']]; return {n: dict(zip(P, a)) for n, a in S['scores'].items()}

def judge_lookup(files):
    out = {'sentence_f1': {}, 'judge_score': {}}
    for f in files:
        for l in open(f):
            d = json.loads(l)
            if d['result'] is not None: out['sentence_f1'][(d['reference'], d['candidate'])] = d['result']['f1']; out['judge_score'][(d['reference'], d['candidate'])] = d['result']['judge']
    return out

def load(split):
    if split == 'val':
        rows = [json.loads(l) for l in open('bench_val_v2d.jsonl')]; ids = {r['case_id'] for r in splits.load('val')}
        sc = {**scores_of('scores_val_layer0.json'), 'finding_f1': scores_of('scores_val_layer1.json')['finding_f1']}
        # dev-era judge sample, restricted to cases that are in the new VAL split
        jr = [json.loads(l) for l in open('bench_v2d_judge.jsonl')]; jr = [r for r in jr if r['case_id'] in ids]; jl = judge_lookup(['judge2_scores_v2.jsonl'])
    else:
        rows = [json.loads(l) for l in open('bench_test_v2d.jsonl')]; ids = {r['case_id'] for r in splits.load('test', script='usmeta.step19_pairs')}
        sc = {**scores_of('scores_test_layer0.json'), 'finding_f1': scores_of('scores_test_layer1.json')['finding_f1']}
        jr = []
        for f in ('judge_test_v2_bench.jsonl', 'judge_big_v2_bench.jsonl'): jr += [json.loads(l) for l in open(f)]
        jl = judge_lookup(['judge_test_v2.jsonl', 'judge_big_v2.jsonl'])
    assert all(r['case_id'] in ids for r in rows), f'{split}: bench rows outside the {split} split'
    jset = {(r['reference'], r['candidate']) for r in jr}; sc.update(jl); return rows, sc, jset

def cases_of(rows, jset=None):
    """{case: dict(ds, group, E=[(row)], H=[(row)])}; with jset only rows the judge saw"""
    C = {}
    for r in rows:
        k = (r['reference'], r['candidate'])
        if jset is not None and k not in jset: continue
        if r['kind'] == 'error' or (r['kind'] == 'harmless' and r['harmless_type'] in HT):
            c = C.setdefault(r['case_id'], dict(ds=r['dataset'], group=f"{r['dataset']}:{r['group_id']}", E=[], H=[]))
            c['E' if r['kind'] == 'error' else 'H'].append(r)
    return C

def score_of(sc, name, r): return sc[name].get((r['reference'], r['candidate']))

def pref(C, sc, name, sel=lambda r: True):
    """per case (strict, tie, half) over error x harmless pairs; returns lists + groups"""
    s, t, h, g = [], [], [], []
    for cid, c in C.items():
        e = [score_of(sc, name, r) for r in c['E'] if sel(r)]; hh = [score_of(sc, name, r) for r in c['H']]
        e = [x for x in e if x is not None]; hh = [x for x in hh if x is not None]
        if not e or not hh: continue
        E, H = np.array(e)[:, None], np.array(hh)[None, :]; lt, eq = float((E < H).mean()), float((E == H).mean())
        s.append(lt); t.append(eq); h.append(lt + 0.5 * eq); g.append(c['group'])
    return s, t, h, g

def cutoff(Cval, sc, name, ds=None):
    e = [score_of(sc, name, r) for c in Cval.values() if ds is None or c['ds'] == ds for r in c['E']]; e = [x for x in e if x is not None]
    return (float(np.percentile(e, 90)), len(e)) if e else (None, 0)

def flags(C, sc, name, cut, kind, sel=lambda r: True):
    v, g = [], []
    for c in C.values():
        for r in c[kind]:
            x = score_of(sc, name, r)
            if x is not None and sel(r): v.append(float(x <= cut)); g.append(c['group'])
    return v, g

def fm(a, d=2): return '—' if a is None else f'{a[0]:.{d}f} ({a[1]:.{d}f}–{a[2]:.{d}f})'
def mark(n_groups): return ' †' if n_groups < MIN_N else ''

def main(out):
    os.makedirs(out, exist_ok=True)
    rv, sv, jv = load('val'); rt, st, jt = load('test'); Cv, Ct = cases_of(rv), cases_of(rt)
    Cvj, Ctj = cases_of(rv, jv), cases_of(rt, jt)
    cuts = {}; rows_csv = []; res = {}
    dss = sorted(ORGAN, key=lambda d: (ORGAN[d], d))
    pooled_cut = {n: cutoff(Cvj, sv, n) for n in JUDGE}                      # judge: pooled val cut-off
    for n in ALL:
        for ds in dss:
            cut, nv = pooled_cut[n] if n in JUDGE else cutoff(Cv, sv, n, ds); cuts[f'{n}|{ds}'] = dict(cutoff=cut, n_val_errors=nv, pooled_over_val_datasets=n in JUDGE)
    def cell(C, sc, name, ds_list, sel=lambda r: True, label=''):
        Cs = {k: v for k, v in C.items() if v['ds'] in ds_list}; s, t, h, g = pref(Cs, sc, name, sel)
        if not s: return None
        d = dict(n_cases=len(s), n_groups=len(set(g)), pref_strict=gboot(s, g), tie=gboot(t, g), pref_half=gboot(h, g))
        # sensitivity / FPR with each dataset's own val cut-off
        sens, sg, fpr, fg = [], [], [], []
        for ds in ds_list:
            cut = cuts[f'{name}|{ds}']['cutoff']
            if cut is None: continue
            Cd = {k: v for k, v in C.items() if v['ds'] == ds}; a, b = flags(Cd, sc, name, cut, 'E', sel); sens += a; sg += b; a, b = flags(Cd, sc, name, cut, 'H'); fpr += a; fg += b
        d['sensitivity'] = gboot(sens, sg) if sens else None; d['fpr'] = gboot(fpr, fg) if fpr else None; d['n_error_rows'] = len(sens); d['n_harmless_rows'] = len(fpr)
        return d
    # ---- 1. per dataset and per organ
    for n in ALL:
        C, sc = (Ctj, st) if n in JUDGE else (Ct, st)
        for ds in dss: res[(n, ds, 'all')] = cell(C, sc, n, [ds])
        for org in ('breast', 'thyroid', 'fetal head'): res[(n, f'ORGAN:{org}', 'all')] = cell(C, sc, n, [d for d in dss if ORGAN[d] == org])
    # ---- 2. by error type (field) per dataset
    fields = sorted({r['field'] for r in rt if r['kind'] == 'error'})
    for n in ALL:
        C, sc = (Ctj, st) if n in JUDGE else (Ct, st)
        for ds in dss:
            for f in fields:
                if any(r['field'] == f for c in C.values() if c['ds'] == ds for r in c['E']): res[(n, ds, f)] = cell(C, sc, n, [ds], sel=lambda r, f=f: r['field'] == f)
    # ---- csv
    with open(os.path.join(out, 'cells.csv'), 'w', newline='') as fh:
        w = csv.writer(fh); w.writerow(['scorer', 'dataset', 'organ', 'error_field', 'n_cases', 'n_groups', 'too_small', 'pref_strict', 'pref_lo', 'pref_hi', 'tie', 'pref_half_auroc', 'half_lo', 'half_hi', 'sensitivity', 'sens_lo', 'sens_hi', 'fpr', 'fpr_lo', 'fpr_hi'])
        for (n, ds, f), d in res.items():
            if d: w.writerow([n, ds, ORGAN.get(ds, ds), f, d['n_cases'], d['n_groups'], int(d['n_groups'] < MIN_N), *d['pref_strict'], d['tie'][0], *d['pref_half'], *(d['sensitivity'] or ['', '', '']), *(d['fpr'] or ['', '', ''])])
    json.dump(cuts, open(os.path.join(out, 'cutoffs_val.json'), 'w'), indent=1)
    # ---- 3. transfer: cut-off from A's val -> B's test (same organ), text scorers only
    tr = []
    for n in TEXT:
        for org in ('breast', 'thyroid', 'fetal head'):
            ds_org = [d for d in dss if ORGAN[d] == org]
            for A in ds_org:
                for B in ds_org:
                    if A == B: continue
                    ca, cb = cuts[f'{n}|{A}']['cutoff'], cuts[f'{n}|{B}']['cutoff']
                    if ca is None or cb is None: continue
                    CB = {k: v for k, v in Ct.items() if v['ds'] == B}
                    fa, ga = flags(CB, st, n, ca, 'H'); fb, _ = flags(CB, st, n, cb, 'H'); ea, gea = flags(CB, st, n, ca, 'E'); eb, _ = flags(CB, st, n, cb, 'E')
                    dh = [x - y for x, y in zip(fa, fb)]; de = [x - y for x, y in zip(ea, eb)]
                    tr.append(dict(scorer=n, organ=org, cutoff_from=A, applied_to=B, cut_A=ca, cut_B_own=cb, fpr_own=float(np.mean(fb)), fpr_transfer=float(np.mean(fa)), delta_fpr=gboot(dh, ga), sens_own=float(np.mean(eb)), sens_transfer=float(np.mean(ea)), delta_sens=gboot(de, gea), groups_B=len(set(ga))))
    with open(os.path.join(out, 'transfer.csv'), 'w', newline='') as fh:
        w = csv.writer(fh); w.writerow(['scorer', 'organ', 'cutoff_from_val_of', 'applied_to_test_of', 'cutoff_A', 'cutoff_B_own', 'fpr_own', 'fpr_transfer', 'delta_fpr', 'dfpr_lo', 'dfpr_hi', 'sens_own', 'sens_transfer', 'delta_sens', 'dsens_lo', 'dsens_hi', 'groups_B'])
        for t in tr: w.writerow([t['scorer'], t['organ'], t['cutoff_from'], t['applied_to'], round(t['cut_A'], 4), round(t['cut_B_own'], 4), round(t['fpr_own'], 3), round(t['fpr_transfer'], 3), *[round(x, 3) for x in t['delta_fpr']], round(t['sens_own'], 3), round(t['sens_transfer'], 3), *[round(x, 3) for x in t['delta_sens']], t['groups_B']])
    # ---- markdown tables
    md = []
    def tab(title, keys, label):
        md.extend([f'### {title}', '', '| scorer | ' + ' | '.join(label) + ' |', '|---|' + '---|' * len(label)])
    json.dump({f'{k[0]}|{k[1]}|{k[2]}': v for k, v in res.items()}, open(os.path.join(out, 'cells.json'), 'w'), indent=1)
    return res, cuts, tr, dss, fields

if __name__ == '__main__':
    main(sys.argv[1])
