"""python3 -m usmeta.judge2_report --scores judge2_scores.jsonl --bench bench_v2d_judge.jsonl --out DIR"""
import json, os, argparse, math, collections
import numpy as np
from . import layer0b, layer0, judge2

def build(bench, scores):
    rows = [json.loads(l) for l in open(bench)]; R = {}
    for l in open(scores):
        d = json.loads(l); R[(d['reference'], d['candidate'])] = d['result']
    keep = [r for r in rows if R.get((r['reference'], r['candidate'])) is not None]; dropped = len(rows) - len(keep)
    P = sorted({(r['reference'], r['candidate']) for r in keep})
    S = {'pairs': [list(p) for p in P], 'scores': {n: [R[p][k] for p in P] for n, k in (('sentence_f1', 'f1'), ('sentence_precision', 'precision'), ('sentence_recall', 'recall'), ('judge_score', 'judge'))}}
    return keep, S, R, dropped

def category_accuracy(rows, R):
    """for planted errors: does the judge list the planted category? (any listed category matches); and does it list ANY error (detection)"""
    acc = collections.defaultdict(list); det = collections.defaultdict(list)
    for r in rows:
        if r['kind'] != 'error': continue
        res = R[(r['reference'], r['candidate'])]; acc[(r['dataset'], r['category'])].append(r['category'] in res['cats']); det[(r['dataset'], r['category'])].append(res['n_err'] > 0)
    return acc, det

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--scores', default='judge2_scores.jsonl'); ap.add_argument('--bench', default='bench_v2d_judge.jsonl'); ap.add_argument('--out', required=True); a = ap.parse_args()
    rows, S, R, dropped = build(a.bench, a.scores); res = layer0b.analyse(rows, S); os.makedirs(a.out, exist_ok=True)
    json.dump(res, open(os.path.join(a.out, 'results_partA_layer2.json'), 'w'), indent=1)
    acc, det = category_accuracy(rows, R); lm = sum(1 for v in R.values() if v and v['len_mismatch']); tot = sum(1 for v in R.values() if v)
    lines = layer0b.tables(res) + layer0b.cat_tables(res)
    lines += ['## Judge category accuracy (planted category listed by the judge) and detection (judge lists any error)', '', '| dataset | category | n | category accuracy | any error listed |', '|---|---|---|---|---|']
    for k in sorted(acc): lines.append(f'| {k[0]} | {k[1]} | {len(acc[k])} | {np.mean(acc[k]):.2f} | {np.mean(det[k]):.2f} |')
    open(os.path.join(a.out, 'tables.md'), 'w').write('\n'.join(lines))
    json.dump(dict(rows=len(rows), dropped_missing=dropped, len_mismatch=lm, judged=tot, cat_acc_overall=float(np.mean([x for v in acc.values() for x in v])), detect_overall=float(np.mean([x for v in det.values() for x in v]))), open(os.path.join(a.out, 'meta.json'), 'w'))
    print('rows', len(rows), 'dropped (judge unparseable)', dropped, 'len_mismatch', lm, 'of', tot)
