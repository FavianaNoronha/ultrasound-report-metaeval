"""Step 32: stricter free-text extractor (extractor v3) and a re-run of the Step 28 metrics with it. NEW file; step27_extractor.py (model, few-shot examples, JSON-to-facts mapping, comparer), step27_run.py and step28_natural_errors.py are imported unchanged.
v3 changes ONLY the instruction text (prompt version 'v3', same model Qwen2.5-7B-Instruct 4-bit, greedy, same dev-only few-shot examples, same output schema): extract only facts explicitly stated, null otherwise, never infer pathology, halo, count or composition.
The v3 calls are cached separately in results/partA/step32_extractor_v3/cache.jsonl (key includes the variant name 'v3'), the Step 27 cache is not touched.
    python3 -m usmeta.step32_extractor_v3 validate | step28 | check | report"""
import os, sys, json, re, time, random, csv, collections, argparse
import numpy as np
from . import splits, schema, step27_extractor as X, step27_run as R27, step28_natural_errors as S28

ROOT = X.ROOT; OUT = os.path.join(ROOT, 'results', 'partA', 'step32_extractor_v3'); os.makedirs(OUT, exist_ok=True)
X.CACHE = os.path.join(OUT, 'cache.jsonl'); X.OUT = OUT; S28.OUT = OUT         # separate cache and output folder for this step (module-level paths of the imported code)
V3 = ("You extract facts from an ultrasound report into JSON. Reply with ONE line of JSON only, containing every key listed below, in this order.\n"
      "STRICT RULES:\n"
      "1. Fill a key ONLY with a fact that is explicitly written in the report. If the report does not state it, the value is null. Never infer, guess or complete.\n"
      "2. Never infer pathology. pathology is non-null only if the report itself states benign, malignant or normal as the pathology or diagnosis. Words such as suspicious, concerning, possible malignancy, biopsy recommended, a BI-RADS or TI-RADS category, or the impression are NOT a stated pathology: use null.\n"
      "3. Never infer halo, calcifications or posterior acoustic features: fill them only if the report mentions them (an echogenic halo, calcifications, posterior shadowing or enhancement). Not mentioned means null.\n"
      "4. count: only a number or number word that is written (a single / one, two, three). 'multiple', 'several' or a plural without a number is null.\n"
      "5. composition (thyroid): only if the report states solid, cystic, spongiform or similar as the composition. Echogenicity words (hypoechoic, hyperechoic, isoechoic, heterogeneous) belong to echo, never to composition.\n"
      "6. Presence: breast lesion_present is true only if a mass or lesion is described, false only if the report says there is none (or that the breast is normal), null if the report does not say. Thyroid: count is 0 only if the report says there is no nodule (normal thyroid without nodules); if a nodule or mass is described without a number, count is null and the other stated fields are still filled.\n"
      "7. Copy numbers and units exactly as written (do not convert).\n\nKEYS:\n{keys}")
X.INSTR['v3'] = V3

def extractor(shots=None): return X.Extractor('v3', shots=shots)

# ---------------------------------------------------------------- validate on dev + val templated sets
def sample(split, n=100, seed=0):
    ids = {r['case_id'] for r in splits.load(split)}; pool = collections.defaultdict(list)
    for l in open(os.path.join(ROOT, 'bench_v2d.jsonl')):
        r = json.loads(l)
        if r['case_id'] in ids and r['kind'] != 'identical': pool[(r['organ'], r['kind'])].append(r)
    refs = {}
    for l in open(os.path.join(ROOT, 'bench_v2d.jsonl')):
        r = json.loads(l)
        if r['case_id'] in ids and r['kind'] == 'identical': refs.setdefault(r['organ'], {})[r['case_id']] = r
    out = []; rng = random.Random(seed)
    for o in R27.ORGS:
        seen = set()
        for kind, k in (('reference', 25), ('error', 40), ('harmless', n - 65)):
            cand = list(refs[o].values()) if kind == 'reference' else pool[(o, kind)]; rng.shuffle(cand); got = 0
            for r in cand:
                t = r['reference'] if kind == 'reference' else r['candidate']
                if t in seen: continue
                seen.add(t); out.append(dict(organ=o, kind=kind, text=t, case_id=r['case_id'], dataset=r['dataset'])); got += 1
                if got == k: break
    return out

def agreement(items, flats):
    ag = collections.defaultdict(lambda: [0, 0]); allok = collections.defaultdict(list)
    for it, f in zip(items, flats):
        o = it['organ']; k = R27.known(o, it['text']); ok = True
        for fk in R27.FLAT_FIELDS[o]:
            m = R27.same(fk, f.get(fk), k.get(fk)); ag[o][0] += m; ag[o][1] += 1; ok &= m
        allok[o].append(ok)
    return {o: dict(field_agreement=a / b, fields=b, all_fields_correct=float(np.mean(allok[o])), reports=len(allok[o])) for o, (a, b) in ag.items()}, sum(a for a, _ in ag.values()) / sum(b for _, b in ag.values())

def run_validate(a):
    ex = extractor(); dl = time.time() + a.max_hours * 3600; res = {}
    for split in ('dev', 'val'):
        items = sample(split); flats, bad = R27.run_texts(ex, items, dl, f'v3-{split}')
        if flats is None: return
        per, pooled = agreement(items, flats); res[split] = dict(per_organ=per, pooled_field_agreement=pooled, parse_failures=bad, n=len(items))
        res[split]['wrong_examples'] = [dict(organ=it['organ'], text=it['text'][:200], diffs={fk: [R27.known(it['organ'], it['text']).get(fk), f.get(fk)] for fk in R27.FLAT_FIELDS[it['organ']] if not R27.same(fk, f.get(fk), R27.known(it['organ'], it['text']).get(fk))}) for it, f in zip(items, flats) if any(not R27.same(fk, f.get(fk), R27.known(it['organ'], it['text']).get(fk)) for fk in R27.FLAT_FIELDS[it['organ']])][:25]
    old = json.load(open(os.path.join(ROOT, 'results', 'partA', 'step27_llm_extractor', 'dev_validation.json')))
    res['v2_dev_for_reference'] = dict(all_fields_correct=old['all_fields_correct'], per_field_agreement_mean={o: float(np.mean([v['agreement'] for k, v in old['fields'].items() if k.startswith(o + '.')])) for o in R27.ORGS})
    res['criterion'] = dict(threshold=0.98, passed=all(res[s]['pooled_field_agreement'] >= 0.98 for s in ('dev', 'val')) and all(v['field_agreement'] >= 0.98 for s in ('dev', 'val') for v in res[s]['per_organ'].values()))
    json.dump(res, open(os.path.join(OUT, 'validation.json'), 'w'), indent=1); print(json.dumps({k: v for k, v in res.items() if k not in ('dev', 'val')}, indent=1)); print({s: (round(res[s]['pooled_field_agreement'], 4), {o: round(v['field_agreement'], 4) for o, v in res[s]['per_organ'].items()}) for s in ('dev', 'val')})

# ---------------------------------------------------------------- Step 28 re-run with v3
def prepare():
    for f in ('selected.json', 'reports.jsonl'):
        src = os.path.join(ROOT, 'results', 'partA', 'step28_natural_errors', f); dst = os.path.join(OUT, f)
        if not os.path.exists(dst): open(dst, 'w').write(open(src).read())

def run_step28(a):
    prepare(); S = S28.load_all(); ex = extractor(); out = {}; t0 = time.time()
    for i, s in enumerate(S):
        if time.time() - t0 > a.max_hours * 3600: print('time limit'); return
        flat, ok = ex.facts(s['organ'], s['report']); js = S28.raw_json(s['organ'], ex.raw(s['organ'], s['report'])); rf, rok = ex.facts(s['organ'], s['reference'])
        out[s['case_id']] = dict(flat=flat, ok=ok, raw=js, ref_extracted=rf, ref_ok=rok, regex=S28.qwen_real.regex_reading(s['report']))
        if i % 20 == 0: print('extract v3', i, len(S), round(time.time() - t0), 's', flush=True)
    json.dump(out, open(os.path.join(OUT, 'extraction.json'), 'w')); print('parse failures', sum(not v['ok'] for v in out.values()))
    sc = json.load(open(os.path.join(ROOT, 'results', 'partA', 'step28_natural_errors', 'scores.json')))          # word scorers, RaTEScore, judge: unchanged saved scores; only llm_finding_f1 depends on the extractor
    assert sc['case_ids'] == [s['case_id'] for s in S]
    sc['llm_finding_f1'] = [X.llm_finding_f1(out[s['case_id']]['ref_extracted'], out[s['case_id']]['flat'], s['organ']) for s in S]; json.dump(sc, open(os.path.join(OUT, 'scores.json'), 'w'))
    S28.analyse(a)

# ---------------------------------------------------------------- fresh hand-check sheet
def run_check(a):
    S = S28.load_all(); E = json.load(open(os.path.join(OUT, 'extraction.json'))); done = {r['id']: r for r in csv.DictReader(open(os.path.join(ROOT, 'docs', 'step28_check.csv'), encoding='utf-8'))}
    used = {r['report_text'] for r in done.values()}; rng = random.Random(1); pick = []
    for organ, n in (('breast', 12), ('thyroid', 12), ('fetal', 6)):
        pool = [s for s in S if s['organ'] == organ and s['report'] not in used]; rng.shuffle(pool); pick += pool[:n]
    rng.shuffle(pick)
    with open(os.path.join(ROOT, 'docs', 'step32_check.csv'), 'w', newline='') as fh:
        w = csv.writer(fh); w.writerow(['id', 'organ', 'dataset', 'report_text', 'llm_extracted_facts', 'label_facts', 'extraction_right_or_wrong (fill: right / wrong)', 'note'])
        for k, s in enumerate(pick): w.writerow([f'C{k + 1:02d}', s['organ'], s['dataset'], s['report'], json.dumps(E[s['case_id']]['flat'], ensure_ascii=False), json.dumps(S28.label_flat(s['organ'], s['ref_facts'])), '', ''])
    json.dump([dict(id=f'C{k + 1:02d}', case_id=s['case_id'], organ=s['organ']) for k, s in enumerate(pick)], open(os.path.join(OUT, 'check_sheet_key.json'), 'w'))
    print('wrote docs/step32_check.csv:', collections.Counter(s['organ'] for s in pick))

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd'); ap.add_argument('--max-hours', type=float, default=3.0); a = ap.parse_args()
    {'validate': run_validate, 'step28': run_step28, 'check': run_check}[a.cmd](a)
