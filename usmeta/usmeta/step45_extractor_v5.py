"""Step 45, Part B: extractor v5 evaluated on the free-text set A (writer-made, automatic gold), against v4 on the same reports. NEW file; step27_extractor (model, dev-only few-shot, mapping), step43 (the v4 text) and step45_freetext / step45_numchecker are imported unchanged.
v5 = Qwen2.5-7B-Instruct 4-bit, greedy, same dev-only few-shot examples as v3 / v4, plus:
  (1) a stricter instruction (V5 below);
  (2) a per-organ STRICT SCHEMA applied to the model's JSON (JSON-constrained in the sense of validation, not grammar-constrained decoding, which mlx_lm does not offer here): keys outside the organ's schema are dropped (no BI-RADS on thyroid or fetal head, no TI-RADS on breast), values outside the allowed
      vocabulary become null after a fixed synonym map (no free-form repair);
  (3) regex values override the model for numbers, sides, counts and categories (step45_numchecker.parse): size, head circumference, count, side, BI-RADS (breast only) and TI-RADS (thyroid only) come ONLY from the text by regex (a number the text does not contain cannot appear).
    python3 -m usmeta.step45_extractor_v5 run --variant v4|v5 --set devval|test | score --set devval|test"""
import os, sys, json, re, time, collections, argparse
import numpy as np
from . import schema, step27_extractor as X, step45_freetext as FT, step45_numchecker as NC
from .step10d_analysis import gboot

ROOT = X.ROOT; OUT = os.path.join(ROOT, 'results', 'partA', 'step45_improve_scorers', 'extractor'); P = lambda f: os.path.join(OUT, f); os.makedirs(OUT, exist_ok=True)
V5 = ("You extract facts from an ultrasound report into JSON. Reply with ONE line of JSON only, containing every key listed below, in this order, and no other key.\n"
      "RULES:\n"
      "1. Fill a key only with a fact the report itself states; otherwise null. Never infer, guess or complete. A key not in the list must not appear.\n"
      "2. Record every stated fact: if the report states a value for a key anywhere (findings, summary, impression, a category line), fill that key.\n"
      "3. Use one of the allowed values listed for the key when the report's words match it; otherwise copy the report's own words in lower case. Do not narrow a range or combination of terms to one term.\n"
      "4. BI-RADS belongs to breast reports only and TI-RADS to thyroid reports only. Fetal head reports have only plane and head circumference.\n"
      "5. echo, composition, margin, shape, foci and posterior features describe the lesion or nodule itself, not the surrounding tissue.\n"
      "6. pathology is benign, malignant or normal only if the report states a diagnosis in those terms; histology only if a histologic type is named. A category, a suspicion or a recommendation is not a pathology.\n"
      "7. Fill halo, calcifications and posterior features only if the report mentions them (present or absent).\n"
      "8. Copy numbers and units exactly as written.\n\nKEYS:\n{keys}")
X.INSTR['v5'] = V5

# ---------------------------------------------------------------- strict schema (allowed values per organ and key; synonyms mapped to the schema vocabulary)
ALLOWED = {
 'breast': dict(orientation={'wider than tall', 'taller than wide'}, shape={'oval', 'round', 'irregular'}, echo={'anechoic', 'hypoechoic', 'hyperechoic', 'isoechoic', 'heterogeneous', 'complex cystic/solid'},
                posterior={'shadowing', 'enhancement', 'combined', 'no'}, halo={'yes', 'no'}, pathology={'benign', 'malignant', 'normal'}),
 'thyroid': dict(orientation={'wider than tall', 'taller than wide'}, composition={'solid', 'cystic', 'predominantly solid', 'predominantly cystic', 'spongiform', 'dense'}, echo={'hypoechoic', 'hyperechoic', 'isoechoic', 'marked hypoechoic', 'anechoic'},
                margin={'well defined', 'well defined smooth', 'ill defined', 'microlobulated', 'spiculated', 'macrolobulated'}),
 'fetal': dict(plane={'trans thalamic', 'trans cerebellum', 'trans ventricular'}),
}
SYN = {'wider-than-tall': 'wider than tall', 'taller-than-wide': 'taller than wide', 'well-defined': 'well defined', 'well-defined smooth': 'well defined smooth', 'ill-defined': 'ill defined', 'poorly defined': 'ill defined', 'markedly hypoechoic': 'marked hypoechoic',
       'trans-thalamic': 'trans thalamic', 'transthalamic': 'trans thalamic', 'trans-cerebellar': 'trans cerebellum', 'trans cerebellar': 'trans cerebellum', 'transcerebellar': 'trans cerebellum', 'trans-ventricular': 'trans ventricular', 'transventricular': 'trans ventricular',
       'posterior acoustic shadowing': 'shadowing', 'posterior acoustic enhancement': 'enhancement', 'combined posterior features': 'combined', 'no posterior acoustic features': 'no', 'absent': 'no', 'present': 'yes'}

def norm(v):
    if isinstance(v, bool): return 'yes' if v else 'no'
    return SYN.get(re.sub(r'\s+', ' ', str(v).strip().lower()), re.sub(r'\s+', ' ', str(v).strip().lower()))

def norm_margin_breast(v):
    s = norm(v)
    if re.fullmatch(r'(well[- ]defined|smooth|well[- ]circumscribed|circumscribed|sharply (defined|marginated))( and smooth| smooth)?', s): return 'circumscribed'
    m = re.match(r'(?:not|non)[- ]circumscribed\s*(?:\(([^)]*)\))?', s)
    if m:
        q = sorted({w.strip() for w in re.split(r'[,/;]| and ', m.group(1) or '') if w.strip()}); return 'not circumscribed' + (f" ({', '.join(q)})" if q else '')
    if re.search(r'indistinct|ill[- ]defined|irregular|spiculated|angular|microlobulated', s): q = sorted({w for w in ('indistinct', 'angular', 'spiculated', 'microlobulated') if w in s}); return 'not circumscribed' + (f" ({', '.join(q)})" if q else '')
    return None

def strict(organ, js, text):
    """validated model JSON in the model's own key names (no extra keys; allowed values only; numbers / sides / counts / categories filled from the regex layer only)"""
    keys = [k for k, _, _ in X.FIELDS[organ]]; out = {k: None for k in keys}; al = ALLOWED[organ]; rx = NC.parse(text, organ)
    for k in keys:
        v = js.get(k) if isinstance(js, dict) else None
        if v in (None, '', 'null', 'None', 'N/A', 'not stated'): continue
        if k in al:
            nv = norm(v); out[k] = nv if nv in al[k] else None
        elif k == 'margin' and organ == 'breast': out[k] = norm_margin_breast(v)
        elif k in ('position', 'histology', 'calcifications'):
            s = norm(v)
            if k == 'position': s = s.replace(' ', '-'); out[k] = s if re.fullmatch(r'(upper|middle|lower)-(left|central|right)', s) else None
            elif k == 'calcifications': out[k] = 'no' if s in ('no', 'none', 'absent') else s
            else: out[k] = s
        elif k == 'foci': s = norm(v); out[k] = 'none' if s in ('no', 'none', 'absent') else s
        elif k == 'lesion_present': out[k] = bool(v) if isinstance(v, bool) else str(v).lower() in ('true', 'yes', 'present')
    # regex layer: numbers, sides, counts, categories
    if organ == 'fetal':
        out['hc'] = {'value': rx['hc_mm'], 'unit': 'mm'} if 'hc_mm' in rx else None
    else:
        out['size'] = ({'value': rx['size_mm'], 'unit': 'mm'} if 'size_mm' in rx else ({'value': rx['size_pct'], 'unit': '%'} if 'size_pct' in rx else None)); out['count'] = rx.get('count')
        if organ == 'breast': out['side'] = rx.get('side'); out['birads'] = rx.get('birads')
        else: out['tirads'] = rx.get('tirads')
    return out

def facts_v5(organ, raw, text):
    m = re.search(r'\{.*\}', raw or '', re.S)
    try: js = json.loads(m.group(0)); assert isinstance(js, dict)
    except Exception: js = {}
    sj = strict(organ, js, text); flat, ok = X.to_flat(organ, json.dumps(sj)); return flat, ok, sj

# ---------------------------------------------------------------- comparison with the gold facts
def vmatch(k, got, gold):
    if got is None or gold is None: return got is None and gold is None
    if k == 'hc_mm': return abs(float(got) - float(gold)) < 0.06
    if k in ('size_mm', 'size_pct', 'count'): return abs(float(got) - float(gold)) < 0.5
    g, s = norm(got), norm(gold)
    if k == 'margin' and 'circumscribed' in str(gold):
        a, b = norm_margin_breast(g), norm_margin_breast(s); return a == b
    return g.replace('-', ' ') == s.replace('-', ' ')

FIELDS = {o: [fk for _, fk, _ in X.FIELDS[o]] for o in ('breast', 'thyroid', 'fetal')}
for o in FIELDS: FIELDS[o] = [('size_mm' if fk == 'size' else 'hc_mm' if fk == 'hc' else fk) for fk in FIELDS[o]]
for o in ('breast', 'thyroid'): FIELDS[o].insert(FIELDS[o].index('size_mm') + 1, 'size_pct')
if 'lesion' not in FIELDS['breast']: FIELDS['breast'].insert(0, 'lesion')
if 'lesion' not in FIELDS['thyroid']: FIELDS['thyroid'].insert(0, 'lesion')

def match_report(organ, gold, flat, text):
    """per-field match of the extracted flat facts against the gold facts; a field the gold does not have but the extractor fills counts as right only if the independent lexicon check says the report states that value"""
    res = {}; t = ' '.join(text.lower().split())
    g = gold if gold.get('lesion') != 'absent' else {k: v for k, v in gold.items() if k in ('lesion', 'birads', 'path')}
    for k in FIELDS[organ]:
        got, want = flat.get(k), g.get(k)
        if want is None and got is not None:
            try: res[k] = bool(FT.check_field(organ, k, got, t))
            except Exception: res[k] = False
        else: res[k] = vmatch(k, got, want)
    return res

# ---------------------------------------------------------------- running
def reports(which):
    A = json.load(open(FT.P('set_A.json')))['cases']; out = []
    for cid, c in sorted(A.items()):
        if c['set'] != which: continue
        for r in c['true_reports']: out.append(dict(id=f"{cid}|true|{r['style']}", case_id=cid, organ=c['organ'], group=c['group'], dataset=c['dataset'], text=r['text'], gold=c['gold'], kind='true'))
        if c['twin_report']: out.append(dict(id=f"{cid}|twin|{c['twin_report']['style']}", case_id=cid, organ=c['organ'], group=c['group'], dataset=c['dataset'], text=c['twin_report']['text'], gold=c['twin'], kind='twin'))
    return out

def cmd_run(a):
    from . import step43_extractor_v4 as V43
    X.CACHE = P(f'cache_{a.variant}.jsonl'); X.OUT = OUT
    if a.variant == 'v4': X.INSTR['v4'] = V43.V4
    ex = X.Extractor(a.variant); R = reports(a.set); out = {}; t0 = time.time(); dl = t0 + a.max_hours * 3600
    for i, r in enumerate(R):
        if time.time() > dl: print('time cap'); break
        raw = ex.raw(r['organ'], r['text'])
        if a.variant == 'v5': flat, ok, sj = facts_v5(r['organ'], raw, r['text'])
        else: flat, ok = X.to_flat(r['organ'], raw); sj = None
        out[r['id']] = dict(flat=flat, ok=ok, strict=sj, raw=raw)
        if i % 50 == 0: print(a.variant, a.set, i, len(R), round(time.time() - t0), 's', flush=True)
    json.dump(out, open(P(f'extraction_{a.variant}_{a.set}.json'), 'w'), ensure_ascii=False); print('saved', len(out), 'of', len(R))

def score_variant(variant, which):
    R = reports(which); E = json.load(open(P(f'extraction_{variant}_{which}.json'))); rows = []
    for r in R:
        e = E.get(r['id'])
        if e is None: continue
        m = match_report(r['organ'], r['gold'], e['flat'], r['text']); rows.append(dict(id=r['id'], organ=r['organ'], group=r['group'], dataset=r['dataset'], kind=r['kind'], full=all(m.values()), fields=m, parse_ok=e['ok']))
    return rows

def cmd_score(a):
    res = {}; per = {}
    for v in ('v4', 'v5'):
        if not os.path.exists(P(f'extraction_{v}_{a.set}.json')): continue
        rows = score_variant(v, a.set); per[v] = rows; res[v] = {}
        for o in ('breast', 'thyroid', 'fetal', 'ALL'):
            sub = [r for r in rows if (o == 'ALL' or r['organ'] == o) and r['kind'] == 'true']
            if not sub: continue
            g = gboot([float(r['full']) for r in sub], [r['group'] for r in sub]); fa = {}
            for k in FIELDS[o if o != 'ALL' else 'breast']:
                pass
            res[v][o] = dict(reports=len(sub), groups=len({r['group'] for r in sub}), full_match=g, too_small=len({r['group'] for r in sub}) < 30)
            if o != 'ALL': res[v][o]['per_field'] = {k: float(np.mean([r['fields'][k] for r in sub])) for k in FIELDS[o]}
    if 'v4' in per and 'v5' in per:
        d4 = {r['id']: r for r in per['v4']}; res['paired'] = {}
        for o in ('breast', 'thyroid', 'fetal'):
            pairs = [(float(r['full']), float(d4[r['id']]['full']), r['group']) for r in per['v5'] if r['organ'] == o and r['kind'] == 'true' and r['id'] in d4]
            if pairs: res['paired'][o] = dict(n=len(pairs), diff_v5_minus_v4=gboot([a_ - b_ for a_, b_, _ in pairs], [g for _, _, g in pairs]))
    json.dump(res, open(P(f'scores_{a.set}.json'), 'w'), indent=1); print(json.dumps({v: {o: (round(d['full_match'][0], 3), round(d['full_match'][1], 3), d['reports']) for o, d in res[v].items()} for v in ('v4', 'v5') if v in res}, indent=0)); return res

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd'); ap.add_argument('--variant', default='v5'); ap.add_argument('--set', default='devval'); ap.add_argument('--max-hours', type=float, default=3.0); a = ap.parse_args()
    {'run': cmd_run, 'score': cmd_score}[a.cmd](a)
