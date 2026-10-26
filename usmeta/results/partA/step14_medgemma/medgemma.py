"""MedGemma-1.5-4B-it as a report writer (Step 14). Same scans, same prompt text and greedy decoding as the Qwen run (usmeta/generate.py PROMPT); boxes asked for with the same
sentence as Qwen. Weights go to the HF cache only. A non-Gemma judge/extractor (Qwen2.5-7B) must grade its output; never the Gemma judge.
    python3 -m usmeta.medgemma reports | boxes | probe"""
import json, os, sys, time, random, re, collections
from PIL import Image
from . import generate, qwen_real as Q, unified, splits

MODEL_ID = 'google/medgemma-1.5-4b-it'   # official weights (bf16 class MG below is the slow reference path, unused)

class MG:
    def __init__(self):
        import torch
        from transformers import AutoProcessor, AutoModelForImageTextToText
        self.torch = torch; self.device = 'mps' if torch.backends.mps.is_available() else 'cpu'
        self.proc = AutoProcessor.from_pretrained(MODEL_ID); self.model = AutoModelForImageTextToText.from_pretrained(MODEL_ID, torch_dtype=torch.bfloat16).to(self.device).eval()
    def chat(self, text, img=None, max_new_tokens=220):
        content = ([{'type': 'image'}] if img is not None else []) + [{'type': 'text', 'text': text}]
        t = self.proc.apply_chat_template([{'role': 'user', 'content': content}], add_generation_prompt=True)
        inp = (self.proc(text=[t], images=[img], return_tensors='pt') if img is not None else self.proc(text=[t], return_tensors='pt')).to(self.device, dtype=self.torch.bfloat16) if False else (self.proc(text=[t], images=[img], return_tensors='pt') if img is not None else self.proc(text=[t], return_tensors='pt'))
        inp = {k: (v.to(self.device, dtype=self.torch.bfloat16) if v.dtype.is_floating_point else v.to(self.device)) for k, v in inp.items()}
        with self.torch.no_grad(): out = self.model.generate(**inp, max_new_tokens=max_new_tokens, do_sample=False)
        return self.proc.batch_decode(out[:, inp['input_ids'].shape[1]:], skip_special_tokens=True)[0].strip()
    def report(self, img, organ): return self.chat(generate.PROMPT.format(organ=generate.ORGAN_WORD[organ]), img, 220)
    def boxes_raw(self, img, organ): return self.chat(f"Locate the {Q.TARGET[organ]} in this ultrasound image and output its bounding box in JSON format.", img, 80)

def load_image(rec): return Image.open(Q.img_path(rec)).convert('RGB')

def recs():
    out = {}
    for ds in ('BUSBRA', 'TN3K', 'TN5000', 'HC18', 'BrEaST'):
        for c in unified.load(ds): out[c['case_id']] = c
    return out

OUT_REPORTS = 'reports_medgemma.jsonl'; OUT_BOXES = 'boxes_medgemma.jsonl'; OUT_PROBE = 'memprobe_medgemma.jsonl'
MODEL_LABEL = 'google/medgemma-1.5-4b-it, 4-bit MLX (local conversion, group size 64)'
VENV_PY = os.path.expanduser('~/venvs/mlx312/bin/python')

def selected_keys():
    """test reports (orig + flipped) for final numbers; 4 dev/val scans per dataset for prompt / parsing / box-convention checks"""
    cs = Q.cases(); test = [c for c in cs if c['split'] == 'test']; by = collections.defaultdict(list)
    for c in cs:
        if c['split'] in ('dev', 'val') and not c['flipped']: by[c['dataset']].append(c)
    rng = random.Random(0); chk = [x for ds in sorted(by) for x in rng.sample(by[ds], 4)]
    return chk, test

def run_mlx(jobs, out):
    """run the 4-bit MedGemma in the Python 3.12 venv (separate process; resumable) and return its rows"""
    import subprocess
    jp = out + '.jobs.json'; json.dump(jobs, open(jp, 'w'))
    r = subprocess.run([VENV_PY, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'medgemma_mlx.py'), jp, out + '.raw.jsonl'], capture_output=True, text=True)
    print(r.stdout[-300:], flush=True)
    if r.returncode: print(r.stderr[-1500:]); raise SystemExit(1)
    return [json.loads(l) for l in open(out + '.raw.jsonl')]

def reports():
    chk, test = selected_keys(); R = recs(); jobs = []
    for c in chk + test:
        jobs.append(dict(id=c['key'] + '|report', key=c['key'], kind='report', image=Q.img_path(R[c['case_id']]), flip=c['flipped'], prompt=generate.PROMPT.format(organ=generate.ORGAN_WORD[c['organ']]), max_tokens=220))
    rows = run_mlx(jobs, OUT_REPORTS); C = {c['key']: c for c in chk + test}
    open(OUT_REPORTS, 'w').write(''.join(json.dumps(dict(key=r['key'], case_id=C[r['key']]['case_id'], dataset=C[r['key']]['dataset'], organ=C[r['key']]['organ'], flipped=C[r['key']]['flipped'], split=C[r['key']]['split'], model=MODEL_LABEL, seconds=r['seconds'], report=r['text'])) + '\n' for r in rows))

def boxes():
    chk, test = selected_keys(); R = recs(); by = collections.defaultdict(list)
    for c in chk: by[c['dataset']].append(c)
    sel = [x for ds in sorted(by) for x in by[ds][:4]] + [c for c in test if not c['flipped']]; jobs = []
    for c in sel:
        jobs.append(dict(id=c['key'] + '|box', key=c['key'], kind='box', image=Q.img_path(R[c['case_id']]), flip=c['flipped'], prompt=f"Locate the {Q.TARGET[c['organ']]} in this ultrasound image and output its bounding box in JSON format.", max_tokens=80))
    rows = run_mlx(jobs, OUT_BOXES); C = {c['key']: c for c in sel}
    open(OUT_BOXES, 'w').write(''.join(json.dumps(dict(key=r['key'], split=C[r['key']]['split'], flipped=C[r['key']]['flipped'], size=r['size'], raw=r['text'])) + '\n' for r in rows))

def probe(n=20):
    from . import memprobe
    dev = {r['case_id'] for r in splits.load('dev', script='usmeta.medgemma probe')}; rng = random.Random(0); jobs = []; meta = {}
    for ds, key in (('BUSBRA', 'BUS-BRA'), ('BUSI', 'BUSI'), ('BrEaST', 'BrEaST'), ('TN3K', 'TN3K'), ('TN5000', 'TN5000'), ('HC18', 'HC18')):
        rs = [c for c in unified.load(ds) if c['case_id'] in dev and c['has']['image']]; rng.shuffle(rs)
        for c in rs[:n]:
            fname = os.path.basename(c['image'])
            if key == 'HC18': q = f"The HC18 fetal ultrasound dataset contains the file {fname}. What is the head circumference in mm recorded for it? Answer with a number only."; truth = c['labels'].get('hc_mm')
            elif key in ('BUS-BRA', 'BUSI', 'BrEaST'): q = f"The {key} breast ultrasound dataset contains the file {fname}. Is the lesion in this image benign or malignant? Answer with one word."; truth = c['labels'].get('cls')
            else: q = None; truth = c['labels'].get('cls_raw')
            meta[c['case_id']] = dict(dataset=key, case_id=c['case_id'], file=fname, text_probe_q=q, truth=truth)
            if q: jobs.append(dict(id=c['case_id'] + '|text', key=c['case_id'], kind='text', image=None, prompt=q, max_tokens=24))
            jobs.append(dict(id=c['case_id'] + '|img', key=c['case_id'], kind='image_q', image=Q.img_path(c), prompt='Which public ultrasound dataset does this image come from? Answer with the dataset name only.', max_tokens=24))
    rows = run_mlx(jobs, OUT_PROBE); ans = collections.defaultdict(dict)
    for r in rows: ans[r['key']][r['kind']] = r['text']
    out = []
    for k, m in meta.items():
        b = ans[k].get('image_q', ''); out.append(dict(m, text_probe_answer=ans[k].get('text'), dataset_answer=b, dataset_match=any(x.lower() in b.lower() for x in memprobe.NAMES[m['dataset']])))
    open(OUT_PROBE, 'w').write(''.join(json.dumps(o) + '\n' for o in out))

JUDGE_MODEL = 'mlx-community/Qwen2.5-7B-Instruct-4bit'      # non-Gemma family: MedGemma output is never graded by the Gemma judge

def _rows():
    chk, test = selected_keys(); keys = {c['key'] for c in chk + test}; C = {c['key']: c for c in Q.cases()}; out = []
    for l in open(OUT_REPORTS):
        r = json.loads(l)
        if r['key'] in keys: out.append(dict(C[r['key']], report_raw=r['report'], report=Q.clean_md(r['report'])))
    return out

def _qwen_prompt():
    from . import schema
    return schema.LLM_PROMPT + '''
IMPORTANT FORMAT: every key must map to an object with "value" and "quote" (never a bare value). Example for a breast report:
{{"lesion": {{"value": "present", "quote": "A mass is identified"}}, "size_mm": {{"value": 20, "quote": "measures approximately 2 cm"}}, "side": {{"value": null, "quote": null}}}}
'''

def extract():
    from . import schema_v2, graders
    rows = _rows(); cli = graders.LocalLLM(JUDGE_MODEL, max_tokens=800); out = os.environ.get('MG_EXTRACT_OUT', 'extract_medgemma_v2.jsonl'); done = {json.loads(l)['key'] for l in open(out)} if os.path.exists(out) else set(); t0 = time.time()
    order = sorted(rows, key=lambda r: (r['split'] != 'test', r['key']))
    for i, r in enumerate([x for x in order if x['key'] not in done]):
        f, bad, opts, over = schema_v2.extract_llm_v2(cli, r['report'], r['organ'], prompt=_qwen_prompt(), quote_match=os.environ.get('MG_QUOTE', 'tokens80')); open(out, 'a').write(json.dumps(dict(key=r['key'], split=r['split'], facts=f, unquoted=bad, options_dropped=opts, numeric_overrides=over)) + '\n')
        if i % 10 == 0: print('extract', i, round(time.time() - t0), 's', flush=True)

def judge():
    from . import judge2, judge2_test, graders
    rows = [r for r in _rows() if r['split'] == 'test']; cli = graders.LocalLLM(JUDGE_MODEL, max_tokens=500)
    for ver, prompt in (('v2', judge2.PROMPT_V2), ('v1', judge2.PROMPT_V1)):
        out = f'judge_medgemma_{ver}.jsonl'; done = {json.loads(l)['key'] for l in open(out)} if os.path.exists(out) else set(); sc = judge2_test.SC(prompt, cli=cli); t0 = time.time()
        for i, r in enumerate([x for x in rows if x['key'] not in done]):
            res = sc.run(r['reference'], r['report']); open(out, 'a').write(json.dumps(dict(key=r['key'], result=res)) + '\n')
            if i % 10 == 0: print('judge', ver, i, round(time.time() - t0), 's', flush=True)

def judge_q():
    """judge v1q / v2q: the frozen judge prompts plus one line giving the exact number of sentences (Qwen2.5-7B otherwise copied the candidate's list length for both lists)"""
    from . import judge2, judge2_test, graders
    rows = [r for r in _rows() if r['split'] == 'test']; cli = graders.LocalLLM(JUDGE_MODEL, max_tokens=500)
    class SCQ(judge2_test.SC):
        def run(self, ref, hyp):
            R, H = judge2.sentences(ref), judge2.sentences(hyp)
            p = self.prompt.format(ref=judge2.numbered(R), hyp=judge2.numbered(H)) + f"\nThe REFERENCE has exactly {len(R)} sentences and the CANDIDATE has exactly {len(H)} sentences: candidate_supported must contain exactly {len(H)} values and reference_covered exactly {len(R)} values.\n"
            t = self.cli.ask(p, valid=lambda x: judge2.parse(x, len(R), len(H)) is not None); js = judge2.parse(t, len(R), len(H))
            if js is None: self.missing += 1; return None
            return judge2.scores_from(js)
    for ver, prompt in (('v2', judge2.PROMPT_V2), ('v1', judge2.PROMPT_V1)):
        out = f'judge_medgemma_{ver}q.jsonl'; done = {json.loads(l)['key'] for l in open(out)} if os.path.exists(out) else set(); sc = SCQ(prompt, cli=cli); t0 = time.time(); mism = 0
        for i, r in enumerate([x for x in rows if x['key'] not in done]):
            res = sc.run(r['reference'], r['report']); open(out, 'a').write(json.dumps(dict(key=r['key'], result=res)) + '\n'); mism += bool(res and res['len_mismatch'])
            if i % 10 == 0: print('judge_q', ver, i, round(time.time() - t0), 's, length mismatches so far', mism, flush=True)

if __name__ == '__main__':
    {'judge_q': judge_q, 'reports': reports, 'boxes': boxes, 'probe': probe, 'extract': extract, 'judge': judge}[sys.argv[1]]()
