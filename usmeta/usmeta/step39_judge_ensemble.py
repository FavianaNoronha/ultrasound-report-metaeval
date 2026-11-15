"""Step 39: judge stability by averaging over prompt wordings. NEW file; judge2.py (frozen PROMPT_V2), judge2_test.SC, the Step 21c paraphrases / swap and their saved replies are imported / read unchanged.
Pre-registration: results/partA/step39_judge_ensemble/PREREG.md (committed before any new test-split judge call).
Prompts: P0 = frozen judge prompt (prompt_v2); P1 = Step 21c paraphraseA; P2 = Step 21c paraphraseB plus a verbatim-copy rule (amended after the dev/val gate, see PREREG); P3 = P0 text with the candidate in the REFERENCE slot and vice versa (Step 21c 'swap'); P4, P5 = two NEW paraphrases (below; P5 also with the verbatim-copy rule).
Set A = {P0, P1, P2}, set B = {P3, P4, P5}; ensemble score = mean judge_score over a set. Same model (Gemma-2-9B-it 4-bit MLX), greedy, same parser.
    python3 -m usmeta.step39_judge_ensemble devval | test | analyse"""
import os, sys, json, random, hashlib, collections, time, argparse
import numpy as np
from . import judge2, judge2_test, splits, step21_judge_sens as S21
from .layer0 import auroc_case
from .step10d_analysis import gboot

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'); OUT = os.path.join(ROOT, 'results', 'partA', 'step39_judge_ensemble'); P = lambda f: os.path.join(OUT, f)
TAIL = """
REFERENCE sentences:
{ref}

CANDIDATE sentences:
{hyp}

Reply with JSON only:
{{"candidate_supported": [true or false for each CANDIDATE sentence, in order],
 "reference_covered": [true or false for each REFERENCE sentence, in order],
 "errors": [{{"field": "<what differs>", "severity": "critical|major|minor", "category": "false finding|missed finding|wrong location|wrong severity/category|wrong measurement"}}]}}
"""
PARA_C = """Compare two ultrasound reports sentence by sentence. The REFERENCE is the correct report and the CANDIDATE is the report to be checked. Judge only whether the statements match; do not judge whether the findings are realistic or complete.
How to decide:
- For each CANDIDATE sentence answer true if the REFERENCE says the same thing (identical words or a rewording), otherwise false.
- For each REFERENCE sentence answer true if the CANDIDATE says the same thing (identical words or a rewording), otherwise false.
- A different word order, a different style, or a different unit for the same measurement (10 mm and 1 cm) is not a difference.
- If the two reports say exactly the same, every answer is true and the error list stays empty.
- Put an item in the error list only when a fact really differs: invented, omitted or changed (a number, a position, a size, a category).
""" + TAIL
PARA_D = """You will check an ultrasound CANDIDATE report against its REFERENCE. This is a content comparison only; whether the findings are plausible or complete is not your concern.
Instructions:
a) A CANDIDATE sentence is supported (true) when the REFERENCE contains the same information, in the same or in different words.
b) A REFERENCE sentence is covered (true) when the CANDIDATE contains the same information, in the same or in different words.
c) Wording, sentence order, writing style and unit conversions (10 mm = 1 cm) are not differences.
d) Two reports with the same content get all true values and no errors.
e) List an error only for a factual difference: something added, missing or altered (value, location, size, category).
""" + TAIL
COPY_RULE_B = "5. Add an entry to errors only for a real factual difference (something added, left out, or changed: value, location, size, category)."
PARA_B2 = S21.PARA_B.replace("4. Identical reports: all values true, no errors.", "4. If the two reports are identical, every value must be true and the errors list must be empty.").replace(COPY_RULE_B, COPY_RULE_B + "\n6. A sentence that appears word for word in both reports is always true, however short or unusual it looks.")
COPY_RULE_D = "e) List an error only for a factual difference: something added, missing or altered (value, location, size, category)."
PARA_D2 = """Go through an ultrasound CANDIDATE report and its REFERENCE report, sentence by sentence. The REFERENCE is the correct report. Decide only whether the two say the same thing; do not decide whether the findings are realistic or complete.
Method:
- Mark each CANDIDATE sentence true when the REFERENCE contains the same statement (the same words or a rewording), otherwise false.
- Mark each REFERENCE sentence true when the CANDIDATE contains the same statement (the same words or a rewording), otherwise false.
- Another word order, another style, or another unit for the same measurement (10 mm and 1 cm) is not a difference.
- If the two reports say exactly the same, every mark is true and the error list stays empty.
- Add an item to the error list only when a fact really differs: invented, omitted or changed (a number, a position, a size, a category).
""" + TAIL
assert PARA_B2 != S21.PARA_B
PROMPTS = {'P0': judge2.PROMPT_V2, 'P1': S21.PARA_A, 'P2': PARA_B2, 'P3': judge2.PROMPT_V2, 'P4': PARA_C, 'P5': PARA_D2}; SWAP = {'P3'}; SET_A = ('P0', 'P1', 'P2'); SET_B = ('P3', 'P4', 'P5')
def sha(t): return hashlib.sha256(t.encode()).hexdigest()
ORGAN = S21.ORGAN

class Judge:
    def __init__(self, name): self.name = name; self.sc = judge2_test.SC(PROMPTS[name]); self.swap = name in SWAP
    def run(self, ref, hyp):
        r = self.sc.run(*((hyp, ref) if self.swap else (ref, hyp))); return None if r is None else dict(judge=r['judge'], f1=r['f1'])

def run_pairs(name, pairs, cache_file, label, deadline=None):
    done = {}
    if os.path.exists(cache_file):
        for l in open(cache_file): d = json.loads(l); done[(d['reference'], d['candidate'])] = d['result']
    todo = [p for p in dict.fromkeys(pairs) if p not in done]; j = Judge(name) if todo else None; t0 = time.time(); n = 0
    for i, (r, h) in enumerate(todo):
        if deadline and time.time() > deadline: print(label, name, 'time limit'); break
        done[(r, h)] = j.run(r, h); open(cache_file, 'a').write(json.dumps(dict(reference=r, candidate=h, result=done[(r, h)])) + '\n'); n += 1
        if i % 20 == 0: print(label, name, i, len(todo), round(time.time() - t0), 's', flush=True)
    return done, n, time.time() - t0

def cmd_devval(a):
    """dev / val ONLY: identical-copy gate for all six prompts (all identical copies of the dev / val judge sample, up to 24, one per distinct reference), parse failures, seconds per call"""
    ids = {r['case_id'] for s in ('dev', 'val') for r in splits.load(s)}; rows = [json.loads(l) for l in open(os.path.join(ROOT, 'bench_v2d_judge.jsonl'))]; by = collections.defaultdict(lambda: collections.defaultdict(list)); rng = random.Random(0)
    for r in rows:
        if r['case_id'] in ids: by[r['dataset']][r['case_id']].append(r)
    cases = []
    for ds in sorted(by):
        ok = sorted(c for c, rs in by[ds].items() if any(r['kind'] == 'identical' for r in rs) and any(r['kind'] == 'error' for r in rs) and any(r['kind'] == 'harmless' for r in rs)); rng.shuffle(ok)
        if ok: cases.append(ok[0])
    sel = [r for ds in sorted(by) for c in cases if c in by[ds] for r in by[ds][c]]; other = [(r['reference'], r['candidate']) for r in sel if r['kind'] != 'identical'][:40]
    ident = []; seen = set()
    for r in sel + [r for ds in sorted(by) for c, rs in sorted(by[ds].items()) for r in rs if r['kind'] == 'identical']:
        if r['kind'] == 'identical' and r['reference'] not in seen: seen.add(r['reference']); ident.append((r['reference'], r['candidate']))
    ident = ident[:24]; res = {'cases': cases, 'n_identical': len(ident), 'n_other': len(other), 'prompts': {}}
    for name in PROMPTS:
        d, n, sec = run_pairs(name, ident + (other if name in ('P2', 'P4', 'P5') else []), P(f'devval_{name}.jsonl'), 'devval')
        gi = [d[p] for p in ident]; res['prompts'][name] = dict(identical_scores=[None if x is None else x['judge'] for x in gi], identical_mean=(float(np.mean([x['judge'] for x in gi if x])) if any(gi) else None), identical_f1_mean=(float(np.mean([x['f1'] for x in gi if x])) if any(gi) else None),
                                                                    unparsed_identical=sum(x is None for x in gi), unparsed_other=(sum(d[p] is None for p in other) if name in ('P2', 'P4', 'P5') else None), new_calls=n, seconds=sec)
    tot_calls = sum(v['new_calls'] for v in res['prompts'].values()); tot_s = sum(v['seconds'] for v in res['prompts'].values()); res['seconds_per_call'] = tot_s / tot_calls if tot_calls else None; res['gate_passed'] = all(v['identical_mean'] == 1.0 and v['unparsed_identical'] == 0 for v in res['prompts'].values())
    json.dump(res, open(P('devval_gate.json'), 'w'), indent=1); print(json.dumps({k: v for k, v in res.items() if k != 'prompts'}, indent=1)); print({k: (v['identical_mean'], v['unparsed_identical'], v['unparsed_other']) for k, v in res['prompts'].items()})

# ---------------------------------------------------------------- test (one run) and analysis
CLOCK = P('compute_clock.json')
def clock_start():
    if os.path.exists(CLOCK): return json.load(open(CLOCK))['start']
    t = time.time(); json.dump(dict(start=t, start_iso=time.strftime('%Y-%m-%d %H:%M:%S')), open(CLOCK, 'w')); return t

def saved(prompt):
    """saved replies of P0 (Steps 10d + 12), P1 / P2 / P3 (Step 21c) as {(ref, cand): result}"""
    files = {'P0': [os.path.join(ROOT, 'judge_test_v2.jsonl'), os.path.join(ROOT, 'judge_big_v2.jsonl')], 'P1': [os.path.join(S21.OUT, 'replies_paraphraseA.jsonl')], 'P3': [os.path.join(S21.OUT, 'replies_swap.jsonl')]}[prompt]; d = {}
    for f in files:
        for l in open(f):
            x = json.loads(l)
            if x['result'] is not None: d[(x['reference'], x['candidate'])] = dict(judge=x['result']['judge'], f1=x['result']['f1'])
    return d

def h1_rows(): return [json.loads(l) for l in open(os.path.join(S21.OUT, 'sample.jsonl'))]          # the 89 Step 21c cases, 432 pairs

def extra_rows(per_ds):
    """the H2 extension: per dataset the next `per_ds` cases of the Step 12 sample after the 10 used by Step 21c (same shuffled order), all their error + harmless rows"""
    rows = []
    for f in ('judge_test_v2_bench.jsonl', 'judge_big_v2_bench.jsonl'): rows += [json.loads(l) for l in open(os.path.join(ROOT, f))]
    orig = saved('P0'); by = collections.defaultdict(lambda: collections.defaultdict(list)); rng = random.Random(0)
    for r in rows:
        if (r['reference'], r['candidate']) in orig and r['kind'] in ('error', 'harmless'): by[r['dataset']][r['case_id']].append(r)
    out = []; seen = {(r['reference'], r['candidate']) for r in h1_rows()}
    for ds in sorted(by):
        ids = sorted(c for c, rs in by[ds].items() if {r.get('harmless_type') for r in rs if r['kind'] == 'harmless'} >= {'small', 'matched', 'large'} and any(r['kind'] == 'error' for r in rs)); rng.shuffle(ids)
        for c in ids[S21.N_CASES:S21.N_CASES + per_ds]:
            for r in by[ds][c]:
                k = (r['reference'], r['candidate'])
                if k not in seen: seen.add(k); out.append(r)
    return out

def balanced_case_order(rows):
    """H1 cases in a seeded, dataset-round-robin order: any prefix of the schedule is balanced across the 10 datasets"""
    by = collections.defaultdict(list)
    for r in rows:
        if r['case_id'] not in by[r['dataset']]: by[r['dataset']].append(r['case_id'])
    rng = random.Random(0)
    for ds in sorted(by): rng.shuffle(by[ds])
    out = []; i = 0
    while any(i < len(by[d]) for d in by):
        for d in sorted(by):
            if i < len(by[d]): out.append(by[d][i])
        i += 1
    return out

def cmd_test(a):
    """one test run. CALL ORDER (an implementation detail, changed after the first 48 replies of an earlier dataset-ordered schedule; no reply was discarded): case by case in a seeded dataset-round-robin order, and for every pair P2, P4, P5 in turn,
    so that if the compute cap stops the run the finished pairs are complete for all three prompts and balanced across datasets. H2 extras (none planned) would follow."""
    cfg = json.load(open(P('config.json'))); start = clock_start(); deadline = start + cfg['compute_cap_hours'] * 3600; splits.load('test', script='usmeta.step39_judge_ensemble')              # one logged test read
    H1 = h1_rows(); X = extra_rows(cfg['h2_extra_cases_per_dataset']) if cfg['h2_extra_cases_per_dataset'] else []; json.dump(X, open(P('h2_extra_rows.json'), 'w')); print('H1 pairs', len(H1), '| H2 extra pairs', len(X), flush=True)
    from . import graders
    shared = graders.LocalLLM('mlx-community/gemma-2-9b-it-4bit', max_tokens=500)                                  # one model instance for all prompts (same cache dir as before: replies are reused)
    J = {n: judge2_test.SC(PROMPTS[n], cli=shared) for n in ('P2', 'P4', 'P5')}; done = {}
    for n in J:
        done[n] = {}
        if os.path.exists(P(f'test_{n}.jsonl')):
            for l in open(P(f'test_{n}.jsonl')): d = json.loads(l); done[n][(d['reference'], d['candidate'])] = d['result']
    by = collections.defaultdict(list)
    for r in H1: by[r['case_id']].append(r)
    t0 = time.time(); calls = 0; n_cases_done = 0
    for ci, cid in enumerate(balanced_case_order(H1)):
        for r in by[cid]:
            for n in ('P2', 'P4', 'P5'):
                k = (r['reference'], r['candidate'])
                if k in done[n]: continue
                if time.time() > deadline: print('compute cap reached: stopping, no extension on test; cases completed', n_cases_done); return
                s_ = J[n].run(*((k[1], k[0]) if n in SWAP else k)); res = None if s_ is None else dict(judge=s_['judge'], f1=s_['f1']); done[n][k] = res; open(P(f'test_{n}.jsonl'), 'a').write(json.dumps(dict(reference=k[0], candidate=k[1], result=res)) + '\n'); calls += 1
        n_cases_done += 1
        if ci % 5 == 0: print('test case', ci + 1, 'of', len(by), '| calls this run', calls, '|', round(time.time() - t0), 's', flush=True)
    print('all H1 pairs scored; calls this run', calls)

def load_scores():
    S = {n: saved(n) for n in ('P0', 'P1', 'P3')}
    for n in ('P2', 'P4', 'P5', 'P1'):
        f = P(f'test_{n}.jsonl')
        if os.path.exists(f):
            for l in open(f):
                x = json.loads(l)
                if x['result'] is not None: S.setdefault(n, {})[(x['reference'], x['candidate'])] = x['result']
    return S

def share(vals, groups): return gboot(vals, groups) if vals else None

def cmd_analyse(a):
    S = load_scores(); H1 = h1_rows(); X = json.load(open(P('h2_extra_rows.json'))) if os.path.exists(P('h2_extra_rows.json')) else []; cfg = json.load(open(P('config.json'))); res = {}
    j = lambda n, r: (S.get(n, {}).get((r['reference'], r['candidate'])) or {}).get('judge')
    # ---- H1
    def h1(rows, tag):
        ens, sing, grp, miss = [], [], [], 0
        for r in rows:
            v = {n: j(n, r) for n in ('P0', 'P1', 'P2', 'P3', 'P4', 'P5')}
            if any(x is None for x in v.values()): miss += 1; continue
            A = np.mean([v['P0'], v['P1'], v['P2']]); B = np.mean([v['P3'], v['P4'], v['P5']]); ens.append(float(abs(A - B) > 0.1)); sing.append(float(abs(v['P0'] - v['P3']) > 0.1)); grp.append(r['group_id'] + ':' + r['dataset'])
        e, s = share(ens, grp), share(sing, grp); return dict(pairs=len(ens), missing_pairs=miss, groups=len(set(grp)), too_small=len(set(grp)) < 30, ensemble_share=e, single_share=s)
    allr = H1
    res['H1'] = {'pooled': h1(allr, 'ALL'), **{o: h1([r for r in allr if ORGAN[r['dataset']] == o], o) for o in ('breast', 'thyroid', 'fetal head')}}
    pp = res['H1']['pooled']; res['H1']['supported'] = bool(pp['ensemble_share'] and pp['ensemble_share'][0] < 0.10 and pp['ensemble_share'][2] < pp['single_share'][0])
    # ---- H2: per-case AUROC vs matched synonym and vs harmless_small, ensemble_A vs P0 alone (cases with P0, P1, P2 for every pair)
    rows2 = H1 + X; by = collections.defaultdict(list)
    for r in rows2: by[r['case_id']].append(r)
    def case_vals(cs):
        out = {'matched': [], 'small': []}
        for c, rs in cs.items():
            err = [r for r in rs if r['kind'] == 'error']; ok = True; sc = {}
            for r in rs:
                v = [j(n, r) for n in ('P0', 'P1', 'P2')]
                if any(x is None for x in v): ok = False; break
                sc[(r['reference'], r['candidate'])] = (v[0], float(np.mean(v)))
            if not ok or not err: continue
            for ht in ('matched', 'small'):
                hh = [r for r in rs if r['kind'] == 'harmless' and r.get('harmless_type') == ht]
                if not hh: continue
                a0 = auroc_case([sc[(r['reference'], r['candidate'])][0] for r in err], [sc[(r['reference'], r['candidate'])][0] for r in hh]); aE = auroc_case([sc[(r['reference'], r['candidate'])][1] for r in err], [sc[(r['reference'], r['candidate'])][1] for r in hh])
                out[ht].append((a0, aE, rs[0]['group_id'] + ':' + rs[0]['dataset'], c))
        return out
    def h2(cs):
        cv = case_vals(cs); out = {}
        for ht, v in cv.items():
            if not v: continue
            g = [x[2] for x in v]; ng = len(set(g)); d = [x[1] - x[0] for x in v]
            out[ht] = dict(cases=len(v), groups=ng, too_small=ng < 30, auroc_P0=gboot([x[0] for x in v], g), auroc_ensembleA=gboot([x[1] for x in v], g), difference=gboot(d, g))
        return out
    res['H2'] = {'pooled': h2(by), **{o: h2({c: rs for c, rs in by.items() if ORGAN[rs[0]['dataset']] == o}) for o in ('breast', 'thyroid', 'fetal head')}}
    res['H2']['supported'] = bool(all(res['H2']['pooled'].get(ht) and res['H2']['pooled'][ht]['difference'][1] > -0.02 for ht in ('matched', 'small')))
    res['H2']['cases_h1_only'] = {o: len({r['case_id'] for r in H1 if ORGAN[r['dataset']] == o}) for o in ('breast', 'thyroid', 'fetal head')}; res['H2']['cases_total_by_organ'] = {o: len({c for c, rs in by.items() if ORGAN[rs[0]['dataset']] == o}) for o in ('breast', 'thyroid', 'fetal head')}
    res['config'] = cfg; json.dump(res, open(P('results.json'), 'w'), indent=1); print('H1 supported:', res['H1']['supported'], '| H2 supported:', res['H2']['supported'])

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd'); ap.add_argument('--max-hours', type=float, default=3.0); a = ap.parse_args()
    {'devval': cmd_devval, 'test': cmd_test, 'analyse': cmd_analyse}[a.cmd](a)
