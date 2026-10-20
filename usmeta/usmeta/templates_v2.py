"""True reports v2: built ONLY from facts in the unified records (usmeta/local_data/*.jsonl). No LLM, nothing invented.

facts(rec) -> {field: (value, provenance)}   provenance: labelled (expert/dataset label) | measured (computed from a
mask/ellipse and a pixel size) | approximate (computed from a mask/box but with a caveat, or a rough proxy).
render(rec_or_facts, organ_kind, style) -> text, style in terse | standard | long.
Lexicon structure (sources and 'to confirm' marks in docs/templates_sources.md):
  breast  = ACR BI-RADS US lexicon (shape, orientation, margin, echo pattern, posterior features, calcifications, assessment)
  thyroid = ACR TI-RADS lexicon (composition, echogenicity, shape/orientation, margin, echogenic foci) -- TR level only where labelled
  fetal   = ISUOG-style biometry (head circumference in mm, plane)
"""
import json, math, os, re

STYLES = ('terse', 'standard', 'long')
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, '..', 'local_data')
NA = {'not applicable', 'not available', '', 'none', None}

def ramanujan(a_full, b_full):
    """circumference of an ellipse from FULL axis lengths"""
    a, b = a_full / 2, b_full / 2
    return math.pi * (3 * (a + b) - math.sqrt((3 * a + b) * (a + 3 * b)))

def _region(rec):
    r = rec.get('region')
    if not r: return {}
    f = {}
    f['count'] = (r['n'], 'measured')
    f['pos'] = (r['pos'], 'approximate')           # thirds of the image, not anatomical
    x0, y0, x1, y1 = r['box']
    f['orient'] = ('wider than tall' if (x1 - x0) >= (y1 - y0) else 'taller than wide', 'approximate')  # box proxy for orientation
    if rec.get('pixel_mm') and r['kind'] in ('mask', 'ellipse', 'outline'):
        f['size_mm'] = (round(r['major_px'] * rec['pixel_mm']), 'approximate' if rec['dataset'] == 'BrEaST' else 'measured')
    else:
        f['size_pct'] = (round(100 * max(x1 - x0, y1 - y0) / r['W']), 'measured')   # longest box side as % of image width
    return f

def _clean(v):
    v = str(v).strip().lower()
    return None if v in NA else v

def facts(rec):
    """ordered fact dict for one record; missing fields are simply absent"""
    L, d, ds, f = rec['labels'], rec['labels'].get('desc') or {}, rec['dataset'], {}
    if ds == 'HC18':
        f['hc_mm'] = (L['hc_mm'], 'labelled'); return f
    if ds == 'FetalHead':
        f['plane'] = (L['plane'].lower().replace('-', ' '), 'labelled')
        r = rec.get('region')
        if r and rec.get('pixel_mm'):
            f['hc_mm'] = (round(ramanujan(r['major_px'], r['minor_px']) * rec['pixel_mm'], 0), 'approximate')
        return f
    cls = L.get('cls')
    if rec['organ'] == 'breast':
        if cls == 'normal' or not rec.get('region'):
            f['lesion'] = ('absent', 'labelled' if cls == 'normal' else 'approximate')
            if cls == 'normal': f['path'] = ('normal', 'labelled')
            if L.get('birads') is not None and ds == 'BrEaST': f['birads'] = (str(L['birads']).lower(), 'labelled')
            return f
        f['lesion'] = ('present', 'measured')
        f.update(_region(rec))
        if ds == 'BrEaST':
            for k, kk in (('shape', 'shape'), ('margin', 'margin'), ('echo', 'echogenicity'), ('post', 'posterior_features'),
                          ('calc', 'calcifications'), ('halo', 'halo')):
                v = _clean(d.get(kk))
                if v is not None:
                    if k == 'margin': v = (lambda m: 'not circumscribed (' + m[1].replace('&', ', ') + ')' if m else v)(re.match(r'not circumscribed - (.*)', v))
                    f[k] = (v, 'labelled')
        if ds == 'BUS-BRA' and L.get('side'): f['side'] = (L['side'], 'labelled')
        if L.get('birads') is not None: f['birads'] = (str(L['birads']).lower(), 'labelled')
        if cls: f['path'] = (cls, 'labelled')
        if L.get('hist'): f['hist'] = (L['hist'], 'labelled')
        return f
    # thyroid (diagnosis class of TN3K/TN5000 deliberately NOT included: meaning of class 0/1 unconfirmed)
    if not rec.get('region'):
        f['lesion'] = ('absent', 'approximate'); return f
    f['lesion'] = ('present', 'measured'); f.update(_region(rec))
    if ds == 'DDTI':
        for k, kk in (('comp', 'composition'), ('echo', 'echogenicity'), ('margin', 'margins'), ('foci', 'calcifications')):
            v = _clean(d.get(kk))
            if v is None: continue
            if k == 'foci': v = 'none' if v == 'non' else v.rstrip('s') + 's'
            if k == 'margin': v = v.replace('ill- defined', 'ill defined')
            if k == 'echo': v = v.replace('echogenicity', 'echoic')
            f[k] = (v, 'labelled')
        if L.get('tirads') is not None: f['tirads'] = (str(L['tirads']).lower(), 'labelled')
    return f

# ---------------------------------------------------------------- rendering
def _size(f):
    if 'size_mm' in f:
        a = '' if f['size_mm'][1] == 'measured' else 'approximately '
        return f"{a}{f['size_mm'][0]:.0f} mm"
    if 'size_pct' in f: return f"about {f['size_pct'][0]}% of the image width"
    return None

def _v(f, k): return f[k][0] if k in f else None
def _s(x): return x[0].upper() + x[1:] if x else x
def _join(parts): return ' '.join(p for p in parts if p)

def render_breast(f, style):
    if _v(f, 'lesion') == 'absent':
        b = f" BI-RADS {f['birads'][0]}." if 'birads' in f else ''
        t = {'terse': 'No lesion.', 'standard': 'No focal lesion is seen.', 'long': 'The breast ultrasound image shows no focal lesion.'}[style]
        return t + b + (' Pathology: normal.' if _v(f, 'path') == 'normal' else '')
    sh, ori, mg, ec, po, ca, ha = (_v(f, k) for k in ('shape', 'orient', 'margin', 'echo', 'post', 'calc', 'halo'))
    sz, pos, side = _size(f), _v(f, 'pos'), _v(f, 'side')
    cnt = _v(f, 'count'); multi = cnt and cnt > 1
    postt = {'no': 'no posterior acoustic features', 'shadowing': 'posterior acoustic shadowing', 'enhancement': 'posterior acoustic enhancement',
             'combined': 'combined posterior features'}.get(po, po)
    calct = {'no': 'no calcifications'}.get(ca, f'calcifications ({ca})' if ca else None)
    halot = {'no': 'no echogenic halo', 'yes': 'an echogenic halo'}.get(ha)
    assess = f"BI-RADS {f['birads'][0]}" if 'birads' in f else None
    path = f"{f['path'][0]}" if 'path' in f else None
    hist = f"{f['hist'][0]}" if 'hist' in f else None
    where = ' '.join(x for x in (f'{side} breast,' if side else None, f'{pos.replace("-", " ")} part of the image' if pos else None) if x)
    if style == 'terse':
        a = ', '.join(x for x in [f'{sh} mass' if sh else 'mass', ori, f'{mg} margin' if mg else None, ec, postt, calct, halot,
                                  sz, where.rstrip(',') if where else None, f'{cnt} lesions' if multi else None] if x)
        return _join([a + '.', f'{assess}.' if assess else None, f'Pathology: {path}.' if path else None, f'Histology: {hist}.' if hist else None])
    if style == 'standard':
        s1 = f"A{'n' if (sh or ' ')[0] in 'aeiou' else ''} {sh + ' ' if sh else ''}mass{' (' + ori + ')' if ori else ''}"
        w = [x for x in [f'{mg} margins' if mg else None, f'{ec} echo pattern' if ec else None] if x]
        s1 += (' with ' + ' and '.join(w) if w else '') + (f' is seen in the {where}' if where else ' is seen') + (f', measuring {sz}' if sz else '') + '.'
        if multi: s1 += f' {cnt} lesions are identified.'
        s2 = _s(' and '.join(x for x in [postt, calct, halot] if x)) + '.' if any([postt, calct, halot]) else None
        return _join([s1, s2, f'Assessment: {assess}.' if assess else None, f'Pathology: {path}.' if path else None,
                      f'Histology: {hist}.' if hist else None])
    s1 = 'On breast ultrasound a mass is identified' + (f' in the {where}' if where else '') + '.'
    s2 = ('It is ' + ' and '.join(x for x in [sh, ori] if x) + (f', with {mg} margins' if mg else '') + (f' and a {ec} echo pattern' if ec else '') + '.') if (sh or ori or mg or ec) else None
    s3 = f'Its longest diameter is {sz}.' if sz else None
    s4 = ('Associated features: ' + '; '.join(x for x in [postt, calct, halot] if x) + '.') if any([postt, calct, halot]) else None
    return _join([s1, s2, s3, f'{cnt} lesions are identified in total.' if multi else None, s4,
                  f'Overall impression: {assess}.' if assess else None, f'Pathology: {path}.' if path else None, f'Histologic type: {hist}.' if hist else None])

def render_thyroid(f, style):
    if _v(f, 'lesion') == 'absent':
        return {'terse': 'No nodule.', 'standard': 'No focal nodule is seen.', 'long': 'The thyroid ultrasound image shows no focal nodule.'}[style]
    cnt = _v(f, 'count'); n = {1: 'a single nodule', 2: 'two nodules'}.get(cnt, 'three or more nodules')
    comp, ec, mg, fo, ori, pos, tr = (_v(f, k) for k in ('comp', 'echo', 'margin', 'foci', 'orient', 'pos', 'tirads'))
    sz = _size(f); where = f'{pos.replace("-", " ")} part of the image' if pos else None
    foc = None if fo is None else ('no echogenic foci' if fo == 'none' else f'echogenic foci ({fo})')
    trt = f'TI-RADS {tr}' if tr else None
    if style == 'terse':
        return _join([', '.join(x for x in [n, comp, ec, mg + ' margin' if mg else None, ori, foc, sz, where] if x) + '.', f'{trt}.' if trt else None])
    if style == 'standard':
        s1 = f'{_s(n)} is seen in the {where}' if where else f'{_s(n)} is seen'
        s1 += (f', measuring {sz}' if sz else '') + '.'
        d = [x for x in [comp and f'{comp} composition', ec and f'{ec} echotexture' if ec else None, mg and f'{mg} margins', ori, foc] if x]
        return _join([s1, (_s(', '.join(d)) + '.') if d else None, f'Assessment: {trt}.' if trt else None])
    s1 = 'On thyroid ultrasound ' + n + (' is' if cnt == 1 else ' are') + ' identified' + (f' in the {where}' if where else '') + '.'
    s2 = f'The longest dimension is {sz}.' if sz else None
    d = [x for x in [comp and f'composition {comp}', ec and f'echogenicity {ec}', mg and f'margins {mg}', ori and f'shape {ori}', foc] if x]
    return _join([s1, s2, ('Features: ' + '; '.join(d) + '.') if d else None, f'Overall impression: {trt}.' if trt else None])

def render_fetal(f, style):
    hc = _v(f, 'hc_mm'); pl = _v(f, 'plane')
    approx = 'approximately ' if 'hc_mm' in f and f['hc_mm'][1] == 'approximate' else ''
    if hc is None and pl is None: return {'terse': 'Fetal head.', 'standard': 'Fetal head.', 'long': 'Fetal head ultrasound.'}[style]
    h = None if hc is None else f'{hc:.1f}' if f['hc_mm'][1] == 'labelled' else f'{hc:.0f}'
    if style == 'terse': return _join([f'{pl.capitalize()} plane.' if pl else None, f'HC {approx}{h} mm.' if h else None])
    if style == 'standard': return _join([f'Fetal head, {pl} plane.' if pl else 'Fetal head.', f'Head circumference {approx}{h} mm.' if h else None])
    return _join([f'Fetal head ultrasound{", " + pl + " plane" if pl else ""}.', f'The head circumference measures {approx}{h} mm.' if h else None])

def render(f, organ, style):
    return {'breast': render_breast, 'thyroid': render_thyroid, 'fetal': render_fetal}[organ](f, style)

# ---------------------------------------------------------------- build
def load(ds): return [json.loads(l) for l in open(os.path.join(DATA, ds + '.jsonl'))]
DATASETS = ['BrEaST', 'BUSBRA', 'BUSI', 'UDIAT', 'BUSUCLM', 'TN3K', 'TN5000', 'DDTI', 'HC18', 'FetalHead']

def build(datasets=DATASETS):
    for ds in datasets:
        for rec in load(ds):
            f = facts(rec)
            yield dict(case_id=rec['case_id'], dataset=rec['dataset'], organ=rec['organ'], group_id=rec['group_id'],
                       facts={k: v[0] for k, v in f.items()}, provenance={k: v[1] for k, v in f.items()},
                       styles={s: render(f, rec['organ'], s) for s in STYLES})

if __name__ == '__main__':
    out = os.path.join(HERE, '..', 'true_reports_v2.jsonl'); n = 0
    with open(out, 'w') as fh:
        for r in build(): fh.write(json.dumps(r) + '\n'); n += 1
    print(n, 'true reports ->', out)
