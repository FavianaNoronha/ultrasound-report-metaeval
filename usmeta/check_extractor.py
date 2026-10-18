import json, random, sys
sys.path.insert(0, '.')
from usmeta import graders, freetext
items = [json.loads(l) for l in open('bench_small.jsonl')]
random.seed(int(sys.argv[1]) if len(sys.argv)>1 else 1); by = {}
for i in items: by.setdefault(i.get('ftype', i['organ']), []).append(i)
sel = [x for o, v in by.items() for x in random.sample(v, 5)]
cli = graders.LocalLLM('mlx-community/gemma-2-9b-it-4bit')
print(len(sel), 'reports; types', list(by)); print('agreement', round(freetext.agreement(cli, sel), 3))
