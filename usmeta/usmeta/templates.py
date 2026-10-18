"""Organ templates, perturbations (planted errors) and harmless rewordings.

Every item is one (reference, candidate) pair:
  kind          error | harmless | identical
  perturbation  what was changed (e.g. birads, margin, pathology, hc_mm)
  severity      1 minor, 2 major, 3 critical. PROVISIONAL: set by us, to be confirmed by a clinician.
  magnitude     size of the change where one exists (BI-RADS steps, mm)
  evidence      ground-truth facts from the dataset annotation (stand-in for what an image check should recover)
"""
import re, random

SEV_NOTE = "provisional (author-assigned); needs clinician confirmation"

# ----------------------------------------------------------------- BREAST (BrEaST-style labels)
POST = {'no': 'no posterior acoustic features', 'shadowing': 'posterior acoustic shadowing',
        'enhancement': 'posterior acoustic enhancement', 'combined': 'combined posterior features'}
BIRADS_ORDER = {'2': 0, '3': 1, '4a': 2, '4b': 3, '4c': 4, '5': 5}
BENIGN_SIDE = {'2', '3'}

def _clean(v): return str(v).strip().lower()

def breast_record(r):
    m = _clean(r['Margin']).replace('not circumscribed - ', 'non-circumscribed, ').replace('&', ' and ')
    return dict(shape=_clean(r['Shape']), margin=m, echo=_clean(r['Echogenicity']),
                post=_clean(r['Posterior_features']), calc=_clean(r['Calcifications']),
                halo=_clean(r['Halo']), birads=_clean(r['BIRADS']), path=_clean(r['Classification']))

def _calc(c): return 'no calcifications' if c == 'no' else f'calcifications ({c})'
def _halo(h): return 'with an echogenic halo' if h == 'yes' else 'without a halo'

def breast_std(d):
    return (f"A {d['shape']} mass is seen with {d['margin']} margins and {d['echo']} echotexture. "
            f"There are {POST.get(d['post'], d['post'])}, {_calc(d['calc'])}, and the mass is {_halo(d['halo'])}. "
            f"Assessment: BI-RADS {d['birads']}. Pathology: {d['path']}.")

def breast_mild(t):
    for a, b in [('is seen with', 'is identified with'), ('margins', 'borders'), ('echotexture', 'echogenicity'),
                 ('There are', 'Also noted:'), ('and the mass is', 'while the mass is'),
                 ('Assessment:', 'Impression:'), ('without a halo', 'lacking a halo')]:
        t = t.replace(a, b)
    return t

def breast_strong(d):
    return (f"Pathology: {d['path']}. Assessment is BI-RADS {d['birads']}. The lesion appears {d['shape']} in contour, "
            f"its borders being {d['margin']}, and internally {d['echo']}. Regarding secondary findings: "
            f"{_halo(d['halo'])}; {_calc(d['calc'])}; {POST.get(d['post'], d['post'])} behind the lesion.")

_SWAP = {'shape': {'irregular': 'oval', 'oval': 'irregular', 'round': 'irregular'},
         'echo': {'hypoechoic': 'hyperechoic', 'hyperechoic': 'hypoechoic', 'anechoic': 'hyperechoic',
                  'isoechoic': 'hypoechoic', 'heterogeneous': 'anechoic', 'complex cystic/solid': 'anechoic'},
         'post': {'no': 'shadowing', 'shadowing': 'enhancement', 'enhancement': 'shadowing', 'combined': 'no'},
         'halo': {'yes': 'no', 'no': 'yes'}}
BREAST_FIELD_SEV = dict(path=3, birads=2, margin=2, calc=2, shape=1, echo=1, post=1, halo=1)

def breast_errors(d):
    """yield (perturbation, magnitude, severity, erroneous_record)"""
    out = []
    e = dict(d); e['path'] = {'benign': 'malignant', 'malignant': 'benign'}.get(d['path'], d['path'])
    if e != d: out.append(('pathology', None, 3, e))
    if d['birads'] in BIRADS_ORDER:
        for b in BIRADS_ORDER:
            if b == d['birads']: continue
            e = dict(d); e['birads'] = b
            mag = abs(BIRADS_ORDER[b] - BIRADS_ORDER[d['birads']])
            cross = (d['birads'] in BENIGN_SIDE) != (b in BENIGN_SIDE)
            sev = 3 if cross and mag >= 2 else 2 if cross or mag >= 2 else 1
            out.append(('birads', mag, sev, e))
    e = dict(d); e['margin'] = 'circumscribed' if d['margin'] != 'circumscribed' else 'non-circumscribed, spiculated and indistinct'
    out.append(('margin', None, 2, e))
    e = dict(d); e['calc'] = 'in a mass' if d['calc'] == 'no' else 'no'
    out.append(('calcifications', None, 2, e))
    for k, name in (('shape', 'shape'), ('echo', 'echogenicity'), ('post', 'posterior_features'), ('halo', 'halo')):
        e = dict(d); e[k] = _SWAP[k].get(d[k], d[k])
        if e != d: out.append((name, None, 1, e))
    return out

# ----------------------------------------------------------------- THYROID (nodule size/location/count/pathology)
CNT = {1: 'a single nodule', 2: 'two nodules'}
def _cnt(n): return CNT.get(n, 'three or more nodules')

def thyroid_std(r):
    return (f"The largest nodule is {r['size']} relative to the image and lies in the {r['loc']} part of the image. "
            f"The scan shows {_cnt(r['count'])} in total. Pathology: {r['path']}.")

def thyroid_mild(t):
    for a, b in [('The largest nodule', 'The biggest nodule'), ('lies in', 'is located in'),
                 ('part of the image', 'area of the image'), ('The scan shows', 'The scan contains'),
                 ('Pathology:', 'Pathology label:')]:
        t = t.replace(a, b)
    return t

def thyroid_strong(r):
    return (f"Pathology label: {r['path']}. In total the scan contains {_cnt(r['count'])}; the biggest one, "
            f"{r['size']} compared with the image, is located in the {r['loc']} area.")

def thyroid_errors(r):
    out = []
    e = dict(r); e['path'] = {'benign': 'malignant', 'malignant': 'benign', 'class 0': 'class 1', 'class 1': 'class 0'}[r['path']]
    out.append(('pathology', None, 3, e))
    e = dict(r); e['count'] = {1: 2, 2: 1}.get(r['count'], 1); out.append(('count', None, 2, e))
    v, h = r['loc'].split('-'); e = dict(r); e['loc'] = v + '-' + {'left': 'right', 'right': 'left', 'central': 'right'}[h]
    out.append(('location', None, 2, e))
    e = dict(r); e['size'] = {'small': 'large', 'medium': 'large', 'large': 'small'}[r['size']]; out.append(('size', None, 1, e))
    return out

# ----------------------------------------------------------------- FETAL (HC18 head circumference, numeric)
def fetal_std(r):
    return f"The fetal head circumference measures {r['hc']:.1f} mm at an image scale of {r['px']:.3f} mm per pixel."
def fetal_mild(t): return t.replace('measures', 'is').replace('at an image scale of', 'with a scale of')
def fetal_unit(r):
    return f"The fetal head circumference measures {r['hc']/10:.2f} cm at an image scale of {r['px']:.3f} mm per pixel."
def fetal_strong(r):
    return f"Image scale is {r['px']:.3f} mm per pixel, and the head circumference comes to {r['hc']:.1f} millimetres."
FETAL_MM = [1, 2, 5, 10, 20, 40]
def fetal_sev(mm): return 1 if mm <= 2 else 2 if mm <= 10 else 3
def fetal_errors(r, rng):
    out = []
    for mm in FETAL_MM:
        e = dict(r); e['hc'] = max(1.0, r['hc'] + mm * rng.choice([-1, 1])); out.append(('hc_mm', mm, fetal_sev(mm), e))
    return out

# ----------------------------------------------------------------- BREAST, BUS-BRA labels (BI-RADS, histology, pathology, side)
BB_ORDER = {'2': 0, '3': 1, '4': 2, '5': 3}
def busbra_std(d):
    return (f"A breast mass is seen in the {d['side']} breast. Assessment: BI-RADS {d['birads']}. "
            f"Pathology: {d['path']}. Histology: {d['hist']}.")
def busbra_mild(t):
    for a, b in [('is seen in', 'is identified in'), ('Assessment:', 'Impression:'), ('Histology:', 'Histologic type:')]:
        t = t.replace(a, b)
    return t
def busbra_strong(d):
    return (f"Pathology: {d['path']}; histology: {d['hist']}. Impression is BI-RADS {d['birads']} "
            f"for the lesion in the {d['side']} breast.")
def busbra_errors(d, hist_pool, rng):
    out = []
    e = dict(d); e['path'] = 'malignant' if d['path'] == 'benign' else 'benign'; out.append(('pathology', None, 3, e))
    for b in BB_ORDER:
        if b == d['birads']: continue
        e = dict(d); e['birads'] = b; mag = abs(BB_ORDER[b] - BB_ORDER[d['birads']])
        cross = (d['birads'] in BENIGN_SIDE) != (b in BENIGN_SIDE)
        out.append(('birads', mag, 3 if cross and mag >= 2 else 2 if cross or mag >= 2 else 1, e))
    e = dict(d); e['side'] = 'right' if d['side'] == 'left' else 'left'; out.append(('side', None, 2, e))
    alt = [h for h in hist_pool[d['path']] if h != d['hist']]
    if alt:
        e = dict(d); e['hist'] = rng.choice(alt); out.append(('histology_same_class', None, 1, e))
    return out

# ----------------------------------------------------------------- builders
def _item(organ, ds, case, kind, pert, mag, sev, ref, cand, evidence, image=None):
    return dict(organ=organ, dataset=ds, case_id=case, image=image, kind=kind, perturbation=pert,
                magnitude=mag, severity=sev, reference=ref, candidate=cand, evidence=evidence)

def build_breast(df, seed=0, ds='BrEaST'):
    items = []
    df = df[df['Classification'].astype(str).str.lower() != 'normal']
    for _, r in df.iterrows():
        d = breast_record(r); ref = breast_std(d); case = f"{ds}-{r['CaseID']}"; img = r.get('Image_filename')
        ev = dict(d)
        items.append(_item('breast', ds, case, 'identical', 'none', None, 0, ref, ref, ev, img))
        items.append(_item('breast', ds, case, 'harmless', 'mild_paraphrase', None, 0, ref, breast_mild(ref), ev, img))
        items.append(_item('breast', ds, case, 'harmless', 'strong_rewrite', None, 0, ref, breast_strong(d), ev, img))
        for pert, mag, sev, e in breast_errors(d):
            items.append(_item('breast', ds, case, 'error', pert, mag, sev, ref, breast_std(e), ev, img))
    return items

def build_thyroid(recs, seed=0, n=None):
    rng = random.Random(seed); recs = list(recs)
    if n and len(recs) > n: recs = rng.sample(recs, n)
    import numpy as np
    q1, q2 = np.quantile([r['ratio'] for r in recs], [1/3, 2/3])
    items = []
    for i, r in enumerate(recs):
        r = dict(r); r['size'] = 'small' if r['ratio'] < q1 else 'medium' if r['ratio'] < q2 else 'large'
        ref = thyroid_std(r); ds = r.get('ds', 'thyroid'); case = f"{ds}-{r.get('split','')}{r.get('file', i)}"
        ev = dict(path=r['path'], count=r['count'], loc=r['loc'], size=r['size'])
        items.append(_item('thyroid', ds, case, 'identical', 'none', None, 0, ref, ref, ev, r.get('file')))
        items.append(_item('thyroid', ds, case, 'harmless', 'mild_paraphrase', None, 0, ref, thyroid_mild(ref), ev, r.get('file')))
        items.append(_item('thyroid', ds, case, 'harmless', 'strong_rewrite', None, 0, ref, thyroid_strong(r), ev, r.get('file')))
        for pert, mag, sev, e in thyroid_errors(r):
            items.append(_item('thyroid', ds, case, 'error', pert, mag, sev, ref, thyroid_std(e), ev, r.get('file')))
    return items

def build_fetal(rows, seed=0, n=None, ds='HC18'):
    """rows: list of dict(file, px, hc)"""
    rng = random.Random(seed); rows = list(rows)
    if n and len(rows) > n: rows = rng.sample(rows, n)
    items = []
    for r in rows:
        ref = fetal_std(r); case = f"{ds}-{r['file']}"; ev = dict(hc=r['hc'], px=r['px'])
        items.append(_item('fetal', ds, case, 'identical', 'none', None, 0, ref, ref, ev, r['file']))
        items.append(_item('fetal', ds, case, 'harmless', 'mild_paraphrase', None, 0, ref, fetal_mild(ref), ev, r['file']))
        items.append(_item('fetal', ds, case, 'harmless', 'unit_rewrite', None, 0, ref, fetal_unit(r), ev, r['file']))
        items.append(_item('fetal', ds, case, 'harmless', 'strong_rewrite', None, 0, ref, fetal_strong(r), ev, r['file']))
        for pert, mag, sev, e in fetal_errors(r, rng):
            items.append(_item('fetal', ds, case, 'error', pert, mag, sev, ref, fetal_std(e), ev, r['file']))
    return items


def build_busbra(df, seed=0, n=None, ds='BUS-BRA'):
    """df: BUS-BRA bus_data.csv. Keeps left/right images (drops the 'single' side rows)."""
    rng = random.Random(seed); df = df[df['Side'].isin(['left', 'right'])]
    rows = [dict(file=r['ID'], side=r['Side'], birads=str(r['BIRADS']), path=str(r['Pathology']).lower(),
                 hist=str(r['Histology']).lower()) for _, r in df.iterrows()]
    if n and len(rows) > n: rows = rng.sample(rows, n)
    pool = {}
    for r in rows: pool.setdefault(r['path'], set()).add(r['hist'])
    pool = {k: sorted(v) for k, v in pool.items()}
    items = []
    for r in rows:
        d = {k: r[k] for k in ('side', 'birads', 'path', 'hist')}; ref = busbra_std(d); case = f"{ds}-{r['file']}"
        def it(kind, pert, mag, sev, cand): 
            x = _item('breast', ds, case, kind, pert, mag, sev, ref, cand, dict(d), r['file']); x['ftype'] = 'busbra'; return x
        items.append(it('identical', 'none', None, 0, ref))
        items.append(it('harmless', 'mild_paraphrase', None, 0, busbra_mild(ref)))
        items.append(it('harmless', 'strong_rewrite', None, 0, busbra_strong(d)))
        for pert, mag, sev, e in busbra_errors(d, pool, rng): items.append(it('error', pert, mag, sev, busbra_std(e)))
    return items
