"""Step 45, Part A: free-text set with AUTOMATIC gold (no human grader). NEW file; the frozen templates / schema / splits are imported unchanged.
Pre-registration: results/partA/step45_improve_scorers/PREREG.md (committed before any Step 45 number).
Writer: Qwen2.5-7B-Instruct 4-bit (MLX), temperature 0.7, fixed per-item seed; it gets ONLY the structured facts (the flat facts of the templated reference, the same fields the template uses) and writes a report in one of 3 styles
(terse, narrative, impression-first). Gold = the supplied facts. A deterministic lexicon check (below; independent of every extractor under test) keeps only reports that state every gold value; drops are counted, not charged to the extractor.
Each kept case also gets a planted-error twin (one field changed in the facts, from the case's planted-error candidates of the benchmark, same writer) and, for the limit-of-detection part (C), graded size / head-circumference twins.
    python3 -m usmeta.step45_freetext plan | generate [--max-hours H] | gold | summary
Sizes are smaller than the PREREG (a 5 s / report writer on a 16 GB Mac): see results.md of Part A for the deviation."""
import os, sys, json, re, time, random, hashlib, zlib, collections, argparse
from . import schema, splits

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(ROOT, 'results', 'partA', 'step45_improve_scorers', 'freetext'); P = lambda f: os.path.join(OUT, f)
MODEL = 'mlx-community/Qwen2.5-7B-Instruct-4bit'; TEMP = 0.7; SEED = 45; MAX_TOK = 230
ORGANS = ('breast', 'thyroid', 'fetal'); STYLES = ('terse', 'narrative', 'impression_first')
N_DEVVAL = {'dev': 60, 'val': 30}; N_TEST = 90             # cases per organ (PREREG: 600 cases per sample; reduced for compute, see results.md)
LOD_PER_GROUP = 40; SIZE_FACTORS = (1.05, 1.10, 1.25, 2.0); HC_SHIFTS = (1, 2, 5, 10)

SYS = ("You are a sonographer writing an ultrasound report from a structured list of findings. State EVERY item of the list exactly once, with its numbers and category labels unchanged "
       "(for example BI-RADS 4b stays BI-RADS 4b, 25 mm stays 25 mm, 22% of the image width stays 22% of the image width). Do not mention anything that is not in the list: no extra finding, number, diagnosis, recommendation or comparison.")
STYLE_TXT = {'terse': 'Style: terse and telegraphic, 1 to 3 short lines of fragments, as a busy radiologist would dictate.',
             'narrative': 'Style: a short paragraph of flowing prose (2 to 5 sentences), like the findings section of a radiology report.',
             'impression_first': "Style: start with one 'Impression:' sentence that gives the key finding, then a short 'Findings:' section."}

# ---------------------------------------------------------------- facts -> readable list for the writer
def describe(organ, f):
    L = []
    if organ == 'fetal':
        if 'plane' in f: L.append(f"scan plane: {f['plane']}")
        if 'hc_mm' in f: L.append(f"head circumference: {f['hc_mm']:g} mm")
        return L
    if f.get('lesion') == 'absent':
        L.append('no lesion or nodule is seen' if organ == 'breast' else 'no nodule is seen')
        if 'birads' in f: L.append(f"BI-RADS category: {f['birads']}")
        if 'path' in f: L.append(f"pathology: {f['path']}")
        return L
    L.append('a lesion (mass) is present' if organ == 'breast' else 'a thyroid nodule is present')
    if 'count' in f: L.append(f"number of {'lesions' if organ == 'breast' else 'nodules'}: {f['count']}" + (' (three or more)' if f['count'] == 3 else ''))
    if 'side' in f: L.append(f"side: {f['side']} breast")
    if 'pos' in f: L.append(f"position in the image: {f['pos'].replace('-', ' ')} part of the image")
    if 'orient' in f: L.append(f"orientation: {f['orient']}")
    if 'size_mm' in f: L.append(f"size: about {f['size_mm']} mm")
    if 'size_pct' in f: L.append(f"size: about {f['size_pct']}% of the image width")
    if 'shape' in f: L.append(f"shape: {f['shape']}")
    if 'comp' in f: L.append(f"composition: {f['comp']}")
    if 'margin' in f: L.append(f"margin: {f['margin']}")
    if 'echo' in f: L.append(f"echo pattern: {f['echo']}")
    if 'post' in f: L.append({'shadowing': 'posterior acoustic shadowing', 'enhancement': 'posterior acoustic enhancement', 'combined': 'combined posterior acoustic features', 'no': 'no posterior acoustic features'}[f['post']])
    if 'calc' in f: L.append('no calcifications' if f['calc'] == 'no' else f"calcifications: {f['calc']}")
    if 'foci' in f: L.append('no echogenic foci' if f['foci'] == 'none' else f"echogenic foci: {f['foci']}")
    if 'halo' in f: L.append('echogenic halo: ' + ('present' if f['halo'] == 'yes' else 'absent'))
    if 'birads' in f: L.append(f"BI-RADS category: {f['birads']}")
    if 'tirads' in f: L.append(f"TI-RADS category: {f['tirads']}")
    if 'path' in f: L.append(f"pathology: {f['path']}")
    if 'hist' in f: L.append(f"histologic type: {f['hist']}")
    return L

def messages(organ, f, style):
    return [{'role': 'system', 'content': SYS}, {'role': 'user', 'content': STYLE_TXT[style] + '\nFindings list:\n' + '\n'.join('- ' + x for x in describe(organ, f)) + '\nReport:'}]

# ---------------------------------------------------------------- deterministic gold check (lexicon + exact numbers; independent of every extractor under test)
def _num(n):
    return re.escape(f'{n:g}')

def _has(p, t): return re.search(p, t) is not None

def check_field(organ, k, v, t):
    """True if the report t (lower case) states the gold value v of field k"""
    if k == 'lesion':
        absent = _has(r"\bno (focal |visible |discrete |definite |suspicious )?(lesions?|masses|mass|nodules?)\b|(lesions?|masses|mass|nodules?) (is|are) (not seen|absent|not identified|not visualized)|no (focal )?abnormality|within normal limits|\bnormal\b", t)
        return absent if v == 'absent' else (_has(r'\b(mass|lesion|nodule)', t) and not absent)
    if k == 'count':
        if v == 1: return _has(r'\b(single|solitary|one|1|isolated)\b', t)
        if v == 2: return _has(r'\b(two|2|pair)\b', t)
        return _has(r'\b(three|3|four|4|five|5|multiple|several|numerous)\b', t)
    if k == 'side': return _has(r'\b' + v + r'\b', t)
    if k == 'pos':
        vert, hor = v.split('-'); V = {'upper': 'upper|superior|top', 'middle': 'middle|mid', 'lower': 'lower|inferior|bottom'}[vert]; H = {'left': 'left', 'right': 'right', 'central': 'central|centre|center|midline'}[hor]
        if vert == 'middle' and hor == 'central': return _has(r'(middle|mid)[ -]*(central|centre|center)|(central|centre|center)[ -]*(middle|mid)|(central|centre|center) (part|portion|region|area)|(in|at) the (centre|center|middle)', t)
        return _has(r'(' + V + r')[ -]*(' + H + r')|(' + H + r')[ -]*(' + V + r')', t) or (_has(r'\b(' + V + r')\b', t) and _has(r'\b(' + H + r')\b', t))
    if k == 'orient':
        return _has(r'wider[- ]than[- ]tall|horizontal(ly)? oriented|parallel (orientation|to the skin)', t) if v == 'wider than tall' else _has(r'taller[- ]than[- ]wide|vertical(ly)? oriented|non-?parallel', t)
    if k == 'size_mm': return _has(r'(?<![\d.])' + _num(v) + r'(\.0)?\s*mm\b', t) or _has(r'(?<![\d.])' + _num(v / 10) + r'\s*cm\b', t)
    if k == 'size_pct': return _has(r'(?<![\d.])' + _num(v) + r'(\.0)?\s*(%|percent|per cent)', t)
    if k == 'hc_mm': return _has(r'(?<![\d.])' + _num(v) + r'(\.0)?\s*mm\b', t) or _has(r'(?<![\d.])' + _num(round(v / 10, 2)) + r'\s*cm\b', t)
    if k == 'shape': return _has(r'\b' + v + r'\b', t)
    if k == 'margin':
        if organ == 'breast':
            if v == 'circumscribed': return _has(r'(?<!not )(?<!non-)(?<!non )\bcircumscribed', t) and not _has(r'not circumscribed', t)
            if not _has(r'not circumscribed|non-?circumscribed', t): return False
            q = re.findall(r'[a-z]+', v.split('(', 1)[1]) if '(' in v else []
            return all(_has({'indistinct': r'indistinct|ill[- ]defined|poorly defined', 'angular': 'angular', 'spiculated': 'spiculat', 'microlobulated': 'microlobulat'}.get(w, w), t) for w in q)
        if v == 'well defined': return _has(r'well[- ]defined', t)
        if v == 'well defined smooth': return _has(r'well[- ]defined', t) and _has(r'smooth', t)
        if v == 'ill defined': return _has(r'ill[- ]defined|poorly defined|indistinct', t)
        return _has(v, t)
    if k == 'echo':
        if v == 'complex cystic/solid': return _has(r'complex', t)
        if v == 'marked hypoechoic': return _has(r'marked(ly)? hypoechoic|very hypoechoic', t)
        if v == 'hypoechoic': return _has(r'(?<!marked )(?<!markedly )(?<!very )hypoechoic', t) and not _has(r'(markedly|marked|very) hypoechoic', t) or _has(r'(?<!marked )(?<!markedly )(?<!very )hypoechoic', t)
        return _has(r'\b' + v + r'\b', t)
    if k == 'post':
        return {'shadowing': _has(r'shadow', t) and not _has(r'no (posterior )?(acoustic )?shadow', t), 'enhancement': _has(r'enhanc', t) and not _has(r'no (posterior )?(acoustic )?enhanc', t), 'combined': _has(r'combined|shadow[^.]*enhanc|enhanc[^.]*shadow', t),
                'no': _has(r'no posterior|posterior (acoustic )?features (are )?(absent|none)|without posterior|no (acoustic )?(shadowing|enhancement)', t)}[v]
    if k == 'calc':
        if v == 'no': return _has(r'no (internal |visible )?calcification|calcifications? (are |is )?(absent|not (seen|present|identified))|without calcification', t)
        if not _has(r'calcification', t): return False
        return {'in a mass': _has(r'in a (mass|lesion)|in the (mass|lesion)|within the (mass|lesion)|within a (mass|lesion)|intramass', t) , 'intraductal': _has('intraductal', t), 'indefinable': _has('indefinable|indeterminate|unclassifi', t)}.get(v, _has(re.escape(v), t))
    if k == 'halo':
        absent = _has(r'no (echogenic )?halo|halo:? (is )?(absent|none|not (seen|present|identified))|without (an? )?(echogenic )?halo', t)
        return absent if v == 'no' else (_has(r'halo', t) and not absent)
    if k == 'birads': return _has(r'bi-?rads\s*(category|assessment|classification|score)?\s*[:\-]?\s*(is |of |as )?(category )?' + re.escape(v) + r'\b', t)
    if k == 'tirads': return _has(r'ti-?rads\s*(category|assessment|classification|score)?\s*[:\-]?\s*(is |of |as )?(category )?' + re.escape(v) + r'\b', t)
    if k == 'path':
        other = {'benign': 'malignant', 'malignant': 'benign'}.get(v)
        return _has(r'(?<!non-)(?<!non )\b' + v + r'\b', t) and not (other and _has(r'(?<!non-)(?<!non )\b' + other + r'\b', t) and v != 'normal')
    if k == 'hist': return v.lower() in t or all(w in t for w in re.findall(r'[a-z]+', v.lower()) if len(w) > 2) and len(re.findall(r'[a-z]+', v)) > 1
    if k == 'comp':
        if v == 'solid': return _has(r'(?<!predominantly )(?<!mostly )(?<!partly )\bsolid', t) and not _has(r'predominantly solid|mostly solid|partly solid|solid[- ]cystic|cystic[- ]solid', t)
        if v == 'cystic': return _has(r'(?<!predominantly )(?<!mostly )\bcystic', t) and not _has(r'predominantly cystic|mostly cystic|solid[- ]cystic|cystic[- ]solid', t)
        return _has(v, t)
    if k == 'foci':
        if v == 'none': return _has(r'no (echogenic )?(foci|calcification)|without (echogenic )?(foci|calcification)|echogenic foci (are )?(absent|not)', t)
        return _has(v[:-1] if v.endswith('s') else v, t)
    if k == 'plane': return _has({'trans thalamic': r'trans[- ]?thalamic', 'trans cerebellum': r'trans[- ]?cerebell', 'trans ventricular': r'trans[- ]?ventric'}[v], t)
    raise KeyError(k)

def gold_check(organ, facts, text):
    """(all stated?, list of gold fields the report does not state)"""
    t = ' '.join(text.lower().split()); miss = []
    fs = facts if facts.get('lesion') != 'absent' else {k: v for k, v in facts.items() if k in ('lesion', 'birads', 'path')}
    for k, v in fs.items():
        if k == 'lesion' and v == 'present' and organ in ('breast', 'thyroid'):
            pass
        try: ok = check_field(organ, k, v, t)
        except Exception: ok = False
        if not ok: miss.append(k)
    return (not miss), miss


# ---------------------------------------------------------------- extras check: the report must not state facts that are not in the supplied list (added after the first look at the writer's replies; see results.md)
ENUM = {'breast': dict(shape=['oval', 'round', 'irregular'], echo=['anechoic', 'hypoechoic', 'hyperechoic', 'isoechoic', 'heterogeneous'], post=['shadowing', 'enhancement'], orient=['wider than tall', 'taller than wide'], side=['left', 'right'], path=['benign', 'malignant']),
        'thyroid': dict(comp=['solid', 'cystic', 'spongiform'], echo=['hypoechoic', 'hyperechoic', 'isoechoic', 'anechoic'], margin=['well defined', 'ill defined', 'microlobulated', 'spiculated', 'macrolobulated'], orient=['wider than tall', 'taller than wide']),
        'fetal': dict(plane=['trans thalamic', 'trans cerebellum', 'trans ventricular'])}
MENTION = {'breast': dict(calc=r'calcification', halo=r'\bhalo', birads=r'bi-?rads', hist=None, margin=r'circumscribed|spiculat|angular|microlobulat|indistinct'), 'thyroid': dict(foci=r'echogenic foci|calcification', tirads=r'ti-?rads'), 'fetal': {}}
ALWAYS_EXTRA = {'breast': r'ti-?rads|\bthyroid\b', 'thyroid': r'bi-?rads|\bbreast\b|\b(benign|malignant)\b|patholog', 'fetal': r'bi-?rads|ti-?rads|\b(benign|malignant)\b|breast|thyroid|mass|lesion|nodule'}

def extras(organ, facts, text):
    """fields the report states that the supplied facts do not (or that conflict with them): categories, pathology, numbers with units, enumerated values"""
    t = ' '.join(text.lower().split()); out = []; g = facts if facts.get('lesion') != 'absent' else {k: v for k, v in facts.items() if k in ('lesion', 'birads', 'path')}
    if _has(ALWAYS_EXTRA[organ], t): out.append('wrong_organ_scale_or_diagnosis')
    for k, vals in ENUM[organ].items():
        stated = [v for v in vals if (check_field(organ, k, v, t) if v not in ('well defined', 'ill defined') else _has(v.replace(' ', '[- ]'), t))]
        if k not in g and stated: out.append(k)
        elif k in g and any(v != g[k] and v in stated and not (v in str(g[k]) or str(g[k]) in v) for v in vals): out.append(k + '_conflict')
    for k, pat in MENTION[organ].items():
        if pat and k not in g and _has(pat, t): out.append(k)
    if organ != 'fetal' and 'birads' in g and organ == 'breast':
        cats = set(re.findall(r'bi-?rads\s*(?:category|assessment|classification|score)?\s*[:\-]?\s*(?:is |of |as )?(?:category )?([0-6][abc]?)\b', t))
        if cats - {g['birads']}: out.append('birads_conflict')
    nums = re.findall(r'(\d+(?:\.\d+)?)\s*(mm|cm|%|percent)', t); gold_n = {k: g[k] for k in ('size_mm', 'size_pct', 'hc_mm') if k in g}
    for n, u in nums:
        v = float(n); okn = any((u in ('mm',) and abs(v - gold_n.get(k, -1)) < 0.06) or (u == 'cm' and abs(v * 10 - gold_n.get(k, -1)) < 0.6) for k in ('size_mm', 'hc_mm')) or (u in ('%', 'percent') and abs(v - gold_n.get('size_pct', -1)) < 0.6)
        if not okn: out.append('number'); break
    return sorted(set(out))

# ---------------------------------------------------------------- plan
def load_bench():
    sp = {}
    for l in open(os.path.join(ROOT, 'splits.jsonl')): r = json.loads(l); sp[r['case_id']] = r['split']
    by = {'dev': collections.defaultdict(list), 'val': collections.defaultdict(list), 'test': collections.defaultdict(list)}
    for f, want in (('bench_v2d.jsonl', 'dev'), ('bench_val_v2d.jsonl', 'val'), ('bench_test_v2d.jsonl', 'test')):
        for l in open(os.path.join(ROOT, f)):
            r = json.loads(l)
            if sp.get(r['case_id']) == want: by[want][r['case_id']].append(r)
    return by

def sample_cases(by, split, n_per_organ, rng):
    out = []
    for organ in ORGANS:
        ds = collections.defaultdict(list)
        for cid, rows in sorted(by[split].items()):
            if rows[0]['organ'] != organ: continue
            ref = rows[0]['reference']; errs = [r for r in rows if r['kind'] == 'error']
            if not errs: continue
            ds[rows[0]['dataset']].append(cid)
        for d in ds: rng.shuffle(ds[d])
        order = sorted(ds); picked = []; i = 0
        while len(picked) < n_per_organ and any(ds[d] for d in order):
            d = order[i % len(order)]; i += 1
            if ds[d]: picked.append(ds[d].pop())
        out += picked
    return out

def build_plan():
    rng = random.Random(SEED); by = load_bench(); items = []; cases = {}
    for split, n in (('dev', N_DEVVAL['dev']), ('val', N_DEVVAL['val']), ('test', N_TEST)):
        for cid in sample_cases(by, split, n, rng):
            rows = by[split][cid]; organ = rows[0]['organ']; ref = rows[0]['reference']; gold = schema.extract_rule(ref, organ); errs = [r for r in rows if r['kind'] == 'error']
            rr = random.Random(zlib.crc32(f'{SEED}|{cid}'.encode())); e = rr.choice(errs); twin = schema.extract_rule(e['candidate'], organ)
            cases[cid] = dict(case_id=cid, split=split, set='devval' if split in ('dev', 'val') else 'test', organ=organ, dataset=rows[0]['dataset'], group=f"{rows[0]['dataset']}:{rows[0]['group_id']}", reference=ref, gold=gold,
                              twin_field=e['field'], twin_category=e['category'], twin_severity=e['severity'], twin_candidate_templated=e['candidate'], twin=twin, twin_style=STYLES[zlib.crc32(f'{cid}|tw'.encode()) % 3])
    for cid, c in cases.items():
        for st in STYLES: items.append(dict(id=f'{cid}|true|{st}', case_id=cid, set=c['set'], kind='true', style=st, facts=c['gold']))
        items.append(dict(id=f'{cid}|twin|{c["twin_style"]}', case_id=cid, set=c['set'], kind='twin', style=c['twin_style'], facts=c['twin']))
    for it in items: it['organ'] = cases[it['case_id']]['organ']; it['messages'] = messages(it['organ'], it['facts'], it['style'])
    return cases, items

def lod_items(cases, kept_true_cases):
    """graded size / HC twins for the limit of detection (test cases only, cases whose true reports were kept); 40 cases per field group"""
    rng = random.Random(SEED + 1); groups = collections.defaultdict(list)
    for cid in sorted(kept_true_cases):
        c = cases[cid]
        if c['set'] != 'test': continue
        f = c['gold']; key = next((k for k in ('size_mm', 'size_pct', 'hc_mm') if k in f), None)
        if key: groups[(c['organ'], 'hc_mm' if key == 'hc_mm' else 'size')].append((cid, key))
    items = []
    for g, lst in sorted(groups.items()):
        rng.shuffle(lst)
        for cid, key in lst[:LOD_PER_GROUP]:
            c = cases[cid]; f = dict(c['gold']); v = f[key]; sgn = 1 if zlib.crc32(f'{cid}|sgn'.encode()) % 2 == 0 else -1
            levels = SIZE_FACTORS if key != 'hc_mm' else HC_SHIFTS
            for li, lv in enumerate(levels):
                g2 = dict(f)
                if key == 'hc_mm': new = round(v + sgn * lv, 1); level = lv
                else: new = int(round(v * lv)); level = round(lv - 1, 2)
                if new == v or new <= 0: continue
                g2[key] = new; st = STYLES[(zlib.crc32(cid.encode()) + li) % 3]
                items.append(dict(id=f'{cid}|lod|{key}|{level}', case_id=cid, set='test', kind='lod', style=st, facts=g2, organ=c['organ'], field=key, level=level, old=v, new=new, messages=messages(c['organ'], g2, st)))
    return items

# ---------------------------------------------------------------- generation (resumable, cached)
def load_cache():
    d = {}
    if os.path.exists(P('gen_cache.jsonl')):
        for l in open(P('gen_cache.jsonl')):
            try: r = json.loads(l); d[r['id']] = r
            except Exception: pass
    return d

def cmd_plan(a):
    os.makedirs(OUT, exist_ok=True); cases, items = build_plan()
    json.dump(cases, open(P('cases.json'), 'w'), indent=0); json.dump(dict(items=items, system=SYS, styles=STYLE_TXT, model=MODEL, temperature=TEMP, seed=SEED, max_tokens=MAX_TOK, sample=dict(n_devval=N_DEVVAL, n_test=N_TEST)), open(P('plan.json'), 'w'))
    c = collections.Counter((x['set'], x['organ']) for x in cases.values()); print('cases', dict(c), 'items', len(items), collections.Counter((i['set'], i['kind']) for i in items))

def cmd_generate(a):
    import mlx.core as mx
    from mlx_lm import load, generate
    from mlx_lm.sample_utils import make_sampler
    plan = json.load(open(P('plan.json'))); items = plan['items']; cases = json.load(open(P('cases.json'))); cache = load_cache(); deadline = time.time() + a.max_hours * 3600
    # LOD items are added after the gold check of the true reports (cmd_gold writes lod_plan.json)
    if os.path.exists(P('lod_plan.json')): items = items + json.load(open(P('lod_plan.json')))
    order = {'devval': 0, 'test': 1}; items = sorted(items, key=lambda i: (order[i['set']], {'true': 0, 'twin': 1, 'lod': 2}[i['kind']] if i['set'] == 'test' else 0, i['case_id'] if False else 0))
    todo = [i for i in items if i['id'] not in cache and (a.only is None or i['set'] == a.only or i['kind'] == a.only)]
    print('to generate', len(todo), 'cached', len(cache), flush=True); model, tok = load(MODEL); t0 = time.time(); fh = open(P('gen_cache.jsonl'), 'a'); n = 0
    for it in todo:
        if time.time() > deadline: print('time cap reached after', n, 'items'); break
        prompt = tok.apply_chat_template(it['messages'], add_generation_prompt=True, tokenize=False); mx.random.seed(zlib.crc32(f"{SEED}|{it['id']}".encode()) & 0x7fffffff); s = time.time()
        out = generate(model, tok, prompt=prompt, max_tokens=MAX_TOK, sampler=make_sampler(temp=TEMP)); rec = dict(id=it['id'], reply=out.strip(), seconds=round(time.time() - s, 2), prompt_sha=hashlib.sha256(prompt.encode()).hexdigest(), prompt=prompt)
        fh.write(json.dumps(rec, ensure_ascii=False) + '\n'); fh.flush(); n += 1
        if n % 25 == 0: print(n, len(todo), round(time.time() - t0), 's', flush=True)
    print('done', n, round(time.time() - t0), 's')

# ---------------------------------------------------------------- gold check -> set A
def cmd_gold(a):
    plan = json.load(open(P('plan.json'))); cases = json.load(open(P('cases.json'))); cache = load_cache(); items = {i['id']: i for i in plan['items']}
    if os.path.exists(P('lod_plan.json')):
        for i in json.load(open(P('lod_plan.json'))): items[i['id']] = i
    rec = {}; drop = collections.Counter(); tot = collections.Counter(); miss_fields = collections.Counter(); missing_gen = collections.Counter(); extra_fields = collections.Counter(); drop_reason = collections.Counter()
    for iid, it in items.items():
        if iid not in cache: missing_gen[(it['set'], it['kind'])] += 1; continue
        text = cache[iid]['reply']; ok0, miss = gold_check(it['organ'], it['facts'], text); ex = extras(it['organ'], it['facts'], text); ok = ok0 and not ex; key = (it['set'], it['organ'], it['kind']); tot[key] += 1
        if not ok: drop[key] += 1; [miss_fields.update([(it['organ'], m)]) for m in miss]; [extra_fields.update([(it['organ'], e_)]) for e_ in ex]; (drop_reason.update([(key[0], key[1], key[2], 'missing_gold' if not ok0 else 'extras_only')]))
        rec[iid] = dict(id=iid, case_id=it['case_id'], kind=it['kind'], style=it['style'], text=text, kept=ok, missing_gold=miss, extras=ex, **({k: it[k] for k in ('field', 'level', 'old', 'new')} if it['kind'] == 'lod' else {}))
    # case-level set A: a case is usable if >= 1 true report is kept; its twin needs the twin kept
    setA = {}
    for cid, c in cases.items():
        tr = [rec[f'{cid}|true|{s}'] for s in STYLES if f'{cid}|true|{s}' in rec and rec[f'{cid}|true|{s}']['kept']]; tw = rec.get(f"{cid}|twin|{c['twin_style']}")
        setA[cid] = dict(c, true_reports=[dict(style=r['style'], text=r['text']) for r in tr], twin_report=(dict(style=tw['style'], text=tw['text']) if tw and tw['kept'] else None), n_true_generated=sum(f'{cid}|true|{s}' in rec for s in STYLES))
    lod = [dict(r, organ=cases[r['case_id']]['organ'], group=cases[r['case_id']]['group']) for r in rec.values() if r['kind'] == 'lod' and r['kept']]
    json.dump(dict(cases=setA, lod=lod), open(P('set_A.json'), 'w'), ensure_ascii=False)
    # first pass: the LOD plan depends on the kept true reports (the cases that have any kept true report)
    kept_cases = [cid for cid, c in setA.items() if c['true_reports']]
    if not os.path.exists(P('lod_plan.json')) or a.refresh_lod:
        li = lod_items(cases, kept_cases); json.dump(li, open(P('lod_plan.json'), 'w')); print('lod plan', len(li), 'items (run generate --only lod, then gold again)')
    summ = dict(generated={f'{k[0]}|{k[1]}|{k[2]}': v for k, v in tot.items()}, dropped={f'{k[0]}|{k[1]}|{k[2]}': v for k, v in drop.items()}, missing_generation={f'{k[0]}|{k[1]}': v for k, v in missing_gen.items()},
                missed_gold_fields={f'{o}|{m}': v for (o, m), v in miss_fields.most_common()}, extra_fields={f'{o}|{m}': v for (o, m), v in extra_fields.most_common()}, drop_reason={'|'.join(k): v for k, v in drop_reason.items()}, cases_with_kept_true_report={s: collections.Counter(c['organ'] for c in setA.values() if c['set'] == s and c['true_reports']) for s in ('devval', 'test')})
    summ['cases_with_kept_true_report'] = {s: dict(v) for s, v in summ['cases_with_kept_true_report'].items()}
    json.dump(summ, open(P('gold_summary.json'), 'w'), indent=1); print(json.dumps(summ, indent=1)[:2500])

def cmd_selftest(a):
    """sanity check of the lexicon on the TEMPLATED styles of dev cases (they state every fact, so nearly all should pass)"""
    cases = json.load(open(P('cases.json'))); tr = {}
    for l in open(os.path.join(ROOT, 'true_reports_v2d.jsonl')): r = json.loads(l); tr[r['case_id']] = r
    res = collections.defaultdict(lambda: [0, 0]); bad = collections.Counter()
    for cid, c in cases.items():
        if c['set'] != 'devval' or cid not in tr: continue
        for st, t in tr[cid]['styles'].items():
            if st not in ('standard', 'terse'): continue
            ok, miss = gold_check(c['organ'], c['gold'], t); res[c['organ'], st][0] += ok; res[c['organ'], st][1] += 1
            for m in miss: bad[(c['organ'], m)] += 1
    print({f'{o}|{s}': f'{a}/{b}' for (o, s), (a, b) in res.items()}); print(bad.most_common(12))

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd'); ap.add_argument('--max-hours', type=float, default=4.5); ap.add_argument('--only', default=None); ap.add_argument('--refresh-lod', action='store_true'); a = ap.parse_args()
    {'plan': cmd_plan, 'generate': cmd_generate, 'gold': cmd_gold, 'selftest': cmd_selftest}[a.cmd](a)
