#!/usr/bin/env bash
# Stage 2: the learned scorers, run on your own laptop (needs internet for model downloads).
# Usage: bash run_stage2.sh            -> BERTScore + RaTEScore + GREEN on a 100-cases-per-dataset sample
#        USMETA_JUDGE=anthropic USMETA_JUDGE_MODEL=<model-id> ANTHROPIC_API_KEY=... bash run_stage2.sh judge   -> LLM judge too
set -e
pip install -q -r requirements.txt bert-score
python3 - <<'P'
import json, random, collections
random.seed(0); items=[json.loads(l) for l in open('bench_v1.jsonl')]
cases=collections.defaultdict(set)
for i in items: cases[i['dataset']].add(i['case_id'])
keep={c for s in cases.values() for c in random.sample(sorted(s), min(100,len(s)))}
out=[i for i in items if i['case_id'] in keep]
open('bench_small.jsonl','w').write(''.join(json.dumps(i)+'\n' for i in out)); print(len(out),'items in bench_small.jsonl')
P
G=bleu,rougeL,chrf,fact_checker,evidence_check,bertscore:roberta-large,ratescore
if [ "$1" = judge ]; then G=$G,llm_judge; fi
python3 -m usmeta.run grade --bench bench_small.jsonl --graders $G --out scores_stage2.json
python3 -m usmeta.run report --bench bench_small.jsonl --scores scores_stage2.json --out results_stage2
