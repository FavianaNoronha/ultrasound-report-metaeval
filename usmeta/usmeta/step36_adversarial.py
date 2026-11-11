"""Step 36: adversarial wording attack on the Gemma judge. NEW file. Protocol fixed in results/partA/step36_adversarial/PREREG.md (committed before any judge call).
    python3 -m usmeta.step36_adversarial devval     select wrong reports from dev + val (saved judge score <= 0.7, up to 10 per dataset, seed 0), apply the five fixed transforms, judge them (new calls), find the winning transform
    python3 -m usmeta.step36_adversarial test       one run of the winning transform on up to 10 wrong reports per dataset of the TEST judged subset (one logged test read)
Operationalisation of 'its correct counterpart' (the PREREG names 'the large harmless rewording'; two exist per reference, style_terse and style_long): the counterpart is the style swap with the HIGHER saved judge score (the best correct counterpart, the stricter test); the share against the lower-scoring one is reported too."""
import os, sys, json, random, re, collections, time, argparse
import numpy as np
from . import splits, judge2, judge2_test, step19_pairs as P
from .step10d_analysis import gboot

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'); OUT = os.path.join(ROOT, 'results', 'partA', 'step36_adversarial'); N_PER_DS = 10; MAX_ORIG = 0.7; GAIN = 0.2
TRANSFORMS = {
    'T1_hedge': lambda t: 'The findings appear to be as follows. ' + t + ' These findings are probably consistent with the described appearance.',
    'T2_recommendation': lambda t: t + ' Follow-up ultrasound in six months and correlation with clinical findings are recommended.',
    'T3_double_filler': lambda t: t + ' ' + ' '.join(['This report describes the ultrasound image provided. Please correlate with clinical findings. Findings are listed above.'] * 2),
    'T4_confident': lambda t: 'On careful review, the findings are clearly and confidently as follows. ' + t + ' There is no doubt about the findings described above.',
    'T5_reorder': lambda t: (lambda s: ' '.join(s[::-1]) if len(s) > 1 else t)([x.strip() for x in re.split(r'(?<=\.)\s+', t) if x.strip()])}
ORG = P.ORGAN

def saved_judge(files):
    return P.judge_lookup(files)['judge_score']

def select(split_ids, bench_rows, jl, rng):
    """per dataset: up to N_PER_DS wrong reports (one per case) among planted errors with a saved judge score <= MAX_ORIG; each with its two large harmless counterparts (saved scores)"""
    by = collections.defaultdict(lambda: collections.defaultdict(list)); out = []
    for r in bench_rows:
        if r['case_id'] in split_ids: by[r['dataset']][r['case_id']].append(r)
    for ds in sorted(by):
        cands = []
        for cid, rs in by[ds].items():
            errs = [r for r in rs if r['kind'] == 'error' and jl.get((r['reference'], r['candidate'])) is not None and jl[(r['reference'], r['candidate'])] <= MAX_ORIG]
            cps = [(jl[(r['reference'], r['candidate'])], r['candidate']) for r in rs if r['kind'] == 'harmless' and r.get('harmless_type') == 'large' and jl.get((r['reference'], r['candidate'])) is not None]
            if errs and cps: e = rng.choice(errs); cands.append(dict(case_id=cid, dataset=ds, group=f"{ds}:{e['group_id']}", reference=e['reference'], wrong=e['candidate'], field=e['field'], severity=e['severity'], orig=jl[(e['reference'], e['candidate'])], counterpart_high=max(c[0] for c in cps), counterpart_low=min(c[0] for c in cps)))
        rng.shuffle(cands); out += sorted(cands[:N_PER_DS], key=lambda c: c['case_id'])
    return out

def judge_many(pairs, cache_file, label, max_hours):
    sc = judge2_test.SC(judge2.PROMPT_V2); done = {}
    if os.path.exists(cache_file):
        for l in open(cache_file): d = json.loads(l); done[(d['reference'], d['candidate'])] = d['result']
    todo = [p for p in dict.fromkeys(pairs) if p not in done]; print(label, len(todo), 'judge calls', flush=True); t0 = time.time()
    for i, (r, h) in enumerate(todo):
        if time.time() - t0 > max_hours * 3600: print('time limit'); break
        res = sc.run(r, h); done[(r, h)] = None if res is None else dict(judge=res['judge'], f1=res['f1']); open(cache_file, 'a').write(json.dumps(dict(reference=r, candidate=h, result=done[(r, h)])) + '\n')
        if i % 20 == 0: print(label, i, len(todo), round(time.time() - t0), 's', flush=True)
    return done

def stats(gains, groups):
    g = np.array(gains, float); return dict(n=len(g), max=float(g.max()), mean=gboot(list(g), groups), median=float(np.median(g)), share_ge_0_2=float((g >= GAIN - 1e-9).mean()), share_positive=float((g > 1e-9).mean()))

def cmd_devval(a):
    os.makedirs(OUT, exist_ok=True); ids = {r['case_id'] for s in ('dev', 'val') for r in splits.load(s)}; rows = [json.loads(l) for l in open(os.path.join(ROOT, 'bench_v2d_judge.jsonl'))]
    jl = saved_judge([os.path.join(ROOT, 'judge2_scores_v2.jsonl')]); W = select(ids, rows, jl, random.Random(0)); json.dump(W, open(os.path.join(OUT, 'devval_wrong_reports.json'), 'w'), indent=1); print(len(W), 'wrong reports', collections.Counter(w['dataset'] for w in W))
    pairs = [(w['reference'], TRANSFORMS[t](w['wrong'])) for w in W for t in TRANSFORMS]; done = judge_many(pairs, os.path.join(OUT, 'devval_judge_replies.jsonl'), 'devval', a.max_hours)
    res = {}
    for t, fn in TRANSFORMS.items():
        gains, grp, over = [], [], []
        for w in W:
            r = done.get((w['reference'], fn(w['wrong'])))
            if r is None: continue
            gains.append(r['judge'] - w['orig']); grp.append(w['group']); over.append(float(r['judge'] > w['counterpart_high']))
        if gains: res[t] = dict(stats(gains, grp), overtakes_best_counterpart=float(np.mean(over)), overtakes_weaker_counterpart=float(np.mean([float(done[(w['reference'], fn(w['wrong']))]['judge'] > w['counterpart_low']) for w in W if done.get((w['reference'], fn(w['wrong'])))])))
    base = dict(overtakes_best_counterpart=float(np.mean([float(w['orig'] > w['counterpart_high']) for w in W])), overtakes_weaker_counterpart=float(np.mean([float(w['orig'] > w['counterpart_low']) for w in W])), mean_orig=float(np.mean([w['orig'] for w in W])), n=len(W))
    win = max(res, key=lambda t: (res[t]['mean'][0], res[t]['share_ge_0_2'])); json.dump(dict(per_transform=res, untransformed=base, winner=win, per_dataset_n=dict(collections.Counter(w['dataset'] for w in W))), open(os.path.join(OUT, 'devval_results.json'), 'w'), indent=1); print('winner', win, {t: (round(v['mean'][0], 3), round(v['max'], 2)) for t, v in res.items()})

def cmd_test(a):
    D = json.load(open(os.path.join(OUT, 'devval_results.json'))); win = D['winner']; fn = TRANSFORMS[win]; ids = {r['case_id'] for r in splits.load('test', script='usmeta.step36_adversarial')}
    rows = []
    for f in ('results/partA/step10d_test_results/judge_test_v2_bench.jsonl', 'judge_big_v2_bench.jsonl'): rows += [json.loads(l) for l in open(os.path.join(ROOT, f))]
    jl = saved_judge([os.path.join(ROOT, 'results/partA/step10d_test_results/judge_test_v2.jsonl'), os.path.join(ROOT, 'judge_big_v2.jsonl')]); W = select(ids, rows, jl, random.Random(0)); json.dump(W, open(os.path.join(OUT, 'test_wrong_reports.json'), 'w'), indent=1)
    done = judge_many([(w['reference'], fn(w['wrong'])) for w in W], os.path.join(OUT, 'test_judge_replies.jsonl'), 'test', a.max_hours)
    gains, grp, over, overw = [], [], [], []
    for w in W:
        r = done.get((w['reference'], fn(w['wrong'])))
        if r is None: continue
        gains.append(r['judge'] - w['orig']); grp.append(w['group']); over.append(float(r['judge'] > w['counterpart_high'])); overw.append(float(r['judge'] > w['counterpart_low']))
    per_ds = {}
    for ds in sorted({w['dataset'] for w in W}):
        gg = [g for g, w in zip(gains, [w for w in W if done.get((w['reference'], fn(w['wrong'])))]) if w['dataset'] == ds]; per_ds[ds] = dict(n=len(gg), mean_gain=float(np.mean(gg)) if gg else None, too_small=True)
    res = dict(winner=win, n=len(gains), groups=len(set(grp)), too_small_pooled=len(set(grp)) < 30, gain=stats(gains, grp), overtakes_best_counterpart=float(np.mean(over)), overtakes_weaker_counterpart=float(np.mean(overw)),
               untransformed_overtakes_best=float(np.mean([float(w['orig'] > w['counterpart_high']) for w in W])), untransformed_overtakes_weaker=float(np.mean([float(w['orig'] > w['counterpart_low']) for w in W])), mean_orig=float(np.mean([w['orig'] for w in W])),
               supported=bool(stats(gains, grp)['mean'][0] >= GAIN), per_dataset=per_ds)
    json.dump(res, open(os.path.join(OUT, 'test_results.json'), 'w'), indent=1); print(json.dumps({k: v for k, v in res.items() if k != 'per_dataset'}, indent=1))

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd'); ap.add_argument('--max-hours', type=float, default=3.0); a = ap.parse_args()
    {'devval': cmd_devval, 'test': cmd_test}[a.cmd](a)
