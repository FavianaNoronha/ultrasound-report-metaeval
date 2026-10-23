import numpy as np
from usmeta import location, bench_loc

def test_iou_identical_disjoint_and_known_overlap():
    a = [0, 0, 10, 10]
    assert location.box_iou(a, a) == 1.0 and location.box_iou(a, [20, 20, 30, 30]) == 0.0
    assert abs(location.box_iou(a, [5, 0, 15, 10]) - 50 / 150) < 1e-9          # half overlap -> 50 / (100 + 100 - 50)
    m = np.zeros((10, 10), bool); m[:5] = True; n = np.zeros((10, 10), bool); n[:, :5] = True
    assert location.mask_iou(m, m) == 1.0 and location.dice(m, m) == 1.0 and abs(location.mask_iou(m, n) - 25 / 75) < 1e-9 and abs(location.dice(m, n) - 0.5) < 1e-9

def test_best_match_is_order_independent_and_penalises_missing_boxes():
    g = [[0, 0, 10, 10], [50, 50, 60, 60]]
    assert location.best_match_iou(g, g[::-1]) == 1.0
    assert abs(location.best_match_iou(g, [g[0]]) - 0.5) < 1e-9 and location.best_match_iou(g, []) == 0.0 and location.best_match_iou([], []) == 1.0

def test_inside_fraction():
    m = np.zeros((20, 20), bool); m[5:15, 5:15] = True
    assert location.inside_fraction([5, 5, 15, 15], m) == 1.0 and abs(location.inside_fraction([0, 0, 10, 10], m) - 0.25) < 1e-9

def test_planted_box_errors_hit_their_iou_bands():
    import random
    gt = [[100.0, 100.0, 160.0, 140.0]]; W, H = 400, 300; rng = random.Random(0)
    assert location.best_match_iou(gt, bench_loc.jitter(gt, W, H, rng)) >= 0.85
    assert abs(location.best_match_iou(gt, bench_loc.to_iou(gt, 0.5, W, H)) - 0.5) < 0.05
    assert abs(location.best_match_iou(gt, bench_loc.to_iou(gt, 0.2, W, H)) - 0.2) < 0.05
    assert location.best_match_iou(gt, bench_loc.wrong_side(gt, W, H)) == 0.0
