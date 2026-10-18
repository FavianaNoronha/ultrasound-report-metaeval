"""Turn raw annotation files into the small record lists the builders use."""
import json, collections

def ultrag_thyroid_records(jsonl_path, max_records=None):
    """UltraG-Bench thyroid annotations -> records (ds, path, count, loc, ratio). Keeps nodule samples with a clear
    benign/malignant label. Annotation files are text only (no images)."""
    recs = []; skipped = collections.Counter()
    for line in open(jsonl_path):
        d = json.loads(line)
        nod = [m for m in d['masks'] if m.get('target_type') == 'nodule']
        if not nod: skipped['no nodule mask'] += 1; continue
        paths = {m.get('pathology_label') for m in nod}
        if paths not in ({'benign'}, {'malignant'}): skipped['pathology unclear'] += 1; continue
        nod.sort(key=lambda m: -m.get('mask_area_px', 0))
        recs.append(dict(ds=d['dataset'], file=str(d.get('id', len(recs))), path=paths.pop(), count=len(nod),
                         loc=nod[0].get('location_grid', 'middle-central'), ratio=sum(m.get('area_ratio', 0) for m in nod)))
    print('ultrag thyroid usable', len(recs), 'skipped', dict(skipped))
    return recs


def tn5000_records(root, max_records=None):
    """TN5000 (VOC-style XML boxes) -> thyroid records. Class names 0/1 are kept as 'class 0'/'class 1' (meaning not
    confirmed by us). Skips images whose boxes carry mixed classes. size ratio = largest box area / image area."""
    import glob, os, xml.etree.ElementTree as ET
    recs = []; skipped = collections.Counter()
    for fp in sorted(glob.glob(os.path.join(root, 'Annotations', '*.xml'))):
        r = ET.parse(fp).getroot(); w = int(r.find('size/width').text); h = int(r.find('size/height').text)
        objs = r.findall('object')
        if not objs: skipped['no box'] += 1; continue
        names = {o.find('name').text.strip() for o in objs}
        if len(names) != 1 or names.copy().pop() not in ('0', '1'): skipped['mixed or odd class'] += 1; continue
        bx = []
        for o in objs:
            b = o.find('bndbox'); x0, y0, x1, y1 = (float(b.find(k).text) for k in ('xmin', 'ymin', 'xmax', 'ymax'))
            bx.append(((x1 - x0) * (y1 - y0) / (w * h), (x0 + x1) / 2 / w, (y0 + y1) / 2 / h))
        a, cx, cy = max(bx)
        v = 'upper' if cy < 1/3 else 'middle' if cy < 2/3 else 'lower'; hz = 'left' if cx < 1/3 else 'central' if cx < 2/3 else 'right'
        recs.append(dict(ds='TN5000', split='', file=os.path.basename(fp)[:-4] + '.jpg', path='class ' + names.pop(),
                         count=len(objs), loc=f'{v}-{hz}', ratio=a))
    print('tn5000 usable', len(recs), 'skipped', dict(skipped))
    return recs
