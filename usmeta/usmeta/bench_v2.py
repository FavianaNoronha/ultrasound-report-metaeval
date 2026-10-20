"""bench_v2: planted single errors, harmless rewordings and identical copies built on top of true_reports_v2 (templates_v2).

Reference = the 'standard' style text. Candidates:
  identical                       the reference itself
  harmless  (primary)             terse / long style variants, sentence reorder, synonyms, unit rewrite (mm <-> cm)
  harmless  (secondary, primary=False)  negation rewording, hedging prefix, padding (+1 / +3 neutral sentences)
  error                           ONE changed fact, re-rendered from the facts (so the text stays fluent), with category, field,
                                  old/new value, magnitude and PROVISIONAL severity (guideline-based, pending clinician ranking)
Only error types a record's facts support are generated. Split (dev/test, 30/70) is by group_id (patient / exam) or, where the
dataset has none, by case id (stand-in; flagged in group_source).
"""
import copy, hashlib, json, os, random, re, sys
from . import templates_v2 as T

SEV_NOTE = 'provisional, guideline-based, pending clinician ranking'
BIRADS = ['1', '2', '3', '4a', '4b', '4c', '5']
CATS = ('false finding', 'missed finding', 'wrong location', 'wrong severity/category', 'wrong measurement')

def _set(f, k, v, prov=None): g = dict(f); g[k] = (v, prov or (f[k][1] if k in f else 'labelled')); return g
def _drop(f, *ks): return {k: v for k, v in f.items() if k not in ks}
def _val(f, k): return f[k][0] if k in f else None

def birads_sev(a, b):
    ia, ib = BIRADS.index(a), BIRADS.index(b); cross = (ia <= 2) != (ib <= 2)   # crosses the biopsy line (<=3 vs >=4a)
    return 3 if cross else (2 if abs(ia - ib) >= 2 else 1)

def size_sev(r): return 2 if r in (0.5, 2.0) else 1

def errors(rec, f):
    """yield (category, field, old, new, magnitude, severity, modified_facts)"""
    organ, ds, out = rec['organ'], rec['dataset'], []
    def add(cat, field, old, new, mag, sev, g): out.append((cat, field, old, new, mag, sev, g))
    if organ == 'fetal':
        if 'hc_mm' in f:
            hc = _val(f, 'hc_mm')
            for d, s in ((3, 1), (10, 2), (-10, 2), (30, 3)):
                add('wrong measurement', 'hc_mm', hc, round(hc + d, 1), d, s, _set(f, 'hc_mm', round(hc + d, 1)))
        if 'plane' in f:
            others = [p for p in ('trans thalamic', 'trans cerebellum', 'trans ventricular') if p != _val(f, 'plane')]
            add('wrong severity/category', 'plane', _val(f, 'plane'), others[0], None, 2, _set(f, 'plane', others[0]))
        return out
    if _val(f, 'lesion') == 'absent':
        g = {'lesion': ('present', 'labelled')}
        add('false finding', 'lesion', 'absent', 'present', None, 3, g); return out
    add('missed finding', 'lesion', 'present', 'absent', None, 3, {'lesion': ('absent', 'labelled'), **({'birads': f['birads']} if False else {})})
    if _val(f, 'count') == 1: add('false finding', 'count', 1, 2, 1, 2, _set(f, 'count', 2))
    for k, uk in (('size_mm', 'size_mm'), ('size_pct', 'size_pct')):
        if k in f:
            for r in (0.5, 1.5, 2.0):
                new = round(_val(f, k) * r); new = min(new, 100) if k == 'size_pct' else new
                if new != _val(f, k): add('wrong measurement', k, _val(f, k), new, r, size_sev(r), _set(f, k, new))
    if 'pos' in f:
        v, h = _val(f, 'pos').split('-'); mirror = {'left': 'right', 'right': 'left', 'central': 'central'}
        flip = {'upper': 'lower', 'lower': 'upper', 'middle': 'middle'}
        for new in {f'{v}-{mirror[h]}', f'{flip[v]}-{h}'} - {_val(f, 'pos')}:
            add('wrong location', 'pos', _val(f, 'pos'), new, None, 1, _set(f, 'pos', new))
    if 'side' in f:
        new = 'right' if _val(f, 'side') == 'left' else 'left'; add('wrong location', 'side', _val(f, 'side'), new, None, 3, _set(f, 'side', new))
    if 'orient' in f:
        new = 'taller than wide' if _val(f, 'orient') == 'wider than tall' else 'wider than tall'
        add('wrong severity/category', 'orient', _val(f, 'orient'), new, None, 2 if ds == 'DDTI' else 1, _set(f, 'orient', new))
    if organ == 'breast':
        if _val(f, 'path') in ('benign', 'malignant'):
            new = 'malignant' if f['path'][0] == 'benign' else 'benign'; add('wrong severity/category', 'path', f['path'][0], new, None, 3, _set(f, 'path', new))
        if _val(f, 'birads') in BIRADS:
            for d in (1, -1, 2, -2):
                i = BIRADS.index(f['birads'][0]) + d
                if 1 <= i < len(BIRADS):   # BI-RADS 1 reserved for normal studies
                    add('wrong severity/category', 'birads', f['birads'][0], BIRADS[i], abs(d), birads_sev(f['birads'][0], BIRADS[i]), _set(f, 'birads', BIRADS[i]))
        if _val(f, 'shape') in ('oval', 'round', 'irregular'):
            new = 'oval' if f['shape'][0] == 'irregular' else 'irregular'; add('wrong severity/category', 'shape', f['shape'][0], new, None, 2, _set(f, 'shape', new))
        if 'margin' in f:
            circ = f['margin'][0] == 'circumscribed'; new = 'not circumscribed (spiculated)' if circ else 'circumscribed'
            add('wrong severity/category', 'margin', f['margin'][0], new, None, 2, _set(f, 'margin', new))
        if _val(f, 'echo') in ('hypoechoic', 'hyperechoic'):
            new = 'hyperechoic' if f['echo'][0] == 'hypoechoic' else 'hypoechoic'; add('wrong severity/category', 'echo', f['echo'][0], new, None, 1, _set(f, 'echo', new))
        if _val(f, 'post') in ('shadowing', 'enhancement'):
            new = 'enhancement' if f['post'][0] == 'shadowing' else 'shadowing'; add('wrong severity/category', 'post', f['post'][0], new, None, 1, _set(f, 'post', new))
        if _val(f, 'halo') == 'no': add('false finding', 'halo', 'no', 'yes', None, 1, _set(f, 'halo', 'yes'))
        if _val(f, 'halo') == 'yes': add('missed finding', 'halo', 'yes', 'no', None, 1, _set(f, 'halo', 'no'))
        if _val(f, 'calc') == 'no': add('false finding', 'calc', 'no', 'in a mass', None, 2, _set(f, 'calc', 'in a mass'))
        elif _val(f, 'calc'): add('missed finding', 'calc', f['calc'][0], 'no', None, 2, _set(f, 'calc', 'no'))
        if 'hist' in f and rec['dataset'] in HIST:
            new = next(h for h in HIST[rec['dataset']] if h != f['hist'][0]); add('wrong severity/category', 'hist', f['hist'][0], new, None, 2, _set(f, 'hist', new))
    else:  # thyroid (DDTI descriptors)
        sw = {'comp': {'solid': 'cystic', 'cystic': 'solid', 'predominantly solid': 'predominantly cystic', 'predominantly cystic': 'predominantly solid', 'spongiform': 'solid', 'dense': 'cystic'},
              'echo': {'hypoechoic': 'hyperechoic', 'hyperechoic': 'hypoechoic', 'isoechoic': 'hypoechoic', 'marked hypoechoic': 'hyperechoic'},
              'margin': {'well defined': 'spiculated', 'well defined smooth': 'spiculated', 'ill defined': 'well defined', 'microlobulated': 'well defined',
                         'spiculated': 'well defined', 'macrolobulated': 'spiculated'}}
        for k, m in sw.items():
            if _val(f, k) in m: add('wrong severity/category', k, f[k][0], m[f[k][0]], None, 2, _set(f, k, m[f[k][0]]))
        if _val(f, 'foci') == 'none': add('false finding', 'foci', 'none', 'microcalcifications', None, 2, _set(f, 'foci', 'microcalcifications'))
        elif _val(f, 'foci'): add('missed finding', 'foci', f['foci'][0], 'none', None, 2, _set(f, 'foci', 'none'))
        TI = ['2', '3', '4a', '4b', '4c', '5']
        if _val(f, 'tirads') in TI:
            for d in (1, -1, 2, -2):
                i = TI.index(f['tirads'][0]) + d
                if 0 <= i < len(TI):
                    cross = (TI.index(f['tirads'][0]) <= 1) != (i <= 1)
                    add('wrong severity/category', 'tirads', f['tirads'][0], TI[i], abs(d), 3 if cross else (2 if abs(d) >= 2 else 1), _set(f, 'tirads', TI[i]))
    return out

HIST = {}

# ---------------------------------------------------------------- harmless rewordings
SYN = [('mass', 'lesion'), ('margins', 'borders'), ('echo pattern', 'echogenicity'), ('Assessment:', 'Impression:'), ('is seen', 'is demonstrated'),
       ('is identified', 'is demonstrated'), ('measuring', 'with a size of'), ('Head circumference', 'Cranial circumference'), ('nodule', 'lesion')]
def synonyms(t):
    for a, b in SYN: t = t.replace(a, b)
    return t
def reorder(t):
    s = [x.strip() for x in re.split(r'(?<=\.)\s+', t) if x.strip()]
    return ' '.join(s[::-1]) if len(s) > 1 else t
def units(t):
    return re.sub(r'(\d+(?:\.\d+)?) mm', lambda m: f'{float(m[1]) / 10:g} cm', t)
def negation(t):
    t = t.replace('no calcifications', 'calcifications are absent').replace('no echogenic halo', 'an echogenic halo is absent')
    return t.replace('no posterior acoustic features', 'posterior acoustic features are absent').replace('No focal lesion is seen', 'A focal lesion is not seen')
def hedge(t): return 'The findings appear to be as follows. ' + t
PAD = ['Please correlate with clinical findings.', 'This report describes the ultrasound image provided.', 'Findings are listed below.']
def pad(t, n): return ' '.join(PAD[:n] + [t]) if n == 1 else t + ' ' + ' '.join(PAD[:n])

def harmless(rec, ref):
    s = rec['styles']; out = [('style_terse', s['terse'], True), ('style_long', s['long'], True), ('reorder', reorder(ref), True), ('synonyms', synonyms(ref), True)]
    if ' mm' in ref: out.append(('unit_cm', units(ref), True))
    n = negation(ref)
    if n != ref: out.append(('negation', n, False))
    out += [('hedge', hedge(ref), False), ('pad1', pad(ref, 1), False), ('pad3', pad(ref, 3), False)]
    return [(g, t, p) for g, t, p in out if t != ref]

# ---------------------------------------------------------------- build
def split_of(gid): return 'dev' if int(hashlib.md5(gid.encode()).hexdigest(), 16) % 10 < 3 else 'test'

def build(per_dataset=150, seed=0, datasets=T.DATASETS, keep_all=('BrEaST',)):
    global HIST
    rng = random.Random(seed); out = []; counts = {}
    for ds in datasets:
        recs = T.load(ds); tr = {r['case_id']: r for r in T.build([ds])}
        if ds in ('BUSBRA', 'UDIAT'): HIST[recs[0]['dataset']] = sorted({r['labels'].get('hist') for r in recs if r['labels'].get('hist')} - {None})[:12]
        groups = {}
        for r in recs: groups.setdefault(r['group_id'] or r['case_id'], []).append(r)
        keys = sorted(groups); rng.shuffle(keys); chosen = []
        for k in keys:
            chosen += groups[k]
            if ds not in keep_all and len(chosen) >= per_dataset: break
        counts[ds] = len(chosen)
        for rec in chosen:
            t = tr[rec['case_id']]; f = T.facts(rec); ref = t['styles']['standard']; gid = rec['group_id'] or rec['case_id']
            base = dict(case_id=rec['case_id'], dataset=rec['dataset'], organ=rec['organ'], group_id=gid, group_source='record' if rec['group_id'] else 'case id (stand-in)',
                        split=split_of(gid), reference=ref)
            n = 0
            def emit(**kw):
                nonlocal n; out.append(dict(base, id=f"{rec['case_id']}#{n}", **kw)); n += 1
            emit(kind='identical', category=None, field=None, group='identical', primary=True, magnitude=None, severity=0, candidate=ref)
            for g, txt, prim in harmless(t, ref): emit(kind='harmless', category=None, field=None, group=g, primary=prim, magnitude=None, severity=0, candidate=txt)
            for cat, field, old, new, mag, sev, g in errors(rec, f):
                txt = T.render(g, rec['organ'], 'standard')
                if txt == ref: continue
                emit(kind='error', category=cat, field=field, group='error', primary=True, magnitude=mag, severity=sev, old=old, new=new,
                     candidate=txt, severity_note=SEV_NOTE)
    return out, counts

if __name__ == '__main__':
    rows, counts = build(); path = os.path.join(T.HERE, '..', 'bench_v2.jsonl')
    open(path, 'w').write(''.join(json.dumps(r) + '\n' for r in rows)); print(len(rows), counts)
