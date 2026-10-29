"""Step 19: routing table from SAVED test results (no model runs, no new scoring). For each dataset x error category and each scorer: AUROC of the planted errors of that
category against the harmless rewordings (small + matched + large) of the same case, paired per case, 95% CI by group bootstrap (1,000 resamples, seed 0).
Layers: 0 = BLEU, ROUGE-L, chrF, BERTScore, RaTEScore (scores_test_layer0.json); 1 = finding_f1 (scores_test_layer1.json); 2 = Gemma sentence_check judge, prompt_v2
(Steps 10d + 12 judge files; sentence_f1 and judge_score); 3b = predicted-mask check (Step 16, MedSAM masks from TRUE boxes, position and size errors only; breast + thyroid).
To compare layers on the SAME cases, every scorer in a cell is evaluated on the cases that the judge saw for that category (cell n = those cases); the full-sample Layer 0/1
numbers are in Step 10d/12 and are not repeated here. The true-mask check (Layer 3 circular) is NOT included. No combined scorer is built or claimed.
    python3 -m usmeta.step19 OUT.json OUT.md"""
import json, sys, collections
import numpy as np
from .layer0 import auroc_case
from .step10d_analysis import gboot

HT = ('small', 'matched', 'large'); CATS = ('false finding', 'missed finding', 'wrong location', 'wrong severity/category', 'wrong measurement'); MIN_N = 30
L0 = ['bleu', 'rougeL', 'chrf', 'bertscore[roberta-large]', 'ratescore']
LAYER = {**{n: 'L0' for n in L0}, 'finding_f1': 'L1', 'sentence_f1': 'L2', 'judge_score': 'L2', 'mask_verified (predicted masks)': 'L3b'}

def scores_of(path):
    S = json.load(open(path)); P = [tuple(p) for p in S['pairs']]; return {n: dict(zip(P, a)) for n, a in S['scores'].items()}

def judge_scores():
    out = {'sentence_f1': {}, 'judge_score': {}}; rows = []
    for f in ('judge_test_v2.jsonl', 'judge_big_v2.jsonl'):
        for l in open(f):
            d = json.loads(l)
            if d['result'] is not None:
                out['sentence_f1'][(d['reference'], d['candidate'])] = d['result']['f1']; out['judge_score'][(d['reference'], d['candidate'])] = d['result']['judge']
    for f in ('judge_test_v2_bench.jsonl', 'judge_big_v2_bench.jsonl'): rows += [json.loads(l) for l in open(f)]
    return out, rows

def cell_auroc(cases, sc):
    """cases: {case_id: (group, [error scores], [harmless scores])} -> (values, groups)"""
    v, g = [], []
    for cid, (grp, e, h) in cases.items():
        e = [sc[x] for x in e if x in sc]; h = [sc[x] for x in h if x in sc]
        if e and h: v.append(auroc_case(e, h)); g.append(grp)
    return v, g

def build():
    jsc, jrows = judge_scores(); L = {**scores_of('scores_test_layer0.json'), 'finding_f1': scores_of('scores_test_layer1.json')['finding_f1'], **jsc}
    judged = {(r['reference'], r['candidate']) for r in jrows if (r['reference'], r['candidate']) in jsc['sentence_f1']}
    bench = [json.loads(l) for l in open('bench_test_v2d.jsonl')]; by = collections.defaultdict(list)
    for r in bench: by[r['case_id']].append(r)
    # the judge's cases: for each (case, category) the judged error rows; harmless = judged harmless rows of the case
    res = {}; cells = collections.defaultdict(dict)
    for cid, rs in by.items():
        ds = rs[0]['dataset']; grp = rs[0]['group_id']
        je = [r for r in rs if r['kind'] == 'error' and (r['reference'], r['candidate']) in judged]; jh = [r for r in rs if r['kind'] == 'harmless' and r['harmless_type'] in HT and (r['reference'], r['candidate']) in judged]
        if not je or not jh: continue
        for c in {r['category'] for r in je}:
            cells[(ds, c)][cid] = (grp, [(r['reference'], r['candidate']) for r in je if r['category'] == c], [(r['reference'], r['candidate']) for r in jh])
    for (ds, c), cases in sorted(cells.items()):
        row = {}
        for n, sc in L.items():
            v, g = cell_auroc(cases, sc); row[n] = dict(n=len(v), groups=len(set(g)), auroc=gboot(v, g) if v else None)
        res.setdefault(ds, {})[c] = row
    return res

def image_check():
    """Step 16 predicted-mask check on the same kind of categories: position errors = wrong location; size errors = wrong measurement. Saved masks are re-read (no new MedSAM run)."""
    from . import partb, unified
    sel = json.load(open('local_data/partb/selected.json')); recs = {}
    for ds in partb.DATASETS:
        for c in unified.load(partb.LOADER.get(ds, ds)): recs[c['case_id']] = c
    MR, M = partb.meas_rows(sel, recs); V = partb.verification(sel, M, recs); out = {}
    for ds in ('BrEaST', 'BUS-BRA', 'BUSI', 'UDIAT', 'BUS-UCLM', 'TN3K', 'DDTI', 'TN5000'):
        for cat, sub in (('wrong location', 'position errors'), ('wrong measurement', 'size errors')):
            for nm in ('mvf_exact', 'bleu', 'rougeL', 'chrf', 'bertscore[roberta-large]', 'ratescore'):
                v, g = partb.case_aurocs(V, nm, sub, ds); out.setdefault(ds, {}).setdefault(cat, {})[nm] = dict(n=len(v), groups=len(set(g)), auroc=gboot(v, g) if v else None)
    return out

def fm(a): return '—' if a is None else f'{a[0]:.2f} ({a[1]:.2f}–{a[2]:.2f})'

def winner(row):
    ok = {n: d for n, d in row.items() if d['auroc'] and d['n'] >= MIN_N and n != 'finding_f1'}       # finding_f1 reads the template that wrote the reference: upper bound, not a competitor
    if not ok: return 'too small to compare'
    best = max(ok, key=lambda n: ok[n]['auroc'][0]); top = ok[best]['auroc']
    ties = [n for n, d in ok.items() if n != best and d['auroc'][2] >= top[1] and LAYER[n] != LAYER[best]]       # other-layer scorers whose CI overlaps the best one's
    return f'{best} ({LAYER[best]}) {top[0]:.2f}' + (f'; not clearly better than {", ".join(sorted(set(ties)))}' if ties else '; CI separate from every other layer')

def main(jout, mout):
    R = build(); IM = image_check(); json.dump(dict(judge_cases=R, image_check=IM), open(jout, 'w'), indent=1)
    md = ['# Step 19: routing table (saved TEST results, no new model runs)', '',
          'Per dataset and error category: AUROC (planted errors of that category vs harmless rewordings of the same case; 95% CI, group bootstrap), for the cases the Gemma judge saw in Steps 10d + 12 (every scorer on the same cases). **n < 30 cases: too small to compare** (no winner is named). "Winner" = highest point estimate among scorers; if another layer\'s CI overlaps it, that is said. This is a description of where each layer works, **not** a combined scorer. `finding_f1` is an **upper bound on templated text** (it reads the template that wrote the reference), so it is shown but never named winner; the winner is the best of the other scorers (best-of-7, so its point estimate is optimistic). The two judge columns are two scores of the same judge call.', '']
    for ds, cats in R.items():
        md += [f'## {ds}', '', '| error category | n cases | ' + ' | '.join(L0 + ['finding_f1', 'sentence_f1', 'judge_score']) + ' | winner |', '|---|---|' + '---|' * (len(L0) + 4)]
        for c in CATS:
            if c not in cats: continue
            row = cats[c]; n = row['finding_f1']['n']; md.append(f"| {c}{' †' if n < MIN_N else ''} | {n} | " + ' | '.join(fm(row[k]['auroc']) for k in L0 + ['finding_f1', 'sentence_f1', 'judge_score']) + f' | {winner(row)} |')
        md.append('')
    md += ['## Image check (Step 16: MedSAM masks from TRUE boxes) on position and size errors', '', 'Different case sample from the judge (30 scans per dataset, Step 16), so read it next to, not against, the table above. † n < 30: too small to compare.', '',
           '| dataset | error category | n cases | mvf_exact (predicted masks) | BLEU | ROUGE-L | chrF | BERTScore | RaTEScore |', '|---|---|---|---|---|---|---|---|---|']
    for ds, cats in IM.items():
        for c, row in cats.items():
            n = row['mvf_exact']['n']
            if n: md.append(f"| {ds} | {c}{' †' if n < MIN_N else ''} | {n} | " + ' | '.join(fm(row[k]['auroc']) for k in ('mvf_exact', 'bleu', 'rougeL', 'chrf', 'bertscore[roberta-large]', 'ratescore')) + ' |')
    open(mout, 'w').write('\n'.join(md) + '\n'); print('\n'.join(md))

if __name__ == '__main__': main(sys.argv[1], sys.argv[2])
