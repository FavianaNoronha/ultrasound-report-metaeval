"""Tests for Step 47 amendment 2. Run on the Mac:
PYTHONPATH=usmeta .venv/bin/python -m pytest usmeta/tests/test_step47_amendment2.py
"""
import pytest

from usmeta import step46_eval as s46
from usmeta import step47_audit_route as s47


def row(severity=None, kind="error"):
    return dict(
        organ="breast", severity=severity, kind=kind, group="g1", case="c1",
        gold={"path": "benign", "birads": "3", "size_pct": 20},
        ref="ref", cand="cand",
    )


@pytest.mark.parametrize("planted", [None, 1, 2, 3])
def test_severity_never_read_from_planted_label(planted):
    base = s47.v5_v6_scores(row(None), {"birads": "x", "size_pct": "x"})
    assert s47.v5_v6_scores(row(planted), {"birads": "x", "size_pct": "x"}) == base
    for field in ("path", "birads", "size_pct"):
        assert s46.severity_for("breast", field, s47.blind(row(planted))) == s46.severity_for(
            "breast", field, row(None)
        )


def test_v5_merges_size_concepts_and_v6_has_no_floor():
    v5, v6 = s47.v5_v6_scores(row(), {"size_mm": "x", "size_pct": "x"})
    single, _ = s47.v5_v6_scores(row(), {"size_pct": "x"})
    assert v5 == single
    many = {"path": "x", "birads": "x", "size_pct": "x", "margin": "x", "calc": "x"}
    v5_many, v6_many = s47.v5_v6_scores(row(), many)
    assert 0.0 < v6_many < 1.0


def test_paper_exact_crqs_extremes():
    perfect = s47.crqs_paper_exact(row(), {"path": "benign", "birads": "3", "size_pct": 20})
    assert perfect["normalized"] == pytest.approx(1.0)
    wrong = s47.crqs_paper_exact(row(), {"path": "malignant"})
    assert wrong["raw"] == pytest.approx(-0.6)
    assert wrong["normalized"] == pytest.approx(-0.6 / 0.7)
    assert wrong["clipped"] == 0.0


def test_clopper_pearson_and_miss_rate():
    assert s47.clopper_pearson_upper(0, 400) < 0.02
    assert s47.clopper_pearson_upper(5, 400) > 0.02
    rows = [dict(row(severity=3), v3_route=(i % 100 != 0)) for i in range(400)]
    out = s47.miss_rate_h1(rows)
    assert out["n_major_or_critical"] == 400
    assert out["misses"] == 4
