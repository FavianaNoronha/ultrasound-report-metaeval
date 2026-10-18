"""Grade VLM-written free-text reports against the reference reports.
    python -m usmeta.stage3 --reports reports_qwen.jsonl --extractor mlx-community/gemma-2-9b-it-4bit --out results_stage3_qwen
Extractor and judge are the SAME local model and must not be from the writer's family (recorded in the output)."""
import argparse, json, statistics as st
from . import graders, extract, freetext

THYROID_SKIP = {'path'}   # TN3K/TN5000 class 0/1 meaning unconfirmed -> not graded

def fact_score(o, ref_facts, cand_facts):
    w = dict(extract.WEIGHTS[o])
    if o == 'thyroid': w = {k: v for k, v in w.items() if k not in THYROID_SKIP}
    fs = graders._field_scores(o, ref_facts, cand_facts)
    return sum(w[k] * fs[k] for k in w) / sum(w.values()), sum(cand_facts.get(k) is not None for k in w) / len(w)

def load(reports, bench='bench_v1.jsonl'):
    ref = {}
    for l in open(bench):
        i = json.loads(l)
        if i['kind'] == 'identical': ref[i['case_id']] = i
    out = []
    for l in open(reports):
        r = json.loads(l); it = ref[r['case_id']]; out.append((r, it))
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--reports', required=True); ap.add_argument('--extractor', required=True)
    ap.add_argument('--out', required=True); ap.add_argument('--no-bertscore', action='store_true'); a = ap.parse_args()
    pairs = load(a.reports); llm = graders.LocalLLM(a.extractor); judge = graders.LocalJudge(a.extractor, cli=llm)
    refs = [it['reference'] for _, it in pairs]; hyps = [r['report'] for r, _ in pairs]; res = {}
    for n in ('bleu', 'rougeL', 'chrf'):
        g = graders.make(n); res[n] = [g.score(x, y) for x, y in zip(refs, hyps)]
    fs, cov, ext = [], [], []
    for (r, it) in pairs:
        o = it.get('ftype', it['organ']); f = freetext.extract_llm(llm, r['report'], o) or {k: None for k in freetext.FIELD_HELP[o]}
        s, c = fact_score(o, extract.EXTRACT[o](it['reference']), f); fs.append(s); cov.append(c); ext.append(f)
    res['fact_checker'] = fs; res['fact_coverage'] = cov
    res[judge.name] = [judge.score(x, y, it) for x, y, (_, it) in zip(refs, hyps, pairs)]
    if not a.no_bertscore:
        res['bertscore[roberta-large]'] = graders.make('bertscore:roberta-large').batch(refs, hyps)
    json.dump(dict(extractor_and_judge=a.extractor, writer=pairs[0][0]['model'], judge_missing=judge.missing,
                   rows=[dict(case_id=r['case_id'], dataset=r['dataset'], extracted=e, **{k: v[i] for k, v in res.items()})
                         for i, ((r, _), e) in enumerate(zip(pairs, ext))]), open(a.out + '.json', 'w'))
    lines = [f"Writer: {pairs[0][0]['model']} | extractor+judge: {a.extractor} | judge items missing: {judge.missing}", '']
    for ds in sorted({r['dataset'] for r, _ in pairs}):
        idx = [i for i, (r, _) in enumerate(pairs) if r['dataset'] == ds]
        lines += [f'### {ds} (n={len(idx)}; possibly seen in training)', '', '| scorer | mean |', '|---|---|']
        for k, v in res.items():
            xs = [v[i] for i in idx if v[i] == v[i]]; lines.append(f'| {k} | {st.mean(xs):.2f} |' if xs else f'| {k} | n/a |')
        lines.append('')
    open(a.out + '.md', 'w').write('\n'.join(lines)); print('\n'.join(lines))

if __name__ == '__main__': main()
