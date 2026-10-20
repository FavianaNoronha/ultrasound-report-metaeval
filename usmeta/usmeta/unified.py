"""Unified case records: every dataset converted to ONE format, with capability flags.

A case is a dict:
  case_id, dataset, organ, group_id (patient/exam if known, else a stand-in), image (path), pixel_mm (mm per pixel or None),
  region (None or dict from mask/box/ellipse: kind, n, box, boxes, W, H, area_px, area_frac, cx, cy, pos, major_px, minor_px),
  labels (cls = benign/malignant/normal or class 0/1 raw, birads, tirads, hist, desc{...}), text (None or doctor-written text),
  has (flags: image, region, mm, cls, desc, grade, text).
Nothing is invented: missing = None / False. Output goes to usmeta/local_data/<dataset>.jsonl (git-ignored).
Usage:  python3 -m usmeta.unified build [names...]   |   python3 -m usmeta.unified table   |   python3 -m usmeta.unified check
"""
import os, sys, re, json, csv, glob, zipfile, collections
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(HERE, '..', 'local_data')
CACHE = os.path.expanduser('~/.cache/usmeta/seg')


def find(name):
    """Locate a data folder/file by name under the usual download locations (USMETA_DATA first)."""
    roots = [os.environ.get('USMETA_DATA', ''), '~/Downloads', '~/mnt/Downloads', '~/mnt']
    for r in roots:
        if not r: continue
        p = os.path.join(os.path.expanduser(r), name)
        if os.path.exists(p): return p
    raise FileNotFoundError(name)


def load_mask(path):
    # any colour channel on = lesion (BUS-UCLM paints benign green, malignant red; others are plain white)
    return np.array(Image.open(path).convert('RGB')).max(axis=-1) > 127


def region_feats(m, kind='mask'):
    """Features of a binary mask: components, main box, size, centre (thirds -> position), axes in pixels."""
    H, W = m.shape
    lab, n = ndimage.label(m)
    if n == 0: return None
    areas = np.asarray(ndimage.sum(m, lab, range(1, n + 1)))
    big = areas.max()
    keep = [i + 1 for i, a in enumerate(areas) if a >= max(20, 0.05 * big)]
    boxes = []
    for i in keep:
        ys, xs = np.where(lab == i)
        boxes.append([int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1])
    mi = int(np.argmax([areas[i - 1] for i in keep]))
    ys, xs = np.where(lab == keep[mi])
    cx, cy = float(xs.mean() / W), float(ys.mean() / H)
    ev = np.sort(np.linalg.eigvalsh(np.cov(np.vstack([xs, ys])))) if len(xs) > 2 else np.array([0., 0.])
    v = 'upper' if cy < 1 / 3 else 'middle' if cy < 2 / 3 else 'lower'
    h = 'left' if cx < 1 / 3 else 'central' if cx < 2 / 3 else 'right'
    tot = float(sum(areas[i - 1] for i in keep))
    return dict(kind=kind, n=len(keep), box=boxes[mi], boxes=boxes, W=W, H=H, area_px=int(tot), area_frac=tot / (H * W),
                cx=cx, cy=cy, pos=f'{v}-{h}', major_px=float(4 * np.sqrt(max(ev[1], 0))), minor_px=float(4 * np.sqrt(max(ev[0], 0))))


def box_region(boxes, W, H):
    boxes = [list(map(float, b)) for b in boxes]
    ar = [(b[2] - b[0]) * (b[3] - b[1]) for b in boxes]
    b = boxes[int(np.argmax(ar))]
    cx, cy = (b[0] + b[2]) / 2 / W, (b[1] + b[3]) / 2 / H
    v = 'upper' if cy < 1 / 3 else 'middle' if cy < 2 / 3 else 'lower'
    h = 'left' if cx < 1 / 3 else 'central' if cx < 2 / 3 else 'right'
    return dict(kind='box', n=len(boxes), box=b, boxes=boxes, W=W, H=H, area_px=int(sum(ar)), area_frac=sum(ar) / (W * H),
                cx=cx, cy=cy, pos=f'{v}-{h}', major_px=max(b[2] - b[0], b[3] - b[1]), minor_px=min(b[2] - b[0], b[3] - b[1]))


def case(ds, organ, cid, image, group=None, pixel_mm=None, region=None, text=None, **labels):
    labels = {k: v for k, v in labels.items() if v not in (None, '', {})}
    desc = labels.get('desc')
    has = dict(image=bool(image and os.path.exists(image)), region=region is not None, mm=pixel_mm is not None,
               cls=any(k in labels for k in ('cls', 'cls_raw')), desc=bool(desc), grade=any(k in labels for k in ('birads', 'tirads')),
               text=bool(text))
    return dict(case_id=f'{ds}:{cid}', dataset=ds, organ=organ, group_id=str(group) if group is not None else None, image=image,
                pixel_mm=pixel_mm, region=region, labels=labels, text=text, has=has)


def _norm_cls(s):
    s = str(s).strip().lower()
    return {'benign': 'benign', 'malignant': 'malignant', 'malign': 'malignant', 'normal': 'normal'}.get(s)


# ---------------------------------------------------------------- breast
def brest():
    # Pixel_size in breast.xlsx is centimetres per pixel (inferred: lesion median 13 mm as cm, 1.3 mm as mm); stored here as mm per pixel.
    import openpyxl
    root = find('BrEaST-Lesions_USG-images_and_masks')
    ws = openpyxl.load_workbook(os.path.join(REPO, 'baseline_exp', 'breast.xlsx'), read_only=True).active
    rows = list(ws.iter_rows(values_only=True)); hd = rows[0]
    for r in rows[1:]:
        d = dict(zip(hd, r))
        if not d.get('CaseID'): continue
        img = os.path.join(root, d['Image_filename']); mk = d.get('Mask_tumor_filename')
        reg = region_feats(load_mask(os.path.join(root, mk))) if mk and os.path.exists(os.path.join(root, str(mk))) else None
        desc = {k.lower(): str(d[k]).strip().lower() for k in ('Tissue_composition', 'Shape', 'Margin', 'Echogenicity', 'Posterior_features',
                                                              'Halo', 'Calcifications', 'Skin_thickening') if d.get(k) not in (None, '')}
        yield case('BrEaST', 'breast', d['CaseID'], img, group=d['CaseID'], pixel_mm=(float(d['Pixel_size']) * 10 if d.get('Pixel_size') else None), region=reg,
                   cls=_norm_cls(d.get('Classification')), birads=str(d.get('BIRADS')) if d.get('BIRADS') is not None else None,
                   desc=desc, age=d.get('Age'))


def bus_bra():
    root = os.path.join(find('archive-5'), 'BUSBRA', 'BUSBRA')
    for d in csv.DictReader(open(os.path.join(root, 'bus_data.csv'), encoding='utf-8-sig')):
        img = os.path.join(root, 'Images', d['ID'] + '.png'); mk = os.path.join(root, 'Masks', 'mask_' + d['ID'].split('_', 1)[1] + '.png')
        reg = region_feats(load_mask(mk)) if os.path.exists(mk) else None
        yield case('BUS-BRA', 'breast', d['ID'], img, group=d['Case'], region=reg, cls=_norm_cls(d['Pathology']), birads=d['BIRADS'],
                   hist=d['Histology'].strip().lower(), side=d['Side'].strip().lower())


def busi():
    root = find('Dataset_BUSI_with_GT')
    for c in ('benign', 'malignant', 'normal'):
        for f in sorted(os.listdir(os.path.join(root, c))):
            if '_mask' in f or not f.endswith('.png'): continue
            stem = f[:-4]; m = None
            for mf in glob.glob(os.path.join(root, c, glob.escape(stem) + '_mask*.png')):
                x = load_mask(mf); m = x if m is None else (m | x if m.shape == x.shape else m)
            reg = region_feats(m) if m is not None and m.any() else None
            yield case('BUSI', 'breast', f'{c}/{stem}', os.path.join(root, c, f), group=None, region=reg, cls=c)


def udiat():
    root = os.path.join(find('archive-4'), 'UDIAT_Dataset_B', 'UDIAT_Dataset_B')
    import openpyxl
    rows = list(openpyxl.load_workbook(os.path.join(root, 'DatasetB.xlsx'), read_only=True).active.iter_rows(values_only=True))
    for r in rows[1:]:
        if not r[0]: continue
        i = str(r[0]).zfill(6); img = os.path.join(root, 'original', i + '.png'); mk = os.path.join(root, 'GT', i + '.png')
        reg = region_feats(load_mask(mk)) if os.path.exists(mk) else None
        yield case('UDIAT', 'breast', i, img, group=None, region=reg, cls=_norm_cls(r[1]), hist=str(r[2]).strip().lower() if r[2] else None)


def bus_uclm():
    root = os.path.join(find('archive-8'), 'BUS-UCLM Breast ultrasound lesion segmentation dataset',
                        'BUS-UCLM Breast ultrasound lesion segmentation dataset', 'BUS-UCLM')
    for d in csv.DictReader(open(os.path.join(root, 'INFO.csv'), encoding='utf-8-sig'), delimiter=';'):
        f = d['Image']; mk = os.path.join(root, 'masks', f)
        reg = region_feats(load_mask(mk)) if os.path.exists(mk) else None
        yield case('BUS-UCLM', 'breast', f[:-4], os.path.join(root, 'images', f), group=f.split('_')[0], region=reg,
                   cls=_norm_cls(d['Label']), doppler=d['Doppler'], marks=d['Marks'])


def hisbreast():
    """Text only. Streams each JSON from the zip and keeps just exam id, conclusion and clinical diagnosis (images dropped)."""
    z = zipfile.ZipFile(find('HiSBreast.zip'))
    for jn in sorted(n for n in z.namelist() if n.startswith('json/') and n.endswith('.json')):
        recs = json.loads(z.read(jn))['RECORDS']
        base = os.path.basename(jn)
        for k, r in enumerate(recs):
            txt = (r.get('MO_TA') or '').replace('<br />', ' ').strip()
            yield case('HiSBreast', 'breast', f'{base}_{k}', f'zip:images/{base}_{k}.png', group=r.get('SO_PHIEU_CDHA'),
                       text=dict(lang='vi', raw=txt) if txt else None, dx=(r.get('CHANDOANBENH') or '').strip())
        del recs


# ---------------------------------------------------------------- thyroid
def tn3k():
    root = find('archive-6')
    for r in json.load(open(os.path.join(REPO, 'baseline_exp', 'tn3k_records.json'))):
        sp = r['split']; f = r['file']
        img = os.path.join(root, f'{sp}-image', f); mk = os.path.join(root, f'{sp}-mask', f)
        reg = region_feats(load_mask(mk)) if os.path.exists(mk) else None
        yield case('TN3K', 'thyroid', f'{sp}/{f}', img, group=None, region=reg, cls_raw=r['path'], split=sp)


def tn5000():
    import xml.etree.ElementTree as ET
    root = find('TN5000_forReview')
    for fp in sorted(glob.glob(os.path.join(root, 'Annotations', '*.xml'))):
        r = ET.parse(fp).getroot(); W = int(r.find('size/width').text); H = int(r.find('size/height').text)
        objs = r.findall('object'); names = {o.find('name').text.strip() for o in objs}
        bx = [[float(o.find('bndbox/' + k).text) for k in ('xmin', 'ymin', 'xmax', 'ymax')] for o in objs]
        reg = box_region(bx, W, H) if bx else None
        stem = os.path.basename(fp)[:-4]
        yield case('TN5000', 'thyroid', stem, os.path.join(root, 'JPEGImages', stem + '.jpg'), group=None, region=reg,
                   cls_raw=('class ' + names.copy().pop()) if len(names) == 1 else None)


def ddti():
    import xml.etree.ElementTree as ET
    root = find('archive-9')
    for fp in sorted(glob.glob(os.path.join(root, '*.xml')), key=lambda p: int(os.path.basename(p)[:-4])):
        num = os.path.basename(fp)[:-4]
        try: r = ET.parse(fp).getroot()
        except ET.ParseError: continue
        g = lambda t: (r.findtext(t) or '').strip().lower() or None
        desc = {k: g(k) for k in ('composition', 'echogenicity', 'margins', 'calcifications') if g(k)}
        for mark in r.findall('mark'):
            idx = (mark.findtext('image') or '').strip(); img = os.path.join(root, f'{num}_{idx}.jpg')
            if not os.path.exists(img): continue
            W, H = Image.open(img).size; reg = None
            try: regions = json.loads(mark.findtext('svg') or '[]')
            except Exception: regions = []
            if regions:
                im = Image.new('L', (W, H), 0); dr = ImageDraw.Draw(im)
                for rg in regions:
                    pts = [(p['x'], p['y']) for p in rg.get('points', [])]
                    if len(pts) >= 3: dr.polygon(pts, fill=255)
                reg = region_feats(np.array(im) > 127, kind='outline')
            yield case('DDTI', 'thyroid', f'{num}_{idx}', img, group=num, region=reg, tirads=g('tirads'), desc=desc,
                       age=g('age'), sex=g('sex'))


# ---------------------------------------------------------------- fetal head
def hc18():
    root = find('archive-7'); rows = list(csv.DictReader(open(os.path.join(root, 'training_set_pixel_size_and_HC.csv'), encoding='utf-8-sig')))
    for d in rows:
        f = d['filename']; img = os.path.join(root, 'training_set', f)
        an = os.path.join(root, 'training_set', f.replace('.png', '_Annotation.png'))
        reg = region_feats(ndimage.binary_fill_holes(load_mask(an)), kind='ellipse') if os.path.exists(an) else None
        yield case('HC18', 'fetal', f[:-4], img, group=None, pixel_mm=float(d['pixel size(mm)']), region=reg,
                   hc_mm=float(d['head circumference (mm)']))


def fetal_planes():
    base = find('Trans-cerebellum').rsplit('/', 1)[0]
    cols = {'brain': (255, 0, 0), 'csp': (0, 255, 0), 'lv': (0, 0, 255)}
    for plane in ('Trans-cerebellum', 'Trans-thalamic', 'Trans-ventricular'):
        pdir = os.path.join(base, plane); seg = (glob.glob(os.path.join(pdir, '*egmentation*.zip')) or [None])[0]
        out = os.path.join(CACHE, plane)
        if seg and not os.path.isdir(os.path.join(out, 'SegmentationClass')):
            os.makedirs(out, exist_ok=True); zipfile.ZipFile(seg).extractall(out)
        pix = {}
        pc = glob.glob(os.path.join(pdir, '*ixel*.csv'))[0]
        for row in csv.reader(open(pc, encoding='utf-8-sig')):
            try: pix[row[0].strip()] = float(row[1])
            except (ValueError, IndexError): pass
        for f in sorted(os.listdir(os.path.join(pdir, plane))):
            if not f.endswith('.png'): continue
            mk = os.path.join(out, 'SegmentationClass', f); reg = None; structs = {}
            if os.path.exists(mk):
                rgb = np.array(Image.open(mk).convert('RGB'))
                for nm, c in cols.items():
                    m = np.all(rgb == np.array(c), axis=-1)
                    if m.any():
                        structs[nm] = region_feats(m)
                reg = structs.get('brain')
                if reg: reg = dict(reg, structs={k: v for k, v in structs.items() if k != 'brain'})
            yield case('FetalHead', 'fetal', f[:-4], os.path.join(pdir, plane, f), group=f.split('_')[0], pixel_mm=pix.get(f), region=reg, plane=plane)


ADAPTERS = dict(BrEaST=brest, BUSBRA=bus_bra, BUSI=busi, UDIAT=udiat, BUSUCLM=bus_uclm, HiSBreast=hisbreast,
                TN3K=tn3k, TN5000=tn5000, DDTI=ddti, HC18=hc18, FetalHead=fetal_planes)


def build(names):
    os.makedirs(OUT, exist_ok=True)
    for n in names:
        p = os.path.join(OUT, n + '.jsonl'); k = 0
        with open(p, 'w') as fh:
            for c in ADAPTERS[n]():
                fh.write(json.dumps(c) + '\n'); k += 1
        print(n, k, 'cases ->', os.path.relpath(p), flush=True)


def load(name): return [json.loads(l) for l in open(os.path.join(OUT, name + '.jsonl'))]


def table():
    print(f"{'dataset':10} {'cases':>6} {'groups':>6} {'region':>7} {'mm':>5} {'class':>6} {'desc':>5} {'grade':>6} {'text':>5}  region kinds")
    for n in ADAPTERS:
        p = os.path.join(OUT, n + '.jsonl')
        if not os.path.exists(p): print(n, '(not built)'); continue
        cs = load(n); N = len(cs); pc = lambda k: f"{100 * sum(c['has'][k] for c in cs) / N:5.0f}%"
        kinds = dict(collections.Counter((c['region'] or {}).get('kind', 'none') for c in cs))
        gr = len({c['group_id'] for c in cs if c['group_id']})
        print(f"{n:10} {N:6} {gr or '-':>6} {pc('region'):>7} {pc('mm'):>5} {pc('cls'):>6} {pc('desc'):>5} {pc('grade'):>6} {pc('text'):>5}  {kinds}")


def ramanujan(a, b): return np.pi * (3 * (a + b) - np.sqrt((3 * a + b) * (a + 3 * b)))


def check():
    """Sanity checks that our measuring works: HC18 ellipse vs the published head circumference; BrEaST pixel-size unit."""
    cs = [c for c in load('HC18') if c['region']]
    err = []
    for c in cs:
        r = c['region']; a, b = r['major_px'] / 2, r['minor_px'] / 2
        err.append(abs(ramanujan(a, b) * c['pixel_mm'] - c['labels']['hc_mm']))
    print(f'HC18: {len(cs)} head outlines; our circumference from the outline vs the dataset value: median abs error {np.median(err):.2f} mm, 90th pct {np.percentile(err, 90):.2f} mm')
    bs = [c for c in load('BrEaST') if c['region'] and c['pixel_mm']]
    d = np.array([c['region']['major_px'] * c['pixel_mm'] for c in bs])
    print(f'BrEaST: median lesion longest diameter = {np.median(d):.1f} mm  ({len(bs)} lesions; pixel size converted from cm)')
    for n in ('TN3K', 'BUSI', 'BUS-BRA'.replace('-', ''), 'BUSUCLM', 'UDIAT', 'DDTI', 'FetalHead', 'TN5000'):
        p = os.path.join(OUT, n + '.jsonl')
        if not os.path.exists(p): continue
        cs = load(n); miss = [c for c in cs if not c['has']['image']]
        print(f'{n}: images missing on disk {len(miss)}/{len(cs)}; cases without region {sum(not c["has"]["region"] for c in cs)}')


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'table'
    if cmd == 'build': build(sys.argv[2:] or [n for n in ADAPTERS if n != 'HiSBreast'])
    elif cmd == 'table': table()
    elif cmd == 'check': check()
