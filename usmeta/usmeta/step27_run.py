"""Step 27 driver. Subcommands (all write under results/partA/step27_llm_extractor/):
    dev        extractor validation on 100 DEV reports per organ (references, planted errors, template rewordings) with the main prompt; per-field accuracy vs the known facts
    stability  the same 100 dev reports per organ with prompt altA and altB; share of fields that change vs the main prompt
    human      the 29 scored human rewordings (Step 21d), reported separately, prompt NOT changed after this
    test       final run on the judged test subset (the 59 cases per dataset of the Gemma judge; --cap N keeps the first N cases per dataset)
Known facts: rule extractor (schema.extract_rule) on the templated text itself (the reports are generated from facts; Step 6 / 11b validate the rule extractor on them); for references it also equals the dataset facts.
Cache + resume: every model call is cached on disk. --max-hours stops a run cleanly (default 3)."""
import os, sys, json, time, random, collections, argparse
from . import schema, splits, step27_extractor as X

ROOT = X.ROOT; OUT = X.OUT
ORGS = ['breast', 'thyroid', 'fetal']
FLAT_FIELDS = {o: [fk for _, fk, _ in X.FIELDS[o]] for o in ORGS}
for o in ORGS:
    FLAT_FIELDS[o] = [('size_mm' if fk == 'size' else 'hc_mm' if fk == 'hc' else fk) for fk in FLAT_FIELDS[o]]
    if o in ('breast', 'thyroid'): FLAT_FIELDS[o].insert(FLAT_FIELDS[o].index('size_mm') + 1, 'size_pct')

def same(k, a, b):
    if a is None or b is None: return a is None and b is None
    if k == 'hc_mm': return abs(float(a) - float(b)) < 0.06
    return str(a).lower() == str(b).lower()

def dev_sample(n=100, seed=0):
    dev = {r['case_id'] for r in splits.load('dev')}; pool = collections.defaultdict(list)
    for l in open(os.path.join(ROOT, 'bench_v2d.jsonl')):
        r = json.loads(l)
        if r['case_id'] in dev and r['kind'] != 'identical': pool[(r['organ'], r['kind'])].append(r)
    refs = {}
    for l in open(os.path.join(ROOT, 'bench_v2d.jsonl')):
        r = json.loads(l)
        if r['case_id'] in dev and r['kind'] == 'identical': refs.setdefault(r['organ'], {})[r['case_id']] = r
    out = []; rng = random.Random(seed)
    for o in ORGS:
        want = [('reference', 25), ('error', 40), ('harmless', n - 65)]; seen = set()
        for kind, k in want:
            cand = list(refs[o].values()) if kind == 'reference' else pool[(o, kind)]; rng.shuffle(cand); got = 0
            for r in cand:
                t = r['reference'] if kind == 'reference' else r['candidate']
                if t in seen: continue
                seen.add(t); out.append(dict(organ=o, kind=kind, text=t, reference=r['reference'], case_id=r['case_id'], dataset=r['dataset'], group=r.get('group'), field=r.get('field'))); got += 1
                if got == k: break
    return out

def known(o, text): return schema.extract_rule(text, o)

def field_table(items, flats):
    """per field: n_known (known present), recall of those, n_absent, spurious rate where known absent, overall agreement"""
    T = {}
    for o in ORGS:
        for fk in FLAT_FIELDS[o]:
            kn = ok = ab = sp = agree = tot = 0
            for it, f in zip(items, flats):
                if it['organ'] != o: continue
                k = known(o, it['text']).get(fk); e = f.get(fk); tot += 1; agree += same(fk, e, k)
                if k is not None: kn += 1; ok += same(fk, e, k)
                else: ab += 1; sp += e is not None
            T[f'{o}.{fk}'] = dict(n_known=kn, correct=ok, acc_when_present=ok / kn if kn else None, n_absent=ab, spurious=sp, agreement=agree / tot if tot else None)
    return T

def run_texts(ex, items, deadline, tag):
    flats, bad = [], 0; t0 = time.time()
    for i, it in enumerate(items):
        if time.time() > deadline: print('time limit reached at', i, flush=True); return None, None
        f, ok = ex.facts(it['organ'], it['text']); flats.append(f); bad += (not ok)
        if i % 25 == 0: print(tag, i, len(items), round(time.time() - t0), 's', flush=True)
    return flats, bad

def cmd_dev(a):
    items = dev_sample(); ex = X.Extractor('main'); dl = time.time() + a.max_hours * 3600
    flats, bad = run_texts(ex, items, dl, 'dev')
    if flats is None: return
    T = field_table(items, flats); agg = collections.defaultdict(lambda: [0, 0, 0, 0])
    exact = collections.defaultdict(list)
    for it, f in zip(items, flats):
        o = it['organ']; k = known(o, it['text']); exact[o].append(all(same(fk, f.get(fk), k.get(fk)) for fk in FLAT_FIELDS[o]))
    res = dict(n=len(items), parse_failures=bad, fields=T, all_fields_correct={o: sum(v) / len(v) for o, v in exact.items()}, calls=ex.calls, model_seconds=ex.secs,
               kinds={f'{o}.{k}': n for (o, k), n in collections.Counter((i['organ'], i['kind']) for i in items).items()})
    json.dump(res, open(os.path.join(OUT, 'dev_validation.json'), 'w'), indent=1)
    json.dump([dict(it, extracted=f, known=known(it['organ'], it['text'])) for it, f in zip(items, flats)], open(os.path.join(OUT, 'dev_validation_items.json'), 'w'))
    print('parse failures', bad, 'calls', ex.calls, 'secs', round(ex.secs)); print({o: round(v, 3) for o, v in res['all_fields_correct'].items()})
    for k, v in T.items():
        if v['n_known'] or v['spurious']: print(k, v)

def cmd_stability(a):
    import numpy as np
    items = dev_sample(); main = X.Extractor('main'); dl = time.time() + a.max_hours * 3600; base, _ = run_texts(main, items, dl, 'main')
    res = {}
    for var in ('altA', 'altB'):
        ex = X.Extractor(var, shots=main.shots); flats, bad = run_texts(ex, items, dl, var)
        if flats is None: return
        ch = collections.Counter(); tot = collections.Counter(); chtext = collections.Counter(); ntext = collections.Counter()
        for it, f0, f1 in zip(items, base, flats):
            o = it['organ']; diff = False
            for fk in FLAT_FIELDS[o]:
                tot[o] += 1; d = not same(fk, f0.get(fk), f1.get(fk)); ch[o] += d; diff |= d
            ntext[o] += 1; chtext[o] += diff
        # pair-level: llm_finding_f1(reference, candidate) under the main prompt vs this prompt (same measure as the judge's Step 21c flips: change > 0.1, change at all)
        pr = [it for it in items if it['kind'] != 'reference']; d_ = []
        for it in pr:
            o = it['organ']; a0 = X.llm_finding_f1(main.facts(o, it['reference'])[0], main.facts(o, it['text'])[0], o)
            a1 = X.llm_finding_f1(ex.facts(o, it['reference'])[0], ex.facts(o, it['text'])[0], o); d_.append(abs(a1 - a0))
        pairs = dict(n_pairs=len(pr), changed_gt_0_1=float(np.mean([x > 0.1 for x in d_])), changed_at_all=float(np.mean([x > 1e-9 for x in d_])),
                     by_organ={o: dict(n=sum(i['organ'] == o for i in pr), changed_gt_0_1=float(np.mean([x > 0.1 for x, i in zip(d_, pr) if i['organ'] == o]))) for o in ORGS})
        res[var] = dict(pairs=pairs, parse_failures=bad, field_change_share={o: ch[o] / tot[o] for o in ORGS}, fields_compared={o: tot[o] for o in ORGS},
                        reports_with_any_change={o: chtext[o] / ntext[o] for o in ORGS}, pooled_field_change=sum(ch.values()) / sum(tot.values()))
        # also against the known facts, to tell stable-and-right from stable-and-wrong
        res[var]['all_fields_correct'] = {o: float(sum(all(same(fk, f1.get(fk), known(o, it['text']).get(fk)) for fk in FLAT_FIELDS[o]) for it, f1 in zip(items, flats) if it['organ'] == o) / ntext[o]) for o in ORGS}
    json.dump(res, open(os.path.join(OUT, 'stability.json'), 'w'), indent=1); print(json.dumps(res, indent=1))


# ---------------------------------------------------------------- analysis helpers (group bootstrap 1,000 / seed 0, < 30 groups = too small to compare)
import numpy as np
from .step10d_analysis import gboot
from . import step19_pairs as P
HT = ('small', 'matched', 'large'); MIN_G = 30
ORG_NAME = {'breast': 'breast', 'thyroid': 'thyroid', 'fetal': 'fetal head'}

def pair_scores(ex, rows, deadline, tag):
    """llm_finding_f1 for every (reference, candidate) in rows; None if the time limit is hit"""
    texts = list(dict.fromkeys([(r['organ'], r['reference']) for r in rows] + [(r['organ'], r['candidate']) for r in rows])); flat = {}; bad = 0; t0 = time.time()
    for i, (o, t) in enumerate(texts):
        if time.time() > deadline: print('time limit reached at', i, 'of', len(texts), flush=True); return None, None, None
        f, ok = ex.facts(o, t); flat[(o, t)] = f; bad += (not ok)
        if i % 50 == 0: print(tag, i, len(texts), round(time.time() - t0), 's', flush=True)
    sc = {(r['reference'], r['candidate']): X.llm_finding_f1(flat[(r['organ'], r['reference'])], flat[(r['organ'], r['candidate'])], r['organ']) for r in rows}
    return sc, flat, bad

def pref_by(C, sc, htype, organ_of):
    """per case: strict, tie, half over error x harmless(htype) pairs; grouped by group id. C from step19_pairs.cases_of"""
    out = collections.defaultdict(lambda: [[], [], [], []])
    for cid, c in C.items():
        e = [sc.get((r['reference'], r['candidate'])) for r in c['E']]; h = [sc.get((r['reference'], r['candidate'])) for r in c['H'] if htype is None or r['harmless_type'] == htype]
        e = [x for x in e if x is not None]; h = [x for x in h if x is not None]
        if not e or not h: continue
        E, H = np.array(e)[:, None], np.array(h)[None, :]; lt, eq = float((E < H).mean()), float((E == H).mean())
        for key in (organ_of[c['ds']], 'ALL'): o = out[key]; o[0].append(lt); o[1].append(eq); o[2].append(lt + 0.5 * eq); o[3].append(c['group'])
    return out

def cell(v):
    if not v or not v[3]: return None
    s, t, h, g = v; ng = len(set(g)); return dict(cases=len(s), groups=ng, strict=gboot(s, g), tie=gboot(t, g), auroc=gboot(h, g), too_small=ng < MIN_G)

def load_judged(cap):
    """the 59-case-per-dataset judged test subset (Steps 10d + 12); every access to the test split goes through splits.load (logged)"""
    ids = {r['case_id'] for r in splits.load('test', script='usmeta.step27_run')}
    rows = []
    for f in ('results/partA/step10d_test_results/judge_test_v2_bench.jsonl', 'judge_big_v2_bench.jsonl'): rows += [json.loads(l) for l in open(os.path.join(ROOT, f))]
    assert all(r['case_id'] in ids for r in rows)
    order = collections.defaultdict(list)
    for r in rows:
        if r['case_id'] not in order[r['dataset']]: order[r['dataset']].append(r['case_id'])
    keep = {c for ds, o in order.items() for c in (o[:cap] if cap else o)}; seen = set(); out = []
    for r in rows:
        k = (r['case_id'], r['candidate'])
        if r['case_id'] in keep and k not in seen: seen.add(k); out.append(r)
    return out

def cmd_test(a):
    rows = load_judged(a.cap); ex = X.Extractor('main'); dl = time.time() + a.max_hours * 3600; sc, flat, bad = pair_scores(ex, rows, dl, 'test')
    if sc is None: return
    jl = P.judge_lookup([os.path.join(ROOT, 'results/partA/step10d_test_results/judge_test_v2.jsonl'), os.path.join(ROOT, 'judge_big_v2.jsonl')])
    S = {**P.scores_of(os.path.join(ROOT, 'scores_test_layer0.json')), 'finding_f1': P.scores_of(os.path.join(ROOT, 'scores_test_layer1.json'))['finding_f1'], **jl, 'llm_finding_f1': sc}
    jset = {(r['reference'], r['candidate']) for r in rows}; C = P.cases_of(rows, jset); res = {}
    for name in ('llm_finding_f1', 'finding_f1', 'judge_score', 'sentence_f1', 'ratescore'):
        for ht in HT + (None,):
            for key, v in pref_by(C, S[name], ht, P.ORGAN).items(): res[f'{name}|{ht or "all"}|{key}'] = cell(v)
    ident = collections.defaultdict(list)
    for r in rows:
        if r['kind'] == 'identical': ident[r['organ']].append(sc[(r['reference'], r['candidate'])])
    # accuracy of the extractor against the rule-extractor facts on the test candidates (reference + candidates, templated text)
    fa = collections.defaultdict(lambda: [0, 0])
    for (o, t), f in flat.items():
        kf = known(o, t)
        for fk in FLAT_FIELDS[o]: fa[o][1] += 1; fa[o][0] += same(fk, f.get(fk), kf.get(fk))
    out = dict(n_rows=len(rows), n_cases=len(C), cap=a.cap, parse_failures=bad, identical_mean={o: float(np.mean(v)) for o, v in ident.items()}, identical_n={o: len(v) for o, v in ident.items()},
               field_agreement_vs_rule={o: x[0] / x[1] for o, x in fa.items()}, unique_texts=len(flat), calls_this_run=ex.calls, model_seconds=ex.secs, cells=res,
               cases_per_dataset=dict(collections.Counter(v['ds'] for v in C.values())))
    json.dump(out, open(os.path.join(OUT, 'test_results.json'), 'w'), indent=1)
    json.dump([dict(reference=k[0], candidate=k[1], llm_finding_f1=v) for k, v in sc.items()], open(os.path.join(OUT, 'test_pair_scores.json'), 'w'))
    for k in ('identical_mean', 'field_agreement_vs_rule', 'cases_per_dataset', 'parse_failures'): print(k, out[k])

def cmd_human(a):
    D = os.path.join(ROOT, 'results', 'partA', 'step21d_human_sheet'); B = [json.loads(l) for l in open(os.path.join(D, 'human_bench.jsonl'))]
    rows = [dict(r, organ=ORG_H[r['organ']]) for r in B]; ex = X.Extractor('main'); dl = time.time() + a.max_hours * 3600; sc, flat, bad = pair_scores(ex, rows, dl, 'human')
    if sc is None: return
    by = collections.defaultdict(list)
    for r in rows: by[r['item']].append(r)
    res = {}; HK = {'human': 'human', 'small': 'template_small', 'matched': 'template_matched', 'large': 'template_large'}
    for kind, kk in HK.items():
        for org in ('breast', 'thyroid', 'fetal head', 'ALL'):
            v, g = [], []
            for it, bs in by.items():
                if org != 'ALL' and ORG_NAME[bs[0]['organ']] != org: continue
                e = [sc[(b['reference'], b['candidate'])] for b in bs if b['kind'] == 'error']; h = [sc[(b['reference'], b['candidate'])] for b in bs if b['kind'] == kk]
                if e and h: v.append(np.mean([(x < y) + 0.5 * (x == y) for x in e for y in h])); g.append(it)
            res[f'{kind}|{org}'] = dict(n_items=len(v), auroc=gboot(v, g) if v else None, too_small=len(v) < MIN_G)
    hu = [r for r in rows if r['kind'] == 'human']; same_all = []
    for r in hu:
        fr, fh = flat[(r['organ'], r['reference'])], flat[(r['organ'], r['candidate'])]; same_all.append(all(same(fk, fh.get(fk), fr.get(fk)) for fk in FLAT_FIELDS[r['organ']]))
    out = dict(n_items=len(by), parse_failures=bad, human_vs_reference_llm_f1_mean=float(np.mean([sc[(r['reference'], r['candidate'])] for r in hu])),
               human_all_fields_equal_to_reference_extraction=float(np.mean(same_all)), human_identical_gate=float(np.mean([sc[(r['reference'], r['candidate'])] for r in rows if r['kind'] == 'identical'])), cells=res,
               human_pairs=[dict(item=r['item'], organ=r['organ'], llm_finding_f1=sc[(r['reference'], r['candidate'])], extracted_human=flat[(r['organ'], r['candidate'])], extracted_reference=flat[(r['organ'], r['reference'])]) for r in hu])
    json.dump(out, open(os.path.join(OUT, 'human_results.json'), 'w'), indent=1); print({k: v for k, v in out.items() if k not in ('cells', 'human_pairs')})
    for k, v in res.items(): print(k, v)
ORG_H = {'breast': 'breast', 'thyroid': 'thyroid', 'fetal head': 'fetal'}

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd'); ap.add_argument('--max-hours', type=float, default=3.0); ap.add_argument('--cap', type=int, default=0); a = ap.parse_args()
    {'dev': cmd_dev, 'stability': cmd_stability, 'human': cmd_human, 'test': cmd_test}[a.cmd](a)
