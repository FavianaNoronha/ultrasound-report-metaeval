"""Step 11 (Qwen real reports): run the 200 Qwen2.5-VL-3B free-text reports (+ the 20 flip-test reports) through the frozen Layers 1-3 against the true reports.
New file; frozen code untouched. Extractor/judge = Gemma-2-9B (a different family from the writer). Choices on dev/val only; final numbers on test.
    python3 -m usmeta.qwen_real prep | extract_check | extract_test | judge | boxes | analyse"""
import json, re, os, sys, random, collections, time
from . import splits, schema, graders, judge2, judge2_test, location, unified

OUTD = 'qwen_real_work'
def uid(c):
    if c.startswith('BUS-BRA'): return 'BUS-BRA:' + c[len('BUS-BRA-'):]
    if c.startswith('TN3K'): r = c[len('TN3K-'):]; sp = 'trainval' if r.startswith('trainval') else 'test'; return f'TN3K:{sp}/' + r[len(sp):]
    if c.startswith('TN5000'): return 'TN5000:' + c[len('TN5000-'):].replace('.jpg', '')
    if c.startswith('HC18'): return 'HC18:' + c[len('HC18-'):].replace('.png', '')

def clean_md(t):
    """strip markdown (headings, bold, list numbers) so sentence splitting and the extractor see plain text; no content is removed"""
    t = re.sub(r'^\s*#+\s*', '', t, flags=re.M); t = t.replace('**', '').replace('*', '')
    t = re.sub(r'^\s*(\d+\.|-)\s+', '', t, flags=re.M); t = re.sub(r'[ \t]+', ' ', t)
    return ' '.join(x.strip() for x in t.split('\n') if x.strip())

def prep():
    os.makedirs(OUTD, exist_ok=True); tr = {}
    for l in open('true_reports_v2d.jsonl'): r = json.loads(l); tr[r['case_id']] = r
    allsplit = {r['case_id']: (r['split'], r['group_id']) for r in splits.load(None, script='usmeta.qwen_real')}
    rows = []
    for fn, flipped in (('reports_qwen.jsonl', False), ('reports_qwen_flip.jsonl', True)):
        for l in open(fn):
            r = json.loads(l); u = uid(r['case_id']); t = tr[u]; sp, g = allsplit[u]
            rows.append(dict(key=f"{u}|{'flip' if flipped else 'orig'}", case_id=u, dataset=t['dataset'], organ=t['organ'], flipped=flipped, split=sp, group_id=g, reference=t['styles']['standard'], ref_facts=t['facts'], report_raw=r['report'], report=clean_md(r['report'])))
    json.dump(rows, open(f'{OUTD}/cases.json', 'w')); print(len(rows), collections.Counter((r['split'], r['flipped']) for r in rows))

def cases(): return json.load(open(f'{OUTD}/cases.json'))

# ---- independent regex readings used ONLY to cross-check the LLM extractor on free text
def regex_reading(t):
    tl = t.lower(); o = {}
    L, Rr = bool(re.search(r'\bleft\b', tl)), bool(re.search(r'\bright\b', tl))
    if L != Rr: o['side'] = 'left' if L else 'right'
    m = re.search(r'bi-?rads(?: category)?[^0-9a-z]{0,12}([0-6][abc]?)\b', tl)
    if m: o['birads'] = m[1]
    m = re.search(r'(\d+(?:\.\d+)?)\s*(mm|cm)\b', tl)
    if m: o['size_mm'] = float(m[1]) * (10 if m[2] == 'cm' else 1)
    mass = bool(re.search(r'\b(mass|nodule|lesion|cyst|tumou?r)\b', tl)); neg = bool(re.search(r'\bno (?:focal |discrete |definite |obvious )?(?:mass|nodule|lesion|abnormal)|within normal limits|appears normal|normal (?:size|appearance)', tl))
    if mass and not neg: o['lesion'] = 'present'
    elif neg and not mass: o['lesion'] = 'absent'
    return o

def extract_llm_batch(rows, out):
    cli = graders.LocalLLM('mlx-community/gemma-2-9b-it-4bit', max_tokens=800); done = {json.loads(l)['key'] for l in open(out)} if os.path.exists(out) else set(); t0 = time.time()
    for i, r in enumerate([x for x in rows if x['key'] not in done]):
        f, bad = schema.extract_llm(cli, r['report'], r['organ']); open(out, 'a').write(json.dumps(dict(key=r['key'], facts=f, unquoted=bad)) + '\n')
        if i % 10 == 0: print(i, round(time.time() - t0), 's', flush=True)

def extract_check(n=10):
    rows = [r for r in cases() if r['split'] in ('dev', 'val') and not r['flipped']]; rng = random.Random(0); by = collections.defaultdict(list)
    for r in rows: by[r['dataset']].append(r)
    sel = [x for ds in sorted(by) for x in rng.sample(by[ds], n)]; json.dump([r['key'] for r in sel], open(f'{OUTD}/check_keys.json', 'w')); extract_llm_batch(sel, f'{OUTD}/extract_check.jsonl')


def extract_test():
    rows = [r for r in cases() if r['split'] == 'test']; extract_llm_batch(rows, f'{OUTD}/extract_test.jsonl')

def judge():
    """Gemma sentence_check, prompt_v2 and prompt_v1, on TEST pairs (reference true report vs cleaned Qwen report)"""
    rows = [r for r in cases() if r['split'] == 'test']
    for ver, prompt in (('v2', judge2.PROMPT_V2), ('v1', judge2.PROMPT_V1)):
        out = f'{OUTD}/judge_{ver}.jsonl'; done = {json.loads(l)['key'] for l in open(out)} if os.path.exists(out) else set(); sc = judge2_test.SC(prompt); t0 = time.time()
        for i, r in enumerate([x for x in rows if x['key'] not in done]):
            res = sc.run(r['reference'], r['report']); open(out, 'a').write(json.dumps(dict(key=r['key'], result=res)) + '\n')
            if i % 10 == 0: print(ver, i, round(time.time() - t0), 's', flush=True)

# ---------------------------------------------------------------- Qwen boxes (grounding prompt; coordinates are absolute on the resized input -> rescaled)
TARGET = {'breast': 'breast lesion', 'thyroid': 'thyroid nodule', 'fetal': 'fetal head'}
def img_path(rec): return rec['image'].replace(rec['image'].split('/mnt/Downloads')[0] + '/mnt/Downloads', os.path.expanduser('~/Downloads')) if '/mnt/Downloads' in rec['image'] else rec['image']

def parse_boxes(txt):
    out = []
    for m in re.finditer(r'"bbox_2d"\s*:\s*\[\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\]', txt): out.append([float(m[i]) for i in range(1, 5)])
    if not out:
        for m in re.finditer(r'\[\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\]', txt): out.append([float(m[i]) for i in range(1, 5)])
    return out

def qwen_boxes(w, img, organ):
    from PIL import Image
    q = f"Locate the {TARGET[organ]} in this ultrasound image and output its bounding box in JSON format."
    t = w.proc.apply_chat_template([{'role': 'user', 'content': [{'type': 'image'}, {'type': 'text', 'text': q}]}], add_generation_prompt=True)
    inp = w.proc(text=[t], images=[img], return_tensors='pt').to(w.device); thw = inp['image_grid_thw'][0].tolist(); rh, rw = thw[1] * 14, thw[2] * 14
    with w.torch.no_grad(): out = w.model.generate(**inp, max_new_tokens=80, do_sample=False)
    raw = w.proc.batch_decode(out[:, inp['input_ids'].shape[1]:], skip_special_tokens=True)[0].strip(); W, H = img.size
    return raw, [[b[0] * W / rw, b[1] * H / rh, b[2] * W / rw, b[3] * H / rh] for b in parse_boxes(raw)], (rw, rh)

def boxes():
    from PIL import Image
    from . import generate
    rows = cases(); rng = random.Random(0); recs = {}
    for ds in ('BUSBRA', 'TN3K', 'TN5000', 'HC18'):
        for c in unified.load(ds): recs[c['case_id']] = c
    test = [r for r in rows if r['split'] == 'test']                                        # final numbers (originals + flipped)
    dev = [r for r in rows if r['split'] == 'dev' and not r['flipped']]; by = collections.defaultdict(list)
    for r in dev: by[r['dataset']].append(r)
    devs = [x for ds in sorted(by) for x in rng.sample(by[ds], 5)]                         # 20 dev scans: parse check before looking at test
    w = generate.Writer('qwen'); out = f'{OUTD}/boxes.jsonl'; done = {json.loads(l)['key'] for l in open(out)} if os.path.exists(out) else set(); t0 = time.time()
    for i, r in enumerate([x for x in devs + test if x['key'] not in done]):
        rec = recs[r['case_id']]; img = Image.open(img_path(rec)).convert('RGB'); W = img.size[0]
        if r['flipped']: img = img.transpose(Image.FLIP_LEFT_RIGHT)
        raw, bx, size = qwen_boxes(w, img, r['organ'])
        if r['flipped']: bx = [[W - b[2], b[1], W - b[0], b[3]] for b in bx]            # mirror back to the original orientation
        open(out, 'a').write(json.dumps(dict(key=r['key'], split=r['split'], raw=raw, boxes=bx, resized=size)) + '\n')
        if i % 10 == 0: print(i, round(time.time() - t0), 's', flush=True)

if __name__ == '__main__':
    {'prep': prep, 'extract_check': extract_check, 'boxes': boxes, 'extract_test': extract_test, 'judge': judge}[sys.argv[1]]()
