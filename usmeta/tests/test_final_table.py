"""Smoke test: the final combined table builds from the saved result files and keeps its marks (no hand-typed numbers)."""
import os
from usmeta import final_table

def test_final_table_builds_and_has_marks(tmp_path, monkeypatch):
    root = os.path.join(os.path.dirname(__file__), '..'); monkeypatch.chdir(root)
    import importlib; importlib.reload(final_table)
    out = tmp_path / 'final.md'; final_table.main(str(out)); t = out.read_text()
    assert '## A. Templated benchmark' in t and '## B. Real VLM-written reports' in t and '## C. HiSBreast' in t
    assert 'upper bound, templated' in t and 'too small to compare' in t and 'nan' not in t
    assert t.count('#### ') == 10          # one table per dataset
