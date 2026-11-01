"""Step 21d: build the human-rewording sheet (NO model calls). 30 TEST references: 10 breast, 10 thyroid, 10 fetal head, spread over datasets, one per group, each with planted
errors in bench_test_v2d (so matched planted errors from the same reference exist). Test access is logged through usmeta.splits.load.
    python3 -m usmeta.step21_human_sheet build"""
import os, sys, json, csv, random, collections
from . import splits

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'); OUT = os.path.join(ROOT, 'results', 'partA', 'step21d_human_sheet')
ORGAN = {'BrEaST': 'breast', 'BUS-BRA': 'breast', 'BUSI': 'breast', 'UDIAT': 'breast', 'BUS-UCLM': 'breast', 'TN3K': 'thyroid', 'TN5000': 'thyroid', 'DDTI': 'thyroid', 'HC18': 'fetal head', 'FetalHead': 'fetal head'}
QUOTA = {'breast': {'BrEaST': 2, 'BUS-BRA': 2, 'BUSI': 2, 'UDIAT': 2, 'BUS-UCLM': 2}, 'thyroid': {'TN3K': 3, 'TN5000': 3, 'DDTI': 4}, 'fetal head': {'HC18': 5, 'FetalHead': 5}}
INSTR = """# Human-rewording sheet (Step 21d)

**Instructions.** For each row below, write ONE rewording of `reference_text` **by hand, in your own words**, in the `human_rewording` column of `sheet.csv`.
- Keep **every fact**: side, category / BI-RADS / TI-RADS level, size and units, position, number of lesions, finding present/absent, plane, head circumference.
- Do **not** copy the template phrasing (change sentence structure and wording, not only a word or two).
- Do **not** use an AI tool, translator or paraphraser.
- You may change the order of sentences, the units (mm <-> cm) and the style, but not the meaning. Do not add new findings or advice.
- If you cannot reword a row without changing a fact, leave it blank and write the reason in `note`.
- The script checks your facts with a rule extractor that was written for the template wording, so a freely worded sentence may be flagged even when every fact is kept. If you have checked by hand that nothing changed, write `OK` in `note` for that row; flagged rows without `OK` are left out of the scoring.
When the CSV is filled, run `python3 -m usmeta.step21_human_score` (it flags any rewording where a fact changed, then scores).

The 30 references come from the locked TEST split (10 breast, 10 thyroid, 10 fetal head; one per patient/exam group). They are templated, fact-correct reports built from dataset labels, not clinician text.
"""

def build():
    ids = {r['case_id']: r for r in splits.load('test', script='usmeta.step21_human_sheet')}
    bench = [json.loads(l) for l in open(os.path.join(ROOT, 'bench_test_v2d.jsonl'))]; ref = {}; err = collections.Counter()
    for r in bench:
        if r['case_id'] not in ids: continue
        ref[r['case_id']] = r['reference']; err[r['case_id']] += r['kind'] == 'error'
    rng = random.Random(0); rows = []
    for org, q in QUOTA.items():
        for ds, n in q.items():
            cands = sorted(c for c in ref if bench_ds(c) == ds and err[c] >= 3); rng.shuffle(cands); seen = set(); pick = []
            for c in cands:
                g = ids[c]['group_id']
                if g in seen: continue
                seen.add(g); pick.append(c)
                if len(pick) == n: break
            assert len(pick) == n, (ds, len(pick))
            rows += [dict(case_id=c, dataset=ds, organ=org, reference_text=ref[c]) for c in pick]
    os.makedirs(OUT, exist_ok=True)
    for i, r in enumerate(rows, 1): r['id'] = f'H{i:02d}'
    with open(os.path.join(OUT, 'sheet.csv'), 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=['id', 'organ', 'reference_text', 'human_rewording', 'note']); w.writeheader()
        for r in rows: w.writerow(dict(id=r['id'], organ=r['organ'], reference_text=r['reference_text'], human_rewording='', note=''))
    json.dump([{k: r[k] for k in ('id', 'case_id', 'dataset', 'organ')} for r in rows], open(os.path.join(OUT, 'sheet_key.json'), 'w'), indent=1)       # id -> case, kept for scoring (not shown to the rewriter)
    md = INSTR + '\n| id | organ | reference_text | human_rewording |\n|---|---|---|---|\n' + ''.join(f"| {r['id']} | {r['organ']} | {r['reference_text']} | |\n" for r in rows)
    open(os.path.join(OUT, 'sheet.md'), 'w').write(md); print(len(rows), 'rows', collections.Counter(r['dataset'] for r in rows))

_DS = {}
def bench_ds(c):
    if not _DS:
        for l in open(os.path.join(ROOT, 'bench_test_v2d.jsonl')):
            r = json.loads(l); _DS[r['case_id']] = r['dataset']
    return _DS[c]

if __name__ == '__main__':
    if sys.argv[1] == 'build': build()
