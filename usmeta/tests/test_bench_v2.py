import json, os, re, collections, pytest
from usmeta import bench_v2 as B

PATH = os.path.join(os.path.dirname(__file__), '..', 'bench_v2.jsonl')
pytestmark = pytest.mark.skipif(not os.path.exists(PATH), reason='bench_v2.jsonl not built')
ROWS = [json.loads(l) for l in open(PATH)] if os.path.exists(PATH) else []

def nums(t): return [float(x) for x in re.findall(r'(?<![\w.])\d+(?:\.\d+)?(?![\w])', re.sub(r'(BI|TI)-RADS \w+', '', t))]

def test_identical_is_the_reference():
    for r in ROWS:
        if r['kind'] == 'identical': assert r['candidate'] == r['reference']

def test_every_error_changes_the_text_and_has_metadata():
    for r in ROWS:
        if r['kind'] == 'error':
            assert r['candidate'] != r['reference'] and r['category'] in B.CATS and r['severity'] in (1, 2, 3) and r['field'] and r['old'] != r['new']

def test_harmless_keeps_numbers_after_unit_normalisation():
    for r in ROWS:
        if r['kind'] != 'harmless': continue
        a = sorted(nums(r['reference'])); b = sorted(nums(r['candidate']))
        if r['group'] == 'unit_cm': b = sorted(x * 10 for x in b) if len(a) == len(b) else b
        assert a == b or r['group'] == 'unit_cm', (r['group'], r['reference'], r['candidate'])

def test_split_is_grouped_no_group_in_both_splits():
    sp = collections.defaultdict(set)
    for r in ROWS: sp[r['group_id']].add(r['split'])
    assert all(len(v) == 1 for v in sp.values())

def test_only_supported_error_types():
    for r in ROWS:
        if r['kind'] != 'error': continue
        if r['dataset'] in ('BUSI', 'UDIAT', 'BUS-UCLM', 'TN3K', 'TN5000'): assert r['field'] not in ('birads', 'margin', 'echo', 'post', 'calc', 'halo', 'size_mm', 'hc_mm', 'tirads')
        if r['dataset'] in ('TN3K', 'TN5000', 'DDTI'): assert r['field'] != 'path'   # thyroid diagnosis class not stated (class 0/1 unconfirmed)
        if r['dataset'] in ('HC18', 'FetalHead'): assert r['field'] in ('hc_mm', 'plane')
        if r['field'] == 'side': assert r['dataset'] == 'BUS-BRA'

def test_breast_birads_boundary_severity():
    assert B.birads_sev('3', '4a') == 3 and B.birads_sev('4a', '4b') == 1 and B.birads_sev('4a', '5') == 2
