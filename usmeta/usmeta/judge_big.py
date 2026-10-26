"""Step 12: larger judge sample on the locked TEST split (prompt_v2, Gemma-2-9B, frozen settings). New file.
Adds N more test cases per dataset to the 25 already judged in Step 10d (same rows per case: 1 harmless_small, 1 matched, 1 harmless_large, 2 errors of different categories,
identical copies for the first 3 added cases), chosen with a fresh seed among test cases not yet used. Combined analysis uses old + new pairs.
    python3 -m usmeta.judge_big run  ADD_PER_DATASET OUT.jsonl      python3 -m usmeta.judge_big report OUT_DIR"""
import json, sys, os, time, random, collections
import numpy as np
from . import judge2, judge2_test, judge2_report, splits, step10d_analysis as A, layer0

def added_rows(add, seed=1):
    done = {json.loads(l)['case_id'] for l in open('judge_test_v2_bench.jsonl')}; rows = [json.loads(l) for l in open('bench_test_v2d.jsonl')]; by = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in rows: by[r['dataset']][r['case_id']].append(r)
    out = []; rng = random.Random(seed)
    for ds, cases in by.items():
        ids = sorted(c for c in cases if c not in done); rng.shuffle(ids)
        for k, cid in enumerate(ids[:add]):
            rs = cases[cid]; pick = lambda t: [r for r in rs if r['kind'] == 'harmless' and r['harmless_type'] == t]
            for t in ('small', 'matched', 'large'):
                if pick(t): out.append(rng.choice(pick(t)))
            e = [r for r in rs if r['kind'] == 'error']; rng.shuffle(e); seen = set()
            for r in e:
                if r['category'] not in seen and len(seen) < 2: seen.add(r['category']); out.append(r)
            if k < 3: out += [r for r in rs if r['kind'] == 'identical']
    return out

def run(add, out):
    rows = added_rows(add); open(out.replace('.jsonl', '_bench.jsonl'), 'w').write(''.join(json.dumps(r) + '\n' for r in rows))
    done = {(json.loads(l)['reference'], json.loads(l)['candidate']) for l in open(out)} if os.path.exists(out) else set(); sc = judge2_test.SC(judge2.PROMPT_V2)
    todo = list(dict.fromkeys((r['reference'], r['candidate']) for r in rows if (r['reference'], r['candidate']) not in done)); print(len(rows), 'rows;', len(todo), 'pairs', flush=True); t0 = time.time()
    for i, (a, b) in enumerate(todo):
        s = sc.run(a, b); open(out, 'a').write(json.dumps(dict(reference=a, candidate=b, result=s)) + '\n')
        if i % 25 == 0: print(i, len(todo), round(time.time() - t0), 's', flush=True)
    print('done', round(time.time() - t0), 's missing', sc.missing, flush=True)

if __name__ == '__main__':
    if sys.argv[1] == 'run': run(int(sys.argv[2]), sys.argv[3])
