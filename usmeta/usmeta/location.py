"""Step 8 (Layer 3): location / size check against the TRUE masks (no model, no SAM yet: that is Part B).
Loader per dataset -> GT mask (or None), GT boxes [x1, y1, x2, y2] in original pixels.
box_iou / mask_iou / dice; best-match IoU for several lesions uses the Hungarian algorithm (scipy.optimize.linear_sum_assignment), unmatched
boxes count as IoU 0 on the side that has more boxes. HC18: head circumference from the filled ellipse (Ramanujan) with mm error.
"""
import os, glob, csv, json, zipfile
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.optimize import linear_sum_assignment
from . import unified

def box_iou(a, b):
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0])); iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1])); inter = ix * iy
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0.0

def mask_iou(a, b):
    a, b = np.asarray(a, bool), np.asarray(b, bool); u = (a | b).sum()
    return float((a & b).sum() / u) if u else 1.0

def dice(a, b):
    a, b = np.asarray(a, bool), np.asarray(b, bool); s = a.sum() + b.sum()
    return float(2 * (a & b).sum() / s) if s else 1.0

def best_match_iou(gt, pred):
    """mean IoU over max(len(gt), len(pred)) boxes after optimal (Hungarian) one-to-one matching; unmatched = 0"""
    if not gt and not pred: return 1.0
    if not gt or not pred: return 0.0
    M = np.array([[box_iou(g, p) for p in pred] for g in gt]); r, c = linear_sum_assignment(-M)
    return float(M[r, c].sum() / max(len(gt), len(pred)))

def inside_fraction(box, mask):
    """share of a box's area that lies inside a binary mask"""
    x0, y0, x1, y1 = [int(round(v)) for v in box]; x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, mask.shape[1]), min(y1, mask.shape[0])
    if x1 <= x0 or y1 <= y0: return 0.0
    area = (box[2] - box[0]) * (box[3] - box[1])
    return float(mask[y0:y1, x0:x1].sum() / area) if area > 0 else 0.0

def boxes_of(mask, min_frac=0.05):
    lab, n = ndimage.label(mask)
    if n == 0: return []
    areas = np.asarray(ndimage.sum(mask, lab, range(1, n + 1))); out = []
    for i, a in enumerate(areas):
        if a >= max(20, min_frac * areas.max()):
            ys, xs = np.where(lab == i + 1); out.append([float(xs.min()), float(ys.min()), float(xs.max() + 1), float(ys.max() + 1)])
    return out

def ramanujan_hc(a_full, b_full): return unified.ramanujan(a_full / 2, b_full / 2)

def hc_error_mm(mask, pixel_mm, hc_mm):
    ys, xs = np.where(mask); ev = np.sort(np.linalg.eigvalsh(np.cov(np.vstack([xs, ys]))))
    est = ramanujan_hc(4 * np.sqrt(ev[1]), 4 * np.sqrt(ev[0])) * pixel_mm
    return abs(est - hc_mm), est

def _p(*a): return os.path.join(*a)

def gt_mask(rec):
    """true binary mask for a unified record, or None (TN5000 = boxes only; records without lesion)"""
    ds, cid = rec['dataset'], rec['case_id'].split(':', 1)[1]; img = rec['image']; f = unified.load_mask
    try:
        if ds == 'BrEaST':
            root = os.path.dirname(unified.find('BrEaST-Lesions_USG-images_and_masks/' + os.path.basename(img)))
            p = _p(root, os.path.basename(img).replace('.png', '_tumor.png')); return f(p) if os.path.exists(p) else None
        if ds == 'BUS-BRA':
            root = _p(unified.find('archive-5'), 'BUSBRA', 'BUSBRA'); p = _p(root, 'Masks', 'mask_' + cid.split('_', 1)[1] + '.png'); return f(p) if os.path.exists(p) else None
        if ds == 'BUSI':
            root = unified.find('Dataset_BUSI_with_GT'); c, stem = cid.split('/', 1); m = None
            for mf in glob.glob(_p(root, c, glob.escape(stem) + '_mask*.png')):
                x = f(mf); m = x if m is None else (m | x if m.shape == x.shape else m)
            return m
        if ds == 'UDIAT':
            p = _p(unified.find('archive-4'), 'UDIAT_Dataset_B', 'UDIAT_Dataset_B', 'GT', cid + '.png'); return f(p) if os.path.exists(p) else None
        if ds == 'BUS-UCLM':
            root = _p(unified.find('archive-8'), 'BUS-UCLM Breast ultrasound lesion segmentation dataset', 'BUS-UCLM Breast ultrasound lesion segmentation dataset', 'BUS-UCLM')
            p = _p(root, 'masks', cid + '.png'); return f(p) if os.path.exists(p) else None
        if ds == 'TN3K':
            sp, fn = cid.split('/', 1); p = _p(unified.find('archive-6'), f'{sp}-mask', fn); return f(p) if os.path.exists(p) else None
        if ds == 'HC18':
            p = _p(unified.find('archive-7'), 'training_set', cid + '_Annotation.png'); return ndimage.binary_fill_holes(f(p)) if os.path.exists(p) else None
        if ds == 'FetalHead':
            for plane in ('Trans-cerebellum', 'Trans-thalamic', 'Trans-ventricular'):
                p = _p(unified.CACHE, plane, 'SegmentationClass', cid + '.png')
                if os.path.exists(p): return np.all(np.array(Image.open(p).convert('RGB')) == np.array((255, 0, 0)), axis=-1)
        if ds == 'DDTI':
            r = rec['region']
            if not r: return None
            m = np.zeros((r['H'], r['W']), bool); x0, y0, x1, y1 = [int(v) for v in r['box']]
            return None   # outline polygons are re-drawn by unified.ddti only; boxes from the record are used instead
    except Exception: return None
    return None

def gt_boxes(rec, mask=None):
    r = rec.get('region')
    if not r: return []
    return [list(map(float, b)) for b in r['boxes']]
