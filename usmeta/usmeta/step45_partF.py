"""Step 45, Part F: tuned hybrid on set A. NEW file; extractor v5 outputs (Part B), the number checker (Part C) and the Gemma holistic judge replies (step45_gemma, frozen prompt_v2) are imported / read unchanged.
Hybrid: flag a candidate if the number checker or extractor v5 finds a mismatch against the reference facts; otherwise send it to the judge and flag if its holistic score is at or below a threshold. Everything is fixed on the dev/val part of set A (the judged dev/val subset): the extractor rule (conflict only, or conflict + omission) and the judge threshold, so that at most 5.6% of harmless reports are flagged.
Judge alone: the same threshold rule. Test: catch of the planted-error twins and harmless flagged, hybrid vs judge alone on the SAME candidates; paired difference of catch (group bootstrap 1,000, seed 0).
    python3 -m usmeta.step45_partF"""
import os, sys, json, collections, time, platform, subprocess
import numpy as np
from . import step45_numchecker as NC, step45_extractor_v5 as V5, step45_freetext as FT, step45_gemma as GM
from .step10d_analysis import gboot

OUT = os.path.join(FT.ROOT, 'results', 'partA', 'step45_improve_scorers', 'partF'); P = lambda f: os.path.join(OUT, f); os.makedirs(OUT, exist_ok=True); MAXH = 0.056

def load():
    A = json.load(open(FT.P('set_A.json')))['cases']; J = {}
    for l in open(GM.P('f_holistic.jsonl')): r = json.loads(l); J[r['id']] = r
    E = {}
    for w in ('devval', 'test'):
        E.update(json.load(open(V5.P(f'extraction_v5_{w}.json'))))
    rows = []
    for iid, j in J.items():
        if j['result'] is None or iid not in E: continue
        cid = iid.split('|')[0]; c = A[cid]; texts = {f"{cid}|true|{r['style']}": r['text'] for r in c['true_reports']}
        if c['twin_report']: texts[f"{cid}|twin|{c['twin_report']['style']}"] = c['twin_report']['text']
        if iid not in texts: continue
        rows.append(dict(id=iid, set=j['set'], kind=j['kind'], organ=j['organ'], group=j['group'], case=cid, ref=c['reference'], cand=texts[iid], gold=c['gold'], flat=E[iid]['flat'], judge=j['result']['judge']))
    return rows

def ext_mismatch(organ, gold, flat, mode):
    g = gold if gold.get('lesion') != 'absent' else {k: v for k, v in gold.items() if k in ('lesion', 'birads', 'path')}
    for k in V5.FIELDS[organ]:
        gv, fv = g.get(k), flat.get(k)
        if gv is not None and fv is not None and not V5.vmatch(k, fv, gv): return True            # conflict
        if mode == 'conflict_omission' and gv is not None and fv is None and k != 'lesion': return True      # omission
    return False

def rule_flag(r, mode):
    if NC.score(r['ref'], r['cand'], r['organ']) < 1.0: return True
    return ext_mismatch(r['organ'], r['gold'], r['flat'], mode)

def pick_threshold(rows, flags_rule):
    """largest judge threshold t (flag = judge <= t, only for candidates the rules did not flag) with harmless flagged <= 5.6% on these rows"""
    H = [i for i, r in enumerate(rows) if r['kind'] == 'harmless']; best = None
    for t in sorted({r['judge'] for r in rows}):
        fl = [flags_rule[i] or rows[i]['judge'] <= t for i in range(len(rows))]
        if np.mean([fl[i] for i in H]) <= MAXH: best = t
    return best

def main():
    R = load(); dv = [r for r in R if r['set'] == 'devval']; te = [r for r in R if r['set'] == 'test']; res = dict(pairs=dict(devval=len(dv), test=len(te)))
    tune = {}
    for mode in ('conflict', 'conflict_omission'):
        fr = [rule_flag(r, mode) for r in dv]; t = pick_threshold(dv, fr); Hh = [i for i, r in enumerate(dv) if r['kind'] == 'harmless']; Ee = [i for i, r in enumerate(dv) if r['kind'] == 'error']
        fl = [fr[i] or (t is not None and dv[i]['judge'] <= t) for i in range(len(dv))]
        tune[mode] = dict(judge_threshold=t, rule_flags_harmless=float(np.mean([fr[i] for i in Hh])), hybrid_harmless=float(np.mean([fl[i] for i in Hh])), hybrid_catch=float(np.mean([fl[i] for i in Ee])))
    mode = max(tune, key=lambda m: (tune[m]['hybrid_harmless'] <= MAXH, tune[m]['hybrid_catch'])); tj = pick_threshold(dv, [False] * len(dv)); Hh = [i for i, r in enumerate(dv) if r['kind'] == 'harmless']; Ee = [i for i, r in enumerate(dv) if r['kind'] == 'error']
    tune['chosen_rule_mode'] = mode; tune['judge_alone_threshold'] = tj; tune['judge_alone_devval'] = dict(harmless=float(np.mean([dv[i]['judge'] <= tj for i in Hh])) if tj is not None else None, catch=float(np.mean([dv[i]['judge'] <= tj for i in Ee])) if tj is not None else None, n_harmless=len(Hh), n_error=len(Ee)); res['tuning'] = tune
    th = tune[mode]['judge_threshold']; fr = [rule_flag(r, mode) for r in te]; fh = np.array([fr[i] or (th is not None and te[i]['judge'] <= th) for i in range(len(te))], float); fj = np.array([(tj is not None and r['judge'] <= tj) for r in te], float)
    kind = np.array([r['kind'] for r in te]); g = np.array([r['group'] for r in te]); eH = kind == 'harmless'; eE = kind == 'error'; res['test'] = {}
    for name, fl in (('hybrid', fh), ('judge_alone', fj), ('rules_only', np.array(fr, float))):
        res['test'][name] = dict(catch=gboot(fl[eE].tolist(), g[eE].tolist()), harmless_flagged=gboot(fl[eH].tolist(), g[eH].tolist()))
    d = fh[eE] - fj[eE]; res['test']['paired_catch_diff_hybrid_minus_judge'] = gboot(d.tolist(), g[eE].tolist()); res['test']['n'] = dict(errors=int(eE.sum()), harmless=int(eH.sum()), groups=len(set(g)))
    res['test']['by_organ'] = {o: dict(n_err=int((eE & (np.array([r['organ'] for r in te]) == o)).sum()), hybrid_catch=float(fh[eE & (np.array([r['organ'] for r in te]) == o)].mean()), judge_catch=float(fj[eE & (np.array([r['organ'] for r in te]) == o)].mean())) for o in ('breast', 'thyroid', 'fetal') if (eE & (np.array([r['organ'] for r in te]) == o)).sum()}
    h = res['test']['hybrid']; res['pass'] = dict(catch_ge_80=bool(h['catch'][0] >= 0.80), harmless_le_5_6=bool(h['harmless_flagged'][0] <= MAXH), beats_judge_ci_excludes_0=bool(res['test']['paired_catch_diff_hybrid_minus_judge'][1] > 0)); res['pass']['passed'] = all(res['pass'].values())
    st = json.load(open(GM.P('f_status.json'))) if os.path.exists(GM.P('f_status.json')) else {}; res['status'] = dict(st, planned_pairs=len(GM.f_pairs()), judged_pairs=len(R))
    json.dump(res, open(P('results.json'), 'w'), indent=1); print(json.dumps(res['pass'])); print(json.dumps(res['test'], indent=0)[:1200]); print(json.dumps(res['tuning'], indent=0)[:900])

if __name__ == '__main__': main()
