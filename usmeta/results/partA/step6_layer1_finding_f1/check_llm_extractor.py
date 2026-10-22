import json, sys, random, time, collections
sys.path.insert(0, '.')
from usmeta import schema, graders
tr = {json.loads(l)['case_id']: json.loads(l) for l in open('true_reports_v2d.jsonl')}
random.seed(int(sys.argv[2]) if len(sys.argv) > 2 else 0); by = collections.defaultdict(list)
for r in tr.values(): by[r['dataset']].append(r)
sel = [x for ds, v in by.items() for x in random.sample(v, int(sys.argv[1]))]
cli = graders.LocalLLM('mlx-community/gemma-2-9b-it-4bit', max_tokens=800)
hit = collections.Counter(); tot = collections.Counter(); bad = 0; fails = 0; t0 = time.time(); ex = []
for r in sel:
    for style in ('standard', 'terse', 'long'):
        txt = r['styles'][style]; f, b = schema.extract_llm(cli, txt, r['organ']); bad += b
        if f is None: fails += 1; f = {}
        for k, v in r['facts'].items():
            ok = (k == 'hc_mm' and f.get(k) is not None and abs(f[k] - v) < 0.06) or str(f.get(k)).lower() == str(v).lower() or (k == 'count' and v == 1 and f.get(k) in (None, 1))
            tot[(r['dataset'], k)] += 1; hit[(r['dataset'], k)] += bool(ok)
            if not ok and len(ex) < 12: ex.append((r['dataset'], style, k, v, f.get(k)))
T = sum(tot.values()); H = sum(hit.values())
print('LLM extractor field agreement', round(H / T, 4), 'on', T, 'fields;', 'unquoted values dropped', bad, 'parse failures', fails, 'seconds', round(time.time() - t0))
per = collections.defaultdict(lambda: [0, 0])
for (ds, k), n in tot.items(): per[k][0] += hit[(ds, k)]; per[k][1] += n
print({k: round(a / b, 2) for k, (a, b) in per.items()})
print(ex)
json.dump({'agreement': H / T, 'fields': T, 'per_field': {k: a / b for k, (a, b) in per.items()}, 'unquoted': bad, 'parse_fail': fails}, open(f'llm_extractor_check_seed{sys.argv[2] if len(sys.argv) > 2 else 0}.json', 'w'))
