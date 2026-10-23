import json, os, collections, pytest
from usmeta import splits

pytestmark = pytest.mark.skipif(not os.path.exists(splits.SPLITS), reason='splits not built')

def rows(): return [json.loads(l) for l in open(splits.SPLITS)]

def test_no_group_spans_two_splits_and_every_case_once():
    R = rows(); g = collections.defaultdict(set)
    for r in R: g[r['group_id']].add(r['split'])
    assert all(len(v) == 1 for v in g.values()) and len({r['case_id'] for r in R}) == len(R)

def test_sizes_are_about_40_20_40_per_dataset():
    R = rows(); n = collections.Counter(r['dataset'] for r in R); t = collections.Counter((r['dataset'], r['split']) for r in R)
    for ds in n:
        assert abs(t[(ds, 'dev')] / n[ds] - 0.4) < 0.05 and abs(t[(ds, 'val')] / n[ds] - 0.2) < 0.05 and abs(t[(ds, 'test')] / n[ds] - 0.4) < 0.05

def test_near_duplicate_clusters_are_not_split():
    R = {r['case_id']: r for r in rows()}
    for l in open(os.path.join(splits.ROOT, 'duplicates.jsonl')):
        d = json.loads(l)
        if d['dist'] <= 4 and d['ds_a'] == d['ds_b'] and d['a'] in R and d['b'] in R: assert R[d['a']]['split'] == R[d['b']]['split']

def test_load_logs_test_access_but_not_dev(tmp_path, monkeypatch):
    monkeypatch.setattr(splits, 'LOG', str(tmp_path / 'test_access.log'))
    splits.load('dev', script='t'); assert not os.path.exists(splits.LOG)
    t = splits.load('test', script='my_script.py'); line = open(splits.LOG).read()
    assert 'my_script.py' in line and 'split=test' in line and all(r['split'] == 'test' for r in t)
