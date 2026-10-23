import json, sys, random, collections, time
sys.path.insert(0, '.')
from usmeta import judge2
rows = [json.loads(l) for l in open('bench_v2d.jsonl')]
by = collections.defaultdict(list)
for r in rows:
    if r['kind'] == 'identical': by[r['dataset']].append(r)
random.seed(int(sys.argv[2]) if len(sys.argv) > 2 else 0); n = int(sys.argv[1]); sc = judge2.SentenceCheck(); bad = []; tot = 0; t0 = time.time()
for ds, v in by.items():
    for r in random.sample(v, n):
        s = sc.run(r['reference'], r['candidate']); tot += 1
        if s is None or s['f1'] < 1 or s['judge'] < 1: bad.append((ds, None if s is None else (round(s['f1'], 2), s['judge'], s['cats']), r['reference'][:80]))
print('identical copies', tot, 'not exactly 1.0:', len(bad), 'missing', sc.missing, round(time.time() - t0), 's'); print(*bad, sep='\n')
