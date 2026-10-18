"""Inspect AI task: does an LLM judge separate planted clinical errors from harmless rewording?

    pip install inspect-ai
    inspect eval usmeta/inspect_task.py --model anthropic/<model-id> -T bench=bench.jsonl -T organ=breast --limit 300
    inspect eval usmeta/inspect_task.py --model openai/<model-id> ...        # same eval, another judge

Each sample is a (reference, candidate) pair. Gold label: 'error' for planted errors, 'harmless' for rewordings and
identical copies. The scorer reads the judge's JSON, calls it 'error' if it lists any discrepancy, and records the
severity-weighted score in metadata. Accuracy here is a quick view; use usmeta.meta for AUROC / severity analysis.
"""
import json, re, random
from inspect_ai import Task, task
from inspect_ai.dataset import Sample, MemoryDataset
from inspect_ai.solver import generate
from inspect_ai.scorer import scorer, accuracy, stderr, Score, CORRECT, INCORRECT
from usmeta.graders import JUDGE_PROMPT, judge_to_score

def _samples(bench, organ, per_kind, seed):
    items = [json.loads(l) for l in open(bench)]
    if organ: items = [i for i in items if i['organ'] == organ]
    rng = random.Random(seed); rng.shuffle(items); count = {}; out = []
    for i in items:
        gold = 'error' if i['kind'] == 'error' else 'harmless'
        if count.get(gold, 0) >= per_kind: continue
        count[gold] = count.get(gold, 0) + 1
        out.append(Sample(input=JUDGE_PROMPT.replace('{ref}', i['reference']).replace('{hyp}', i['candidate']),
                          target=gold, metadata=dict(organ=i['organ'], perturbation=i['perturbation'],
                                                     severity=i['severity'], case_id=i['case_id'])))
    return out

@scorer(metrics=[accuracy(), stderr()])
def judge_verdict():
    async def score(state, target):
        m = re.search(r'\{.*\}', state.output.completion, re.S)
        try: js = json.loads(m.group(0))
        except Exception: return Score(value=INCORRECT, explanation='unparseable judge output')
        pred = 'error' if js.get('errors') else 'harmless'
        return Score(value=CORRECT if pred == target.text else INCORRECT, answer=pred,
                     metadata=dict(judge_score=judge_to_score(js), n_errors=len(js.get('errors', []))))
    return score

@task
def usmeta_judge(bench='bench.jsonl', organ=None, per_kind=200, seed=0):
    return Task(dataset=MemoryDataset(_samples(bench, organ, int(per_kind), seed)), solver=generate(), scorer=judge_verdict())
