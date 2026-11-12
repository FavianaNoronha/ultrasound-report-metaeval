"""Step 37 RadGraph-F1 worker. Runs in the separate venv ~/.venvs/radgraph (radgraph 0.1.18, RadGraph-XL model from StanfordAIMI/RRG_scorers, CPU) and needs nothing from the usmeta package.
    python step37_rg_worker.py PAIRS.json OUT.json
PAIRS.json = list of [reference, hypothesis]. Every unique text is annotated once (cached in local_data/step37/rg_annotations.jsonl, git-ignored: it may hold HiSBreast text);
the official radgraph reward functions give the three F1 levels per pair: simple (entity tokens), partial (entity tokens whose relations exist; used as RadGraph-F1 in Step 37), complete (entities and relations).
OUT.json = {"ref|||hyp": [simple, partial, complete]}. Resumable."""
import sys, os, json, time, hashlib
from radgraph import RadGraph
from radgraph.radgraph import compute_reward
HERE = os.path.dirname(os.path.abspath(__file__)); CACHE = os.path.join(HERE, '..', 'local_data', 'step37', 'rg_annotations.jsonl')
def key(t): return hashlib.sha256(t.encode()).hexdigest()
def main(pairs_file, out_file, batch=64, max_seconds=None):
    pairs = json.load(open(pairs_file)); texts = sorted({t for p in pairs for t in p}); ann = {}
    if os.path.exists(CACHE):
        for l in open(CACHE): d = json.loads(l); ann[d['k']] = d['a']
    todo = [t for t in texts if key(t) not in ann]; print(len(pairs), 'pairs;', len(texts), 'unique texts;', len(todo), 'to annotate', flush=True); t0 = time.time()
    if todo:
        rg = RadGraph(model_type='radgraph-xl', batch_size=16)
        for i in range(0, len(todo), batch):
            chunk = todo[i:i + batch]; out = rg(chunk)
            with open(CACHE, 'a') as fh:
                for j, t in enumerate(chunk): ann[key(t)] = out[str(j)]; fh.write(json.dumps(dict(k=key(t), a=out[str(j)])) + '\n')
            if (i // batch) % 20 == 0: print('annotated', i + len(chunk), len(todo), round(time.time() - t0), 's', flush=True)
            if max_seconds and time.time() - t0 > max_seconds: print('time limit'); break
    res = {}
    for r, h in pairs:
        if key(r) in ann and key(h) in ann: res[r + '|||' + h] = list(compute_reward(ann[key(h)], ann[key(r)], 'all'))
    json.dump(res, open(out_file, 'w')); print('scored', len(res), 'of', len(pairs), 'pairs', flush=True)
if __name__ == '__main__': main(sys.argv[1], sys.argv[2], max_seconds=float(sys.argv[3]) if len(sys.argv) > 3 else None)
