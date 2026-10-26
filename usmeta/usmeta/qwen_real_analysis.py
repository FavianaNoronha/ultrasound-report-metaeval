"""Analysis for the Qwen real-report run (TEST split only for final numbers). python3 -m usmeta.qwen_real_analysis OUT_DIR"""
import json, sys, os, collections
import numpy as np
from scipy.stats import spearmanr
from . import qwen_real as Q, schema, location, unified, graders
from .step10d_analysis import gboot

THIRDS = {f'{v}-{h}' for v in ('upper', 'middle', 'lower') for h in ('left', 'central', 'right')}
CAT = dict(lesion='missed/false finding', count='false/missed finding (count)', side='wrong location', pos='wrong location', size_mm='wrong measurement', size_pct='wrong measurement', hc_mm='wrong measurement',
           birads='wrong severity/category', tirads='wrong severity/category', path='wrong severity/category', hist='wrong severity/category', orient='wrong severity/category')

def judge_cmp(ref, cand, a):
    """one reference attribute vs the report: 'correct' | 'wrong' | 'not stated' | 'not comparable' (different unit/vocabulary)"""
    if cand is None: return 'not stated'
    if a == 'pos': return 'correct' if cand == ref else ('wrong' if cand in THIRDS else 'not comparable')
    if a in ('size_pct',): return 'not comparable'
    if a == 'size_mm': return 'not comparable'
    if a == 'hc_mm': return 'correct' if schema.attr_credit('hc_mm', ref, cand) >= 0.5 else 'wrong'
    if a == 'count': return 'correct' if int(cand) == int(ref) else 'wrong'
    return 'correct' if str(cand).lower() == str(ref).lower() else 'wrong'

def main(out):
    os.makedirs(out, exist_ok=True); cs = [c for c in Q.cases() if c['split'] == 'test']; E = {json.loads(l)['key']: json.loads(l) for l in open(f'{Q.OUTD}/extract_test.jsonl')}
    J = {v: {json.loads(l)['key']: json.loads(l)['result'] for l in open(f'{Q.OUTD}/judge_{v}.jsonl')} for v in ('v1', 'v2')}
    B = {json.loads(l)['key']: json.loads(l) for l in open(f'{Q.OUTD}/boxes.jsonl')}
    recs = {c['case_id']: c for ds in ('BUSBRA', 'TN3K', 'TN5000', 'HC18') for c in unified.load(ds)}
    res = collections.defaultdict(dict); attr = collections.defaultdict(lambda: collections.Counter()); rows = []
    bleu, chrf = graders.make('bleu'), graders.make('chrf')
    for c in cs:
        if c['flipped']: continue
        k, ds, ref = c['key'], c['dataset'], c['ref_facts']; f = (E.get(k) or {}).get('facts') or {}
        rf = schema.to_findings(ref, c['organ']); cf = schema.to_findings(f, c['organ']); p, r, f1, cr = schema.finding_scores(rf, cf)
        for (e, a), v in schema.flat_attrs(rf).items():
            a0 = a if e not in ('calcifications', 'halo', 'foci') else 'status'
            key = 'lesion' if (e, a) == ('lesion', 'status') else a
            cand = f.get('lesion') if key == 'lesion' else f.get(key)
            attr[(ds, key)][judge_cmp(v if key != 'lesion' else 'present', cand if key != 'lesion' else cand, key) if key != 'lesion' else ('correct' if cand == 'present' else ('wrong' if cand == 'absent' else 'not stated'))] += 1
        row = dict(key=k, dataset=ds, group=c['group_id'], precision=p, recall=r, finding_f1=f1)
        for v in ('v1', 'v2'):
            j = J[v].get(k); row[f'sentence_f1_{v}'] = j['f1'] if j else None; row[f'judge_score_{v}'] = j['judge'] if j else None; row[f'judge_cats_{v}'] = (j['cats'] if j else None); row[f'judge_nerr_{v}'] = (j['n_err'] if j else None)
        row['bleu'] = bleu.score(c['reference'], c['report']); row['chrf'] = chrf.score(c['reference'], c['report'])
        b = B.get(k); rec = recs[c['case_id']]
        if b is not None:
            m = location.gt_mask(rec); gt = [list(map(float, x)) for x in rec['region']['boxes']]
            if m is None:
                m = np.zeros((rec['region']['H'], rec['region']['W']), bool)
                for x in gt: m[int(x[1]):int(x[3]), int(x[0]):int(x[2])] = True
            gtm = np.zeros_like(m)
            for x in gt: gtm[int(x[1]):int(x[3]), int(x[0]):int(x[2])] = True
            bx = b['boxes']; row['parsed'] = bool(bx); row['iou'] = location.best_match_iou(gt, bx) if bx else 0.0
            row['support_gtbox'] = float(np.mean([location.inside_fraction(x, gtm) >= 0.5 for x in bx])) if bx else 0.0
            if bx:
                u = np.zeros_like(m)
                for x in bx: u[max(int(x[1]), 0):max(int(x[3]), 0), max(int(x[0]), 0):max(int(x[2]), 0)] = True
                row['pix_precision'] = float((u & m).sum() / u.sum()) if u.sum() else 0.0; row['pix_recall'] = float((u & m).sum() / m.sum()) if m.sum() else 0.0
        rows.append(row)
    json.dump(rows, open(f'{out}/rows.json', 'w'))
    # per dataset summary
    summ = {}
    for ds in sorted({r['dataset'] for r in rows}):
        R = [r for r in rows if r['dataset'] == ds]; g = lambda key: [r[key] for r in R if r.get(key) is not None]; gg = lambda key: [r['group'] for r in R if r.get(key) is not None]
        s = dict(n=len(R), groups=len({r['group'] for r in R}))
        for key in ('precision', 'recall', 'finding_f1', 'sentence_f1_v1', 'sentence_f1_v2', 'judge_score_v1', 'judge_score_v2', 'bleu', 'chrf', 'iou', 'support_gtbox', 'pix_precision', 'pix_recall'):
            if g(key): s[key] = gboot(g(key), gg(key))
        if g('iou'): s['iou_ge_0.5'] = float(np.mean([x >= 0.5 for x in g('iou')])); s['iou_n'] = len(g('iou')); s['parse_rate'] = float(np.mean([bool(r.get('parsed')) for r in R if 'parsed' in r]))
        for v in ('v1', 'v2'):
            ne = [r[f'judge_nerr_{v}'] for r in R if r.get(f'judge_nerr_{v}') is not None]
            if ne: s[f'judge_{v}_lists_any_error'] = float(np.mean([x > 0 for x in ne])); cats = collections.Counter(c for r in R if r.get(f'judge_cats_{v}') for c in r[f'judge_cats_{v}']); s[f'judge_{v}_categories'] = dict(cats)
        # Spearman text-score vs IoU
        iou = [r for r in R if r.get('iou') is not None]
        s['spearman_vs_iou'] = {k: (float(spearmanr([r[k] for r in iou], [r['iou'] for r in iou])[0]) if len(iou) > 4 and len({r[k] for r in iou if r.get(k) is not None}) > 1 and all(r.get(k) is not None for r in iou) else None) for k in ('bleu', 'chrf', 'finding_f1', 'sentence_f1_v2')}
        summ[ds] = s
    attrs = {f'{k[0]}|{k[1]}': dict(v) for k, v in attr.items()}
    # flip test
    flips = []
    for c in Q.cases():
        if c['flipped'] and c['split'] == 'test':
            o = f"{c['case_id']}|orig"; f = c['key']; fo, ff = (E.get(o) or {}).get('facts'), (E.get(f) or {}).get('facts')
            if fo is None or ff is None: continue
            keys = set(fo) | set(ff); same = [fo.get(a) == ff.get(a) for a in keys if a not in ('side', 'pos')]
            bo, bf = B.get(o), B.get(f); mirror_iou = location.best_match_iou(bo['boxes'], bf['boxes']) if bo and bf and bo['boxes'] and bf['boxes'] else None
            flips.append(dict(case=c['case_id'], dataset=c['dataset'], facts_same_share=float(np.mean(same)) if same else None, side_changed=fo.get('side') != ff.get('side') if ('side' in fo or 'side' in ff) else None, box_iou_orig_vs_mirrored_back=mirror_iou))
    json.dump(dict(summary=summ, attributes=attrs, flips=flips), open(f'{out}/results.json', 'w'), indent=1)
    return summ, attrs, flips

if __name__ == '__main__': main(sys.argv[1])
