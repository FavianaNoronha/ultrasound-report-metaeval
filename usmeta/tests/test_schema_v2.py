import json
from usmeta import schema_v2, graders

def run(tmp_path, report, reply, organ='breast'):
    cli = graders.LocalLLM('m', str(tmp_path), runner=lambda p: json.dumps(reply)); return schema_v2.extract_llm_v2(cli, report, organ)

def test_decimal_dropped_by_the_model_is_corrected_from_the_quote(tmp_path):
    rep = 'A hypoechoic mass measuring approximately 10.6 mm in diameter is present.'
    f, bad, opts, over = run(tmp_path, rep, {'size_mm': {'value': 106, 'quote': 'measuring approximately 10.6 mm in diameter'}})
    assert f['size_mm'] == 11 and over == 1                     # 10.6 mm, rounded to the nearest mm like v1

def test_cm_in_quote_gives_mm_and_agreeing_values_are_untouched(tmp_path):
    f, _, _, over = run(tmp_path, 'The mass is 1.2 cm wide.', {'size_mm': {'value': 12, 'quote': 'The mass is 1.2 cm wide.'}}); assert f['size_mm'] == 12 and over == 0
    f, _, _, over = run(tmp_path, 'The mass measures 3 cm x 2 cm.', {'size_mm': {'value': 3, 'quote': '3 cm x 2 cm'}}); assert f['size_mm'] == 30 and over == 1

def test_head_circumference_cm_to_mm_one_decimal(tmp_path):
    f, *_ = run(tmp_path, 'Head circumference 25.88 cm.', {'hc_mm': {'value': 25.88, 'quote': 'Head circumference 25.88 cm'}}, 'fetal'); assert f['hc_mm'] == 258.8

def test_option_list_copied_as_value_is_dropped_and_counted(tmp_path):
    rep = 'Some nodules appear solid while others appear cystic.'
    f, bad, opts, over = run(tmp_path, rep, {'comp': {'value': 'solid|cystic', 'quote': 'Some nodules appear solid'}, 'echo': {'value': 'hypoechoic', 'quote': 'x'}}, 'thyroid')
    assert 'comp' not in f and opts == 1 and bad == 1          # the echo quote is not in the report -> dropped as unquoted (v1 rule)

def test_boolean_lesion_maps_and_missing_quote_is_dropped(tmp_path):
    f, *_ = run(tmp_path, 'A mass is seen.', {'lesion': {'value': True, 'quote': 'A mass is seen'}, 'size_mm': {'value': 5, 'quote': None}})
    assert f['lesion'] == 'present' and 'size_mm' not in f

def test_looser_quote_rule_accepts_shortened_quotes_only_when_asked(tmp_path):
    rep = 'The mass measures approximately 2 cm in its greatest dimension.'
    reply = {'size_mm': {'value': 20, 'quote': 'mass measures 2 cm greatest dimension'}}
    f, bad, *_ = run(tmp_path, rep, reply); assert 'size_mm' not in f and bad == 1                       # exact rule (frozen default)
    cli = graders.LocalLLM('m', str(tmp_path / 'b'), runner=lambda p: json.dumps(reply))
    f, bad, *_ = schema_v2.extract_llm_v2(cli, rep, 'breast', quote_match='tokens80'); assert f['size_mm'] == 20 and bad == 0

def test_medgemma_box_parser_conventions_and_named_keys():
    from usmeta import medgemma_analysis as A
    raw = '```json\n[{"box_2d": [100, 200, 300, 400]}]\n```'
    assert A.mg_boxes(raw, 1000, 1000, 'yxyx1000') == [[200.0, 100.0, 400.0, 300.0]] and A.mg_boxes(raw, 1000, 1000, 'xyxy1000') == [[100.0, 200.0, 300.0, 400.0]]
    named = '[{"label": "x", "bounding_box": {"xmin": 100, "ymin": 200, "xmax": 300, "ymax": 400}}]'
    assert A.mg_boxes(named, 1000, 1000, 'xyxy1000') == [[100.0, 200.0, 300.0, 400.0]] and A.mg_boxes('no box here', 10, 10, 'xyxy1000') == []
