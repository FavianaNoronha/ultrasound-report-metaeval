"""Unit tests for the pure helpers of Part B (usmeta/partb.py): prompt boxes, jitter, largest region, Hausdorff, contrast. No model is loaded."""
import numpy as np
from usmeta import partb

def disk(n, cx, cy, r):
    y, x = np.ogrid[:n, :n]; return (x - cx) ** 2 + (y - cy) ** 2 <= r * r

def test_box_of_and_largest_region():
    m = np.zeros((40, 40), bool); m[5:15, 10:30] = True; m[30:33, 30:33] = True
    assert partb.box_of(m) == [10.0, 5.0, 33.0, 33.0]
    t = partb.largest(m); assert t.sum() == 200 and partb.box_of(t) == [10.0, 5.0, 30.0, 15.0]

def test_jitter_exact_is_identity_and_is_deterministic_and_inside_image():
    b = [20.0, 30.0, 60.0, 70.0]
    assert partb.jitter_box(b, 0.0, 100, 100, 'k') == b
    a = partb.jitter_box(b, 0.2, 100, 100, 'case1'); assert a == partb.jitter_box(b, 0.2, 100, 100, 'case1')
    big = partb.jitter_box([0.0, 0.0, 100.0, 100.0], 0.2, 100, 100, 'x'); assert big[0] >= 0 and big[1] >= 0 and big[2] <= 100 and big[3] <= 100

def test_jitter_enlarges_by_the_fraction_and_shifts_centre_by_half_fraction():
    b = [40.0, 40.0, 60.0, 60.0]; a = partb.jitter_box(b, 0.1, 200, 200, 'z'); w, h = a[2] - a[0], a[3] - a[1]
    assert abs(w - 22.0) < 1e-9 and abs(h - 22.0) < 1e-9
    assert abs(abs((a[0] + a[2]) / 2 - 50) - 1.0) < 1e-9 and abs(abs((a[1] + a[3]) / 2 - 50) - 1.0) < 1e-9

def test_hausdorff_zero_for_identical_and_grows_with_shift():
    a = disk(80, 40, 40, 15); assert partb.hausdorff(a, a) == (0.0, 0.0)
    b = disk(80, 50, 40, 15); hd, hd95 = partb.hausdorff(a, b); assert 9 <= hd <= 11 and hd95 <= hd
    assert all(np.isnan(partb.hausdorff(a, np.zeros_like(a))))

def test_contrast_is_high_for_a_bright_lesion_on_dark_background_and_zero_for_flat():
    m = disk(80, 40, 40, 10); g = np.full((80, 80), 50.0); g[m] = 200.0
    assert partb.contrast(g, m) > 0.5 and partb.contrast(np.full((80, 80), 90.0), m) == 0.0

def test_case_aurocs_pooling_excludes_fetal_head_for_lesions():
    V = [dict(case_id='a', dataset='BUSI', group='g1', kind='error', field='pos', s=0.0), dict(case_id='a', dataset='BUSI', group='g1', kind='harmless', field=None, s=1.0),
         dict(case_id='b', dataset='HC18', group='g2', kind='error', field='pos', s=1.0), dict(case_id='b', dataset='HC18', group='g2', kind='harmless', field=None, s=0.0)]
    assert partb.case_aurocs(V, 's', 'position errors', 'LESIONS')[0] == [1.0] and sorted(partb.case_aurocs(V, 's', 'position errors')[0]) == [0.0, 1.0]
