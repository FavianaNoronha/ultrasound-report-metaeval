"""Step 45, Parts D and F: all Gemma-2-9B-it 4-bit calls in ONE process (the model is loaded once; every reply is cached under .llm_cache by graders.LocalLLM, key = model + prompt). NEW file; judge2 (frozen holistic prompt_v2), judge2_test, step19_pairs and the Part A set are imported unchanged.
 F calls: the frozen holistic judge on set A pairs (reference = templated reference text, candidate = the writer-made free-text report): all test pairs and a dev/val subset (for the thresholds).
 D calls: the claim-by-claim judge, two prompt variants, on a seeded sample of the Step 44 judge subset (test) and of its val judge pool (for the val-fixed threshold).
Caps (stop and write what exists as incomplete): F 2 h, D 3 h of compute; order inside each part is seeded and interleaved so that a cut leaves a balanced sample.
    python3 -m usmeta.step45_gemma run [--cap-f 2] [--cap-d 3] | status"""
import os, sys, json, re, time, random, hashlib, zlib, collections, argparse
from . import graders, judge2, step19_pairs as P19, step45_freetext as FT

ROOT = FT.ROOT; OUT = os.path.join(ROOT, 'results', 'partA', 'step45_improve_scorers', 'gemma'); P = lambda f: os.path.join(OUT, f); os.makedirs(OUT, exist_ok=True)
MODEL = 'mlx-community/gemma-2-9b-it-4bit'; SEED = 45; D_TEST = 350; D_VAL = 150; F_DEVVAL_CASES = 40          # cases per organ of set A dev/val used for the thresholds

CLAIM_V1 = ("You are a sonographer-radiologist checking an AI-written ultrasound report (CANDIDATE) against a REFERENCE report.\n"
            "Step 1: split the CANDIDATE into its separate factual claims (one fact per claim: a measurement, a location, a shape, a category, a diagnosis, a presence or absence).\n"
            "Step 2: for each candidate claim decide: supported (the REFERENCE states the same fact; wording, order and units may differ, 10 mm = 1 cm), contradicted (the REFERENCE states a different value), or unsupported (the REFERENCE does not state it).\n"
            "Step 3: list the REFERENCE facts that the CANDIDATE does not state or states differently (omitted).\n"
            "Ignore wording and style. Do not judge medical plausibility. If the reports agree in meaning, every claim is supported and omitted is empty.\n\n"
            "REFERENCE:\n{ref}\n\nCANDIDATE:\n{cand}\n\n"
            'Reply with JSON only: {{"claims": [{{"claim": "<one fact of the candidate>", "verdict": "supported|contradicted|unsupported"}}], "omitted": ["<reference fact missing from the candidate>"]}}\n')
CLAIM_V2 = ("Compare two ultrasound reports fact by fact.\n"
            "First list the separate facts of the REFERENCE (sizes, positions, shapes, categories, diagnoses, presence / absence). Then, for every fact of the CANDIDATE, check it against the REFERENCE: it is supported if the REFERENCE says the same (other words, order or units are fine), contradicted if the REFERENCE gives a different value, unsupported if the REFERENCE does not mention it. "
            "Finally name each REFERENCE fact that the CANDIDATE leaves out or changes (omitted).\n"
            "Judge facts only, not style or plausibility. Identical meaning means all supported and nothing omitted.\n\n"
            "REFERENCE:\n{ref}\n\nCANDIDATE:\n{cand}\n\n"
            'Output JSON only, in this form: {{"claims": [{{"claim": "...", "verdict": "supported" or "contradicted" or "unsupported"}}], "omitted": ["..."]}}\n')
VARIANTS = {'c1': CLAIM_V1, 'c2': CLAIM_V2}

def parse_claims(txt):
    m = re.search(r'\{.*\}', txt or '', re.S)
    try: js = json.loads(re.sub(r',\s*([}\]])', r'\1', m.group(0)))
    except Exception: return None
    cl, om = js.get('claims'), js.get('omitted', [])
    if not isinstance(cl, list) or not isinstance(om, list): return None
    verd = [str(c.get('verdict', '')).lower() for c in cl if isinstance(c, dict)]
    if cl and not verd: return None
    return dict(n_claims=len(verd), supported=sum(v.startswith('support') for v in verd), contradicted=sum(v.startswith('contra') for v in verd), unsupported=sum(v.startswith('unsupp') or v.startswith('not') for v in verd), omitted=len(om))

def claim_score(r):
    """1 - (candidate claims not supported + reference facts omitted) / (candidate claims + omitted); 1.0 = nothing wrong"""
    bad = r['n_claims'] - r['supported'] + r['omitted']; tot = r['n_claims'] + r['omitted']
    return 1.0 if tot == 0 else max(0.0, 1.0 - bad / tot)

class Runner:
    def __init__(self):
        self.llm = graders.LocalLLM(MODEL, max_tokens=700); self.sc = judge2.SentenceCheck(cli=self.llm); self.t0 = time.time()
    def holistic(self, ref, cand):
        r = self.sc.run(ref, cand); return None if r is None else dict(judge=r['judge'], f1=r['f1'], n_err=r['n_err'], cats=r['cats'])
    def claim(self, variant, ref, cand):
        txt = self.llm.ask(VARIANTS[variant].format(ref=ref, cand=cand), valid=lambda t: parse_claims(t) is not None)
        r = parse_claims(txt) if txt else None
        return None if r is None else dict(r, score=claim_score(r))

# ---------------------------------------------------------------- the pair lists
def f_pairs():
    A = json.load(open(FT.P('set_A.json')))['cases']; out = []
    for which in ('devval', 'test'):
        per = collections.defaultdict(list)
        for cid, c in sorted(A.items()):
            if c['set'] != which or not c['true_reports'] or not c['twin_report']: continue
            per[c['organ']].append(cid)
        rng = random.Random(SEED)
        for o in per:
            ids = list(per[o]); rng.shuffle(ids); keep = ids if which == 'test' else ids[:F_DEVVAL_CASES]
            for cid in keep:
                c = A[cid]
                for r in c['true_reports']: out.append(dict(id=f'{cid}|true|{r["style"]}', set=which, case=cid, organ=o, group=c['group'], kind='harmless', ref=c['reference'], cand=r['text']))
                out.append(dict(id=f"{cid}|twin|{c['twin_report']['style']}", set=which, case=cid, organ=o, group=c['group'], kind='error', ref=c['reference'], cand=c['twin_report']['text']))
    rng = random.Random(SEED + 1); rng.shuffle(out); out.sort(key=lambda p: p['set'] != 'devval'); return out         # dev/val first (thresholds), each block shuffled so a cut stays balanced

def d_pairs():
    rows, sc, jset = P19.load('test'); vrows, vsc, vjset = P19.load('val'); out = []
    for which, R, S, N in (('val', vrows, vsc, D_VAL), ('test', rows, sc, D_TEST)):
        pool = [r for r in R if (r['reference'], r['candidate']) in S['judge_score'] and ((which == 'val' and (r['reference'], r['candidate']) in vjset) or (which == 'test' and (r['reference'], r['candidate']) in jset))]
        seen = set(); uniq = []
        for r in pool:
            k = (r['reference'], r['candidate'])
            if k not in seen: seen.add(k); uniq.append(r)
        rng = random.Random(SEED + (2 if which == 'val' else 3)); rng.shuffle(uniq)
        for r in uniq[:N]: out.append(dict(id=f"{which}|{r['id']}", set=which, case=r['case_id'], organ=r['organ'], group=f"{r['dataset']}:{r['group_id']}", kind=r['kind'], ht=r.get('harmless_type'), ref=r['reference'], cand=r['candidate'], holistic=S['judge_score'][(r['reference'], r['candidate'])]))
    rng = random.Random(SEED + 4); rng.shuffle(out); out.sort(key=lambda p: p['set'] != 'val'); return out

def append(fn, rec):
    with open(P(fn), 'a') as fh: fh.write(json.dumps(rec) + '\n')

def done(fn):
    d = {}
    if os.path.exists(P(fn)):
        for l in open(P(fn)): r = json.loads(l); d[r['id']] = r
    return d

def cmd_run(a):
    R = Runner(); t_all = time.time()
    # ------------- F: holistic judge on set A
    fp = f_pairs(); dn = done('f_holistic.jsonl'); dl = time.time() + a.cap_f * 3600; n = 0; stopped_f = False; t0 = time.time()
    print('F pairs', len(fp), 'done', len(dn), flush=True)
    for p in fp:
        if p['id'] in dn: continue
        if time.time() > dl: stopped_f = True; print('F cap reached'); break
        r = R.holistic(p['ref'], p['cand']); append('f_holistic.jsonl', dict(id=p['id'], set=p['set'], kind=p['kind'], organ=p['organ'], group=p['group'], case=p['case'], result=r)); n += 1
        if n % 25 == 0: print('F', n, round(time.time() - t0), 's', flush=True)
    json.dump(dict(pairs=len(fp), generated_this_run=n, stopped_by_cap=stopped_f, seconds=round(time.time() - t0)), open(P('f_status.json'), 'w'))
    # ------------- D: claim-by-claim, two variants per pair
    dp = d_pairs(); dd = {v: done(f'd_{v}.jsonl') for v in VARIANTS}; dl = time.time() + a.cap_d * 3600; n = 0; stopped_d = False; t0 = time.time()
    print('D pairs', len(dp), flush=True)
    for p in dp:
        if all(p['id'] in dd[v] for v in VARIANTS): continue
        if time.time() > dl: stopped_d = True; print('D cap reached'); break
        for v in VARIANTS:
            if p['id'] in dd[v]: continue
            r = R.claim(v, p['ref'], p['cand']); append(f'd_{v}.jsonl', dict(id=p['id'], set=p['set'], kind=p['kind'], ht=p.get('ht'), organ=p['organ'], group=p['group'], holistic=p['holistic'], result=r)); n += 1
        if n % 20 == 0: print('D', n, round(time.time() - t0), 's', flush=True)
    json.dump(dict(pairs=len(dp), calls_this_run=n, stopped_by_cap=stopped_d, seconds=round(time.time() - t0)), open(P('d_status.json'), 'w')); print('all done', round(time.time() - t_all), 's')

def cmd_status(a):
    print({fn: len(done(fn)) for fn in ('f_holistic.jsonl', 'd_c1.jsonl', 'd_c2.jsonl')}); print('F pairs', len(f_pairs()), 'D pairs', len(d_pairs()))

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd'); ap.add_argument('--cap-f', type=float, default=2.0); ap.add_argument('--cap-d', type=float, default=3.0); a = ap.parse_args(); {'run': cmd_run, 'status': cmd_status}[a.cmd](a)
