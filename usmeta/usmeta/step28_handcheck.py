"""Step 28 hand check: summarise docs/step28_check.csv (30 reports, filled by the owner: right / wrong per extraction) -> results/partA/step28_natural_errors/hand_check.json. No model calls."""
import csv, json, os, math, collections
from . import step28_natural_errors as S
rows = list(csv.DictReader(open(os.path.join(S.ROOT, 'docs', 'step28_check.csv'), encoding='utf-8'))); K = [k for k in rows[0] if k.startswith('extraction_right')][0]
def wilson(k, n, z=1.96):
    if not n: return None
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)); return [p, (c - h) / d, (c + h) / d]
by = collections.defaultdict(lambda: [0, 0]); items = []
for r in rows:
    v = r[K].strip().lower(); assert v in ('right', 'wrong'), r['id']; by[r['organ']][1] += 1; by[r['organ']][0] += v == 'right'; items.append(dict(id=r['id'], organ=r['organ'], dataset=r['dataset'], verdict=v, note=r['note'].strip(), extracted=r['llm_extracted_facts']))
nonfetal = [i for i in items if i['organ'] != 'fetal']; res = dict(n=len(items), right=sum(i['verdict'] == 'right' for i in items), by_organ={o: dict(right=a, n=n, share_right=wilson(a, n)) for o, (a, n) in by.items()},
    overall=wilson(sum(i['verdict'] == 'right' for i in items), len(items)), non_fetal=wilson(sum(i['verdict'] == 'right' for i in nonfetal), len(nonfetal)), non_fetal_n=len(nonfetal),
    fetal_note='all 12 fetal-head extractions are empty ({}) because the writer states no head circumference or plane; marked right', wrong_notes=[dict(id=i['id'], organ=i['organ'], note=i['note']) for i in items if i['verdict'] == 'wrong'])
json.dump(res, open(os.path.join(S.OUT, 'hand_check.json'), 'w'), indent=1); print(json.dumps({k: v for k, v in res.items() if k != 'wrong_notes'}, indent=1))
