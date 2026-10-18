"""Rule-based fact extraction from templated or lightly reworded reports.

This is the v0 stand-in for a learned/LLM extractor. It only understands our own wording, so any grader built on
it is an UPPER BOUND on the templated data, not evidence about free-text reports.
"""
import re

BREAST_FIELDS = ['path', 'birads', 'margin', 'calc', 'shape', 'echo', 'post', 'halo']

def breast_facts(t):
    t = t.lower(); f = {}
    m = re.search(r'pathology: (\w+)', t) or re.search(r'pathology: (\w+)', t)
    f['path'] = m.group(1) if m else None
    m = re.search(r'bi-rads (\w+)', t); f['birads'] = m.group(1) if m else None
    m = re.search(r'with (.+?) (?:margins|borders)', t) or re.search(r'borders being (.+?), and internally', t)
    f['margin'] = m.group(1).strip() if m else None
    f['calc'] = 'no' if 'no calcifications' in t else ('yes:' + re.search(r'calcifications \(([^)]*)\)', t).group(1)) if re.search(r'calcifications \(', t) else None
    m = re.search(r'\ba (\w+) mass', t) or re.search(r'appears (\w+) in contour', t); f['shape'] = m.group(1) if m else None
    m = re.search(r'(anechoic|hypoechoic|hyperechoic|isoechoic|heterogeneous|complex cystic/solid)', t); f['echo'] = m.group(1) if m else None
    f['post'] = ('shadowing' if 'shadowing' in t else 'enhancement' if 'enhancement' in t else
                 'combined' if 'combined posterior' in t else 'no' if 'no posterior' in t else None)
    f['halo'] = 'no' if ('without a halo' in t or 'lacking a halo' in t) else 'yes' if 'halo' in t else None
    return f

def thyroid_facts(t):
    t = t.lower(); f = {}
    m = re.search(r'(benign|malignant|class [01])', t); f['path'] = m.group(1) if m else None
    m = re.search(r'(a single nodule|two nodules|three or more nodules)', t); f['count'] = m.group(1) if m else None
    m = re.search(r'(?:lies|located) in the ([a-z]+-[a-z]+)', t); f['loc'] = m.group(1) if m else None
    m = re.search(r'(?:is|,) (small|medium|large)\b', t); f['size'] = m.group(1) if m else None
    return f

def fetal_facts(t):
    t = t.lower(); f = {'hc': None}
    m = re.search(r'([\d.]+)\s*(mm|cm|millimetres)(?!\s*per pixel)', t)
    if m:
        v = float(m.group(1)); f['hc'] = round(v * 10, 1) if m.group(2) == 'cm' else round(v, 1)
    return f

def busbra_facts(t):
    t = t.lower(); f = {}
    m = re.search(r'pathology: (\w+)', t); f['path'] = m.group(1) if m else None
    m = re.search(r'bi-rads (\w+)', t); f['birads'] = m.group(1) if m else None
    m = re.search(r'(left|right) breast', t); f['side'] = m.group(1) if m else None
    m = re.search(r'histolog(?:y|ic type): ([^.;]+)', t); f['hist'] = m.group(1).strip() if m else None
    return f

EXTRACT = {'busbra': busbra_facts, 'breast': breast_facts, 'thyroid': thyroid_facts, 'fetal': fetal_facts}
# provisional severity weights per field (sum used to normalise)
WEIGHTS = {
    'busbra': dict(path=3, birads=2, side=2, hist=1),
    'breast': dict(path=3, birads=2, margin=2, calc=2, shape=1, echo=1, post=1, halo=1),
    'thyroid': dict(path=3, count=2, loc=2, size=1),
    'fetal': dict(hc=3),
}
FETAL_TOL_MM = 20.0   # numeric field: score falls linearly to 0 at 20 mm error
