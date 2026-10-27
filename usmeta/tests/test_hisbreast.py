"""Unit tests for the HiSBreast code. Synthetic example strings only: no real HiSBreast text, translation or exam id appears here.
The last tests also guard the repo: nothing from usmeta/local_data/hisbreast/ may be tracked by git."""
import json, os, subprocess, tempfile
import pytest
from usmeta import hisbreast, hisbreast_validate as V, hisbreast_parse as P, hisbreast_bench as B

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
LOCAL = os.path.abspath(hisbreast.OUT)

# ---- hisbreast.py
def test_hid_is_deterministic_salted_and_12_hex():
    a = hisbreast.hid('EX-0001'); assert a == hisbreast.hid('EX-0001') and a == hisbreast.hid(' EX-0001'.strip())
    assert len(a) == 12 and all(c in '0123456789abcdef' for c in a) and a != hisbreast.hid('EX-0002') and 'EX-0001' not in a

def test_clean_removes_br_and_collapses_space():
    assert hisbreast.clean('a<br/>b <br>  c\n d') == 'a b c d' and hisbreast.clean(None) == ''

def test_split_file_one_split_per_exam_and_ids_are_hashed():
    p = os.path.join(LOCAL, 'hisbreast_splits.jsonl')
    if not os.path.exists(p): pytest.skip('local HiSBreast data not present')
    R = [json.loads(l) for l in open(p)]; ids = [r['exam'] for r in R]
    assert len(ids) == len(set(ids)) and {r['split'] for r in R} <= {'dev', 'val', 'test'} and all(len(i) == 12 for i in ids)
    # the split key is the exam id: every exam of exams.jsonl has exactly one split and the same id always maps to the same split
    ex = {json.loads(l)['exam'] for l in open(os.path.join(LOCAL, 'exams.jsonl'))}
    assert ex == set(ids)

# ---- hisbreast_validate.py: key-fact extraction
def test_facts_numbers_cm_to_mm_and_percent():
    f = V.facts('Mass 1.5 cm and 8 mm.', 'en'); assert f['numbers'] == {8.0: 1, 15.0: 1}
    assert V.facts('Mass 1,2 cm', 'en')['numbers'] == {12.0: 1}          # decimal comma
    assert V.facts('Khối 15 mm', 'vi')['numbers'] == V.facts('Mass 1.5 cm', 'en')['numbers']

def test_facts_birads_codes_and_numbers_exclude_the_code():
    f = V.facts('BI-RADS 4a, mass 10 mm', 'en'); assert f['birads'] == ['4a'] and f['numbers'] == {10.0: 1}
    assert V.facts('BIRADS: 3', 'en')['birads'] == ['3'] and V.facts('No code here', 'en')['birads'] == []
    assert V.facts('BI-RADS loại 2', 'vi')['birads'] == ['2']

def test_facts_side_en_and_vi():
    assert V.facts('Right breast cyst', 'en')['side'] == ['R'] and V.facts('Left breast cyst', 'en')['side'] == ['L']
    assert V.facts('Bilateral cysts', 'en')['side'] == ['B'] and V.facts('Nang vú phải', 'vi')['side'] == ['R']
    assert V.facts('Hai bên', 'vi')['side'] == ['B'] and V.facts('trái', 'vi')['side'] == ['L'] and V.facts('Cyst', 'en')['side'] == []

def test_facts_negation_and_no_abnormality():
    f = V.facts('No abnormality recorded', 'en'); assert f['neg'] and f['noabn']
    g = V.facts('Mass in the right breast', 'en'); assert not g['neg'] and not g['noabn']
    h = V.facts('Không thấy bất thường', 'vi'); assert h['neg']

def test_facts_axillary_flag_and_concepts():
    assert V.facts('Enlarged axillary lymph node', 'en')['c_axillary'] and not V.facts('Mass', 'en')['c_axillary']
    assert V.facts('hạch nách to', 'vi')['c_axillary'] and V.facts('Cyst, follow up', 'en')['c_cyst'] and V.facts('Cyst, follow up', 'en')['c_followup']

def test_compare_separates_hard_and_soft_mismatches():
    a = V.facts('Right breast cyst, BI-RADS 2', 'en')
    assert V.compare(a, a) == ([], [])
    b = V.facts('Left breast cyst, BI-RADS 2', 'en'); assert V.compare(a, b)[0] == ['side']
    c = V.facts('Right breast cyst, BI-RADS 3', 'en'); assert V.compare(a, c)[0] == ['birads']
    d = V.facts('Right breast mass, BI-RADS 2', 'en'); h, s = V.compare(a, d); assert h == [] and 'c_cyst' in s and 'c_mass' in s

def test_degenerate_catches_cjk_and_runaway_length():
    assert V.degenerate('ngắn', 'mass 肿块') and V.degenerate('a b', ' '.join(['x'] * 20)) and not V.degenerate('a b c', 'one two three')
    assert V.strip_prefix('English: Cyst <end_of_turn>'.replace('<end_of_turn>', '')) == 'Cyst'

# ---- hisbreast_parse.py: parser fields
def test_parse_fields_english():
    p = P.parse('Right breast mass, BI-RADS 4a, axillary lymph node enlarged, biopsy recommended', 'en')
    assert p['side'] == 'right' and p['birads'] == '4a' and p['axillary'] and p['recommendation'] == 'biopsy' and p['finding'] == 'mass'
    q = P.parse('Bilateral cysts, BI-RADS 2 and BI-RADS 3', 'en'); assert q['side'] == 'both' and q['birads'] == '3' and q['finding'] == 'cyst' and q['birads_all'] == ['2', '3']

def test_parse_no_abnormality_and_unspecified_side():
    p = P.parse('No abnormality recorded', 'en'); assert p['finding'] == 'no_abnormality' and p['side'] == 'unspecified' and p['birads'] is None and not p['suspicious']
    assert P.parse('Suspicious for malignancy', 'en')['suspicious'] and P.parse('Follow up in 6 months', 'en')['recommendation'] == 'followup'

def test_parse_vietnamese_synthetic():
    p = P.parse('Nang vú phải, BI-RADS 2, theo dõi', 'vi'); assert p['side'] == 'right' and p['finding'] == 'cyst' and p['birads'] == '2' and p['recommendation'] == 'followup'

# ---- hisbreast_bench.py: planted-error generators
def errs(t): return {(e[0], e[1]): e for e in B.errors_for(t)}

def test_birads_plus_minus_one_and_3_to_4a_rule():
    E = [e for e in B.errors_for('Mass, BI-RADS 3') if e[0] == 'birads']; news = {e[4] for e in E}
    assert news == {'Mass, BI-RADS 2', 'Mass, BI-RADS 4A'}                       # 3 -> 4A (not 4) going up
    up = [e for e in E if e[4].endswith('4A')][0]; assert up[2] == 3 and up[3] == 1  # crossing the 3 / 4A line is the critical severity
    assert B.birads_sev(B.ORDER.index('2'), B.ORDER.index('3')) == 1 and B.birads_sev(B.ORDER.index('3'), B.ORDER.index('4a')) == 3 and B.birads_sev(B.ORDER.index('4a'), B.ORDER.index('4b')) == 1
    assert B.birads_sev(B.ORDER.index('1'), B.ORDER.index('4a')) == 3 and B.birads_sev(B.ORDER.index('4a'), B.ORDER.index('5')) == 2

def test_birads_edges_have_one_direction_only():
    assert {e[4] for e in B.errors_for('Cyst BI-RADS 1') if e[0] == 'birads'} == {'Cyst BI-RADS 2'}
    assert {e[4] for e in B.errors_for('Mass BI-RADS 6') if e[0] == 'birads'} == {'Mass BI-RADS 5'}
    assert {e[4] for e in B.errors_for('Mass BI-RADS 4B') if e[0] == 'birads'} == {'Mass BI-RADS 4A', 'Mass BI-RADS 4C'}

def test_side_swap_keeps_case_and_only_when_one_side_named():
    e = errs('Right breast cyst'); assert e[('side_swap', 'wrong location')][4] == 'Left breast cyst'
    assert errs('LEFT breast cyst')[('side_swap', 'wrong location')][4] == 'RIGHT breast cyst'
    assert not any(k[0] == 'side_swap' for k in errs('Right and left breast cysts')) and not any(k[0] == 'side_swap' for k in errs('Breast cyst'))

def test_negation_flip_both_directions():
    assert errs('No abnormality recorded')[('negation_flip', 'false finding')][4] == 'Mass seen'
    m = errs('Mass in right breast | Axillary node normal')[('negation_flip', 'missed finding')][4]
    assert m == 'No abnormality recorded | Axillary node normal'

def test_axillary_missed_and_invented():
    t = 'Cyst | Axillary lymph node enlarged'; assert errs(t)[('missed_axillary', 'missed finding')][4] == 'Cyst'
    assert errs('Cyst')[('invented_axillary', 'false finding')][4].endswith('| Axillary lymph node enlarged')

def test_size_doubled_and_recommendation_and_benign_swap():
    assert errs('Mass 10 mm')[('size_x2', 'wrong measurement')][4] == 'Mass 20 mm' and errs('Mass 1.5 cm')[('size_x2', 'wrong measurement')][3] == 2.0
    assert 'biopsy recommended' in errs('Cyst, follow up')[('recommendation', 'wrong severity/category')][4]
    assert 'suspicious for malignancy' in errs('Benign mass')[('benign_to_suspicious', 'wrong severity/category')][4]
    assert 'benign' in errs('Suspicious for malignancy')[('suspicious_to_benign', 'wrong severity/category')][4]

def test_every_error_differs_from_the_original_and_is_nonempty():
    for t in ['Right breast cyst, BI-RADS 2 | follow up', 'No abnormality recorded', 'Mass 12 mm, BI-RADS 4A, biopsy', 'Both sides']:
        for e in B.errors_for(t): assert e[4].strip() and e[4].strip().lower() != t.lower()

def test_harmless_variants_keep_the_facts():
    t = 'Right breast mass | BI-RADS 3 | follow up'
    H = {h[0]: h[2] for h in B.harmless_for(t)}
    assert set(H) >= {'reorder', 'form_sentence', 'form_bullet', 'synonym1'} and H['reorder'] == 'follow up | BI-RADS 3 | Right breast mass'
    for h in H.values(): assert V.facts(h, 'en')['birads'] == ['3'] and V.facts(h, 'en')['side'] == ['R']
    assert H['synonym1'] == 'Right breast lesion | BI-RADS 3 | follow up'

# ---- repo guard: nothing from local_data/hisbreast may be tracked by git
def _git(*a): return subprocess.run(['git', *a], cwd=ROOT, capture_output=True, text=True)

def test_no_local_hisbreast_file_is_tracked():
    r = _git('ls-files'); assert r.returncode == 0
    bad = [f for f in r.stdout.splitlines() if 'local_data' in f or f.lower().endswith('hisbreast.zip') or f.endswith('uncertain_cases.csv')]
    assert bad == []
    assert _git('check-ignore', '-q', 'local_data/hisbreast/exams.jsonl').returncode == 0   # the folder is git-ignored

def test_no_hisbreast_text_translation_or_exam_id_in_tracked_files():
    p = os.path.join(LOCAL, 'exams_translated.jsonl')
    if not os.path.exists(p): pytest.skip('local HiSBreast data not present')
    needles = set()
    for l in open(p):
        e = json.loads(l); needles.add(e['exam'])
        for k in ('vi', 'vi_clean', 'en'):
            v = (e.get(k) or '').strip()
            if len(v) >= 25: needles.add(v)
    for l in open(os.path.join(LOCAL, 'translations.jsonl')):
        for v in json.loads(l).values():
            if isinstance(v, str) and len(v.strip()) >= 25: needles.add(v.strip())
    assert needles
    with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False, encoding='utf-8') as fh:
        fh.write('\n'.join(sorted(n for n in needles if '\n' not in n)) + '\n'); pf = fh.name
    try:
        r = _git('grep', '-l', '-F', '-f', pf, '--', '.', ':!tests/test_hisbreast.py')
        assert r.returncode == 1 and r.stdout == '', 'HiSBreast text or exam id found in tracked files: ' + r.stdout[:300]
    finally: os.unlink(pf)
