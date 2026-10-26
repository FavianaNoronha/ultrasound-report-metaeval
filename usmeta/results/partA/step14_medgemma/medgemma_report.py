"""Step 14: numbers for the MedGemma-1.5-4B (4-bit MLX) report. python3 -m usmeta.medgemma_report OUT_DIR"""
import json, sys, os, collections
import numpy as np
from . import medgemma_analysis as A, medgemma as M, qwen_real as Q, schema, qwen_real_analysis as QA
from .step10d_analysis import gboot

def main(out):
    rows, meta = A.per_case(out); json.dump(rows, open(f'{out}/rows.json', 'w'))
    DS = {'BUS-BRA': ['BUS-BRA'], 'BrEaST': ['BrEaST'], 'TN3K': ['TN3K'], 'TN5000': ['TN5000'], 'HC18': ['HC18'], 'breast (BUS-BRA + BrEaST, pooled)': ['BUS-BRA', 'BrEaST'], 'thyroid (TN3K + TN5000, pooled)': ['TN3K', 'TN5000']}
    comp = A.compare(rows, DS)
    # MedGemma alone, per dataset
    alone = {}
    for ds in ['BUS-BRA', 'BrEaST', 'TN3K', 'TN5000', 'HC18']:
        R = [r for r in rows if r['dataset'] == ds]; s = dict(n=len(R), groups=len({r['group'] for r in R}))
        for k in ('precision', 'recall', 'finding_f1', 'sentence_f1_v2', 'sentence_f1_v1', 'judge_score_v2', 'iou', 'support_gtbox'):
            v = [r.get(f'medgemma_{k}') for r in R]; ok = [(x, r['group']) for x, r in zip(v, R) if x is not None]
            if ok: s[k] = gboot([a for a, _ in ok], [g for _, g in ok])
        s['iou_ge_0.5'] = float(np.mean([r['medgemma_iou'] >= 0.5 for r in R if 'medgemma_iou' in r])); s['box_parse_rate'] = float(np.mean([r['medgemma_parsed'] for r in R if 'medgemma_parsed' in r]))
        s['any_error_v2'] = float(np.mean([r['medgemma_nerr_v2'] > 0 for r in R if r.get('medgemma_nerr_v2') is not None])); alone[ds] = s
    # attributes (reference attribute vs what the MedGemma report states)
    C = {c['key']: c for c in Q.cases()}; E = {json.loads(l)['key']: json.loads(l) for l in open('extract_medgemma_v2.jsonl')}; attr = collections.defaultdict(collections.Counter)
    for r in rows:
        c = C[r['key']]; f = (E.get(r['key']) or {}).get('facts') or {}
        for key, v in c['ref_facts'].items():
            cand = f.get(key); cmp_ = ('correct' if cand == 'present' else ('wrong' if cand == 'absent' else 'not stated')) if key == 'lesion' else QA.judge_cmp(v, cand, key)
            attr[f"{c['dataset']}|{key}"][cmp_] += 1
    # judge error categories (v2q)
    JM = {json.loads(l)['key']: json.loads(l)['result'] for l in open('judge_medgemma_v2q.jsonl')}; cats = collections.defaultdict(collections.Counter)
    for k, j in JM.items():
        if j and not C[k]['flipped']:
            for c in j['cats']: cats[C[k]['dataset']][c] += 1
    # flips (extractor facts stay the same?)
    flips = []
    for c in Q.cases():
        if c['flipped'] and c['split'] == 'test':
            o = f"{c['case_id']}|orig"; fo, ff = (E.get(o) or {}).get('facts'), (E.get(c['key']) or {}).get('facts')
            if fo is None or ff is None: continue
            keys = set(fo) | set(ff); same = [fo.get(a) == ff.get(a) for a in keys if a not in ('side', 'pos')]
            flips.append(dict(case=c['case_id'], dataset=c['dataset'], facts_same_share=float(np.mean(same)) if same else None, side_changed=(fo.get('side') != ff.get('side')) if ('side' in fo or 'side' in ff) else None))
    # extractor stats
    est = dict(reports=len(E), unparsed=sum(e['facts'] is None for e in E.values()), quote_dropped=sum(e['unquoted'] for e in E.values()), numeric_overrides=sum(e.get('numeric_overrides', 0) for e in E.values()))
    json.dump(dict(comparison=comp, medgemma_alone=alone, attributes={k: dict(v) for k, v in attr.items()}, judge_categories={k: dict(v) for k, v in cats.items()}, flips=flips, extractor=est, box=meta), open(f'{out}/results.json', 'w'), indent=1)
    return comp, alone, attr, cats, flips, est, meta

if __name__ == '__main__': main(sys.argv[1])
