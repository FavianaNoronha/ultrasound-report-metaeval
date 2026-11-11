"""Step 35: limit of detection. NEW file; Step 21b saved candidates and scores are reused, the frozen templates / scorers are imported unchanged.
For each scorer and field, the smallest error at which the AUROC of planted size / head-circumference errors vs the matched one-word synonyms of the same reference reaches 0.80, with 95% CIs (group bootstrap, 1,000 resamples, seed 0).
Size errors (breast size_mm / size_pct, thyroid size_pct): multiplicative factors of the stated size; Step 21b factors 0.5, 0.7, 0.8, 0.9, 0.95, 1.3, 1.5, 2.0 (saved scores reused) plus NEW 1.05, 1.10, 1.25; levels are the relative error |factor - 1| (both directions pooled): 5, 10, 20, 25, 30, 50, 100 %.
Head circumference (fetal head, hc_mm): NEW additive shifts of +-1, 2, 5, 10, 20 mm of the stated value (both signs pooled).
LOD = smallest level whose pooled AUROC >= 0.80 (point estimate); its CI = percentiles of the same rule over the bootstrap resamples (resamples where no level reaches 0.80 count as "above the largest level tested"). Non-monotone curves are flagged (a larger level below 0.80 after the LOD).
Scorers: BLEU, ROUGE-L, chrF, BERTScore, RaTEScore, finding_f1 (upper bound), Gemma judge_score / sentence_f1 (capped: 12 cases per dataset for the NEW candidates; Step 21b replies reused), the Step 16 predicted-mask check (oracle box, exact rule) and the Step 29 label-free U-Net check (tolerance rule, breast and thyroid scans).
    python3 -m usmeta.step35_lod build | text | judge | analyse"""
import os, sys, json, math, random, collections, time, functools
import numpy as np
from . import templates_v2 as T, layer0, layer1, partb, layer3, unified, schema, step20, step21_dose as D21, step29_seg as G29
from .layer0 import auroc_case
from .step10d_analysis import gboot

ROOT = D21.ROOT; OUT = os.path.join(ROOT, 'results', 'partA', 'step35_lod'); P = lambda f: os.path.join(OUT, f); THRESH = 0.80
NEW_FACTORS = [1.05, 1.10, 1.25]; HC_SHIFTS = [-20, -10, -5, -2, -1, 1, 2, 5, 10, 20]; SIZE = ('size_mm', 'size_pct'); N_JUDGE = 12
SIZE_LEVELS = [0.05, 0.10, 0.20, 0.25, 0.30, 0.50, 1.00]; HC_LEVELS = [1, 2, 5, 10, 20]
ORGAN = D21.ORGAN; LOADER = D21.LOADER

def rel_level(fac): return round(abs(fac - 1.0), 2)

def build():
    """NEW candidates only (size factors 1.05, 1.10, 1.25; HC shifts) from the test references of bench_test_v2d; the Step 21b candidates keep their saved scores"""
    os.makedirs(OUT, exist_ok=True); bench = [json.loads(l) for l in open(os.path.join(ROOT, 'bench_test_v2d.jsonl'))]; by = collections.defaultdict(list)
    for b in bench: by[b['case_id']].append(b)
    recs = {}
    for ds in ORGAN:
        for c in T.load(LOADER.get(ds, ds)): recs[c['case_id']] = c
    rows = []; skipped = 0
    for cid, bs in by.items():
        rec = recs[cid]; f = T.facts(rec); ref = bs[0]['reference']; key = next((k for k in SIZE + ('hc_mm',) if k in f), None)
        if key is None or T.render(f, rec['organ'], 'standard') != ref: skipped += 1; continue
        v, prov = f[key]; base = dict(case_id=cid, dataset=bs[0]['dataset'], organ=ORGAN[bs[0]['dataset']], group_id=bs[0]['group_id'], kind='error', field=key, reference=ref)
        if key == 'hc_mm':
            for sh in HC_SHIFTS:
                new = round(v + sh, 1)
                if new <= 0: continue
                g = dict(f); g[key] = (new, prov); txt = T.render(g, rec['organ'], 'standard')
                if txt != ref: rows.append(dict(base, factor=None, shift_mm=sh, level=abs(sh), old=v, new=new, candidate=txt))
        else:
            for fac in NEW_FACTORS:
                new = round(v * fac); new = min(new, 100) if key == 'size_pct' else new
                if new == v or new <= 0: continue
                g = dict(f); g[key] = (new, prov); txt = T.render(g, rec['organ'], 'standard')
                if txt != ref: rows.append(dict(base, factor=fac, shift_mm=None, level=rel_level(fac), old=v, new=new, candidate=txt))
    open(P('candidates_new.jsonl'), 'w').write(''.join(json.dumps(r) + '\n' for r in rows)); print(len(rows), 'new rows;', skipped, 'cases skipped'); print(collections.Counter((r['organ'], r['field'], r['level']) for r in rows).most_common(8))

def text_scores():
    rows = [json.loads(l) for l in open(P('candidates_new.jsonl'))]; tmp = [dict(r, organ={'breast': 'breast', 'thyroid': 'thyroid', 'fetal head': 'fetal'}[r['organ']]) for r in rows]
    open(P('_bench.jsonl'), 'w').write(''.join(json.dumps(r) + '\n' for r in tmp)); layer1.score(P('_bench.jsonl'), P('scores_layer1.json')); layer0.score(P('_bench.jsonl'), P('scores_layer0.json'))

def judge():
    from . import judge2, judge2_test
    rows = [json.loads(l) for l in open(P('candidates_new.jsonl'))]; rng = random.Random(0); by = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in rows: by[r['dataset']][r['case_id']].append(r)
    jids = set()
    for f in ('judge_test_v2_bench.jsonl', 'judge_big_v2_bench.jsonl'): jids |= {json.loads(l)['case_id'] for l in open(os.path.join(ROOT, f))}
    plan = []
    for ds, cs in by.items():
        ids = sorted(c for c in cs if c in jids); rng.shuffle(ids)
        for c in ids[:N_JUDGE]: plan += cs[c]
    out = P('judge_replies.jsonl'); done = {(json.loads(l)['reference'], json.loads(l)['candidate']) for l in open(out)} if os.path.exists(out) else set()
    todo = list(dict.fromkeys((r['reference'], r['candidate']) for r in plan if (r['reference'], r['candidate']) not in done)); print(len(plan), 'rows;', len(todo), 'pairs to judge', flush=True)
    sc = judge2_test.SC(judge2.PROMPT_V2); t0 = time.time()
    for i, (a, b) in enumerate(todo):
        s = sc.run(a, b); open(out, 'a').write(json.dumps(dict(reference=a, candidate=b, result=s)) + '\n')
        if i % 25 == 0: print(i, len(todo), round(time.time() - t0), 's', flush=True)
    print('done', round(time.time() - t0), 's')

def lookups():
    S = D21.lookups()                                                                                           # Step 21b scores (old candidates) + its judge replies
    for f in ('scores_layer0.json', 'scores_layer1.json'):
        if os.path.exists(P(f)):
            s = json.load(open(P(f))); Pp = [tuple(p) for p in s['pairs']]
            for n, a in s['scores'].items():
                if n in S: S[n].update(dict(zip(Pp, a)))
    if os.path.exists(P('judge_replies.jsonl')):
        for l in open(P('judge_replies.jsonl')):
            d = json.loads(l)
            if d['result'] is not None: S['sentence_f1'][(d['reference'], d['candidate'])] = d['result']['f1']; S['judge_score'][(d['reference'], d['candidate'])] = d['result']['judge']
    return S

def all_rows():
    old = [json.loads(l) for l in open(D21.P('candidates.jsonl'))]; rows = []
    for r in old:
        if r['kind'] == 'matched': rows.append(r)
        elif r['field'] == 'hc_mm': continue            # Step 21b HC errors were multiplicative; the additive mm shifts below replace them for the HC limit of detection
        else: rows.append(dict(r, level=rel_level(r['factor']), shift_mm=None))
    rows += [json.loads(l) for l in open(P('candidates_new.jsonl'))]
    # matched synonyms of the fetal-head cases are in the old file with kind 'matched'; keep them
    return rows

def image_scores(rows):
    out = D21.image_scores(rows)                                                                                  # Step 16 predicted masks, oracle box, exact rule (as Step 21b)
    ch = json.load(open(os.path.join(ROOT, 'results', 'partA', 'step20_tolerance_image_check', 'tuning_devval.json')))['chosen']; tau, pm = ch['tau'], ch['position']; unet = {}
    md = os.path.join(G29.LOCAL, 'masks'); recs = step20.recs_all(); M = {}
    for fn in os.listdir(md):
        cid = None
    sel = json.load(open(os.path.join(partb.LOCAL, 'selected.json')))
    for s in sel:
        if s['dataset'] in ('HC18', 'FetalHead'): continue
        f = os.path.join(md, s['case_id'].replace(':', '_').replace('/', '_') + '.npz')
        if not os.path.exists(f): continue
        z = np.load(f); H, W = map(int, z['shape']); pm_ = np.unpackbits(z['mask'])[:H * W].reshape(H, W).astype(bool); M[s['case_id']] = partb.pred_meas(recs[s['case_id']], pm_)
    schema.extract_rule = functools.lru_cache(maxsize=None)(schema.extract_rule)
    for r in rows:
        if r['case_id'] in M: unet[(r['reference'], r['candidate'])] = step20.tol_score(r['candidate'], {'breast': 'breast', 'thyroid': 'thyroid', 'fetal head': 'fetal'}[r['organ']], M[r['case_id']], tau, pm)
    return out, unet

def lod_of(auc_by_level, levels):
    for i, lv in enumerate(levels):
        v = auc_by_level.get(lv)
        if v is not None and v >= THRESH: return i
    return None

def analyse():
    rows = all_rows(); S = lookups(); S['image_medsam_oracle_exact'], S['image_unet_tolerance'] = image_scores(rows); names = ['bleu', 'rougeL', 'chrf', 'bertscore[roberta-large]', 'ratescore', 'finding_f1', 'sentence_f1', 'judge_score', 'image_medsam_oracle_exact', 'image_unet_tolerance']
    by = collections.defaultdict(list)
    for r in rows: by[r['case_id']].append(r)
    res = {}; rng = np.random.default_rng(0)
    for org, field in (('breast', 'size_mm'), ('breast', 'size_pct'), ('thyroid', 'size_pct'), ('fetal head', 'hc_mm')):
        levels = HC_LEVELS if field == 'hc_mm' else SIZE_LEVELS; cs = {c: rs for c, rs in by.items() if rs[0]['organ'] == org and any(r['kind'] == 'error' and r['field'] == field for r in rs)}
        for n in names:
            sc = S[n]; per = {lv: [] for lv in levels}; grp = {lv: [] for lv in levels}
            for c, rs in cs.items():
                h = [sc.get((r['reference'], r['candidate'])) for r in rs if r['kind'] == 'matched']; h = [x for x in h if x is not None]
                if not h: continue
                for lv in levels:
                    e = [sc.get((r['reference'], r['candidate'])) for r in rs if r['kind'] == 'error' and r['field'] == field and r['level'] == lv]; e = [x for x in e if x is not None]
                    if e: per[lv].append(auroc_case(e, h)); grp[lv].append(rs[0]['group_id'])
            if not any(per[lv] for lv in levels): continue
            point = {lv: (float(np.mean(per[lv])) if per[lv] else None) for lv in levels}; ng = {lv: len(set(grp[lv])) for lv in levels}; ci = {lv: (gboot(per[lv], grp[lv]) if per[lv] else None) for lv in levels}
            lod = lod_of(point, levels); allg = sorted({g for lv in levels for g in grp[lv]}); gi = {g: i for i, g in enumerate(allg)}
            arrs = {lv: (np.array([gi[g] for g in grp[lv]]), np.array(per[lv])) for lv in levels if per[lv]}; boots = []
            for _ in range(1000):
                counts = np.bincount(rng.integers(0, len(allg), len(allg)), minlength=len(allg)); pt = {}
                for lv, (g_, a_) in arrs.items():
                    w = counts[g_]; pt[lv] = float((w * a_).sum() / w.sum()) if w.sum() else None
                boots.append(lod_of(pt, levels))
            enc = [(len(levels) if b is None else b) for b in boots]; lo, hi = int(np.percentile(enc, 2.5)), int(np.percentile(enc, 97.5)); lab = lambda i: ('>' + str(levels[-1])) if i >= len(levels) else str(levels[i])
            nonmono = lod is not None and any((point[levels[j]] is not None and point[levels[j]] < THRESH) for j in range(lod + 1, len(levels)))
            res[f'{n}|{org}|{field}'] = dict(levels=levels, auroc=point, auroc_ci=ci, groups=ng, lod=(levels[lod] if lod is not None else None), lod_ci=[lab(lo), lab(hi)], nonmonotone=nonmono, too_small_levels=[lv for lv in levels if ng[lv] < 30])
    json.dump(res, open(P('results.json'), 'w'), indent=1); print(len(res), 'cells')

if __name__ == '__main__':
    {'build': build, 'text': text_scores, 'judge': judge, 'analyse': analyse}[sys.argv[1]]()
