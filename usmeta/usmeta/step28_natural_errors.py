"""Step 28: natural-error validity test. Do the scorers track the REAL mistakes of a report writer (Qwen2.5-VL-3B, frozen writer prompt of Steps 11/14), or only surface similarity?
    python3 -m usmeta.step28_natural_errors select | write | extract | score | analyse | check
NEW file; generate.py (PROMPT, Writer), schema.py, graders.py, judge2*.py are imported unchanged. Test split only (usmeta.splits.load, logged); one image per patient/group.
Truth = the label facts of the reference (true_reports_v2d 'facts'). Factual accuracy = finding_f1-style fact F1 between the Qwen7B-extracted facts of the report and the label facts (Step 27 extractor, same prompt).
CAVEAT (stated in results.md): llm_finding_f1 shares the extractor with the accuracy measure, so its agreement with accuracy is partly built in; it is not an independent check."""
import os, sys, json, re, random, time, collections, argparse
import numpy as np
from scipy.stats import spearmanr, kendalltau
from . import splits, unified, partb, schema, graders, generate, judge2, judge2_test, qwen_real, step27_extractor as X
from .layer0 import auroc_case

ROOT = X.ROOT; OUT = os.path.join(ROOT, 'results', 'partA', 'step28_natural_errors'); N_PER_ORGAN = 60       # reduced from 100: the 3 h cap (writer ~30 s per image)
ORGAN_OF = {'BrEaST': 'breast', 'BUS-BRA': 'breast', 'BUSI': 'breast', 'UDIAT': 'breast', 'BUS-UCLM': 'breast', 'TN3K': 'thyroid', 'TN5000': 'thyroid', 'DDTI': 'thyroid', 'HC18': 'fetal', 'FetalHead': 'fetal'}
DS_OF = {'breast': ['BrEaST', 'BUS-BRA', 'BUSI', 'UDIAT', 'BUS-UCLM'], 'thyroid': ['TN3K', 'TN5000', 'DDTI'], 'fetal': ['HC18', 'FetalHead']}
LOADER = {'BUS-BRA': 'BUSBRA', 'BUS-UCLM': 'BUSUCLM'}
SCORERS = ['bleu', 'rougeL', 'chrf', 'bertscore[roberta-large]', 'ratescore', 'llm_finding_f1', 'judge_score', 'sentence_f1']
def P(f): return os.path.join(OUT, f)

def existing_reports():
    """reports of the same writer / prompt / greedy decoding already generated in Steps 11 (original images, not the flip test)"""
    out = {}
    for fn in ('reports_qwen.jsonl', 'reports_qwen_brest.jsonl'):
        for l in open(os.path.join(ROOT, fn)):
            r = json.loads(l)
            if not r.get('flipped'): out[qwen_real.uid(r['case_id'])] = r['report']
    return out

def select():
    os.makedirs(OUT, exist_ok=True); test = {r['case_id']: r for r in splits.load('test', script='usmeta.step28_natural_errors')}; ex = existing_reports(); rng = random.Random(0)
    tr = {}
    for l in open(os.path.join(ROOT, 'true_reports_v2d.jsonl')): r = json.loads(l); tr[r['case_id']] = r
    sel = []
    for organ, dss in DS_OF.items():
        quota = {d: N_PER_ORGAN // len(dss) for d in dss}
        for d in dss:
            pool = {}
            for rec in unified.load(LOADER.get(d, d)):
                if rec['case_id'] in test and rec['case_id'] in tr and os.path.exists(partb.img_path(rec)):
                    pool.setdefault(test[rec['case_id']]['group_id'], []).append(rec)     # one image per patient/group
            groups = sorted(pool); rng.shuffle(groups)
            reuse = [g for g in groups if any(r['case_id'] in ex for r in pool[g])]; fresh = [g for g in groups if g not in reuse]
            for g in (reuse + fresh)[:quota[d]]:
                recs = pool[g]; rec = next((r for r in recs if r['case_id'] in ex), recs[0])
                sel.append(dict(case_id=rec['case_id'], dataset=d, organ=organ, group_id=g, image=partb.img_path(rec), reused=rec['case_id'] in ex, reference=tr[rec['case_id']]['styles']['standard'], ref_facts=tr[rec['case_id']]['facts']))
    json.dump(sel, open(P('selected.json'), 'w'), indent=1); print(len(sel), 'images;', collections.Counter((s['organ'], s['reused']) for s in sel), collections.Counter(s['dataset'] for s in sel))

def write(a):
    import torch
    sel = json.load(open(P('selected.json'))); ex = existing_reports(); out = P('reports.jsonl'); done = {json.loads(l)['case_id'] for l in open(out)} if os.path.exists(out) else set(); w = None; t_start = time.time()
    for s in sel:
        if s['case_id'] in done: continue
        if s['reused']: open(out, 'a').write(json.dumps(dict(case_id=s['case_id'], source='reused (Steps 11/14 writer run)', report=ex[s['case_id']])) + '\n'); continue
        if time.time() - t_start > a.max_hours * 3600: print('time limit reached'); return
        if w is None: torch.manual_seed(0); w = generate.Writer('qwen')
        from PIL import Image
        t = time.time(); rep = w.report(Image.open(s['image']).convert('RGB'), s['organ'])
        open(out, 'a').write(json.dumps(dict(case_id=s['case_id'], source='new', seconds=round(time.time() - t, 1), report=rep)) + '\n'); print(s['case_id'], round(time.time() - t, 1), 's', flush=True)

def load_all():
    sel = json.load(open(P('selected.json'))); rep = {}
    for l in open(P('reports.jsonl')): r = json.loads(l); rep[r['case_id']] = r['report']
    for s in sel: s['report_raw'] = rep.get(s['case_id']); s['report'] = qwen_real.clean_md(s['report_raw']) if s['report_raw'] else None
    return [s for s in sel if s['report']]

def raw_json(organ, raw):
    m = re.search(r'\{.*\}', raw or '', re.S)
    try: return json.loads(m.group(0))
    except Exception: return {}

def label_flat(organ, facts):
    f = dict(facts)
    if f.get('count', 0) and f['count'] > 3: f['count'] = 3          # labels use 4 for 'three or more'; the extractor convention is 3
    if organ == 'thyroid' and f.get('lesion') == 'absent': f = {'lesion': 'absent'}
    return f

def extract(a):
    S = load_all(); ex = X.Extractor('main'); out = {}; t0 = time.time()
    for i, s in enumerate(S):
        if time.time() - t0 > a.max_hours * 3600: print('time limit'); break
        flat, ok = ex.facts(s['organ'], s['report']); js = raw_json(s['organ'], ex.raw(s['organ'], s['report'])); rf, rok = ex.facts(s['organ'], s['reference'])
        out[s['case_id']] = dict(flat=flat, ok=ok, raw=js, ref_extracted=rf, ref_ok=rok, regex=qwen_real.regex_reading(s['report']))
        if i % 20 == 0: print('extract', i, len(S), round(time.time() - t0), 's', flush=True)
    json.dump(out, open(P('extraction.json'), 'w')); print('parse failures', sum(not v['ok'] for v in out.values()))

# ---------------------------------------------------------------- truth comparison
def key_facts(s, E):
    """{key fact: (stated, correct)} for the key facts present in the labels. stated = the report gives a value for it AND it is checkable against the label"""
    o, T, js, fl = s['organ'], label_flat(s['organ'], s['ref_facts']), E['raw'], E['flat']; k = {}
    def nn(x): return x not in (None, '', 'null')
    # presence
    if o == 'breast': st = nn(js.get('lesion_present')); ev = fl.get('lesion') == 'present'
    elif o == 'thyroid': st = nn(js.get('count')) or any(nn(js.get(x)) for x in ('position', 'orientation', 'size', 'composition', 'echo', 'margin', 'foci')); ev = fl.get('lesion') == 'present'
    else: st = False; ev = None
    if o != 'fetal': k['presence'] = (st, st and ev == (T.get('lesion') == 'present'))
    if 'side' in T: k['side'] = (nn(js.get('side')), nn(js.get('side')) and fl.get('side') == T['side'])
    if o != 'fetal' and T.get('lesion') == 'present':
        for sk in ('size_mm', 'size_pct'):
            if sk in T:
                st = sk in fl; k['size'] = (st, st and schema.attr_credit(sk, T[sk], fl[sk]) >= 0.5)       # <= 25% relative error
    for ck in ('birads', 'tirads', 'path'):
        if ck in T: k[ck] = (ck in fl, ck in fl and str(fl[ck]) == str(T[ck]))
    if o == 'fetal':
        if 'hc_mm' in T: st = 'hc_mm' in fl; k['hc'] = (st, st and schema.attr_credit('hc_mm', T['hc_mm'], fl['hc_mm']) >= 0.5)
        if 'plane' in T: k['plane'] = ('plane' in fl, 'plane' in fl and fl['plane'] == T['plane'])
    return k

def fact_f1(s, E): return schema.finding_scores(schema.to_findings(label_flat(s['organ'], s['ref_facts']), s['organ']), schema.to_findings(E['flat'], s['organ']))[2]

def score(a):
    S = load_all(); E = json.load(open(P('extraction.json'))); refs = [s['reference'] for s in S]; hyps = [s['report'] for s in S]; res = {}
    sc = json.load(open(P('scores.json'))) if os.path.exists(P('scores.json')) else {}
    for spec in ('bleu', 'rougeL', 'chrf', 'bertscore:roberta-large', 'ratescore'):
        g = graders.make(spec)
        if g.name in sc: continue
        sc[g.name] = [float(x) for x in (g.batch(refs, hyps) if hasattr(g, 'batch') else [g.score(r, h) for r, h in zip(refs, hyps)])]; print('scored', g.name, flush=True)
    sc['llm_finding_f1'] = [X.llm_finding_f1(E[s['case_id']]['ref_extracted'], E[s['case_id']]['flat'], s['organ']) for s in S]
    json.dump(sc, open(P('scores.json'), 'w'))
    jf = P('judge_replies.jsonl'); done = {(json.loads(l)['reference'], json.loads(l)['candidate']): json.loads(l)['result'] for l in open(jf)} if os.path.exists(jf) else {}
    j = judge2_test.SC(judge2.PROMPT_V2); t0 = time.time()
    for i, s in enumerate(S):
        k = (s['reference'], s['report'])
        if k in done: continue
        if time.time() - t0 > a.max_hours * 3600: print('time limit'); return
        done[k] = j.run(*k); open(jf, 'a').write(json.dumps(dict(reference=k[0], candidate=k[1], result=done[k])) + '\n')
        if i % 10 == 0: print('judge', i, len(S), round(time.time() - t0), 's', flush=True)
    sc['judge_score'] = [done[(s['reference'], s['report'])]['judge'] if done[(s['reference'], s['report'])] else None for s in S]
    sc['sentence_f1'] = [done[(s['reference'], s['report'])]['f1'] if done[(s['reference'], s['report'])] else None for s in S]
    sc['case_ids'] = [s['case_id'] for s in S]; json.dump(sc, open(P('scores.json'), 'w')); print('scores saved')

def boot_stat(fn, x, y, n=1000, seed=0):
    """fn(x, y) over images; bootstrap over images (one image per group)"""
    x, y = np.asarray(x, float), np.asarray(y, float); v = fn(x, y); rng = np.random.default_rng(seed); m = []
    for _ in range(n):
        i = rng.integers(0, len(x), len(x)); xi, yi = x[i], y[i]
        if len(set(xi)) < 2 or len(set(yi)) < 2: continue
        m.append(fn(xi, yi))
    return (float(v), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))) if m and v == v else (float(v), None, None)

def auroc_two(score, wrong):
    sc, w = np.asarray(score, float), np.asarray(wrong, bool)
    if w.all() or (~w).all(): return float('nan')
    c, bad = sc[~w][:, None], sc[w][None, :]; return float(((c > bad) + 0.5 * (c == bad)).mean())

def analyse(a):
    S = load_all(); E = json.load(open(P('extraction.json'))); sc = json.load(open(P('scores.json'))); assert sc['case_ids'] == [s['case_id'] for s in S]
    rows = []
    for i, s in enumerate(S):
        e = E[s['case_id']]; kf = key_facts(s, e); st = {k: v for k, v in kf.items() if v[0]}; nw = sum(1 for v in st.values() if not v[1])
        rows.append(dict(i=i, case_id=s['case_id'], organ=s['organ'], dataset=s['dataset'], acc=fact_f1(s, e), n_key=len(kf), n_stated=len(st), n_wrong=nw, keyfacts={k: list(v) for k, v in kf.items()}, parse_ok=e['ok']))
    res = dict(n_images=len(S), per_organ_n=dict(collections.Counter(r['organ'] for r in rows)), by_organ={}); names = [n for n in sc if n != 'case_ids' and not all(v is None for v in sc[n])]
    for org in ('breast', 'thyroid', 'fetal', 'ALL'):
        R = [r for r in rows if org == 'ALL' or r['organ'] == org]; cell = dict(n_images=len(R), too_small=len(R) < 30, metrics={})
        cell['mean_fact_f1'] = float(np.mean([r['acc'] for r in R])); cell['share_with_a_wrong_key_fact'] = float(np.mean([r['n_wrong'] > 0 for r in R])); cell['share_stating_no_key_fact'] = float(np.mean([r['n_stated'] == 0 for r in R]))
        chk = [r for r in R if r['n_stated'] > 0]; cell['n_checkable'] = len(chk); cell['n_wrong_reports'] = sum(r['n_wrong'] > 0 for r in chk); cell['n_fully_correct'] = sum(r['n_wrong'] == 0 for r in chk)
        for n in names:
            x = [sc[n][r['i']] for r in R]; ok = [(v is not None) for v in x]; Rv = [r for r, o in zip(R, ok) if o]; xv = [v for v in x if v is not None]
            m = dict(n=len(Rv))
            if len(Rv) >= 5 and len(set(xv)) > 1 and len(set(r['acc'] for r in Rv)) > 1:
                m['spearman'] = boot_stat(lambda a_, b_: spearmanr(a_, b_)[0], xv, [r['acc'] for r in Rv]); m['kendall'] = boot_stat(lambda a_, b_: kendalltau(a_, b_)[0], xv, [r['acc'] for r in Rv])
            C = [(v, r['n_wrong'] > 0) for v, r in zip(xv, Rv) if r['n_stated'] > 0]
            if C and len({w for _, w in C}) == 2: m['auroc_wrong_vs_correct'] = boot_stat(lambda a_, b_: auroc_two(a_, b_), [v for v, _ in C], [w for _, w in C]); m['auroc_n'] = len(C)
            cell['metrics'][n] = m
        res['by_organ'][org] = cell
    # per-field correctness
    pf = collections.defaultdict(lambda: [0, 0, 0])
    for r in rows:
        for k, (st, ok) in r['keyfacts'].items(): d = pf[(r['organ'], k)]; d[0] += 1; d[1] += bool(st); d[2] += bool(ok)
    res['per_field'] = {f'{o}.{k}': dict(in_labels=a_, stated=b_, correct_of_stated=c_, accuracy_of_stated=(c_ / b_ if b_ else None)) for (o, k), (a_, b_, c_) in sorted(pf.items())}
    # regex vs LLM extractor agreement on the same reports (fields the regex reading covers)
    ag = collections.defaultdict(lambda: [0, 0, 0, 0])
    for s in S:
        e = E[s['case_id']]; rg, fl = e['regex'], e['flat']
        for k in ('side', 'birads', 'size_mm', 'lesion'):
            a_, b_ = rg.get(k), fl.get(k); d = ag[(s['organ'], k)]
            if a_ is not None and b_ is not None: d[0] += 1; d[1] += (abs(a_ - b_) <= 0.1 * max(a_, 1) if k == 'size_mm' else str(a_) == str(b_))
            else: d[2] += 1; d[3] += (a_ is None and b_ is None)
    res['regex_vs_llm'] = {f'{o}.{k}': dict(both_stated=a_, agree_when_both_stated=(b_ / a_ if a_ else None), one_or_none_missing=c_, both_missing=d_) for (o, k), (a_, b_, c_, d_) in sorted(ag.items())}
    res['parse_failures'] = sum(not r['parse_ok'] for r in rows); res['rows'] = rows
    json.dump(res, open(P('results.json'), 'w'), indent=1); print('saved results.json')

def check(a):
    import csv
    S = load_all(); E = json.load(open(P('extraction.json'))); rng = random.Random(0); pick = rng.sample(S, 30); os.makedirs(os.path.join(ROOT, 'docs'), exist_ok=True)
    with open(os.path.join(ROOT, 'docs', 'step28_check.csv'), 'w', newline='') as fh:
        w = csv.writer(fh); w.writerow(['id', 'organ', 'dataset', 'report_text', 'llm_extracted_facts', 'label_facts', 'extraction_right_or_wrong (fill: right / wrong)', 'note'])
        for k, s in enumerate(pick): w.writerow([f'C{k + 1:02d}', s['organ'], s['dataset'], s['report'], json.dumps(E[s['case_id']]['flat'], ensure_ascii=False), json.dumps(label_flat(s['organ'], s['ref_facts'])), '', ''])
    print('wrote docs/step28_check.csv')

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd'); ap.add_argument('--max-hours', type=float, default=3.0); a = ap.parse_args()
    {'select': lambda a: select(), 'write': write, 'extract': extract, 'score': score, 'analyse': analyse, 'check': check}[a.cmd](a)
