"""Pluggable graders. Every grader maps (reference, candidate, item) -> score where HIGHER = better report.

Built in (no downloads): bleu, rougeL, chrf, fact_checker, fact_f1, evidence_check, judge_mock
Optional (need extra packages / models, run on your own machine): bertscore:<model>, ratescore, green, llm_judge
"""
import re, json, os
from . import extract

# ---------------------------------------------------------------- word-overlap baselines
def _tok(t): return re.findall(r"[a-z0-9]+", t.lower())

def rouge_l(ref, hyp):
    a, b = _tok(ref), _tok(hyp)
    dp = [[0]*(len(b)+1) for _ in range(len(a)+1)]
    for i in range(len(a)):
        for j in range(len(b)):
            dp[i+1][j+1] = dp[i][j]+1 if a[i] == b[j] else max(dp[i][j+1], dp[i+1][j])
    l = dp[-1][-1]
    if not l: return 0.0
    p, r = l/len(b), l/len(a); return 2*p*r/(p+r)

class Bleu:
    name = 'bleu'
    def __init__(self):
        from sacrebleu.metrics import BLEU; self.m = BLEU(effective_order=True)
    def score(self, ref, hyp, item=None): return self.m.sentence_score(hyp, [ref]).score/100

class Chrf:
    name = 'chrf'
    def __init__(self):
        from sacrebleu.metrics import CHRF; self.m = CHRF()
    def score(self, ref, hyp, item=None): return self.m.sentence_score(hyp, [ref]).score/100

class RougeL:
    name = 'rougeL'
    def score(self, ref, hyp, item=None): return rouge_l(ref, hyp)

# ---------------------------------------------------------------- fact checkers (rule based, v0)
def _field_scores(organ, ref_facts, cand_facts):
    """per-field agreement in [0,1]; numeric fields graded by distance"""
    out = {}
    for k in extract.WEIGHTS[organ]:
        a, b = ref_facts.get(k), cand_facts.get(k)
        if k == 'hc':
            out[k] = 0.0 if (a is None or b is None) else max(0.0, 1 - abs(a-b)/extract.FETAL_TOL_MM)
        else:
            out[k] = 1.0 if (a == b and a is not None) else 0.0
    return out

class FactChecker:
    """Severity-weighted field agreement between candidate and REFERENCE text. Upper bound on templated reports."""
    name = 'fact_checker'
    def score(self, ref, hyp, item):
        o = item.get('ftype', item['organ']); fs = _field_scores(o, extract.EXTRACT[o](ref), extract.EXTRACT[o](hyp))
        w = extract.WEIGHTS[o]; return sum(w[k]*fs[k] for k in w)/sum(w.values())

class FactF1:
    """Unweighted share of agreeing fields (every field counts the same)."""
    name = 'fact_f1'
    def score(self, ref, hyp, item):
        o = item.get('ftype', item['organ']); fs = _field_scores(o, extract.EXTRACT[o](ref), extract.EXTRACT[o](hyp))
        return sum(fs.values())/len(fs)

class EvidenceCheck:
    """Checks the candidate's claims against dataset ANNOTATIONS (item['evidence']), not against the reference text.
    v0 uses ground-truth labels/masks as the evidence, so it is an ORACLE image check (upper bound).
    Real version: replace item['evidence'] with facts recovered from the image (segmentation model or VLM)."""
    name = 'evidence_check'
    def score(self, ref, hyp, item):
        o = item.get('ftype', item['organ']); ev = item['evidence']; cand = extract.EXTRACT[o](hyp)
        if o == 'thyroid': ev = dict(ev, count=_cnt_text(ev['count']))
        if o == 'breast': ev = dict(ev, calc='no' if ev['calc'] == 'no' else 'yes:' + ev['calc'])
        w = extract.WEIGHTS[o]; fs = _field_scores(o, ev, cand)
        return sum(w[k]*fs[k] for k in w)/sum(w.values())

def _cnt_text(n): return {1: 'a single nodule', 2: 'two nodules'}.get(n, 'three or more nodules')

# ---------------------------------------------------------------- LLM judge (pluggable backend)
JUDGE_PROMPT = """You are a sonographer-radiologist grading an AI-written ultrasound report against a reference report.
List every clinically meaningful discrepancy in the CANDIDATE compared with the REFERENCE. Ignore wording, order and
style when the meaning is unchanged. For each discrepancy give a severity: critical (changes diagnosis or management),
major (changes a clinically relevant finding), minor (small descriptive difference).
Reply with JSON only: {"errors":[{"field":"...","severity":"critical|major|minor"}]}

REFERENCE:
{ref}

CANDIDATE:
{hyp}
"""
PENALTY = dict(critical=0.6, major=0.3, minor=0.1)

def judge_to_score(js):
    errs = js.get('errors', [])
    return max(0.0, 1 - sum(PENALTY.get(e.get('severity', 'minor'), 0.1) for e in errs))

class JudgeMock:
    """Deterministic stand-in that mimics a judge using the rule-based extractor. For tests only; NOT a real judge."""
    name = 'judge_mock'
    def score(self, ref, hyp, item):
        o = item.get('ftype', item['organ']); a, b = extract.EXTRACT[o](ref), extract.EXTRACT[o](hyp)
        errs = []
        for k, w in extract.WEIGHTS[o].items():
            if a.get(k) != b.get(k): errs.append(dict(field=k, severity='critical' if w >= 3 else 'major' if w == 2 else 'minor'))
        return judge_to_score(dict(errors=errs))

class LLMJudge:
    """Real LLM judge. Set USMETA_JUDGE=anthropic|openai and the matching API key; USMETA_JUDGE_MODEL for the model id.
    UNTESTED against live APIs in this repo's CI (no keys there)."""
    def __init__(self, label=None):
        self.provider = os.environ.get('USMETA_JUDGE', 'anthropic'); self.model = os.environ.get('USMETA_JUDGE_MODEL')
        self.name = label or f'llm_judge[{self.provider}:{self.model}]'
        if not self.model: raise RuntimeError('Set USMETA_JUDGE_MODEL to a model id')
    def _call(self, prompt):
        if self.provider == 'anthropic':
            import anthropic; c = anthropic.Anthropic()
            r = c.messages.create(model=self.model, max_tokens=400, messages=[{'role': 'user', 'content': prompt}])
            return r.content[0].text
        if self.provider == 'openai':
            from openai import OpenAI; c = OpenAI()
            r = c.chat.completions.create(model=self.model, messages=[{'role': 'user', 'content': prompt}])
            return r.choices[0].message.content
        raise RuntimeError('unknown provider')
    def score(self, ref, hyp, item=None):
        txt = self._call(JUDGE_PROMPT.replace('{ref}', ref).replace('{hyp}', hyp))
        m = re.search(r'\{.*\}', txt, re.S)
        try: return judge_to_score(json.loads(m.group(0)))
        except Exception: return float('nan')

# ---------------------------------------------------------------- optional learned metrics (run locally)
class BertScore:
    def __init__(self, model='distilbert-base-uncased'):
        self.model = model; self.name = f'bertscore[{model}]'
    def batch(self, refs, hyps, items=None):
        from bert_score import score
        return score(hyps, refs, model_type=self.model, lang='en', batch_size=64, verbose=False)[2].tolist()
    def score(self, ref, hyp, item=None): return self.batch([ref], [hyp])[0]

class RaTEScore:
    """pip install RaTEScore  (radiology entity-aware metric; built for chest/CT/MRI text). API from its README; untested here."""
    name = 'ratescore'
    def __init__(self):
        from RaTEScore import RaTEScore as R; self.r = R()
    def batch(self, refs, hyps, items=None): return list(self.r.compute_score(hyps, refs))
    def score(self, ref, hyp, item=None): return self.batch([ref], [hyp])[0]

class Green:
    """pip install green-score  (LLM-based error counter, Stanford AIMI). API from its README; untested here; needs a GPU."""
    name = 'green'
    def __init__(self):
        from green_score import GREEN; self.g = GREEN('StanfordAIMI/GREEN-radllama2-7b', output_dir='.')
    def batch(self, refs, hyps, items=None):
        _, _, scores, _, _ = self.g(refs, hyps); return list(scores)
    def score(self, ref, hyp, item=None): return self.batch([ref], [hyp])[0]

REGISTRY = {'bleu': Bleu, 'rougeL': RougeL, 'chrf': Chrf, 'fact_checker': FactChecker, 'fact_f1': FactF1,
            'evidence_check': EvidenceCheck, 'judge_mock': JudgeMock, 'llm_judge': LLMJudge,
            'ratescore': RaTEScore, 'green': Green, 'bertscore': BertScore}

def make(spec):
    """'bertscore:roberta-large' -> BertScore('roberta-large'); 'llm_judge' -> LLMJudge()"""
    name, _, arg = spec.partition(':')
    cls = REGISTRY[name]
    return cls(arg) if arg else cls()

def grade(items, specs, progress=True):
    """returns dict[grader_name] -> list of scores aligned with items"""
    out = {}
    for spec in specs:
        g = make(spec)
        if hasattr(g, 'batch'):
            s = g.batch([i['reference'] for i in items], [i['candidate'] for i in items], items)
        else:
            s = [g.score(i['reference'], i['candidate'], i) for i in items]
        out[g.name] = s
        if progress: print('graded', g.name, len(s))
    return out
