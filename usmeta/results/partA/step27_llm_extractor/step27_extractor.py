"""Step 27: LLM fact extractor (Qwen2.5-7B-Instruct, 4-bit MLX, greedy) + the UNCHANGED finding_f1 comparer = `llm_finding_f1`.
NEW file: schema.py (frozen) is only imported. The comparer is schema.to_findings + schema.finding_scores (same credit rules and tolerances).
The extractor reads a report and fills a fixed per-organ JSON (null = not stated); plain code (no model) then maps it onto the schema's flat facts.
Few-shot examples come from DEV cases only (ids in FEWSHOT). Prompt variants: main (used for every reported number), altA / altB (reworded, stability check only).
Every call is cached on disk (results/partA/step27_llm_extractor/cache.jsonl, key = sha256(model|variant|report)); runs resume from it. The test split is not touched here."""
import os, re, json, copy, time, hashlib
from . import schema

MODEL = 'mlx-community/Qwen2.5-7B-Instruct-4bit'
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'); OUT = os.path.join(ROOT, 'results', 'partA', 'step27_llm_extractor'); CACHE = os.path.join(OUT, 'cache.jsonl')

# organ -> ordered list of (json key, flat fact key, allowed values / format)
FIELDS = {
 'breast': [('lesion_present', 'lesion', 'true if a mass/lesion is described, false if the report says there is none'), ('count', 'count', 'number of lesions (integer)'),
            ('side', 'side', '"left" or "right" (the breast)'), ('position', 'pos', 'position in the image, e.g. "upper-central", "middle-left", "lower-right"'),
            ('orientation', 'orient', '"wider than tall" or "taller than wide"'), ('size', 'size', '{"value": number, "unit": "mm" or "cm" or "%"} exactly as written (% = percent of image width)'),
            ('shape', 'shape', '"oval", "round" or "irregular"'), ('margin', 'margin', '"circumscribed", or "not circumscribed (<terms>)" e.g. "not circumscribed (indistinct)"'),
            ('echo', 'echo', '"anechoic", "hypoechoic", "hyperechoic", "isoechoic", "heterogeneous" or "complex cystic/solid"'),
            ('posterior', 'post', '"shadowing", "enhancement", "combined" or "no" (no posterior acoustic features)'), ('halo', 'halo', '"yes" or "no" (echogenic halo)'),
            ('calcifications', 'calc', '"no", or the calcification type/location as written'), ('birads', 'birads', 'category only, e.g. "3", "4a", "5"'),
            ('pathology', 'path', '"benign", "malignant" or "normal"'), ('histology', 'hist', 'histologic type as written, lower case')],
 'thyroid': [('count', 'count', 'number of nodules (integer; 0 if none; "three or more" = 3)'), ('position', 'pos', 'position in the image, e.g. "upper-central", "middle-left"'),
             ('orientation', 'orient', '"wider than tall" or "taller than wide"'), ('size', 'size', '{"value": number, "unit": "mm" or "cm" or "%"} exactly as written (% = percent of image width)'),
             ('composition', 'comp', '"solid", "cystic", "predominantly solid", "predominantly cystic", "spongiform" or "dense"'),
             ('echo', 'echo', '"hypoechoic", "hyperechoic", "isoechoic", "marked hypoechoic" or "anechoic"'),
             ('margin', 'margin', '"well defined", "well defined smooth", "ill defined", "microlobulated", "spiculated" or "macrolobulated"'),
             ('foci', 'foci', '"none", or the echogenic foci type as written, e.g. "microcalcifications"'), ('tirads', 'tirads', 'category only, e.g. "3", "4a", "5"')],
 'fetal': [('plane', 'plane', '"trans thalamic", "trans cerebellum" or "trans ventricular"'), ('hc', 'hc', '{"value": number, "unit": "mm" or "cm"} head circumference exactly as written')],
}
NUMERIC = {'count'}

# few-shot cases: DEV only. (case_id, style key in true_reports_v2d 'styles', or 'cm' = the unit_cm harmless rewording from bench_v2d)
FEWSHOT = {'breast': [('BrEaST:79', 'cm'), ('BUS-BRA:bus_0001-l', 'terse'), ('BrEaST:61', 'standard')],
           'thyroid': [('DDTI:3_1', 'standard'), ('TN3K:test/0003.jpg', 'terse'), ('DDTI:54_1', 'standard')],
           'fetal': [('FetalHead:Patient00168_Plane3_3_of_3', 'standard'), ('HC18:376_2HC', 'cm'), ('FetalHead:Patient01304_Plane3_5_of_6', 'standard')]}

INSTR = {
 'main': ('You extract facts from an ultrasound report into JSON. Reply with ONE line of JSON only, containing every key listed below, in this order. '
          'Use null for any field the report does not state; never guess or infer. Copy numbers and units exactly as written (do not convert).\n\nKEYS:\n{keys}'),
 'altA': ('Read the ultrasound report and return its findings as a single-line JSON object with exactly the keys below. A key whose information is not in the report must be null. '
          'Do not infer anything that is not written. Report measurements with the unit that appears in the text.\n\nFIELDS:\n{keys}'),
 'altB': ('Task: turn the ultrasound report into structured data. Output only a JSON object on one line. Include all of these keys; set a key to null when the report is silent about it, '
          'and do not make assumptions. Keep sizes in the units used by the report.\n\nSCHEMA (key: allowed values):\n{keys}'),
}
def _keys(organ, variant):
    f = FIELDS[organ]
    if variant == 'altB': f = list(reversed(f))                         # reordered schema listing (output order follows the examples)
    return '\n'.join(f'- {k}: {d}' for k, _, d in f)

def gold_json(organ, facts, text):
    """few-shot answer from the case's known facts; size/hc keep the unit WRITTEN in the shown text"""
    f = dict(facts); o = {}
    for k, fk, _ in FIELDS[organ]:
        if k == 'lesion_present': o[k] = f.get('lesion', 'present') == 'present'
        elif k == 'size':
            if 'size_mm' in f:
                m = re.search(r'(\d+(?:\.\d+)?) (mm|cm)\b', text); o[k] = {'value': float(m[1]) if '.' in m[1] else int(m[1]), 'unit': m[2]}
            elif 'size_pct' in f: o[k] = {'value': f['size_pct'], 'unit': '%'}
            else: o[k] = None
        elif k == 'hc':
            if 'hc_mm' in f:
                m = re.search(r'(\d+(?:\.\d+)?) (mm|cm)\b', text); v = m[1]; o[k] = {'value': float(v) if '.' in v else int(v), 'unit': m[2]}
            else: o[k] = None
        elif k == 'count': o[k] = (0 if f.get('lesion') == 'absent' else f.get('count')) if organ == 'thyroid' else f.get('count')
        elif k == 'halo': o[k] = f.get('halo')
        else: o[k] = f.get(fk)
    return o

def _dump(o): return json.dumps(o, ensure_ascii=False, separators=(', ', ': '))
def build_messages(organ, variant, shots):
    """shots: list of (text, answer-dict). The shared prefix (instructions + examples) is identical for every report of an organ and variant."""
    inst = INSTR[variant].format(keys=_keys(organ, variant)); msgs = [{'role': 'system', 'content': inst}]
    keys = [k for k, _, _ in FIELDS[organ]]
    if variant == 'altB': keys = list(reversed(keys))
    for t, a in shots: msgs += [{'role': 'user', 'content': 'REPORT:\n' + t}, {'role': 'assistant', 'content': _dump({k: a[k] for k in keys})}]
    return msgs

def load_shots():
    from . import splits
    dev = {r['case_id'] for r in splits.load('dev')}; tr = {}
    for l in open(os.path.join(ROOT, 'true_reports_v2d.jsonl')):
        r = json.loads(l); tr[r['case_id']] = r
    bench = {}
    for l in open(os.path.join(ROOT, 'bench_v2d.jsonl')):
        r = json.loads(l)
        if r['group'] == 'unit_cm': bench.setdefault(r['case_id'], r['candidate'])
    out = {}
    for organ, lst in FEWSHOT.items():
        sh = []
        for cid, st in lst:
            assert cid in dev, cid                                   # dev only
            r = tr[cid]; text = bench[cid] if st == 'cm' else r['styles'][st]
            facts = schema.extract_rule(text, organ); sh.append((text, gold_json(organ, facts, text)))
        out[organ] = sh
    return out

class Extractor:
    def __init__(self, variant='main', model=MODEL, max_tokens=260, shots=None):
        self.variant, self.model_id, self.max_tokens = variant, model, max_tokens; self._m = None; self.shots = shots or load_shots(); self.base = {}
        os.makedirs(OUT, exist_ok=True); self.cache = {}; self.calls = 0; self.secs = 0.0
        if os.path.exists(CACHE):
            for l in open(CACHE): d = json.loads(l); self.cache[d['key']] = d['raw']
    def key(self, organ, text): return hashlib.sha256(f'{self.model_id}|{self.variant}|{organ}|{text}'.encode()).hexdigest()
    def _load(self):
        if self._m is None:
            from mlx_lm import load; self._m = load(self.model_id)
    def _prefix(self, organ):
        """prompt cache for the shared prefix (instructions + few-shot); copied per call so every report sees exactly the same context"""
        if organ not in self.base:
            self._load(); from mlx_lm.models.cache import make_prompt_cache
            model, tok = self._m; msgs = build_messages(organ, self.variant, self.shots[organ])
            full = tok.apply_chat_template(msgs + [{'role': 'user', 'content': 'REPORT:\nX'}], add_generation_prompt=True, tokenize=False)
            pre = full[:full.rindex('<|im_start|>user')]; ids = tok.encode(pre); cache = make_prompt_cache(model)
            import mlx.core as mx
            model(mx.array(ids)[None], cache=cache); mx.eval([c.state for c in cache]); self.base[organ] = (pre, len(ids), cache)
        return self.base[organ]
    def raw(self, organ, text):
        k = self.key(organ, text)
        if k in self.cache: return self.cache[k]
        self._load(); from mlx_lm import generate; model, tok = self._m; pre, n, cache = self._prefix(organ)
        full = pre + f'<|im_start|>user\nREPORT:\n{text}<|im_end|>\n<|im_start|>assistant\n'; ids = tok.encode(full)
        assert ids[:n] == tok.encode(pre), 'prefix tokenisation drifted'
        t0 = time.time(); out = generate(model, tok, prompt=ids[n:], max_tokens=self.max_tokens, prompt_cache=copy.deepcopy(cache)); self.secs += time.time() - t0; self.calls += 1
        self.cache[k] = out; open(CACHE, 'a').write(json.dumps(dict(key=k, variant=self.variant, organ=organ, raw=out)) + '\n'); return out
    def facts(self, organ, text):
        """(flat facts, parse_ok): flat facts use the same keys/values as schema.extract_rule"""
        return to_flat(organ, self.raw(organ, text))

# ---------------------------------------------------------------- JSON -> flat facts (no model; one mapping for every report)
def _num(v):
    try: return float(v)
    except Exception: return None

def to_flat(organ, raw):
    m = re.search(r'\{.*\}', raw or '', re.S)
    try: js = json.loads(m.group(0)); assert isinstance(js, dict)
    except Exception: return {}, False
    f = {}
    for k, fk, _ in FIELDS[organ]:
        v = js.get(k)
        if v in (None, '', 'null', 'None', 'N/A', 'not stated'): continue
        if k in ('size', 'hc'):
            if isinstance(v, dict): val, unit = _num(v.get('value')), str(v.get('unit') or '').strip().lower()
            else:
                mm = re.match(r'\s*(\d+(?:\.\d+)?)\s*(mm|cm|%)?', str(v)); val, unit = (float(mm[1]), (mm[2] or '')) if mm else (None, '')
            if val is None: continue
            if unit in ('%', 'percent', 'pct'): f['size_pct'] = int(round(val)) if k == 'size' else None
            else:
                mm_ = val * 10 if unit == 'cm' else val
                if k == 'size': f['size_mm'] = int(round(mm_))
                else: f['hc_mm'] = round(mm_, 1)
            f = {a: b for a, b in f.items() if b is not None}; continue
        if k == 'lesion_present':
            f['lesion'] = 'present' if (v is True or str(v).lower() in ('true', 'yes', 'present')) else 'absent'; continue
        if k == 'count':
            n = _num(v)
            if n is not None: f['count'] = int(round(n))
            continue
        if isinstance(v, bool): v = 'yes' if v else 'no'
        v = re.sub(r'\s+', ' ', str(v).strip().lower())
        if k == 'position': v = v.replace(' ', '-').replace('part-of-the-image', '').strip('-')
        if k == 'birads' or k == 'tirads': v = re.sub(r'^(bi-?rads|ti-?rads)\s*', '', v)
        f[fk] = schema._norm_llm(fk, v, organ) if fk in ('calc', 'foci', 'halo', 'post', 'margin') else v
    if organ == 'thyroid':
        if f.get('count') == 0: f = {'lesion': 'absent'}
        elif any(schema.FIELD_ENTITY[k] == 'lesion' for k in f): f['lesion'] = 'present'
        else: f['lesion'] = 'absent'
        if f['lesion'] == 'absent': f = {'lesion': 'absent'}
    elif organ == 'breast':
        if 'lesion' not in f: f['lesion'] = 'present' if any(schema.FIELD_ENTITY[k] == 'lesion' for k in f if k != 'lesion') else 'absent'
        if f['lesion'] == 'absent': f = {k: v for k, v in f.items() if k in ('lesion', 'birads', 'path')}
    return f, True

def llm_finding_f1(ref_flat, cand_flat, organ):
    """the unchanged comparer applied to extracted facts"""
    return schema.finding_scores(schema.to_findings(ref_flat, organ), schema.to_findings(cand_flat, organ))[2]
