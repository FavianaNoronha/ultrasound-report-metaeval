"""Step 34: metamorphic checks (no ground truth needed). NEW file. Relations and thresholds are fixed in this docstring before any score is computed.
Items: (i) 300 templated test references (100 per organ, seed 0, one per case); (ii) the 41 HiSBreast test texts (local only: no HiSBreast text, translation or id leaves local_data; only aggregated rates are written to git);
(iii) the 180 Step 28 writer reports (cleaned text), scored against their label reference. For sets (i) and (ii) the reference r is the text x itself; for (iii) r is the label reference and x the writer report.
Relations (T = transform of x; s(r, y) = scorer):
  R1 unit invariance:      T = mm -> cm (or cm -> mm if no mm). Violation if |s(r,T(x)) - s(r,x)| > delta.
  R2 sentence-order inv.:  T = reverse the sentence order (needs >= 2 sentences). Violation if |s(r,T(x)) - s(r,x)| > delta.
  R3 synonym invariance:   T = one one-token synonym swap (mass<->lesion, margins<->borders, nodule->lesion, echo pattern->echogenicity, is seen->is demonstrated, Assessment->Impression, measuring->with a size of, approximately->about). Same violation rule.
  R4 number swap lowers:   T = swap the first two distinct measurement numbers (value + mm / cm / %), or, with a single measurement number, multiply it by 1.5. Violation if s(r,T(x)) >= s(r,H(x)), H = the harmless baseline of the same text (R3 swap if applicable, else R2 reorder, else x itself): the error must score STRICTLY lower than the harmless rewording.
  R5 negation flip lowers: T = first applicable of: 'No focal lesion/nodule is seen' -> 'A focal lesion is seen'; delete the first 'no ' before a word; delete the first ' not '; insert 'not' after 'is/are seen|present|identified|demonstrated'. Same violation rule as R4.
  R6 monotone in size:     T_f = first measurement number x f for the chain down f = 0.75, 0.5 and up f = 1.25, 2.0. Violation if any step to a larger error raises the score (s(r,T_{f2}(x)) > s(r,T_{f1}(x)), starting from s(r,x)); flat chains are reported separately.
delta = 0.05 (sensitivity 0.10) on the 0-1 score scale. Violation rate = violations / applicable items (an item is applicable when the transform exists); 95% CI: bootstrap over items (1,000 resamples, seed 0); under 30 applicable items: too small to compare.
Scorers: BLEU, ROUGE-L, chrF, BERTScore, RaTEScore (all items); regex finding_f1 (templated items only); Gemma judge_score and llm_finding_f1 (extractor v3) on a capped subset (20 templated, 10 HiSBreast, 20 writer reports).
    python3 -m usmeta.step34_metamorphic build | cheap | llm | analyse"""
import os, sys, json, re, random, math, collections, time, argparse
import numpy as np
from . import splits, schema, graders, judge2, judge2_test, step27_extractor as X, step28_natural_errors as S28, qwen_real, hisbreast, hisbreast_bench
from . import step32_extractor_v3 as V32
from .step10d_analysis import gboot

ROOT = X.ROOT; OUT = os.path.join(ROOT, 'results', 'partA', 'step34_metamorphic'); LOCAL = os.path.join(ROOT, 'local_data', 'step34'); os.makedirs(OUT, exist_ok=True); os.makedirs(LOCAL, exist_ok=True)
X.CACHE = os.path.join(LOCAL, 'extract_cache.jsonl'); X.OUT = LOCAL                           # HiSBreast texts pass through this cache: keep it in the git-ignored local folder
DELTA = 0.05; DELTAS = (0.05, 0.10); MIN_N = 30; DOWN = (0.75, 0.5); UP = (1.25, 2.0)
REL = ['R1', 'R2', 'R3', 'R4', 'R5', 'R6']; RELNAME = {'R1': 'unit invariance', 'R2': 'sentence-order invariance', 'R3': 'synonym invariance', 'R4': 'number swap must lower', 'R5': 'negation flip must lower', 'R6': 'monotone in error size'}
SYN = [('mass', 'lesion'), ('lesion', 'mass'), ('margins', 'borders'), ('echo pattern', 'echogenicity'), ('nodule', 'lesion'), ('is seen', 'is demonstrated'), ('Assessment:', 'Impression:'), ('measuring', 'with a size of'), ('approximately', 'about')]
NUM = re.compile(r'(\d+(?:[.,]\d+)?)(\s*)(mm|cm|%)')

def fmt(v, like):
    s = f'{v:.1f}' if '.' in like or ',' in like else f'{int(round(v))}'
    return s.replace('.', ',') if ',' in like else s
def unit(x):
    if re.search(r'\d\s*mm\b', x): return NUM.sub(lambda m: (f"{float(m[1].replace(',', '.')) / 10:g} cm" if m[3] == 'mm' else m[0]), x)
    if re.search(r'\d\s*cm\b', x): return NUM.sub(lambda m: (f"{float(m[1].replace(',', '.')) * 10:g} mm" if m[3] == 'cm' else m[0]), x)
    return None
def order(x):
    s = [t.strip() for t in re.split(r'(?<=[.!?])\s+', x) if t.strip()]
    return ' '.join(s[::-1]) if len(s) >= 2 else None
def syn(x):
    for a, b in SYN:
        if a in x: return x.replace(a, b, 1)
    return None
def numswap(x):
    ms = list(NUM.finditer(x)); vals = []
    for m in ms:
        if m[1] not in [v[0] for v in vals]: vals.append((m[1], m))
    if len(vals) >= 2:
        (a, ma), (b, mb) = vals[0], vals[1]; i, j = ma.start(1), mb.start(1)
        if ma.start() > mb.start(): ma, mb, a, b = mb, ma, b, a
        return x[:ma.start(1)] + b + x[ma.end(1):mb.start(1)] + a + x[mb.end(1):]
    if len(vals) == 1:
        a, m = vals[0]; return x[:m.start(1)] + fmt(float(a.replace(',', '.')) * 1.5, a) + x[m.end(1):]
    return None
def negflip(x):
    if re.search(r'No focal (lesion|nodule) is seen', x): return re.sub(r'No focal (lesion|nodule) is seen', r'A focal \1 is seen', x, 1)
    m = re.search(r'\b([Nn])o (\w+)', x)
    if m: return x[:m.start()] + (m[2].capitalize() if m[1] == 'N' else m[2]) + x[m.end():]
    if ' not ' in x: return x.replace(' not ', ' ', 1)
    m = re.search(r'\b(is|are) (seen|present|identified|demonstrated)\b', x)
    if m: return x[:m.end(1)] + ' not' + x[m.end(1):]
    return None
def scale(x, f):
    m = NUM.search(x)
    if not m: return None
    v = float(m[1].replace(',', '.')) * f; new = fmt(v, m[1])
    return x[:m.start(1)] + new + x[m.end(1):] if new != m[1] else None

def variants(x):
    """relation -> list of (key, text); R4 / R5 also carry the harmless baseline H(x)"""
    v = {'R1': [('T', unit(x))], 'R2': [('T', order(x))], 'R3': [('T', syn(x))], 'R4': [('T', numswap(x))], 'R5': [('T', negflip(x))], 'R6': [(f'd{f}', scale(x, f)) for f in DOWN] + [(f'u{f}', scale(x, f)) for f in UP]}
    base = syn(x) or order(x) or x; v['H'] = [('H', base)]
    return {k: [(a, b) for a, b in l if b is not None and b != x] if k != 'H' else l for k, l in v.items()}

def build():
    rng = random.Random(0); items = []
    ids = {r['case_id'] for r in splits.load('test', script='usmeta.step34_metamorphic')}; rows = [json.loads(l) for l in open(os.path.join(ROOT, 'bench_test_v2d.jsonl'))]; seen = {}
    for r in rows:
        if r['kind'] == 'identical' and r['case_id'] in ids: seen[r['case_id']] = r
    for organ in ('breast', 'thyroid', 'fetal'):
        pool = sorted(c for c, r in seen.items() if r['organ'] == organ); rng.shuffle(pool)
        for c in pool[:100]: t = seen[c]['reference']; items.append(dict(set='templated', id=c, group=c, organ=organ, ref=t, x=t))
    for k in hisbreast_bench.kept(strict=True):
        if k['split'] == 'test': items.append(dict(set='hisbreast', id='H' + k['exam'], group=k['exam'], organ='breast', ref=k['en'], x=k['en']))
    S28.OUT = os.path.join(ROOT, 'results', 'partA', 'step28_natural_errors')
    for s in S28.load_all(): items.append(dict(set='writer', id=s['case_id'], group=s['case_id'], organ=s['organ'], ref=s['reference'], x=s['report']))
    for i, it in enumerate(items): it['variants'] = variants(it['x'])
    # LLM-scorer subset: 20 templated, 10 HiSBreast, 20 writer reports (seed 0, stratified by organ for the templated)
    sub = {'templated': 20, 'hisbreast': 10, 'writer': 20}; llm_ids = set()
    for st, n in sub.items():
        pool = [it['id'] for it in items if it['set'] == st]; rng.shuffle(pool); llm_ids |= set(pool[:n])
    for it in items: it['llm'] = it['id'] in llm_ids
    json.dump(items, open(os.path.join(LOCAL, 'items.json'), 'w'))
    app = {st: {r: sum(1 for it in items if it['set'] == st and it['variants'].get(r)) for r in REL} for st in sub}; print({st: sum(1 for it in items if it['set'] == st) for st in sub}, app)

def pairs_of(items, llm_only=False):
    out = set()
    for it in items:
        if llm_only and not it['llm']: continue
        out.add((it['ref'], it['x']))
        for r, l in it['variants'].items():
            for k, t in l: out.add((it['ref'], t))
    return sorted(out)

def cmd_cheap(a):
    items = json.load(open(os.path.join(LOCAL, 'items.json'))); P_ = pairs_of(items); fn = os.path.join(LOCAL, 'scores_cheap.json'); S = json.load(open(fn)) if os.path.exists(fn) else {'pairs': [list(p) for p in P_], 'scores': {}}
    refs, hyps = [p[0] for p in P_], [p[1] for p in P_]
    for spec in ('bleu', 'rougeL', 'chrf', 'bertscore:roberta-large', 'ratescore'):
        g = graders.make(spec)
        if g.name in S['scores']: continue
        t = time.time(); s = g.batch(refs, hyps) if hasattr(g, 'batch') else [g.score(r, h) for r, h in zip(refs, hyps)]; S['scores'][g.name] = [float(x) for x in s]; json.dump(S, open(fn, 'w')); print('scored', g.name, len(P_), round(time.time() - t), 's', flush=True)
    org = {it['ref']: ('fetal' if it['organ'] == 'fetal' else it['organ']) for it in items if it['set'] != 'hisbreast'}
    S['scores']['finding_f1'] = [(schema.finding_scores(schema.to_findings(schema.extract_rule(r, org[r]), org[r]), schema.to_findings(schema.extract_rule(h, org[r]), org[r]))[2] if r in org else None) for r, h in P_]; json.dump(S, open(fn, 'w')); print('finding_f1 done')

def cmd_llm(a):
    items = json.load(open(os.path.join(LOCAL, 'items.json'))); P_ = pairs_of(items, llm_only=True); fn = os.path.join(LOCAL, 'scores_llm.json'); S = json.load(open(fn)) if os.path.exists(fn) else {'judge': {}, 'llm_finding_f1': {}}
    org = {it['ref']: it['organ'] for it in items}; t0 = time.time(); dl = t0 + a.max_hours * 3600
    ex = V32.extractor(); flat = {}
    def fl(o, t):
        if (o, t) not in flat: flat[(o, t)] = ex.facts(o, t)[0]
        return flat[(o, t)]
    for i, (r, h) in enumerate(P_):
        if time.time() > dl: print('time limit'); json.dump(S, open(fn, 'w')); return
        k = r + '|||' + h
        if k not in S['llm_finding_f1']:
            o = org[r]; S['llm_finding_f1'][k] = X.llm_finding_f1(fl(o, r), fl(o, h), o)
        if i % 25 == 0: print('llm_f1', i, len(P_), round(time.time() - t0), 's', flush=True); json.dump(S, open(fn, 'w'))
    json.dump(S, open(fn, 'w'))
    sc = judge2_test.SC(judge2.PROMPT_V2)
    for i, (r, h) in enumerate(P_):
        if time.time() > dl: print('time limit'); json.dump(S, open(fn, 'w')); return
        k = r + '|||' + h
        if k not in S['judge']:
            res = sc.run(r, h); S['judge'][k] = None if res is None else dict(judge=res['judge'], f1=res['f1'])
        if i % 25 == 0: print('judge', i, len(P_), round(time.time() - t0), 's', flush=True); json.dump(S, open(fn, 'w'))
    json.dump(S, open(fn, 'w')); print('llm scorers done')

def wilson(k, n, z=1.96):
    if not n: return None
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)); return [p, (c - h) / d, (c + h) / d]

def cmd_analyse(a):
    items = json.load(open(os.path.join(LOCAL, 'items.json'))); C = json.load(open(os.path.join(LOCAL, 'scores_cheap.json'))); Pc = {tuple(p): i for i, p in enumerate(C['pairs'])}; L = json.load(open(os.path.join(LOCAL, 'scores_llm.json'))) if os.path.exists(os.path.join(LOCAL, 'scores_llm.json')) else {'judge': {}, 'llm_finding_f1': {}}
    def get(name, r, t):
        if name in C['scores']: return C['scores'][name][Pc[(r, t)]] if (r, t) in Pc else None
        d = L['judge'].get(r + '|||' + t) if name in ('judge_score', 'sentence_f1') else L['llm_finding_f1'].get(r + '|||' + t)
        return (d['judge'] if name == 'judge_score' else d['f1']) if isinstance(d, dict) else d
    scorers = [('bleu', 'BLEU'), ('rougeL', 'ROUGE-L'), ('chrf', 'chrF'), ('bertscore[roberta-large]', 'BERTScore'), ('ratescore', 'RaTEScore'), ('finding_f1', 'finding_f1 (regex; templated)'), ('llm_finding_f1', 'llm_finding_f1 (v3; subset)'), ('judge_score', 'judge_score (subset)')]
    res = {}
    for name, nm in scorers:
        for st in ('templated', 'hisbreast', 'writer', 'ALL'):
            for rel in REL:
                for delta in DELTAS if rel in ('R1', 'R2', 'R3') else (None,):
                    viol, flat, grp = [], [], []
                    for it in items:
                        if st != 'ALL' and it['set'] != st: continue
                        if name in ('llm_finding_f1', 'judge_score') and not it['llm']: continue
                        if name == 'finding_f1' and it['set'] == 'hisbreast': continue
                        r, x = it['ref'], it['x']; s0 = get(name, r, x)
                        if s0 is None: continue
                        vs = it['variants'].get(rel)
                        if not vs: continue
                        if rel in ('R1', 'R2', 'R3'):
                            s1 = get(name, r, vs[0][1])
                            if s1 is None: continue
                            viol.append(float(abs(s1 - s0) > delta)); grp.append(it['group'])
                        elif rel in ('R4', 'R5'):
                            s1 = get(name, r, vs[0][1]); sh = get(name, r, it['variants']['H'][0][1])
                            if s1 is None or sh is None: continue
                            viol.append(float(s1 >= sh)); grp.append(it['group'])
                        else:
                            chain_d = [s0] + [get(name, r, t) for k, t in vs if k.startswith('d')]; chain_u = [s0] + [get(name, r, t) for k, t in vs if k.startswith('u')]
                            if any(v is None for v in chain_d + chain_u) or (len(chain_d) < 2 and len(chain_u) < 2): continue
                            rises = any(b > a_ for ch in (chain_d, chain_u) for a_, b in zip(ch, ch[1:])); viol.append(float(rises)); flat.append(float(len(set(chain_d + chain_u)) == 1)); grp.append(it['group'])
                    key = f'{name}|{st}|{rel}' + (f'|{delta}' if delta else '')
                    res[key] = dict(n=len(viol), violation=(gboot(viol, grp) if viol else None), too_small=len(viol) < MIN_N, **({'flat_share': float(np.mean(flat))} if flat else {}))
    res['_meta'] = dict(delta=DELTA, deltas=list(DELTAS), applicable={st: {r: sum(1 for it in items if (st == 'ALL' or it['set'] == st) and it['variants'].get(r)) for r in REL} for st in ('templated', 'hisbreast', 'writer', 'ALL')}, items={st: sum(1 for it in items if it['set'] == st) for st in ('templated', 'hisbreast', 'writer')}, llm_subset={st: sum(1 for it in items if it['set'] == st and it['llm']) for st in ('templated', 'hisbreast', 'writer')})
    json.dump(res, open(os.path.join(OUT, 'results.json'), 'w'), indent=1); print('saved results.json', len(res))

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd'); ap.add_argument('--max-hours', type=float, default=3.0); a = ap.parse_args()
    {'build': lambda a: build(), 'cheap': cmd_cheap, 'llm': cmd_llm, 'analyse': cmd_analyse}[a.cmd](a)
