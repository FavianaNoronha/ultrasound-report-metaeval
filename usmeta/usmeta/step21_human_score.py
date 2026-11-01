"""Step 21d: score the filled human-rewording sheet. NOT run until the owner has filled results/partA/step21d_human_sheet/sheet.csv.
    python3 -m usmeta.step21_human_score check [CSV]   facts check only (rule extractor), writes flagged.csv, no scoring
    python3 -m usmeta.step21_human_score score [CSV]   check + BLEU, ROUGE-L, chrF, BERTScore, RaTEScore, finding_f1, Gemma judge (prompt_v2) on the unflagged rewordings
Per item (one reference, one group): AUROC = P(planted-error score < human-rewording score) over the planted errors of the SAME reference (ties 0.5); the same is computed for the
template harmless groups (small / matched / large) on the same references for comparison. 95% CI resamples items (1,000, seed 0); organs are reported separately; n < 30 items per cell:
'too small to compare' (so each organ cell, n = 10, always carries that mark; the pooled 30-item row is labelled pooled)."""
import os, sys, json, csv, collections, random
import numpy as np
from . import schema, layer0, layer1
from .layer0 import auroc_case
from .step10d_analysis import gboot

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'); D = os.path.join(ROOT, 'results', 'partA', 'step21d_human_sheet')
ORG = {'breast': 'breast', 'thyroid': 'thyroid', 'fetal head': 'fetal'}

def load(csvp):
    key = {k['id']: k for k in json.load(open(os.path.join(D, 'sheet_key.json')))}; rows = list(csv.DictReader(open(csvp, encoding='utf-8')))
    return [dict(r, **{k: key[r['id']][k] for k in ('case_id', 'dataset')}) for r in rows]

def fact_check(ref, hyp, organ):
    """compare the facts of the human rewording with the reference using the rule extractor; return (ok, list of attributes whose credit < 1)"""
    o = ORG[organ]; fr, fh = schema.to_findings(schema.extract_rule(ref, o), o), schema.to_findings(schema.extract_rule(hyp, o), o)
    p, r, f1, cred = schema.finding_scores(fr, fh); bad = sorted(f'{e}.{a}={c:.2f}' for (e, a), c in cred.items() if c < 1)
    return f1 >= 0.999 and not bad, bad, f1

def check(csvp):
    rows = [r for r in load(csvp) if r['human_rewording'].strip()]; out = []
    for r in rows:
        ok, bad, f1 = fact_check(r['reference_text'], r['human_rewording'], r['organ']); same = r['human_rewording'].strip() == r['reference_text'].strip()
        out.append(dict(id=r['id'], organ=r['organ'], facts_ok=ok, finding_f1_vs_reference=round(f1, 3), changed_attributes=';'.join(bad), identical_to_reference=same))
    with open(os.path.join(D, 'flagged.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]) if out else ['id']); w.writeheader(); [w.writerow(o) for o in out]
    print(len(rows), 'filled;', sum(not o['facts_ok'] for o in out), 'flagged (a fact changed according to the rule extractor);', sum(o['identical_to_reference'] for o in out), 'identical to the reference'); return out

def build_bench(rows, flagged):
    ok_note = {r['id'] for r in rows if r.get('note', '').strip().upper().startswith('OK')}      # owner confirmed by hand that no fact changed (the rule extractor cannot read free phrasing)
    bad = {o['id'] for o in flagged if (not o['facts_ok'] and o['id'] not in ok_note) or o['identical_to_reference']}; bench = [json.loads(l) for l in open(os.path.join(ROOT, 'bench_test_v2d.jsonl'))]; by = collections.defaultdict(list)
    for b in bench: by[b['case_id']].append(b)
    out = []; rng = random.Random(0)
    for r in rows:
        if not r['human_rewording'].strip() or r['id'] in bad: continue
        bs = by[r['case_id']]; ref = bs[0]['reference']
        assert ref == r['reference_text'], r['id']
        base = dict(item=r['id'], case_id=r['case_id'], dataset=r['dataset'], organ=r['organ'], reference=ref)
        out.append(dict(base, kind='human', candidate=r['human_rewording'].strip()))
        errs = [b for b in bs if b['kind'] == 'error']; rng.shuffle(errs); out += [dict(base, kind='error', field=b['field'], candidate=b['candidate']) for b in errs[:8]]
        out += [dict(base, kind='template_' + b['harmless_type'], candidate=b['candidate']) for b in bs if b['kind'] == 'harmless' and b['harmless_type'] in ('small', 'matched', 'large')]
        out += [dict(base, kind='identical', candidate=ref)]
    return out

def score(csvp):
    flagged = check(csvp); rows = load(csvp); B = build_bench(rows, flagged)
    bp = os.path.join(D, 'human_bench.jsonl'); open(bp, 'w').write(''.join(json.dumps(b) + '\n' for b in B))
    for b in B: b['organ_model'] = ORG[b['organ']]
    tmp = [dict(b, organ=ORG[b['organ']]) for b in B]; open(os.path.join(D, '_tmp_bench.jsonl'), 'w').write(''.join(json.dumps(b) + '\n' for b in tmp))
    layer0.score(os.path.join(D, '_tmp_bench.jsonl'), os.path.join(D, 'scores_layer0.json')); layer1.score(os.path.join(D, '_tmp_bench.jsonl'), os.path.join(D, 'scores_layer1.json'))
    from . import judge2, judge2_test
    sc = judge2_test.SC(judge2.PROMPT_V2); J = {}
    for b in B:
        k = (b['reference'], b['candidate'])
        if k not in J: J[k] = sc.run(*k)
    S = {}
    for f, names in (('scores_layer0.json', None), ('scores_layer1.json', ('finding_f1',))):
        s = json.load(open(os.path.join(D, f))); P = [tuple(p) for p in s['pairs']]
        for n, a in s['scores'].items():
            if names is None or n in names: S[n] = dict(zip(P, a))
    S['sentence_f1'] = {k: v['f1'] for k, v in J.items() if v}; S['judge_score'] = {k: v['judge'] for k, v in J.items() if v}
    res = {}; by = collections.defaultdict(list)
    for b in B: by[b['item']].append(b)
    for n, sc_ in S.items():
        for kind in ('human', 'template_small', 'template_matched', 'template_large'):
            for org in ('breast', 'thyroid', 'fetal head', 'ALL'):
                v, g, t = [], [], []
                for it, bs in by.items():
                    if org != 'ALL' and bs[0]['organ'] != org: continue
                    e = [sc_.get((b['reference'], b['candidate'])) for b in bs if b['kind'] == 'error']; h = [sc_.get((b['reference'], b['candidate'])) for b in bs if b['kind'] == kind]
                    e = [x for x in e if x is not None]; h = [x for x in h if x is not None]
                    if e and h: v.append(auroc_case(e, h)); g.append(it); t.append(float((np.array(e)[:, None] == np.array(h)[None, :]).mean()))
                res[f'{n}|{kind}|{org}'] = dict(n_items=len(v), auroc=gboot(v, g) if v else None, tie=float(np.mean(t)) if t else None, too_small=len(v) < 30)
    json.dump(res, open(os.path.join(D, 'human_results.json'), 'w'), indent=1); print('wrote human_results.json'); return res

if __name__ == '__main__':
    p = sys.argv[2] if len(sys.argv) > 2 else os.path.join(D, 'sheet.csv')
    {'check': check, 'score': score}[sys.argv[1]](p)
