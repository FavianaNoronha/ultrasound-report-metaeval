"""Step 8b repeatability: run the frozen Gemma sentence_check (prompt_v2) 5 times, uncached, on 20 test-sample pairs per organ (same settings, greedy).
Reports verdict flips (the parsed result differs between runs) and mean Kendall tau of the scores between runs."""
import json, sys, random, tempfile, time, itertools
import numpy as np
from scipy.stats import kendalltau
from . import judge2, graders
from .judge2_test import SC

if __name__ == '__main__':
    rows = [json.loads(l) for l in open('judge_test_v2_bench.jsonl')]; rng = random.Random(0); sel = []
    for org in ('breast', 'thyroid', 'fetal'):
        c = [r for r in rows if r['organ'] == org]; rng.shuffle(c); sel += [(org, r['reference'], r['candidate']) for r in c[:20]]
    runs = []; t0 = time.time()
    for k in range(5):
        cli = graders.LocalLLM('mlx-community/gemma-2-9b-it-4bit', cache_dir=tempfile.mkdtemp(), max_tokens=500); sc = SC(judge2.PROMPT_V2, cli=cli)
        runs.append([sc.run(a, b) for _, a, b in sel]); print('run', k, round(time.time() - t0), 's', flush=True)
    out = {}
    for org in ('breast', 'thyroid', 'fetal'):
        ix = [i for i, s in enumerate(sel) if s[0] == org]; flips = 0; taus = []
        for i in ix:
            vs = [json.dumps(r[i], sort_keys=True) for r in runs]; flips += len(set(vs)) > 1
        for a, b in itertools.combinations(range(5), 2):
            x = [runs[a][i]['f1'] if runs[a][i] else np.nan for i in ix]; y = [runs[b][i]['f1'] if runs[b][i] else np.nan for i in ix]
            ok = [j for j in range(len(ix)) if x[j] == x[j] and y[j] == y[j]]
            t = kendalltau([x[j] for j in ok], [y[j] for j in ok])[0] if len(set(x)) > 1 and len(set(y)) > 1 else 1.0; taus.append(1.0 if t != t else float(t))
        out[org] = dict(pairs=len(ix), pairs_with_any_difference=int(flips), median_kendall_tau=float(np.median(taus)), seconds_per_pair=(time.time() - t0) / (5 * len(sel)))
    json.dump(out, open('results_repeatability.json', 'w'), indent=1); print(out)
