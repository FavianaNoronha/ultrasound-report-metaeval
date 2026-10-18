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
