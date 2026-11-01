"""Step 21c: judge sensitivity on a CAPPED subset of the Step 12 sample (Gemma-2-9B 4-bit MLX, greedy). NEW file; judge2.py (prompt_v1/prompt_v2) and the Step 10d/12 replies are untouched.
Variants (output format identical to prompt_v2): swap (candidate text in the REFERENCE slot and vice versa), paraphraseA, paraphraseB (reworded instructions), repeat (the original prompt_v2
again with a FRESH cache, to test repeatability; subset). Original = the saved Step 10d/12 replies.
Sample: 10 cases per dataset from the Step 12 sample, rows per case = 1 small + 1 matched + 1 large harmless + 2 planted errors (as in Step 12). Reduced from 59 cases per dataset to fit the
~3 h limit; organ-level rows reach n >= 30 only for breast and thyroid, every per-dataset cell is 'too small to compare'.
    python3 -m usmeta.step21_judge_sens run | analyse"""
import os, sys, json, random, collections, time
import numpy as np
from . import judge2, judge2_test, graders
from .layer0 import auroc_case
from .step10d_analysis import gboot

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'); OUT = os.path.join(ROOT, 'results', 'partA', 'step21c_judge_sens'); P = lambda f: os.path.join(OUT, f)
N_CASES = 10; N_REPEAT = 2
ORGAN = {'BrEaST': 'breast', 'BUS-BRA': 'breast', 'BUSI': 'breast', 'UDIAT': 'breast', 'BUS-UCLM': 'breast', 'TN3K': 'thyroid', 'TN5000': 'thyroid', 'DDTI': 'thyroid', 'HC18': 'fetal head', 'FetalHead': 'fetal head'}

PARA_A = """You are a specialist in ultrasound reporting. You are given a REFERENCE report and a CANDIDATE report, both already split into numbered sentences. Your job is to compare what they say, nothing else, and not to decide whether any finding is clinically plausible or complete.
Guidance:
- A CANDIDATE sentence counts as supported (true) when the REFERENCE contains it verbatim or states the same facts differently.
- A REFERENCE sentence counts as covered (true) when the CANDIDATE contains it verbatim or states its facts differently.
- Differences in wording, sentence order or style do not matter if the meaning is the same. Units are interchangeable (10 mm = 1 cm).
- When the two reports are identical, every value must be true and the errors list must be empty.
- Record an error only when a fact is different: added, missing, or altered (a value, a location, a size or a category).

REFERENCE sentences:
{ref}

CANDIDATE sentences:
{hyp}

Reply with JSON only:
{{"candidate_supported": [true or false for each CANDIDATE sentence, in order],
 "reference_covered": [true or false for each REFERENCE sentence, in order],
 "errors": [{{"field": "<what differs>", "severity": "critical|major|minor", "category": "false finding|missed finding|wrong location|wrong severity/category|wrong measurement"}}]}}
"""
PARA_B = """Task: act as a sonographer-radiologist and check one ultrasound report (CANDIDATE) against a trusted report (REFERENCE). Only compare the content of the two texts; do not assess medical plausibility or completeness.
Rules:
1. Mark a CANDIDATE sentence true if its content is found in the REFERENCE, either word for word or expressed in other words.
2. Mark a REFERENCE sentence true if its content is found in the CANDIDATE, either word for word or expressed in other words.
3. Ignore differences in phrasing, ordering and style when the meaning stays the same; 10 mm and 1 cm are the same.
4. Identical reports: all values true, no errors.
5. Add an entry to errors only for a real factual difference (something added, left out, or changed: value, location, size, category).

REFERENCE sentences:
{ref}

CANDIDATE sentences:
{hyp}

Reply with JSON only:
{{"candidate_supported": [true or false for each CANDIDATE sentence, in order],
 "reference_covered": [true or false for each REFERENCE sentence, in order],
 "errors": [{{"field": "<what differs>", "severity": "critical|major|minor", "category": "false finding|missed finding|wrong location|wrong severity/category|wrong measurement"}}]}}
"""

def sample():
    rows = []
    for f in ('judge_test_v2_bench.jsonl', 'judge_big_v2_bench.jsonl'): rows += [json.loads(l) for l in open(os.path.join(ROOT, f))]
    orig = {}
    for f in ('judge_test_v2.jsonl', 'judge_big_v2.jsonl'):
        for l in open(os.path.join(ROOT, f)):
            d = json.loads(l)
            if d['result'] is not None: orig[(d['reference'], d['candidate'])] = d['result']
    by = collections.defaultdict(lambda: collections.defaultdict(list)); rng = random.Random(0)
    for r in rows:
        if (r['reference'], r['candidate']) in orig and r['kind'] in ('error', 'harmless'): by[r['dataset']][r['case_id']].append(r)
    out = []; seen = set()
    for ds in sorted(by):
        ids = sorted(c for c, rs in by[ds].items() if {r.get('harmless_type') for r in rs if r['kind'] == 'harmless'} >= {'small', 'matched', 'large'} and any(r['kind'] == 'error' for r in rs)); rng.shuffle(ids)
        for c in ids[:N_CASES]:
            for r in by[ds][c]:
                k = (r['reference'], r['candidate'])
                if k not in seen: seen.add(k); out.append(r)
    return out, orig

def run():
    rows, orig = sample(); os.makedirs(OUT, exist_ok=True); open(P('sample.jsonl'), 'w').write(''.join(json.dumps(r) + '\n' for r in rows)); print(len(rows), 'pairs per variant', flush=True)
    sc = judge2_test.SC(judge2.PROMPT_V2)
    class Fresh(judge2_test.SC):
        def __init__(self): super().__init__(judge2.PROMPT_V2, cli=graders.LocalLLM('mlx-community/gemma-2-9b-it-4bit', cache_dir='.llm_cache_repeat', max_tokens=500))
    reps = {}
    for r in rows: reps.setdefault(r['dataset'], [])
    cases_by_ds = collections.defaultdict(list)
    for r in rows:
        if r['case_id'] not in cases_by_ds[r['dataset']]: cases_by_ds[r['dataset']].append(r['case_id'])
    rep_cases = {c for ds, cs in cases_by_ds.items() for c in cs[:N_REPEAT]}
    class Var(judge2_test.SC):
        def __init__(self, prompt, swap): super().__init__(prompt); self.swap = swap
        def run(self, ref, hyp): return super().run(*((hyp, ref) if self.swap else (ref, hyp)))
    variants = [('swap', Var(judge2.PROMPT_V2, True), None), ('paraphraseA', Var(PARA_A, False), None), ('paraphraseB', Var(PARA_B, False), None), ('repeat', Fresh(), rep_cases)]
    t0 = time.time()
    for name, judge, only in variants:
        out = P(f'replies_{name}.jsonl'); done = {(json.loads(l)['reference'], json.loads(l)['candidate']) for l in open(out)} if os.path.exists(out) else set()
        todo = [r for r in rows if (r['reference'], r['candidate']) not in done and (only is None or r['case_id'] in only)]; print(name, len(todo), 'to judge', flush=True)
        for i, r in enumerate(todo):
            s = judge.run(r['reference'], r['candidate']); open(out, 'a').write(json.dumps(dict(reference=r['reference'], candidate=r['candidate'], result=s)) + '\n')
            if i % 25 == 0: print(name, i, len(todo), round(time.time() - t0), 's', flush=True)
    print('done', round(time.time() - t0), 's', flush=True)

def analyse():
    rows = [json.loads(l) for l in open(P('sample.jsonl'))]; _, orig = sample(); V = {'original': {k: v for k, v in orig.items()}}
    for n in ('swap', 'paraphraseA', 'paraphraseB', 'repeat'):
        f = P(f'replies_{n}.jsonl'); V[n] = {}
        if os.path.exists(f):
            for l in open(f):
                d = json.loads(l)
                if d['result'] is not None: V[n][(d['reference'], d['candidate'])] = d['result']
    by = collections.defaultdict(list)
    for r in rows: by[r['case_id']].append(r)
    res = {}
    for score in ('judge', 'f1'):
        for grp in list(ORGAN) + ['breast', 'thyroid', 'fetal head', 'ALL']:
            cs = {c: rs for c, rs in by.items() if grp in ('ALL',) or rs[0]['dataset'] == grp or ORGAN[rs[0]['dataset']] == grp}
            for var in ('original', 'swap', 'paraphraseA', 'paraphraseB', 'repeat'):
                v, g = [], []
                for c, rs in cs.items():
                    e = [V[var].get((r['reference'], r['candidate'])) for r in rs if r['kind'] == 'error']; h = [V[var].get((r['reference'], r['candidate'])) for r in rs if r['kind'] == 'harmless']
                    if any(x is None for x in e + h): continue          # complete cases only, so every variant is compared on the same cases
                    e = [x[score] for x in e]; h = [x[score] for x in h]
                    if e and h: v.append(auroc_case(e, h)); g.append(rs[0]['group_id'])
                res[f'{score}|{grp}|{var}'] = dict(n_cases=len(v), n_groups=len(set(g)), auroc=gboot(v, g) if v else None, per_case=v, groups=g)
    # change vs original (paired by case) and share of pairs with |delta judge_score| > 0.1
    chg = {}
    for var in ('swap', 'paraphraseA', 'paraphraseB', 'repeat'):
        for grp in list(ORGAN) + ['breast', 'thyroid', 'fetal head', 'ALL']:
            ks = [(r['reference'], r['candidate']) for r in rows if (grp == 'ALL' or r['dataset'] == grp or ORGAN[r['dataset']] == grp) and (r['reference'], r['candidate']) in V[var]]
            d = [abs(V[var][k]['judge'] - V['original'][k]['judge']) for k in ks]; df = [abs(V[var][k]['f1'] - V['original'][k]['f1']) for k in ks]
            a0, a1 = res[f'judge|{grp}|original'], res[f'judge|{grp}|{var}']
            chg[f'{var}|{grp}'] = dict(n_pairs=len(ks), share_judge_changed_gt_0_1=float(np.mean([x > 0.1 for x in d])) if d else None, share_any_change=float(np.mean([x > 1e-9 for x in d])) if d else None,
                                       share_f1_changed_gt_0_1=float(np.mean([x > 0.1 for x in df])) if df else None, mean_abs_delta_judge=float(np.mean(d)) if d else None,
                                       auroc_original=a0['auroc'][0] if a0['auroc'] else None, auroc_variant=a1['auroc'][0] if a1['auroc'] else None,
                                       auroc_change=(a1['auroc'][0] - a0['auroc'][0]) if a0['auroc'] and a1['auroc'] else None, n_cases=a1['n_cases'])
    json.dump(dict(auroc=res, change=chg), open(P('sens_results.json'), 'w'), indent=1); return res, chg

if __name__ == '__main__':
    {'run': run, 'analyse': analyse}[sys.argv[1]]()
