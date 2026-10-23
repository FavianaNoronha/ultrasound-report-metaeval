"""Step 7: Layer 2 AI judge with a local open model (MLX). `sentence_check` follows the RadFact PROTOCOL (sentence-level support in both directions),
implemented with a local Gemma-2-9B prompt; it is NOT the original RadFact code or prompts. One model call per (reference, candidate) pair returns
  candidate_supported[i]  : is candidate sentence i supported by the reference     -> precision
  reference_covered[j]    : is reference sentence j covered by the candidate       -> recall
  errors[]                : discrepancies with severity and an error category      -> judge score + category accuracy
"""
import re, json
from . import graders

CATS = ('false finding', 'missed finding', 'wrong location', 'wrong severity/category', 'wrong measurement')
PROMPT_V1 = """You are a sonographer-radiologist comparing an AI-written ultrasound report (CANDIDATE) with a REFERENCE report.
Ignore wording, order and style when the meaning is unchanged. Units are equivalent (10 mm = 1 cm).

REFERENCE sentences:
{ref}

CANDIDATE sentences:
{hyp}

Reply with JSON only:
{{"candidate_supported": [true or false for each CANDIDATE sentence, in order: true only if everything it states is stated or implied by the REFERENCE],
 "reference_covered": [true or false for each REFERENCE sentence, in order: true only if the CANDIDATE states or implies it],
 "errors": [{{"field": "<what differs>", "severity": "critical|major|minor", "category": "false finding|missed finding|wrong location|wrong severity/category|wrong measurement"}}]}}
Use an empty errors list if the reports agree in meaning.
"""

PROMPT = """You are a sonographer-radiologist comparing an AI-written ultrasound report (CANDIDATE) with a REFERENCE report.
Compare ONLY what the two reports say. Do not judge whether a finding is medically plausible or complete.
Rules:
- A CANDIDATE sentence is supported (true) if it appears word for word in the REFERENCE, or says the same facts in other words.
- A REFERENCE sentence is covered (true) if it appears word for word in the CANDIDATE, or its facts are stated in other words.
- Ignore wording, order and style when the meaning is unchanged. Units are equivalent (10 mm = 1 cm).
- If the two reports are identical, every value is true and errors is empty.
- List an error only when a fact differs: something added, missing, or changed (a value, location, size or category).

REFERENCE sentences:
{ref}

CANDIDATE sentences:
{hyp}

Reply with JSON only:
{{"candidate_supported": [true or false for each CANDIDATE sentence, in order],
 "reference_covered": [true or false for each REFERENCE sentence, in order],
 "errors": [{{"field": "<what differs>", "severity": "critical|major|minor", "category": "false finding|missed finding|wrong location|wrong severity/category|wrong measurement"}}]}}
"""

def sentences(t): return [s.strip() for s in re.split(r'(?<=[.!?])\s+', t.strip()) if s.strip()]

def numbered(ss): return '\n'.join(f'{i + 1}. {s}' for i, s in enumerate(ss))

def parse(txt, nr, nh):
    m = re.search(r'\{.*\}', txt or '', re.S)
    try: js = json.loads(re.sub(r',\s*([}\]])', r'\1', m.group(0)))      # tolerate trailing commas
    except Exception: return None
    cs, rc, er = js.get('candidate_supported'), js.get('reference_covered'), js.get('errors')
    if not (isinstance(cs, list) and isinstance(rc, list) and isinstance(er, list)) or not cs or not rc: return None
    js['len_mismatch'] = (len(cs) != nh or len(rc) != nr)     # model returned a list of the wrong length: score the share of true values, flagged
    return js

def scores_from(js):
    cs, rc = [bool(x) for x in js['candidate_supported']], [bool(x) for x in js['reference_covered']]
    p, r = sum(cs) / len(cs), sum(rc) / len(rc); f1 = 2 * p * r / (p + r) if p + r else 0.0
    return dict(precision=p, recall=r, f1=f1, judge=graders.judge_to_score(dict(errors=[e for e in js['errors'] if isinstance(e, dict)])), cats=[e.get('category') for e in js['errors'] if isinstance(e, dict)], n_err=len(js['errors']), len_mismatch=js['len_mismatch'])

class SentenceCheck:
    def __init__(self, model='mlx-community/gemma-2-9b-it-4bit', cli=None):
        self.cli = cli or graders.LocalLLM(model, max_tokens=500); self.model = model; self.missing = 0
    def run(self, ref, hyp):
        R, H = sentences(ref), sentences(hyp)
        t = self.cli.ask(PROMPT.format(ref=numbered(R), hyp=numbered(H)), valid=lambda x: parse(x, len(R), len(H)) is not None)
        js = parse(t, len(R), len(H))
        if js is None: self.missing += 1; return None
        return scores_from(js)


# ---------------------------------------------------------------- sample + run (resumable: replies are cached on disk)
import os, random, sys, time, collections

def sample_rows(bench='bench_v2d.jsonl', per_dataset=20, seed=0, n_identical=3):
    """per case: 1 harmless_small, 1 matched, 1 harmless_large, 2 errors of different categories (+ identical for the first n_identical cases)"""
    rows = [json.loads(l) for l in open(bench)]; by = collections.defaultdict(lambda: collections.defaultdict(list)); rng = random.Random(seed)
    for r in rows: by[r['dataset']][r['case_id']].append(r)
    out = []
    for ds, cases in by.items():
        ids = sorted(cases); rng.shuffle(ids)
        for k, cid in enumerate(ids[:per_dataset]):
            rs = cases[cid]; pick = lambda t: [r for r in rs if r['kind'] == 'harmless' and r['harmless_type'] == t]
            for t in ('small', 'matched', 'large'):
                if pick(t): out.append(rng.choice(pick(t)))
            e = [r for r in rs if r['kind'] == 'error']; rng.shuffle(e); seen = set()
            for r in e:
                if r['category'] not in seen and len(seen) < 2: seen.add(r['category']); out.append(r)
            if k < n_identical: out += [r for r in rs if r['kind'] == 'identical']
    return out

if __name__ == '__main__':
    per = int(sys.argv[1]) if len(sys.argv) > 1 else 20; out = sys.argv[2] if len(sys.argv) > 2 else 'judge2_scores.jsonl'
    rows = sample_rows(per_dataset=per); open('bench_v2d_judge.jsonl', 'w').write(''.join(json.dumps(r) + '\n' for r in rows))
    done = {(json.loads(l)['reference'], json.loads(l)['candidate']) for l in open(out)} if os.path.exists(out) else set()
    sc = SentenceCheck(); todo = [(r['reference'], r['candidate']) for r in rows if (r['reference'], r['candidate']) not in done]
    todo = list(dict.fromkeys(todo)); print(len(rows), 'rows;', len(todo), 'pairs to judge', flush=True); t0 = time.time()
    for i, (ref, hyp) in enumerate(todo):
        s = sc.run(ref, hyp); open(out, 'a').write(json.dumps(dict(reference=ref, candidate=hyp, result=s)) + '\n')
        if i % 25 == 0: print(i, 'of', len(todo), round(time.time() - t0), 's', flush=True)
    print('done', round(time.time() - t0), 's; missing', sc.missing, flush=True)
