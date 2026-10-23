"""bench_loc: location / size extension of bench_v2d. Candidates are TEXT + BOX(ES) (boxes = what a grounded report writer would output).
Per case (100 per dataset with a region; seed 0):
  identical            text = reference, boxes = true boxes
  harmless             same text + jittered boxes (IoU >= 0.85);  synonym-reworded text + jittered boxes
  error / box_only     text unchanged, boxes moved to IoU ~0.5 (severity 1), ~0.2 (2), 0 on the wrong side of the image (3)
  error / text_pos     text states a wrong image position (from bench_v2d), boxes CORRECT         (text-location error)
  error / text_pos_box text states a wrong image position AND the boxes moved to match the wrong text (consistent but wrong)
  error / size         text size x0.5 / x1.5 / x2 (or HC +3/+10/-10/+30 mm), boxes correct
Severity is PROVISIONAL (box IoU bands; bench_v2d rules for text errors)."""
import json, random, collections, sys
import numpy as np
from . import location, unified

def clip(b, W, H): return [max(0.0, b[0]), max(0.0, b[1]), min(float(W), b[2]), min(float(H), b[3])]

def shift(boxes, dx, dy, W, H): return [clip([b[0] + dx, b[1] + dy, b[2] + dx, b[3] + dy], W, H) for b in boxes]

def jitter(boxes, W, H, rng, tries=50):
    for _ in range(tries):
        out = []
        for b in boxes:
            w, h = b[2] - b[0], b[3] - b[1]; dx, dy = rng.uniform(-.06, .06) * w, rng.uniform(-.06, .06) * h; s = rng.uniform(.95, 1.05)
            cx, cy = (b[0] + b[2]) / 2 + dx, (b[1] + b[3]) / 2 + dy; out.append(clip([cx - w * s / 2, cy - h * s / 2, cx + w * s / 2, cy + h * s / 2], W, H))
        if location.best_match_iou(boxes, out) >= 0.85: return out
    return boxes

def to_iou(boxes, target, W, H):
    """shift ALL boxes sideways so a single box of width w reaches IoU ~ target; direction = the side with more room"""
    big = max(boxes, key=lambda b: (b[2] - b[0]) * (b[3] - b[1])); w = big[2] - big[0]; cx = (big[0] + big[2]) / 2
    d = w * (1 - target) / (1 + target) if target > 0 else w * 1.2
    sign = 1 if (W - cx) >= cx else -1
    out = shift(boxes, sign * d, 0, W, H)
    if location.best_match_iou(boxes, out) > target + 0.15 and target > 0: out = shift(boxes, -sign * d, 0, W, H)
    return out

def wrong_side(boxes, W, H):
    """mirror the boxes about the image centre and push them off the true lesion if they still overlap"""
    out = [clip([W - b[2], b[1], W - b[0], b[3]], W, H) for b in boxes]
    if location.best_match_iou(boxes, out) > 0.0: out = to_iou(boxes, 0.0, W, H)
    return out

THIRD = {'left': 1 / 6, 'central': 3 / 6, 'right': 5 / 6, 'upper': 1 / 6, 'middle': 3 / 6, 'lower': 5 / 6}
def move_to_pos(boxes, pos, W, H):
    """centre the boxes' union on the centre of the stated image third"""
    v, h = pos.split('-'); x0 = min(b[0] for b in boxes); x1 = max(b[2] for b in boxes); y0 = min(b[1] for b in boxes); y1 = max(b[3] for b in boxes)
    return shift(boxes, THIRD[h] * W - (x0 + x1) / 2, THIRD[v] * H - (y0 + y1) / 2, W, H)

def build(per_dataset=100, seed=0, bench='bench_v2d.jsonl', datasets=None):
    rng = random.Random(seed); B = collections.defaultdict(lambda: collections.defaultdict(list))
    for l in open(bench):
        r = json.loads(l); B[r['dataset']][r['case_id']].append(r)
    recs = {}
    for ds in (datasets or unified.ADAPTERS):
        if ds == 'HiSBreast': continue
        for c in unified.load(ds): recs[c['case_id']] = c
    out = []; counts = {}
    for ds, cases in B.items():
        ids = [c for c in sorted(cases) if recs.get(c) and recs[c]['region'] and recs[c]['region']['boxes']]; rng.shuffle(ids); ids = ids[:per_dataset]; counts[ds] = len(ids)
        for cid in ids:
            rs = cases[cid]; rec = recs[cid]; W, H = rec['region']['W'], rec['region']['H']; gt = [list(map(float, b)) for b in rec['region']['boxes']]
            ref = [r for r in rs if r['kind'] == 'identical'][0]['reference']; n = [0]
            def emit(kind, group, text, boxes, category=None, field=None, severity=0, magnitude=None, **kw):
                out.append(dict(id=f'{cid}#L{n[0]}', case_id=cid, dataset=ds, organ=rec['organ'], kind=kind, group=group, category=category, field=field, severity=severity,
                                magnitude=magnitude, reference=ref, candidate=text, boxes=boxes, gt_boxes=gt, W=W, H=H, **kw)); n[0] += 1
            emit('identical', 'identical', ref, gt)
            emit('harmless', 'box_jitter', ref, jitter(gt, W, H, rng))
            syn = [r for r in rs if r['kind'] == 'harmless' and r['group'] == 'synonyms']
            if syn: emit('harmless', 'synonyms_box_jitter', syn[0]['candidate'], jitter(gt, W, H, rng))
            for t, sev in ((0.5, 1), (0.2, 2)): emit('error', 'box_only', ref, to_iou(gt, t, W, H), 'wrong location', 'box', sev, t)
            emit('error', 'box_only', ref, wrong_side(gt, W, H), 'wrong location', 'box', 3, 0.0)
            for r in rs:
                if r['kind'] != 'error': continue
                if r['field'] == 'pos':
                    emit('error', 'text_pos', r['candidate'], gt, 'wrong location', 'pos', r['severity'], None, old=r['old'], new=r['new'])
                    emit('error', 'text_pos_box', r['candidate'], move_to_pos(gt, r['new'], W, H), 'wrong location', 'pos', r['severity'], None, old=r['old'], new=r['new'])
                elif r['field'] in ('size_mm', 'size_pct', 'hc_mm'):
                    emit('error', 'size', r['candidate'], gt, 'wrong measurement', r['field'], r['severity'], r['magnitude'], old=r['old'], new=r['new'])
    return out, counts

if __name__ == '__main__':
    rows, counts = build(); open('bench_loc.jsonl', 'w').write(''.join(json.dumps(r) + '\n' for r in rows)); print(len(rows), counts)
