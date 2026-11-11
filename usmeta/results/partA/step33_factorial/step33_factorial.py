"""Step 33 (factorial): 2x2 fact x wording. NEW file; the frozen builders (bench_v2.errors, templates_v2.render / load / facts), the Step 5-10d saved test scores and the scorer classes are imported unchanged.
Pre-registration: results/partA/step33_factorial/PREREG.md (committed before any cell (d) score or test number).
    python3 -m usmeta.step33_factorial check_dev     builder check on DEV + VAL references only (no scoring)
    python3 -m usmeta.step33_factorial build_test    builds the test blocks (one logged test read) and saves them
    python3 -m usmeta.step33_factorial score         scores cell (d): BLEU, ROUGE-L, chrF, BERTScore, RaTEScore, finding_f1 (all) and the judge (capped)
    python3 -m usmeta.step33_factorial analyse       decomposition, AUROC at matched wording, reversal rates"""
import os, sys, json, random, collections, time, argparse
import numpy as np
from . import splits, schema, graders, judge2, judge2_test, templates_v2 as T, bench_v2 as B, step19_pairs as P
from .layer0 import auroc_case
from .step10d_analysis import gboot

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'); OUT = os.path.join(ROOT, 'results', 'partA', 'step33_factorial'); STYLES = ('terse', 'long'); STYLE_GROUP = {'terse': 'style_terse', 'long': 'style_long'}
TN = {'BUS-BRA': 'BUSBRA', 'BUS-UCLM': 'BUSUCLM'}; ORGAN = {'BrEaST': 'breast', 'BUS-BRA': 'breast', 'BUSI': 'breast', 'UDIAT': 'breast', 'BUS-UCLM': 'breast', 'TN3K': 'thyroid', 'TN5000': 'thyroid', 'DDTI': 'thyroid'}
SCORERS = [('bleu', 'BLEU'), ('rougeL', 'ROUGE-L'), ('chrf', 'chrF'), ('bertscore[roberta-large]', 'BERTScore'), ('ratescore', 'RaTEScore'), ('finding_f1', 'finding_f1 (upper bound)'), ('judge_score', 'judge_score'), ('sentence_f1', 'judge sentence_f1')]
JUDGE_CASES_PER_DS = 12; JUDGE_ERRORS_PER_CASE = 3

def same_value(field, ext, new):
    if ext is None: return False
    try: return abs(float(ext) - float(new)) <= (1.0 if field in ('size_mm', 'size_pct') else 0.0)
    except Exception: return str(ext).strip().lower() == str(new).strip().lower()

def build(rows, tag):
    """rows: bench rows of one split. Returns blocks + drop statistics. Block = dict(case, group, organ, dataset, field, category, severity, style, ref, a_texts, b_text, c_text, d_text)"""
    by = collections.defaultdict(list)
    for r in rows:
        if r['dataset'] in ORGAN: by[r['dataset']].append(r)
    blocks = []; stats = collections.Counter(); reasons = collections.Counter()
    for ds, rs in by.items():
        recs = {c['case_id']: c for c in T.load(TN.get(ds, ds))}; tr = {c['case_id']: c for c in T.build([TN.get(ds, ds)])}; cases = collections.defaultdict(list)
        for r in rs: cases[r['case_id']].append(r)
        for cid, rr in cases.items():
            rec = recs[cid]; f = T.facts(rec); ref = tr[cid]['styles']['standard']; organ = ORGAN[ds]; gid = f"{ds}:{rr[0]['group_id']}"
            a = [r['candidate'] for r in rr if r['kind'] == 'harmless' and r['harmless_type'] in ('small', 'matched')]; blarge = {s: next((r['candidate'] for r in rr if r['kind'] == 'harmless' and r['group'] == STYLE_GROUP[s]), None) for s in STYLES}
            gen = {T.render(g, organ, 'standard'): (cat, field, old, new, mag, sev, g) for cat, field, old, new, mag, sev, g in B.errors(rec, f)}
            for er in [r for r in rr if r['kind'] == 'error']:
                g = gen.get(er['candidate'])
                if g is None: stats['error rows not regenerated (skipped)'] += 1; continue
                cat, field, old, new, mag, sev, gf = g
                for s in STYLES:
                    stats['candidates (d) attempted'] += 1
                    if not a or blarge[s] is None: stats['dropped'] += 1; reasons['no (a) or no large rewording for the reference'] += 1; continue
                    d = T.render(gf, organ, s); ext = schema.extract_rule(d, organ); ref_ext = schema.extract_rule(blarge[s], organ)
                    if d == blarge[s]: stats['dropped'] += 1; reasons['(d) identical to (b)'] += 1; continue
                    if not same_value(field, ext.get(field), new) or (field not in ('lesion',) and same_value(field, ext.get(field), old)): stats['dropped'] += 1; reasons[f'error not shown by the regex extractor ({field})'] += 1; continue
                    if same_value(field, ref_ext.get(field), new): stats['dropped'] += 1; reasons['large harmless text already shows the error value'] += 1; continue
                    stats['kept'] += 1; blocks.append(dict(case=cid, group=gid, organ=organ, dataset=ds, field=field, category=cat, severity=sev, style=s, ref=ref, a_texts=a, b_text=blarge[s], c_text=er['candidate'], d_text=d))
    return blocks, dict(stats), dict(reasons)

def load_rows(split):
    if split == 'test':
        rows = [json.loads(l) for l in open(os.path.join(ROOT, 'bench_test_v2d.jsonl'))]; ids = {r['case_id'] for r in splits.load('test', script='usmeta.step33_factorial')}; assert all(r['case_id'] in ids for r in rows); return rows
    ids = {r['case_id'] for r in splits.load(split)}; return [r for r in (json.loads(l) for l in open(os.path.join(ROOT, 'bench_v2d.jsonl'))) if r['case_id'] in ids]

def cmd_check_dev(a):
    os.makedirs(OUT, exist_ok=True); res = {}
    for split in ('dev', 'val'):
        rows = load_rows(split); blocks, st, rs = build(rows, split); res[split] = dict(stats=st, reasons=rs, kept_by_organ=dict(collections.Counter(b['organ'] for b in blocks)), kept_by_field=dict(collections.Counter(b['field'] for b in blocks)))
        for o in ('breast', 'thyroid'):
            att = sum(1 for _ in blocks if False)
    json.dump(res, open(os.path.join(OUT, 'builder_check_devval.json'), 'w'), indent=1); print(json.dumps(res, indent=1)[:2500])

def cmd_build_test(a):
    rows = load_rows('test'); blocks, st, rs = build(rows, 'test'); json.dump(dict(blocks=blocks, stats=st, reasons=rs), open(os.path.join(OUT, 'test_blocks.json'), 'w')); print(st, rs, collections.Counter(b['organ'] for b in blocks))

def cmd_score(a):
    D = json.load(open(os.path.join(OUT, 'test_blocks.json'))); blocks = D['blocks']; pairs = sorted({(b['ref'], b['d_text']) for b in blocks}); S = json.load(open(os.path.join(OUT, 'd_scores.json'))) if os.path.exists(os.path.join(OUT, 'd_scores.json')) else {}
    refs, hyps = [p[0] for p in pairs], [p[1] for p in pairs]; S['pairs'] = [list(p) for p in pairs]; S.setdefault('scores', {})
    for spec in ('bleu', 'rougeL', 'chrf', 'bertscore:roberta-large', 'ratescore'):
        g = graders.make(spec)
        if g.name in S['scores']: continue
        t = time.time(); s = g.batch(refs, hyps) if hasattr(g, 'batch') else [g.score(r, h) for r, h in zip(refs, hyps)]; S['scores'][g.name] = [float(x) for x in s]; json.dump(S, open(os.path.join(OUT, 'd_scores.json'), 'w')); print('scored', g.name, round(time.time() - t), 's', flush=True)
    if 'finding_f1' not in S['scores']:
        S['scores']['finding_f1'] = [schema.finding_scores(schema.to_findings(schema.extract_rule(r, [b for b in blocks if b['ref'] == r][0]['organ']), [b for b in blocks if b['ref'] == r][0]['organ']), schema.to_findings(schema.extract_rule(h, [b for b in blocks if b['ref'] == r][0]['organ']), [b for b in blocks if b['ref'] == r][0]['organ']))[2] for r, h in pairs] if False else None
    # finding_f1 (regex extractor + the frozen comparer) computed per pair with the block's organ
    org = {}
    for b in blocks: org[b['ref']] = b['organ']
    S['scores']['finding_f1'] = [schema.finding_scores(schema.to_findings(schema.extract_rule(r, org[r]), org[r]), schema.to_findings(schema.extract_rule(h, org[r]), org[r]))[2] for r, h in pairs]; json.dump(S, open(os.path.join(OUT, 'd_scores.json'), 'w'))
    # judge: capped subset
    saved = P.judge_lookup([os.path.join(ROOT, 'results/partA/step10d_test_results/judge_test_v2.jsonl'), os.path.join(ROOT, 'judge_big_v2.jsonl')]); rng = random.Random(0); sel = {}
    for ds in ORGAN:
        cs = collections.defaultdict(list)
        for b in blocks:
            if b['dataset'] == ds: cs[b['case']].append(b)
        ok = []
        for cid, bl in cs.items():
            if all((b['ref'], b['b_text']) in saved['judge_score'] and (b['ref'], b['c_text']) in saved['judge_score'] for b in bl[:1]) and any((b['ref'], t) in saved['judge_score'] for b in bl[:1] for t in b['a_texts']): ok.append(cid)
        rng.shuffle(ok); sel[ds] = sorted(ok)[:0] or ok[:JUDGE_CASES_PER_DS]
    chosen = []
    for ds, cids in sel.items():
        for cid in cids:
            bl = [b for b in blocks if b['case'] == cid and (b['ref'], b['c_text']) in saved['judge_score'] and (b['ref'], b['b_text']) in saved['judge_score']]; errs = sorted({b['c_text'] for b in bl}); rng.shuffle(errs); keep = set(errs[:JUDGE_ERRORS_PER_CASE]); chosen += [b for b in bl if b['c_text'] in keep]
    S['judge_blocks'] = [dict(case=b['case'], c_text=b['c_text'], style=b['style']) for b in chosen]; jf = os.path.join(OUT, 'judge_d_replies.jsonl'); done = {(json.loads(l)['reference'], json.loads(l)['candidate']): json.loads(l)['result'] for l in open(jf)} if os.path.exists(jf) else {}
    j = judge2_test.SC(judge2.PROMPT_V2); todo = sorted({(b['ref'], b['d_text']) for b in chosen} - set(done)); print('judge calls to do', len(todo), 'blocks', len(chosen), flush=True); t0 = time.time()
    for i, (r, h) in enumerate(todo):
        if time.time() - t0 > a.max_hours * 3600: print('time limit'); json.dump(S, open(os.path.join(OUT, 'd_scores.json'), 'w')); return
        res = j.run(r, h); done[(r, h)] = res; open(jf, 'a').write(json.dumps(dict(reference=r, candidate=h, result=res)) + '\n')
        if i % 20 == 0: print('judge', i, len(todo), round(time.time() - t0), 's', flush=True)
    S['judge'] = {f'{r}|||{h}': v for (r, h), v in done.items()}; json.dump(S, open(os.path.join(OUT, 'd_scores.json'), 'w')); print('scores saved')

# ---------------------------------------------------------------- analysis
def eta2(A, Bv, Cv, Dv, w=None):
    """weighted two-way decomposition of the four cell scores of N blocks: fact (C, D vs A, B), wording (B, D vs A, C), interaction, residual (shares of the total sum of squares)"""
    A, Bv, Cv, Dv = map(np.asarray, (A, Bv, Cv, Dv)); w = np.ones(len(A)) if w is None else np.asarray(w, float); W = w.sum()
    if W == 0: return None
    m = lambda x: float((w * x).sum() / W); mA, mB, mC, mD = m(A), m(Bv), m(Cv), m(Dv); g = (mA + mB + mC + mD) / 4; mf1, mf0 = (mC + mD) / 2, (mA + mB) / 2; mw1, mw0 = (mB + mD) / 2, (mA + mC) / 2
    tot = float(sum((w * (x - g) ** 2).sum() for x in (A, Bv, Cv, Dv)))
    if tot == 0: return None
    ss_f = 2 * W * ((mf1 - g) ** 2 + (mf0 - g) ** 2); ss_w = 2 * W * ((mw1 - g) ** 2 + (mw0 - g) ** 2)
    ss_i = W * sum((mc - mf - mw_ + g) ** 2 for mc, mf, mw_ in ((mA, mf0, mw0), (mB, mf0, mw1), (mC, mf1, mw0), (mD, mf1, mw1)))
    return dict(fact=ss_f / tot, wording=ss_w / tot, interaction=ss_i / tot, residual=max(0.0, 1 - (ss_f + ss_w + ss_i) / tot))

def block_scores(blocks, name, sc, dsc, jsc=None):
    """per block (a mean over the reference's (a) texts, b, c, d); None when a score is missing"""
    out = []
    for b in blocks:
        if jsc is not None:
            d = jsc.get((b['ref'], b['d_text'])); d = None if d is None else d['judge' if name == 'judge_score' else 'f1']
        else: d = dsc.get((b['ref'], b['d_text']))
        av = [sc[name].get((b['ref'], t)) for t in b['a_texts']]; av = [x for x in av if x is not None]; bb = sc[name].get((b['ref'], b['b_text'])); cc = sc[name].get((b['ref'], b['c_text']))
        out.append(None if (d is None or not av or bb is None or cc is None) else (float(np.mean(av)), bb, cc, d, av))
    return out

def analyse_scorer(blocks, vals, organ=None, nboot=1000):
    idx = [i for i, (b, v) in enumerate(zip(blocks, vals)) if v is not None and (organ is None or b['organ'] == organ)]
    if not idx: return None
    G = sorted({blocks[i]['group'] for i in idx}); gi = {g: k for k, g in enumerate(G)}
    A = np.array([vals[i][0] for i in idx]); Bv = np.array([vals[i][1] for i in idx]); Cv = np.array([vals[i][2] for i in idx]); Dv = np.array([vals[i][3] for i in idx]); grp = np.array([gi[blocks[i]['group']] for i in idx])
    # per-reference pair statistics: (c vs a), (d vs b), reversal shares
    byref = collections.defaultdict(list)
    for k, i in enumerate(idx): byref[(blocks[i]['case'], blocks[i]['group'])].append(k)
    ref_stats = {}
    for (cid, g), ks in byref.items():
        av = vals[idx[ks[0]]][4]; c_vs_a = []; d_vs_b = []; d_lt_a = []; c_gt_b = []; d_gt_a = []
        cs = {blocks[idx[k]]['c_text']: Cv[k] for k in ks}; bs = {blocks[idx[k]]['style']: Bv[k] for k in ks}
        for c in cs.values():
            for x in av: c_vs_a.append((c < x) + 0.5 * (c == x))
            for bsv in bs.values(): c_gt_b.append(float(c > bsv))
        for k in ks:
            d = Dv[k]; d_vs_b.append((d < Bv[k]) + 0.5 * (d == Bv[k]))
            for x in av: d_lt_a.append(float(d < x)); d_gt_a.append(float(d > x))
        ref_stats[(cid, g)] = (np.mean(c_vs_a), np.mean(d_vs_b), np.mean(d_lt_a), np.mean(c_gt_b), np.mean(d_gt_a))
    refs = list(ref_stats); rs = np.array([ref_stats[r] for r in refs]); rg = [r[1] for r in refs]
    out = dict(n_blocks=len(idx), n_references=len(refs), n_groups=len(G), too_small=len(G) < 30, eta=eta2(A, Bv, Cv, Dv))
    rng = np.random.default_rng(0); boots = collections.defaultdict(list)
    for _ in range(nboot):
        counts = np.bincount(rng.integers(0, len(G), len(G)), minlength=len(G)); e = eta2(A, Bv, Cv, Dv, counts[grp])
        if e:
            for k, v in e.items(): boots['eta_' + k].append(v)
            boots['eta_diff'].append(e['fact'] - e['wording'])
    pc = lambda v: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] if v else None
    out['eta_ci'] = {k[4:]: pc(v) for k, v in boots.items()}
    for j, nm in enumerate(('auroc_c_vs_a', 'auroc_d_vs_b', 'reversal_d_below_a', 'reversal_c_above_b', 'd_above_a')): out[nm] = gboot(list(rs[:, j]), rg)
    out['fact_driven'] = bool(out['eta']['fact'] > out['eta']['wording']) if out['eta'] else None; out['eta_diff_ci'] = out['eta_ci'].get('diff'); return out

def cmd_analyse(a):
    D = json.load(open(os.path.join(OUT, 'test_blocks.json'))); blocks = D['blocks']; S = json.load(open(os.path.join(OUT, 'd_scores.json'))); P_ = [tuple(p) for p in S['pairs']]
    sc = {**P.scores_of(os.path.join(ROOT, 'scores_test_layer0.json')), 'finding_f1': P.scores_of(os.path.join(ROOT, 'scores_test_layer1.json'))['finding_f1'], **P.judge_lookup([os.path.join(ROOT, 'results/partA/step10d_test_results/judge_test_v2.jsonl'), os.path.join(ROOT, 'judge_big_v2.jsonl')])}
    dsc = {n: dict(zip(P_, v)) for n, v in S['scores'].items()}; jsc = {tuple(k.split('|||')): v for k, v in S.get('judge', {}).items() if v}; res = {}
    jset = {(b['case'], b['c_text'], b['style']) for b in [dict(x) for x in S.get('judge_blocks', [])]}
    for name, _ in SCORERS:
        isj = name in ('judge_score', 'sentence_f1'); bl = [b for b in blocks if (b['case'], b['c_text'], b['style']) in jset] if isj else blocks
        vals = block_scores(bl, name, sc, dsc.get(name, {}), jsc if isj else None); res[name] = {o or 'pooled': analyse_scorer(bl, vals, o) for o in (None, 'breast', 'thyroid')}
    res['_build'] = dict(stats=D['stats'], reasons=D['reasons'], kept_by_organ=dict(collections.Counter(b['organ'] for b in blocks)), judge_blocks=len(S.get('judge_blocks', [])))
    json.dump(res, open(os.path.join(OUT, 'results.json'), 'w'), indent=1); print({n: (res[n]['pooled']['fact_driven'], round(res[n]['pooled']['eta']['fact'], 2), round(res[n]['pooled']['eta']['wording'], 2)) for n, _ in SCORERS if res[n]['pooled']})

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd'); ap.add_argument('--max-hours', type=float, default=3.0); a = ap.parse_args()
    {'check_dev': cmd_check_dev, 'build_test': cmd_build_test, 'score': cmd_score, 'analyse': cmd_analyse}[a.cmd](a)
