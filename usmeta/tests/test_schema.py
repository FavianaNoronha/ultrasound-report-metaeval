import json, os, random, pytest
from usmeta import schema, graders

def test_finding_f1_identical_is_one_and_lazy_is_not():
    ref = 'An oval lesion (wider than tall) with circumscribed margins is seen in the upper central part of the image, measuring about 12 mm. Assessment: BI-RADS 3. Pathology: benign.'
    f = schema.to_findings(schema.extract_rule(ref, 'breast'), 'breast')
    assert schema.finding_scores(f, f)[2] == 1.0
    lazy = schema.to_findings(schema.extract_rule('No abnormality.', 'breast'), 'breast')
    assert schema.finding_scores(f, lazy)[2] == 0.0

def test_numeric_credit_is_graded_and_size_error_is_seen():
    assert schema.attr_credit('size_mm', 10, 10) == 1.0 and schema.attr_credit('size_mm', 10, 20) == 0.0 and 0 < schema.attr_credit('size_mm', 10, 12) < 1
    assert schema.attr_credit('hc_mm', 170.0, 173.0) == pytest.approx(0.85)

def test_missed_lesion_gets_zero_recall_and_precision():
    ref = schema.to_findings(schema.extract_rule('A single nodule is seen in the middle central part of the image, measuring about 20% of the image width.', 'thyroid'), 'thyroid')
    cand = schema.to_findings(schema.extract_rule('No focal nodule is seen.', 'thyroid'), 'thyroid')
    p, r, f1, _ = schema.finding_scores(ref, cand); assert (p, r, f1) == (0.0, 0.0, 0.0)

PATH = os.path.join(os.path.dirname(__file__), '..', 'true_reports_v2d.jsonl')
@pytest.mark.skipif(not os.path.exists(PATH), reason='true reports not built')
def test_rule_extractor_matches_labels_on_all_styles():
    rows = [json.loads(l) for l in open(PATH)]; random.seed(0); hit = tot = 0
    for r in random.sample(rows, 2000):
        for s, txt in r['styles'].items():
            ex = schema.extract_rule(txt, r['organ'])
            for k, v in r['facts'].items():
                tot += 1; hit += (k == 'hc_mm' and ex.get(k) is not None and abs(ex[k] - v) < 0.06) or str(ex.get(k)).lower() == str(v).lower() or (k == 'count' and v == 1)
    assert hit / tot > 0.98

def test_llm_extractor_keeps_only_quoted_values_and_normalises(tmp_path):
    rep = 'A mass is seen. No calcifications. Assessment: BI-RADS 4a.'
    reply = json.dumps({'lesion': {'value': 'present', 'quote': 'A mass is seen'}, 'calc': {'value': 'no calcifications', 'quote': 'No calcifications'}, 'birads': {'value': 'BI-RADS 4a', 'quote': 'BI-RADS 4a'},
                        'path': {'value': 'malignant', 'quote': 'malignant tumour'}})
    cli = graders.LocalLLM('m', str(tmp_path), runner=lambda p: reply)
    f, bad = schema.extract_llm(cli, rep, 'breast')
    assert f['calc'] == 'no' and f['birads'] == '4a' and 'path' not in f and bad == 1 and f['lesion'] == 'present'

def test_sentence_check_parsing_tolerates_trailing_commas_and_flags_length_mismatch():
    from usmeta import judge2
    txt = '```json\n{"candidate_supported": [true, false], "reference_covered": [true, true, true], "errors": [{"field": "x", "severity": "major", "category": "wrong measurement"},]}\n```'
    js = judge2.parse(txt, 2, 2); assert js is not None and js['len_mismatch'] is True
    s = judge2.scores_from(js); assert s['precision'] == 0.5 and s['recall'] == 1.0 and s['cats'] == ['wrong measurement'] and abs(s['judge'] - 0.7) < 1e-9
    assert judge2.parse('not json', 2, 2) is None
