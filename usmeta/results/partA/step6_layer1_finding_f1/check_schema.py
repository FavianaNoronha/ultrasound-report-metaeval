import json, sys, collections
sys.path.insert(0, '.')
from usmeta import schema
tr = {}
for l in open('true_reports_v2d.jsonl'):
    r = json.loads(l); tr[r['case_id']] = r
rows = [json.loads(l) for l in open('bench_v2d.jsonl')]
hit = collections.Counter(); tot = collections.Counter(); bad = collections.defaultdict(list)
for r in rows:
    if r['kind'] == 'error': continue
    facts = tr[r['case_id']]['facts']; ex = schema.extract_rule(r['candidate'], r['organ'])
    for k, v in facts.items():
        tot[(r['dataset'], k)] += 1
        ok = (k == 'hc_mm' and ex.get(k) is not None and abs(ex[k] - v) < 0.06) or (ex.get(k) == v) or (str(ex.get(k)).lower() == str(v).lower())
        if k == 'count' and v == 1 and ex.get(k) in (1, None): ok = True
        hit[(r['dataset'], k)] += ok
        if not ok and len(bad[(r['dataset'], k)]) < 2: bad[(r['dataset'], k)].append((v, ex.get(k), r['group'], r['candidate'][:90]))
    for k in ex:
        if k not in facts: tot[(r['dataset'], 'EXTRA:' + k)] += 1
tt = sum(tot[k] for k in tot if not k[1].startswith('EXTRA')); hh = sum(hit.values())
print('overall field agreement', round(hh / tt, 4), 'on', tt, 'fields')
for k in sorted(tot):
    if k[1].startswith('EXTRA'): print('  extra field extracted (not in facts):', k, tot[k])
    elif hit[k] / tot[k] < 0.98: print('  LOW', k, round(hit[k] / tot[k], 3), tot[k], bad[k][:2])
