"""Step 6: ultrasound finding schema + rule-based extractor for templated (v2) wording + structured scorer `finding_f1`.

Schema (entity -> attributes), status in {present, absent, uncertain}:
  breast : lesion{status, count, shape, orient, margin, echo, post, size_mm|size_pct, pos, side}, calcifications{status, type},
           halo{status}, assessment{birads}, pathology{path, hist}                      (BI-RADS lexicon terms)
  thyroid: lesion{status, count, comp, echo, margin, orient, size_mm|size_pct, pos}, foci{status, type}, assessment{tirads}   (TI-RADS terms)
  fetal  : head{hc_mm, plane}
Flat facts use the same keys as templates_v2.facts, so the extractor can be scored against dataset labels field by field.
"""
import re
from . import extract

ORG_ENT = {'breast': ['lesion', 'calcifications', 'halo', 'assessment', 'pathology'], 'thyroid': ['lesion', 'foci', 'assessment'], 'fetal': ['head']}
FIELD_ENTITY = dict(lesion='lesion', count='lesion', shape='lesion', orient='lesion', margin='lesion', echo='lesion', post='lesion', size_mm='lesion', size_pct='lesion',
                    pos='lesion', side='lesion', comp='lesion', calc='calcifications', halo='halo', foci='foci', birads='assessment', tirads='assessment',
                    path='pathology', hist='pathology', hc_mm='head', plane='head')

# ---------------------------------------------------------------- rule-based extractor (v2 templated wording and our harmless rewordings)
ECHO = r'(anechoic|hypoechoic|hyperechoic|isoechoic|heterogeneous|complex cystic/solid|marked hypoechoic)'
COMP = r'(predominantly solid|predominantly cystic|spongiform|solid|cystic|dense)'
TMARG = r'(well defined smooth|well defined|ill defined|microlobulated|spiculated|macrolobulated)'

def _size(t, f):
    m = re.search(r'(\d+(?:\.\d+)?) (mm|cm)\b', t)
    if m and 'hc' not in f: f['size_mm'] = round(float(m[1]) * (10 if m[2] == 'cm' else 1))
    m = re.search(r'(\d+)% of the image width', t)
    if m: f['size_pct'] = int(m[1])

def extract_rule(text, organ):
    """flat facts from templated text; missing = absent from the dict"""
    t = text; tl = text.lower(); f = {}
    if organ == 'fetal':
        m = re.search(r'(?:circumference|hc)\s+(?:measures\s+)?(?:approximately\s+)?(\d+(?:\.\d+)?)\s*(mm|cm)', tl)
        if m: f['hc_mm'] = round(float(m[1]) * (10 if m[2] == 'cm' else 1), 1)
        m = re.search(r'(trans (?:thalamic|cerebellum|ventricular))', tl)
        if m: f['plane'] = m[1]
        return f
    if re.search(r'no (?:focal )?(?:lesion|nodule)|(?:lesion|nodule) is not seen|shows no focal', tl):
        f['lesion'] = 'absent'
        m = re.search(r'bi-rads (\w+)', tl); f['birads'] = m[1] if m else None
        if 'pathology: normal' in tl: f['path'] = 'normal'
        return {k: v for k, v in f.items() if v is not None}
    f['lesion'] = 'present'
    m = re.search(r'(\d+) lesions', tl)
    f['count'] = int(m[1]) if m else {'a single nodule': 1, 'a single lesion': 1, 'two nodules': 2, 'two lesions': 2, 'three or more nodules': 3, 'three or more lesions': 3}.get(
        (re.search(r'(a single (?:nodule|lesion)|two (?:nodules|lesions)|three or more (?:nodules|lesions))', tl) or [None])[0], 1)
    m = re.search(r'(upper|middle|lower) (left|central|right)(?: part of the image)', tl)
    if m: f['pos'] = f'{m[1]}-{m[2]}'
    if 'wider than tall' in tl: f['orient'] = 'wider than tall'
    elif 'taller than wide' in tl: f['orient'] = 'taller than wide'
    _size(tl, f)
    if organ == 'breast':
        m = re.search(r'\b(oval|round|irregular)\b', tl)
        if m: f['shape'] = m[1]
        m = re.search(r'(not circumscribed(?: \([^)]*\))?|circumscribed)(?: margins?| borders?)', tl)
        if m: f['margin'] = m[1]
        m = re.search(r'\b' + ECHO + r'\b(?! cystic)', tl)
        if m: f['echo'] = m[1]
        for k, pat in (('shadowing', r'posterior acoustic shadowing'), ('enhancement', r'posterior acoustic enhancement'), ('combined', r'combined posterior'),
                       ('no', r'no posterior acoustic features|posterior acoustic features are absent')):
            if re.search(pat, tl): f['post'] = k; break
        if re.search(r'no calcifications|calcifications are absent', tl): f['calc'] = 'no'
        else:
            m = re.search(r'calcifications \(([^)]*)\)', tl)
            if m: f['calc'] = m[1]
        if re.search(r'no echogenic halo|echogenic halo is absent', tl): f['halo'] = 'no'
        elif 'echogenic halo' in tl: f['halo'] = 'yes'
        m = re.search(r'(left|right) breast', tl)
        if m: f['side'] = m[1]
        m = re.search(r'bi-rads (\w+)', tl)
        if m: f['birads'] = m[1]
        m = re.search(r'pathology: (\w+)', tl)
        if m: f['path'] = m[1]
        m = re.search(r'histolog(?:y|ic type): ([^.]+)', tl)
        if m: f['hist'] = m[1].strip()
    else:
        m = re.search(COMP + r'(?: composition)|composition ' + COMP, tl)
        if m: f['comp'] = m[1] or m[2]
        else:
            m = re.search(r'(?:nodules?|lesions?), ' + COMP + r',', tl)
            if m: f['comp'] = m[1]
        m = re.search(r'(marked hypoechoic|hypoechoic|hyperechoic|isoechoic|anechoic)', tl)
        if m: f['echo'] = m[1]
        m = re.search(TMARG + r'(?: margins?| borders?)', tl) or re.search(r'margins ' + TMARG, tl)
        if m: f['margin'] = m[1]
        if re.search(r'no echogenic foci', tl): f['foci'] = 'none'
        else:
            m = re.search(r'echogenic foci \(([^)]*)\)', tl)
            if m: f['foci'] = m[1]
        m = re.search(r'ti-rads (\w+)', tl)
        if m: f['tirads'] = m[1]
    return f

def to_findings(f, organ):
    """flat facts -> structured findings: {entity: {'status':..., attrs...}}"""
    out = {}
    for k, v in f.items():
        ent = FIELD_ENTITY[k]; d = out.setdefault(ent, {})
        if k == 'lesion': d['status'] = v
        elif k in ('calc', 'foci', 'halo'):
            d['status'] = 'absent' if v in ('no', 'none') else 'present'
            if v not in ('no', 'none', 'yes'): d['type'] = v
        else: d[k] = v
    return out

# ---------------------------------------------------------------- scorer
NUM_TOL = dict(size_mm=0.5, size_pct=0.5)      # credit falls linearly to 0 at 50% relative error
HC_TOL_MM = 20.0                               # same tolerance as the old fact_checker
def attr_credit(attr, a, b):
    """1.0 = agrees, 0.0 = disagrees or missing; numeric attributes get graded credit"""
    if b is None: return 0.0
    if attr in NUM_TOL: return max(0.0, 1 - abs(a - b) / (NUM_TOL[attr] * a)) if a else float(a == b)
    if attr == 'hc_mm': return max(0.0, 1 - abs(a - b) / HC_TOL_MM)
    return float(str(a) == str(b))

def flat_attrs(findings):
    return {(e, k): v for e, d in findings.items() for k, v in d.items()}

def finding_scores(ref_f, cand_f):
    """precision, recall, F1 over (entity, attribute) pairs + per-attribute credits for the reference attributes"""
    R, C = flat_attrs(ref_f), flat_attrs(cand_f); cr = {}
    for key, a in R.items(): cr[key] = attr_credit(key[1], a, C.get(key))
    tp_r = sum(cr.values()); tp_p = sum(attr_credit(key[1], R[key], b) if key in R else 0.0 for key, b in C.items())
    rec = tp_r / len(R) if R else 1.0; prec = tp_p / len(C) if C else (1.0 if not R else 0.0)
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return prec, rec, f1, cr

class FindingF1:
    name = 'finding_f1'
    def score(self, ref, hyp, item):
        o = item['organ']; p, r, f1, _ = finding_scores(to_findings(extract_rule(ref, o), o), to_findings(extract_rule(hyp, o), o)); return f1
class FindingPrecision:
    name = 'finding_precision'
    def score(self, ref, hyp, item):
        o = item['organ']; return finding_scores(to_findings(extract_rule(ref, o), o), to_findings(extract_rule(hyp, o), o))[0]
class FindingRecall:
    name = 'finding_recall'
    def score(self, ref, hyp, item):
        o = item['organ']; return finding_scores(to_findings(extract_rule(ref, o), o), to_findings(extract_rule(hyp, o), o))[1]
