"""Step 14 analysis: MedGemma-1.5-4B vs Qwen2.5-VL-3B on the same TEST scans (orig only; flips handled separately).
Extractor and judge are Gemma-2-9B for Qwen's reports and Qwen2.5-7B for MedGemma's (a writer is never graded by its own family), so finding_f1 and sentence_check are
NOT identical measuring sticks across the two writers; Layer 0 scorers and box IoU are family-free and are the primary basis for the ranking comparison.
    python3 -m usmeta.medgemma_analysis OUT_DIR"""
import json, os, sys, collections, re
import numpy as np
from . import qwen_real as Q, medgemma as M, schema, location, unified, graders
from .step10d_analysis import gboot
LAY0 = ['bleu', 'rougeL', 'chrf', 'bertscore[roberta-large]', 'ratescore']
MIN_N = 30

def load_jsonl(p): return [json.loads(l) for l in open(p)] if os.path.exists(p) else []

# ---------------------------------------------------------------- box conventions (chosen on DEV scans only)
def mg_boxes(raw, W, H, conv):
    nums = [[float(x) for x in m] for m in re.findall(r'\[\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\]', raw)]
    out = []
    for m in re.finditer(r'"xmin"\s*:\s*(-?[\d.]+)\s*,\s*"ymin"\s*:\s*(-?[\d.]+)\s*,\s*"xmax"\s*:\s*(-?[\d.]+)\s*,\s*"ymax"\s*:\s*(-?[\d.]+)', raw):   # named-key variant: no axis ambiguity
        xa, ya, xb, yb = [float(v) for v in m.groups()]; sx, sy = ((W / 1000, H / 1000) if '1000' in conv else (W / 896, H / 896) if '896' in conv else (1, 1))
        out.append([min(xa, xb) * sx, min(ya, yb) * sy, max(xa, xb) * sx, max(ya, yb) * sy])
    for a, b, c, d in nums:
        if conv == 'yxyx1000': x0, y0, x1, y1 = b / 1000 * W, a / 1000 * H, d / 1000 * W, c / 1000 * H
        elif conv == 'xyxy1000': x0, y0, x1, y1 = a / 1000 * W, b / 1000 * H, c / 1000 * W, d / 1000 * H
        elif conv == 'yxyx896': x0, y0, x1, y1 = b / 896 * W, a / 896 * H, d / 896 * W, c / 896 * H
        elif conv == 'xyxy896': x0, y0, x1, y1 = a / 896 * W, b / 896 * H, c / 896 * W, d / 896 * H
        else: x0, y0, x1, y1 = a, b, c, d
        out.append([min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)])
    return out

CONVS = ['yxyx1000', 'xyxy1000', 'yxyx896', 'xyxy896', 'xyxy_abs']
def pick_convention(R):
    """highest mean best-match IoU on the dev scans (the only use of dev boxes)"""
    B = [b for b in load_jsonl(M.OUT_BOXES) if b['split'] in ('dev', 'val')]; C = {c['key']: c for c in Q.cases()}; sc = {}
    for conv in CONVS:
        v = []
        for b in B:
            c = C[b['key']]; gt = [list(map(float, x)) for x in R[c['case_id']]['region']['boxes']]; W, H = b['size']; bx = mg_boxes(b['raw'], W, H, conv)
            v.append(location.best_match_iou(gt, bx) if bx else 0.0)
        sc[conv] = float(np.mean(v)) if v else None
    return max(sc, key=lambda k: sc[k] or -1), sc, len(B)

def fscores(ref, facts, organ):
    rf = schema.to_findings(ref, organ); cf = schema.to_findings(facts or {}, organ); return schema.finding_scores(rf, cf)[:3]

def per_case(out):
    R = M.recs(); cs = {c['key']: c for c in Q.cases() if c['split'] == 'test' and not c['flipped']}
    mrep = {r['key']: r for r in load_jsonl(M.OUT_REPORTS)}
    EQ = {r['key']: r for r in load_jsonl(f'{Q.OUTD}/extract_test_v2.jsonl')}; EM = {r['key']: r for r in load_jsonl('extract_medgemma_v2.jsonl')}
    JQ = {v: {r['key']: r['result'] for r in load_jsonl(f'{Q.OUTD}/judge_{v}.jsonl')} for v in ('v1', 'v2')}; JM = {v: {r['key']: r['result'] for r in load_jsonl(f'judge_medgemma_{v}q.jsonl')} for v in ('v1', 'v2')}
    BQ = {r['key']: r for r in load_jsonl(f'{Q.OUTD}/boxes.jsonl')}; conv, convsc, ndev = pick_convention(R); BM = {r['key']: r for r in load_jsonl(M.OUT_BOXES)}
    l0 = json.load(open(f'{out}/layer0_scores.json')) if os.path.exists(f'{out}/layer0_scores.json') else {}
    rows = []
    for k, c in cs.items():
        if k not in mrep: continue
        rec = R[c['case_id']]; gt = [list(map(float, x)) for x in rec['region']['boxes']]; mask = location.gt_mask(rec); gtm = np.zeros((rec['region']['H'], rec['region']['W']), bool)
        for x in gt: gtm[int(x[1]):int(x[3]), int(x[0]):int(x[2])] = True
        row = dict(key=k, dataset=c['dataset'], group=c['group_id'])
        for w, E, J, B in (('qwen', EQ, JQ, BQ), ('medgemma', EM, JM, BM)):
            f = (E.get(k) or {}).get('facts'); p, r_, f1 = fscores(c['ref_facts'], f, c['organ']); row[f'{w}_precision'], row[f'{w}_recall'], row[f'{w}_finding_f1'] = p, r_, f1
            for v in ('v1', 'v2'):
                j = J[v].get(k); row[f'{w}_sentence_f1_{v}'] = j['f1'] if j else None; row[f'{w}_judge_score_{v}'] = j['judge'] if j else None; row[f'{w}_nerr_{v}'] = j['n_err'] if j else None
            b = B.get(k)
            if b is not None:
                if w == 'qwen': bx = b['boxes']
                else: bx = mg_boxes(b['raw'], b['size'][0], b['size'][1], conv)
                row[f'{w}_parsed'] = bool(bx); row[f'{w}_iou'] = location.best_match_iou(gt, bx) if bx else 0.0
                row[f'{w}_support_gtbox'] = float(np.mean([location.inside_fraction(x, gtm) >= 0.5 for x in bx])) if bx else 0.0
            for s in LAY0:
                v = l0.get(f'{w}|{k}|{s}')
                if v is not None: row[f'{w}_{s}'] = v
        rows.append(row)
    return rows, dict(box_convention=conv, convention_scores_dev=convsc, dev_boxes=ndev)

SCORERS = [('bleu', 'higher'), ('rougeL', 'higher'), ('chrf', 'higher'), ('bertscore[roberta-large]', 'higher'), ('ratescore', 'higher'), ('finding_f1', 'higher'), ('sentence_f1_v2', 'higher'), ('sentence_f1_v1', 'higher'), ('iou', 'higher')]

def compare(rows, datasets):
    out = {}
    for name, ds in datasets.items():
        R = [r for r in rows if r['dataset'] in ds]; n = len(R); groups = len({r['group'] for r in R}); d = {}
        for s, _ in SCORERS:
            q = [r.get(f'qwen_{s}') for r in R]; m = [r.get(f'medgemma_{s}') for r in R]; ok = [i for i in range(n) if q[i] is not None and m[i] is not None]
            if not ok: continue
            qv = [q[i] for i in ok]; mv = [m[i] for i in ok]; gr = [R[i]['group'] for i in ok]; diff = [a - b for a, b in zip(qv, mv)]
            ci = gboot(diff, gr)
            d[s] = dict(n=len(ok), qwen=float(np.mean(qv)), medgemma=float(np.mean(mv)), diff=ci, winner='Qwen' if ci[1] > 0 else ('MedGemma' if ci[2] < 0 else 'no clear winner'), point_winner='Qwen' if ci[0] > 0 else ('MedGemma' if ci[0] < 0 else 'tie'))
        out[name] = dict(n=n, groups=groups, too_small=(n < MIN_N or groups < MIN_N), scorers=d)
    return out

def layer0_scores(out):
    """BLEU, ROUGE-L, chrF, BERTScore (roberta-large), RaTEScore of every test report (Qwen and MedGemma) vs the true report; family-free scorers"""
    os.makedirs(out, exist_ok=True); cs = {c['key']: c for c in Q.cases() if c['split'] == 'test' and not c['flipped']}; mrep = {r['key']: Q.clean_md(r['report']) for r in load_jsonl(M.OUT_REPORTS)}
    pairs = []
    for k, c in cs.items():
        if k in mrep: pairs += [('qwen', k, c['reference'], c['report']), ('medgemma', k, c['reference'], mrep[k])]
    refs = [p[2] for p in pairs]; hyps = [p[3] for p in pairs]; res = {}
    for spec in ('bleu', 'rougeL', 'chrf', 'bertscore:roberta-large', 'ratescore'):
        g = graders.make(spec); s = g.batch(refs, hyps) if hasattr(g, 'batch') else [g.score(a, b) for a, b in zip(refs, hyps)]
        name = {'bertscore:roberta-large': 'bertscore[roberta-large]'}.get(spec, spec)
        for p, x in zip(pairs, s): res[f'{p[0]}|{p[1]}|{name}'] = float(x)
    json.dump(res, open(f'{out}/layer0_scores.json', 'w')); print('layer0 scored', len(pairs), 'pairs')

if __name__ == '__main__' and sys.argv[1] == 'layer0': layer0_scores(sys.argv[2])
