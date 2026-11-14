"""Step 32 hand check: tally docs/step32_check_filled.csv (one non-clinician reviewer, rubric in row 1).
Reads the filled sheet only; no model calls. Writes results/partA/step32_extractor_v3/hand_check.{json,md}.
Error categories below are the author's manual reading of the reviewer's notes (not machine-classified)."""
import csv, json, math, collections, pathlib
root = pathlib.Path(__file__).parent
rows = list(csv.reader(open(root/'docs/step32_check_filled.csv', encoding='utf-8')))[2:]
rows = [r for r in rows if r and r[0].startswith('C')]
assert len(rows) == 30
V = {r[0]: r[5].strip() for r in rows}
assert set(V.values()) <= {'right', 'wrong'}
organ = {r[0]: r[1] for r in rows}
CAT = {  # manual reading of the notes, wrong rows only
 'birads_as_tirads': ['C05','C07','C08','C09','C10','C11','C12','C15','C22'],
 'stated_category_left_out': ['C04','C20','C27'],
 'shape_narrowed': ['C02','C18','C28'],
 'other_omitted_or_changed_field': ['C17','C19'],
}
wrong = sorted(k for k, v in V.items() if v == 'wrong')
assert sorted(sum(CAT.values(), [])) == wrong, 'category map does not match wrong rows'
def wilson(k, n, z=1.96):
    p = k/n; d = 1+z*z/n; c = p+z*z/(2*n); h = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))
    return round((c-h)/d, 2), round((c+h)/d, 2)
out = {'n': 30, 'right': 30-len(wrong), 'wrong': len(wrong)}
out['right_ci95_wilson'] = wilson(out['right'], 30)
by = collections.defaultdict(lambda: [0, 0])
for k, v in V.items():
    by[organ[k]][0] += v == 'right'; by[organ[k]][1] += 1
out['by_organ'] = {o: {'right': a, 'n': n, 'ci95': wilson(a, n)} for o, (a, n) in by.items()}
bt_r = sum(by[o][0] for o in ('breast', 'thyroid')); bt_n = sum(by[o][1] for o in ('breast', 'thyroid'))
out['breast_thyroid'] = {'right': bt_r, 'n': bt_n, 'ci95': wilson(bt_r, bt_n)}
out['error_categories'] = {k: len(v) for k, v in CAT.items()}
out['borderline'] = {'C06': 'marked right; lobulated dropped to irregular and post:enhancement read from peripheral enhancement; counting it wrong gives 12 right / 18 wrong'}
out['caveats'] = ['one non-clinician reviewer', 'AI use by the reviewer not verified', 'rubric stricter than the Step 28 check (not comparable)', 'fetal-head rows are empty extractions on reports that state nothing']
(root/'results/partA/step32_extractor_v3/hand_check.json').write_text(json.dumps(out, indent=2))
md = ['# Step 32 hand check of extractor v3 (30 free-text Qwen reports)', '',
 f"Sheet: `docs/step32_check_filled.csv`. One non-clinician reviewer; rubric in row 1 (judge the extraction against the report text only; BI-RADS written as `tirads` on thyroid = wrong; a stated BI-RADS/TI-RADS category left out = wrong; a narrowed shape = wrong). AI use by the reviewer was not verified.", '',
 f"**{out['right']} of 30 right (43%, 95% Wilson CI {out['right_ci95_wilson'][0]}-{out['right_ci95_wilson'][1]}).**", '',
 '| organ | right / n | 95% CI |', '|---|---|---|']
md += [f"| {o} | {d['right']} / {d['n']} | {d['ci95'][0]}-{d['ci95'][1]} |" for o, d in out['by_organ'].items()]
md += [f"| breast + thyroid | {bt_r} / {bt_n} | {out['breast_thyroid']['ci95'][0]}-{out['breast_thyroid']['ci95'][1]} |", '',
 'The 17 wrong rows by cause (author reading of the notes): ' + ', '.join(f"{k.replace('_',' ')} {len(v)} ({', '.join(v)})" for k, v in CAT.items()) + '.', '',
 'Borderline: C06 (counted right). Counting it wrong gives 12 right, 18 wrong.', '',
 '**Verdict:** extractor v3 keeps templated agreement (Step 32) but is NOT validated on free text. The v3 labels in the Step 28 re-run therefore stay unreliable, and Step 28 stays inconclusive. The rubric is stricter than the Step 28 check (22 of 30 right; 10 of 18 on breast and thyroid), so the two numbers are not comparable. Fetal-head rows are empty extractions on reports that state nothing and are easy.']
(root/'results/partA/step32_extractor_v3/hand_check.md').write_text('\n'.join(md)+'\n')
print(json.dumps(out, indent=1))
