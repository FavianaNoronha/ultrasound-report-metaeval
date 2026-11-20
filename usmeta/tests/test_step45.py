"""Step 45 unit tests: deterministic gold check, number checker, strict schema of extractor v5 (no model call, no dataset)."""
from usmeta import step45_freetext as FT, step45_numchecker as NC, step45_extractor_v5 as V5

REF = "An irregular mass (wider than tall) with not circumscribed (indistinct) margins and heterogeneous echo pattern is seen in the upper central part of the image, measuring approximately 25 mm. Assessment: BI-RADS 4b. Pathology: malignant."

def test_gold_check_states_every_value():
    gold = {'lesion': 'present', 'count': 1, 'pos': 'upper-central', 'orient': 'wider than tall', 'size_mm': 25, 'shape': 'irregular', 'margin': 'not circumscribed (indistinct)', 'echo': 'heterogeneous', 'birads': '4b', 'path': 'malignant'}
    good = "Single irregular mass in the upper central part of the image, wider than tall, 25 mm, indistinct non-circumscribed margin, heterogeneous echo. BI-RADS 4b. Pathology: malignant."
    assert FT.gold_check('breast', gold, good)[0]
    ok, miss = FT.gold_check('breast', gold, good.replace('25 mm', '2.8 cm'))
    assert not ok and 'size_mm' in miss
    ok, miss = FT.gold_check('breast', gold, good.replace('4b', '4a'))
    assert not ok and 'birads' in miss

def test_number_checker_parse_and_score():
    assert NC.parse(REF, 'breast')['size_mm'] == 25.0 and NC.parse(REF, 'breast')['birads'] == '4b'
    assert NC.score(REF, "A single mass, about 2.5 cm. BI-RADS 4b.", 'breast') == 1.0                  # unit rewrite is harmless
    assert NC.score(REF, "A single mass, about 2.8 cm. BI-RADS 4b.", 'breast') < 1.0                    # 12% size change is flagged
    assert NC.score(REF, "A single mass, about 2.8 cm. BI-RADS 4b.", 'breast', tol_rel=0.15) == 1.0     # within the tolerance
    assert NC.score("Fetal head. HC 318.0 mm.", "Head circumference 31.9 cm.", 'fetal') < 1.0           # 1 mm off
    assert NC.score(REF, "A mass, about 25 mm. BI-RADS 3.", 'breast') < 1.0                              # category mismatch

def test_v5_strict_schema_and_regex_override():
    js = {"lesion_present": True, "count": 3, "side": "left", "size": {"value": 9, "unit": "cm"}, "birads": "2", "margin": "smooth", "halo": "present", "extra": 1}
    s = V5.strict('breast', js, "A single mass in the right breast, 25 mm, with an echogenic halo. BI-RADS 4b.")
    assert s['count'] == 1 and s['side'] == 'right' and s['size'] == {'value': 25.0, 'unit': 'mm'} and s['birads'] == '4b' and 'extra' not in s     # numbers, sides, counts, categories come from the text
    assert s['margin'] == 'circumscribed' and s['halo'] == 'yes'
    t = V5.strict('thyroid', {"count": 1, "tirads": "4", "birads": "4", "echo": "hypoechoic"}, "A nodule, BI-RADS 4, hypoechoic.")
    assert t['tirads'] is None and 'birads' not in t and t['echo'] == 'hypoechoic'                              # BI-RADS never becomes tirads
    f = V5.strict('fetal', {"plane": "trans-thalamic", "hc": None, "birads": "0"}, "Fetal head, trans-thalamic plane. HC 44.3 mm.")
    assert 'birads' not in f and f['plane'] == 'trans thalamic' and f['hc'] == {'value': 44.3, 'unit': 'mm'}
