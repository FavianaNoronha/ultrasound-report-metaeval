import math
from usmeta import graders

def mk(tmp_path, replies):
    it = iter(replies); calls = []
    def runner(p): calls.append(p); return next(it)
    return graders.ClaudeJudge('x', cli=graders.ClaudeCLI('x', str(tmp_path), runner)), calls

def test_parse_score_and_cache(tmp_path):
    j, calls = mk(tmp_path, ['ok {"errors":[{"field":"birads","severity":"critical"}]}'])
    assert abs(j.score('a', 'b') - 0.4) < 1e-9
    assert abs(j.score('a', 'b') - 0.4) < 1e-9 and len(calls) == 1  # second call is cached

def test_retry_once_then_missing_not_zero(tmp_path):
    j, calls = mk(tmp_path, ['garbage', '{"errors":[]}', 'bad', 'worse'])
    assert j.score('a', 'b') == 1.0 and len(calls) == 2
    assert math.isnan(j.score('c', 'd')) and j.missing == 1

def test_local_judge_name_and_score(tmp_path):
    cli = graders.LocalLLM('org/gemma-x', str(tmp_path), runner=lambda p: '{"errors":[]}')
    j = graders.LocalJudge('org/gemma-x', cli=cli)
    assert j.name == 'llm_judge[local:gemma-x]' and j.score('a', 'b') == 1.0

def test_freetext_extractor_nulls(tmp_path):
    from usmeta import freetext
    cli = graders.LocalLLM('m', str(tmp_path), runner=lambda p: '{"hc": "null"}')
    assert freetext.extract_llm(cli, 'x', 'fetal') == {'hc': None}
