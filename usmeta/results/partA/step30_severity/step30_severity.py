"""Step 30: severity breakdown from SAVED scores (no judge, writer or segmentation model call). NEW file.
For each organ and each severity level (1 minor, 2 major, 3 critical; OUR provisional labels, not clinician-confirmed): AUROC of planted error vs harmless rewording (small / matched / large) per case, group bootstrap
(1,000 resamples, seed 0, cells under 30 groups 'too small to compare'), and the Spearman correlation between severity and score drop (drop = 1 - score; identical copies score 1.0).
Scorers: BLEU, ROUGE-L, chrF, BERTScore, RaTEScore, finding_f1 (saved test scores, bench_test_v2d), Gemma sentence_f1 / judge_score (judged subset, Steps 10d + 12), and the Step 20 tolerance-aware image check
(re-scored per candidate from the SAVED masks: oracle-box MedSAM of Step 16 and the Step 29 U-Net; bench_v2d rows of the 228 scans; only errors in mask-checkable fields).
    python3 -m usmeta.step30_severity"""
import os, json, collections, functools, sys, platform, time, subprocess
import numpy as np
from scipy.stats import spearmanr
from . import step19_pairs as P, step20, step24_box_reliability as s24, step29_seg as G, partb, schema
from .layer0 import auroc_case
from .step10d_analysis import gboot

ROOT = G.ROOT; OUT = os.path.join(ROOT, 'results', 'partA', 'step30_severity'); HT = ('small', 'matched', 'large'); MIN_G = 30
ORG = {'BrEaST': 'breast', 'BUS-BRA': 'breast', 'BUSI': 'breast', 'UDIAT': 'breast', 'BUS-UCLM': 'breast', 'TN3K': 'thyroid', 'TN5000': 'thyroid', 'DDTI': 'thyroid', 'HC18': 'fetal head', 'FetalHead': 'fetal head'}
TEXT = [('bleu', 'BLEU'), ('rougeL', 'ROUGE-L'), ('chrf', 'chrF'), ('bertscore[roberta-large]', 'BERTScore'), ('ratescore', 'RaTEScore'), ('finding_f1', 'finding_f1 (upper bound)'), ('sentence_f1', 'judge sentence_f1'), ('judge_score', 'judge_score')]

def text_scores():
    rows = [json.loads(l) for l in open(os.path.join(ROOT, 'bench_test_v2d.jsonl'))]
    sc = {**P.scores_of(os.path.join(ROOT, 'scores_test_layer0.json')), 'finding_f1': P.scores_of(os.path.join(ROOT, 'scores_test_layer1.json'))['finding_f1'], **P.judge_lookup([os.path.join(ROOT, 'results/partA/step10d_test_results/judge_test_v2.jsonl'), os.path.join(ROOT, 'judge_big_v2.jsonl')])}
    return rows, sc

def image_scores():
    """per-candidate Step 20 image-check score for the 228 scans, from saved masks (MedSAM exact box, Step 29 U-Net)"""
    from PIL import Image
    ch = json.load(open(os.path.join(ROOT, 'results', 'partA', 'step20_tolerance_image_check', 'tuning_devval.json')))['chosen']; tau, pm = ch['tau'], ch['position']
    schema.extract_rule = functools.lru_cache(maxsize=None)(schema.extract_rule)
    sel = s24.selection(); ids = {s['case_id']: s for s in sel}; recs = step20.recs_all(); organ_of = {d: o for o, ds in s24.DATASETS_ORGAN.items() for d in ds}; rows = []
    for l in open(os.path.join(ROOT, 'bench_v2d.jsonl')):
        r = json.loads(l)
        if r['case_id'] in ids: rows.append(r)
    S = {'image_medsam_oracle_box': {}, 'image_unet_label_free': {}}; masks = {}
    for cid in ids:
        pmo, _ = s24.load(s24.mask_file(cid, 'exact', 'exact')); z = np.load(os.path.join(G.LOCAL, 'masks', cid.replace(':', '_').replace('/', '_') + '.npz')); H, W = map(int, z['shape']); pmu = np.unpackbits(z['mask'])[:H * W].reshape(H, W).astype(bool)
        masks[cid] = {'image_medsam_oracle_box': partb.pred_meas(recs[cid], pmo), 'image_unet_label_free': partb.pred_meas(recs[cid], pmu)}
    for r in rows:
        if r['kind'] == 'error' and r['field'] not in step20.CHECKABLE: continue
        for name in S: S[name][(r['reference'], r['candidate'])] = step20.tol_score(r['candidate'], r['organ'], masks[r['case_id']][name], tau, pm)
    return rows, S

def build_cases(rows, with_organ=lambda r: ORG[r['dataset']], err_ok=lambda r: True):
    C = {}
    for r in rows:
        if r['kind'] == 'error' and err_ok(r) and r['severity'] in (1, 2, 3): c = C.setdefault(r['case_id'], dict(organ=with_organ(r), group=f"{r['dataset']}:{r['group_id']}", E=collections.defaultdict(list), H=collections.defaultdict(list))); c['E'][r['severity']].append(r)
        elif r['kind'] == 'harmless' and r['harmless_type'] in HT: c = C.setdefault(r['case_id'], dict(organ=with_organ(r), group=f"{r['dataset']}:{r['group_id']}", E=collections.defaultdict(list), H=collections.defaultdict(list))); c['H'][r['harmless_type']].append(r)
    return C

def auroc_cells(C, sc, name):
    out = {}
    for org in ('breast', 'thyroid', 'fetal head', 'ALL'):
        for sev in (1, 2, 3):
            for ht in HT:
                v, g = [], []
                for cid, c in C.items():
                    if org != 'ALL' and c['organ'] != org: continue
                    e = [sc[name].get((r['reference'], r['candidate'])) for r in c['E'][sev]]; h = [sc[name].get((r['reference'], r['candidate'])) for r in c['H'][ht]]; e = [x for x in e if x is not None]; h = [x for x in h if x is not None]
                    if e and h: v.append(auroc_case(e, h)); g.append(c['group'])
                out[f'{org}|{sev}|{ht}'] = dict(cases=len(v), groups=len(set(g)), auroc=gboot(v, g) if v else None, too_small=len(set(g)) < MIN_G)
    return out

def spearman_cells(C, sc, name):
    out = {}
    for org in ('breast', 'thyroid', 'fetal head', 'ALL'):
        sev, drop, grp = [], [], []
        for cid, c in C.items():
            if org != 'ALL' and c['organ'] != org: continue
            for s_, rs in c['E'].items():
                for r in rs:
                    x = sc[name].get((r['reference'], r['candidate']))
                    if x is not None: sev.append(s_); drop.append(1 - x); grp.append(c['group'])
        sev, drop = np.array(sev), np.array(drop)
        if len(sev) < 10 or len(set(sev)) < 2 or len(set(drop)) < 2: out[org] = dict(n=len(sev), groups=len(set(grp)), spearman=None, too_small=True); continue
        rho = float(spearmanr(sev, drop)[0]); idx = collections.defaultdict(list)
        for i, g in enumerate(grp): idx[g].append(i)
        keys = list(idx); rng = np.random.default_rng(0); m = []
        for _ in range(1000):
            pick = rng.integers(0, len(keys), len(keys)); ii = np.concatenate([idx[keys[k]] for k in pick])
            if len(set(sev[ii])) > 1 and len(set(drop[ii])) > 1: m.append(spearmanr(sev[ii], drop[ii])[0])
        out[org] = dict(n=int(len(sev)), groups=len(set(grp)), spearman=[rho, float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))], too_small=len(set(grp)) < MIN_G)
    return out

def main():
    os.makedirs(OUT, exist_ok=True); rows, sc = text_scores(); C = build_cases(rows); res = dict(auroc={}, spearman={}, counts={})
    for org in ('breast', 'thyroid', 'fetal head'):
        for sev in (1, 2, 3):
            e = [r for c in C.values() if c['organ'] == org for r in c['E'][sev]]; res['counts'][f'{org}|{sev}'] = dict(error_rows=len(e), cases=len({r['case_id'] for r in e}), groups=len({f"{r['dataset']}:{r['group_id']}" for r in e}), fields=dict(collections.Counter(r['field'] for r in e)))
    for n, _ in TEXT: res['auroc'][n] = auroc_cells(C, sc, n); res['spearman'][n] = spearman_cells(C, sc, n)
    irows, IS = image_scores(); IC = build_cases(irows, err_ok=lambda r: r['field'] in step20.CHECKABLE)
    for n in IS: res['auroc'][n] = auroc_cells(IC, IS, n); res['spearman'][n] = spearman_cells(IC, IS, n)
    res['image_counts'] = {f'{org}|{sev}': dict(error_rows=len([r for c in IC.values() if c['organ'] == org for r in c['E'][sev]]), cases=len([1 for c in IC.values() if c['organ'] == org and c['E'][sev]])) for org in ('breast', 'thyroid') for sev in (1, 2, 3)}
    json.dump(res, open(os.path.join(OUT, 'results.json'), 'w'), indent=1); print('saved results.json')

if __name__ == '__main__': main()
