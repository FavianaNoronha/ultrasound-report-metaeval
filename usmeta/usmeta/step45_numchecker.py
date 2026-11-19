"""Step 45, Part C (and the regex layer of Part B): deterministic number checker. NEW file, no model.
parse(text, organ) reads size (mm / cm / percent of the image width), head circumference, count, side and the BI-RADS / TI-RADS category from free or templated text.
compare(ref, cand, organ, tol) returns the mismatch of a candidate against the reference: relative size deviation, relative HC deviation, count / side / category mismatch, and a score in [0, 1] (1 = nothing differs).
Tolerance: relative size tolerance and absolute HC tolerance (mm), fixed on dev / val of set A so that at most 2% of harmless rewordings are flagged (see step45_numchecker_run)."""
import re

NUMW = {'one': 1, 'single': 1, 'solitary': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5}

def parse(text, organ):
    t = ' '.join(text.lower().split()); f = {}
    if organ == 'fetal':
        m = re.search(r'(?:head circumference|\bhc\b)[^0-9]{0,40}(\d+(?:\.\d+)?)\s*(mm|cm)', t) or re.search(r'(\d+(?:\.\d+)?)\s*(mm|cm)', t)
        if m: f['hc_mm'] = round(float(m.group(1)) * (10 if m.group(2) == 'cm' else 1), 1)
        return f
    m = re.search(r'(\d+(?:\.\d+)?)\s*(%|percent|per cent)', t)
    if m: f['size_pct'] = float(m.group(1))
    m = re.search(r'(\d+(?:\.\d+)?)\s*(mm|cm)\b', t)
    if m: f['size_mm'] = float(m.group(1)) * (10 if m.group(2) == 'cm' else 1)
    m = re.search(r'\b(two|three|four|five)\b (?:\w+ ){0,2}(?:lesions|nodules|masses)|\b(\d)\s+(?:lesions|nodules|masses)|three or more', t)
    if m: f['count'] = 3 if 'three or more' in m.group(0) else (NUMW.get(m.group(1)) if m.group(1) else int(m.group(2)))
    else:
        m = re.search(r'\b(single|solitary|one|1)\b', t)
        if m: f['count'] = 1
    m = re.search(r'\b(left|right)\b[ -](?:breast)?', t) if organ == 'breast' else None
    if m: f['side'] = m.group(1)
    m = re.search(r'bi-?rads\s*(?:category|assessment|classification|score)?\s*[:\-]?\s*(?:is |of |as )?(?:category )?([0-6][abc]?)\b', t)
    if m: f['birads'] = m.group(1)
    m = re.search(r'ti-?rads\s*(?:category|assessment|classification|score)?\s*[:\-]?\s*(?:is |of |as )?(?:category )?([1-5][abc]?)\b', t)
    if m: f['tirads'] = m.group(1)
    return f

def compare(ref, cand, organ):
    """deviations of the candidate numbers from the reference numbers (None where the reference or candidate does not state the quantity)"""
    r, c = parse(ref, organ), parse(cand, organ); d = {}
    if organ == 'fetal':
        if 'hc_mm' in r: d['hc_abs_mm'] = abs(c['hc_mm'] - r['hc_mm']) if 'hc_mm' in c else None
        return d
    for k in ('size_pct', 'size_mm'):
        if k in r: d[k + '_rel'] = (abs(c[k] - r[k]) / r[k]) if k in c and r[k] else None
    if 'size_pct' in r and 'size_pct' not in c and 'size_mm' in c: d['size_pct_rel'] = None
    for k in ('count', 'side', 'birads', 'tirads'):
        if k in r: d[k + '_mismatch'] = (c.get(k) != r[k]) if k in c else None
    return d

def score(ref, cand, organ, tol_rel=0.0, tol_hc=0.0):
    """1 - largest deviation: relative size / head-circumference deviation beyond the tolerance, or 1.0 for a count / side / category mismatch (capped at 1). 1.0 = nothing differs"""
    d = compare(ref, cand, organ); worst = 0.0
    for k, v in d.items():
        if v is None: continue
        if k.endswith('_rel'): worst = max(worst, 0.0 if v <= tol_rel else min(1.0, v))
        elif k == 'hc_abs_mm': worst = max(worst, 0.0 if v <= tol_hc else min(1.0, v / 10.0 + 0.1))
        elif k.endswith('_mismatch'): worst = max(worst, 1.0 if v else 0.0)
    return 1.0 - worst

def flagged(ref, cand, organ, tol_rel, tol_hc): return score(ref, cand, organ, tol_rel, tol_hc) < 1.0
