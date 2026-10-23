"""Step 10d: headline results on the LOCKED TEST split. New file so the frozen code is not touched.
    python3 -m usmeta.step10d build     -> bench_test_v2d.jsonl  (bench_v2d builder run on test-split cases only, 150 per dataset max) + bench_loc_test.jsonl (100 per dataset)
Every read of the test split goes through usmeta.splits.load('test') (logged)."""
import json, sys, os, collections, random
from . import splits, templates_v2 as T, bench_v2, bench_v2b, bench_loc

def test_ids(): return {r['case_id'] for r in splits.load('test', script='usmeta.step10d')}

def build_bench(out='bench_test_v2d.jsonl', per_dataset=150):
    ids = test_ids(); orig = T.load
    T.load = lambda ds: [r for r in orig(ds) if r['case_id'] in ids]       # the builders then only see test-split cases
    try: rows, counts = bench_v2.build(per_dataset=per_dataset, keep_all=())
    finally: T.load = orig
    tmp = out + '.tmp'; open(tmp, 'w').write(''.join(json.dumps(r) + '\n' for r in rows)); bench_v2b.convert(tmp, tmp + '2'); res = bench_v2b.add_matched(tmp + '2', out)
    os.remove(tmp); os.remove(tmp + '2'); return res, counts

def build_loc(out='bench_loc_test.jsonl', per_dataset=100, src='bench_test_v2d.jsonl'):
    ids = test_ids(); rows, counts = bench_loc.build(per_dataset=per_dataset, bench=src)
    rows = [r for r in rows if r['case_id'] in ids]; open(out, 'w').write(''.join(json.dumps(r) + '\n' for r in rows)); return rows, counts

if __name__ == '__main__':
    if sys.argv[1] == 'build':
        rows, c = build_bench(); print(len(rows), 'rows;', c); lr, lc = build_loc(); print(len(lr), 'loc rows;', lc)
