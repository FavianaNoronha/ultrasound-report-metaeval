import json, os, re, random, pytest
from usmeta import templates_v2 as t

HAVE = os.path.exists(os.path.join(t.DATA, 'HC18.jsonl'))
pytestmark = pytest.mark.skipif(not HAVE, reason='local_data not built')

def nums(text): return [float(x) for x in re.findall(r'(?<![\w.])\d+(?:\.\d+)?(?![\w])', re.sub(r'BI-RADS \w+|TI-RADS \w+', '', text))]

def allowed(r):
    f = r['facts']; a = set()
    for k in ('size_mm', 'size_pct', 'hc_mm', 'count'):
        if k in f: a |= {float(f[k]), round(float(f[k]), 1)}
    a |= {1.0, 2.0, 3.0}   # lesion counts spelled as digits never occur; 'HC' etc. carry no digits
    return a

def test_every_number_in_text_matches_the_facts():
    random.seed(0)
    rows = [r for r in t.build()]; sample = random.sample(rows, 1500)
    for r in sample:
        for s, txt in r['styles'].items():
            for n in nums(txt): assert n in allowed(r), (r['case_id'], s, txt, r['facts'])

def test_all_styles_carry_same_numbers():
    for r in list(t.build())[:3000]:
        ns = {s: sorted(nums(x)) for s, x in r['styles'].items()}
        assert ns['terse'] == ns['standard'] == ns['long'], (r['case_id'], ns)

def test_hc18_ellipse_matches_csv_hc():
    errs = []
    for rec in t.load('HC18'):
        r = rec['region']; errs.append(abs(t.ramanujan(r['major_px'], r['minor_px']) * rec['pixel_mm'] - rec['labels']['hc_mm']))
    assert sum(errs) / len(errs) < 1.5, sum(errs) / len(errs)   # mean abs error in mm

def test_size_mm_is_mask_major_axis_times_pixel_size():
    for rec in t.load('BrEaST'):
        f = t.facts(rec)
        if 'size_mm' in f: assert f['size_mm'][0] == round(rec['region']['major_px'] * rec['pixel_mm'])

def test_thyroid_tn_has_no_diagnosis_class():
    for ds in ('TN3K', 'TN5000'):
        for rec in t.load(ds)[:200]:
            assert 'path' not in t.facts(rec) and 'class' not in ' '.join(t.render(t.facts(rec), 'thyroid', 'long').lower().split())

def test_no_invented_fields_for_datasets_without_labels():
    rec = t.load('BUSI')[0]; f = t.facts(rec)
    assert not ({'birads', 'margin', 'echo', 'calc', 'size_mm'} & set(f))

def test_bus_bra_single_is_not_stated_as_a_side():
    singles = [r for r in t.load('BUSBRA') if r['labels'].get('side') == 'single']
    assert singles and all('side' not in t.facts(r) and 'single breast' not in t.render(t.facts(r), 'breast', 'standard') for r in singles)
