"""Step 10d: run the frozen Gemma sentence_check judge on the TEST split bench with prompt_v2 (main) and prompt_v1 (subset). New file; judge2.py untouched.
    python3 -m usmeta.judge2_test v2 25 judge_test_v2.jsonl      python3 -m usmeta.judge2_test v1 12 judge_test_v1.jsonl"""
import sys, json, os, time
from . import judge2

class SC(judge2.SentenceCheck):
    def __init__(self, prompt, **kw): super().__init__(**kw); self.prompt = prompt
    def run(self, ref, hyp):
        R, H = judge2.sentences(ref), judge2.sentences(hyp)
        t = self.cli.ask(self.prompt.format(ref=judge2.numbered(R), hyp=judge2.numbered(H)), valid=lambda x: judge2.parse(x, len(R), len(H)) is not None)
        js = judge2.parse(t, len(R), len(H))
        if js is None: self.missing += 1; return None
        return judge2.scores_from(js)

if __name__ == '__main__':
    ver, per, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]; prompt = judge2.PROMPT_V2 if ver == 'v2' else judge2.PROMPT_V1
    full = judge2.sample_rows('bench_test_v2d.jsonl', per_dataset=25 if ver == 'v1' else per)       # v1 = the first `per` cases of the same 25-case sample
    if ver == 'v1':
        keep = {}; 
        for r in full: keep.setdefault(r['dataset'], [])
        order = {}
        for r in full:
            o = order.setdefault(r['dataset'], []); 
            if r['case_id'] not in o: o.append(r['case_id'])
        ok = {c for ds, o in order.items() for c in o[:per]}; full = [r for r in full if r['case_id'] in ok]
    open(out.replace('.jsonl', '_bench.jsonl'), 'w').write(''.join(json.dumps(r) + '\n' for r in full))
    done = {(json.loads(l)['reference'], json.loads(l)['candidate']) for l in open(out)} if os.path.exists(out) else set()
    sc = SC(prompt); todo = list(dict.fromkeys((r['reference'], r['candidate']) for r in full if (r['reference'], r['candidate']) not in done)); print(len(full), 'rows;', len(todo), 'pairs', flush=True); t0 = time.time()
    for i, (a, b) in enumerate(todo):
        s = sc.run(a, b); open(out, 'a').write(json.dumps(dict(reference=a, candidate=b, result=s)) + '\n')
        if i % 25 == 0: print(i, len(todo), round(time.time() - t0), 's', flush=True)
    print('done', round(time.time() - t0), 's missing', sc.missing, flush=True)
